import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { AgnuxService } from '../../services/agnux.service';
import { Ventana } from '../../models/ventana.model';
import { SafeHtmlPipe, SafeUrlPipe } from '../../pipes/safe.pipe';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';

@Component({
  selector: 'app-escritorio',
  standalone: true,
  imports: [
    CommonModule, 
    FormsModule, 
    SafeHtmlPipe, 
    SafeUrlPipe,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatInputModule,
    MatFormFieldModule
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
  private currentHtmlWindowId: string | null = null;

  constructor(private agnuxService: AgnuxService) {}

  ngOnInit() {
    this.subscriptions.push(
      this.agnuxService.eventStatus$.subscribe(status => {
        if (status.type === 'TOOL_EXECUTE') {
          const msg = status.msg || '';
          if (msg.includes('reproducir_musica')) {
            this.spawnVentana('musica', '🎵 AGNUX Media Player', { status: 'Playing...' });
          } else if (msg.includes('tool_reproductor_video')) {
            this.spawnVentana('video', '🎬 AGNUX Video Core', { url: '' }); // Extract URL if needed
          }
        } else if (status.type === 'RESULT') {
          // Open or update HTML window
          this.currentHtmlWindowId = this.spawnVentana('html', '⚡ AGNUX OS Intelligence Output', null);
        } else if (status.type === 'ERROR') {
          this.spawnVentana('texto', '❌ Error de Sistema', { error: status.message });
        }
      })
    );

    this.subscriptions.push(
      this.agnuxService.token$.subscribe(token => {
        // Append token to the current HTML window if it exists
        if (this.currentHtmlWindowId) {
          const win = this.ventanas.find(v => v.id === this.currentHtmlWindowId);
          if (win && win.tipo === 'html') {
            win.htmlDinamico = (win.htmlDinamico || '') + token;
          }
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
    
    // Si hay una ventana HTML anterior, limpiamos
    if (this.currentHtmlWindowId) {
        const win = this.ventanas.find(v => v.id === this.currentHtmlWindowId);
        if (win && win.tipo === 'html') win.htmlDinamico = '';
    }

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
}
