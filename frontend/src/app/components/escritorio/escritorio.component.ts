import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { AgnuxService } from '../../services/agnux.service';
import { Ventana } from '../../models/ventana.model';
import { VentanaComponent } from '../ventana/ventana.component';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-escritorio',
  standalone: true,
  imports: [
    CommonModule, 
    FormsModule, 
    VentanaComponent,
    MatIconModule,
    MatButtonModule
  ],
  templateUrl: './escritorio.component.html',
  styleUrls: ['./escritorio.component.css']
})
export class EscritorioComponent implements OnInit, OnDestroy {
  ventanas: Ventana[] = [];
  promptInput: string = '';
  cargando: boolean = false;
  private idCounter = 0;
  private maxZIndex = 100;
  private subscriptions: Subscription[] = [];
  public currentHtmlWindowId: string | null = null;

  constructor(private agnuxService: AgnuxService) {}

  ngOnInit() {
    this.subscriptions.push(
      this.agnuxService.eventStatus$.subscribe(status => {
        if (status.type === 'TOOL_EXECUTE') {
          const msg = status.msg || '';
          if (msg.includes('reproducir_musica')) {
            this.spawnVentana('musica', '🎵 AGNUX Media Player', { status: 'Playing...' });
          } else if (msg.includes('tool_reproductor_video')) {
            this.spawnVentana('video', '🎬 AGNUX Video Core', { url: '' });
          }
        } else if (status.type === 'INFERENCE_START') {
          this.currentHtmlWindowId = this.spawnVentana('html', '⚡ AGNUX OS Intelligence Output', null);
        } else if (status.type === 'ERROR') {
          this.spawnVentana('texto', '❌ Error de Sistema', { error: status.message });
        }
      })
    );

    this.subscriptions.push(
      this.agnuxService.token$.subscribe(token => {
        if (!this.currentHtmlWindowId) {
           this.currentHtmlWindowId = this.spawnVentana('html', '⚡ AGNUX OS Intelligence Output', null);
        }
        const win = this.ventanas.find(v => v.id === this.currentHtmlWindowId);
        if (win && win.tipo === 'html') {
          win.htmlDinamico = (win.htmlDinamico || '') + token;
          win.htmlDinamico = win.htmlDinamico.replace(/\*\*/g, '').replace(/```[a-zA-Z]*\n?/gi, '').replace(/```/g, '');
        }
      })
    );
  }

  ngOnDestroy() {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  spawnVentana(tipo: 'html' | 'musica' | 'video' | 'texto', titulo: string, datos: any): string {
    this.maxZIndex++;
    const id = `win_${this.idCounter++}`;
    // Si ya existe una ventana HTML, podemos reusarla, o crear una nueva
    if (tipo === 'html' && this.currentHtmlWindowId) {
      const existing = this.ventanas.find(v => v.id === this.currentHtmlWindowId);
      if (existing) {
        existing.htmlDinamico = ''; // Reset for new output
        this.enfocarVentana(existing);
        return existing.id;
      }
    }

    const nuevaVentana: Ventana = {
      id,
      titulo,
      tipo,
      datos,
      htmlDinamico: '',
      maximizada: false,
      x: 50 + (this.idCounter * 20),
      y: 50 + (this.idCounter * 20),
      zIndex: this.maxZIndex
    };
    this.ventanas.push(nuevaVentana);
    return id;
  }

  cerrarVentana(id: string) {
    this.ventanas = this.ventanas.filter(v => v.id !== id);
    if (this.currentHtmlWindowId === id) {
      this.currentHtmlWindowId = null;
    }
  }

  toggleMaximizar(win: Ventana) {
    win.maximizada = !win.maximizada;
    this.enfocarVentana(win);
  }

  enfocarVentana(win: Ventana) {
    this.maxZIndex++;
    win.zIndex = this.maxZIndex;
  }

  async ejecutarComando() {
    if (!this.promptInput.trim()) return;
    this.cargando = true;
    
    // Forzamos a abrir una ventana nueva por cada comando, desligando la actual
    this.currentHtmlWindowId = null;

    try {
      await this.agnuxService.enviarPromptStream(this.promptInput);
    } catch (err) {
      console.error(err);
      this.spawnVentana('texto', '❌ Error Local', { error: 'No se pudo conectar con AGNUX' });
    } finally {
      this.cargando = false;
      this.promptInput = ''; // Limpiar input
    }
  }

  async responderVentana(win: Ventana) {
    if (!win.replyInput?.trim()) return;
    win.cargandoRespuesta = true;

    const userText = win.replyInput;
    win.replyInput = '';

    // Mostrar visualmente la entrada del usuario en la consola
    win.htmlDinamico = (win.htmlDinamico || '') + `<br><br><span style="color: #fff; background: rgba(0,255,102,0.2); padding: 2px 4px; border-radius: 4px;">> ${userText}</span><br><br>`;

    // Reasignamos esta ventana como objetivo para el próximo stream
    this.currentHtmlWindowId = win.id;

    // Extraer texto limpio para el contexto
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = win.htmlDinamico;
    const contextText = tempDiv.innerText || tempDiv.textContent || '';

    const promptConContexto = `[CONTEXTO PREVIO DE LA CONVERSACIÓN]:
${contextText.slice(-1000)}

[NUEVA ENTRADA DEL USUARIO CONTINUANDO EL TEMA]:
${userText}`;

    try {
      await this.agnuxService.enviarPromptStream(promptConContexto);
    } catch (err) {
      console.error(err);
      win.htmlDinamico += `<br><span style="color: #ff3366;">[Error Local]</span>`;
    } finally {
      win.cargandoRespuesta = false;
    }
  }
}
