import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { AgnuxService } from '../../services/agnux.service';

@Component({
  selector: 'app-command-bar',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './command-bar.component.html',
  styleUrls: ['./command-bar.component.css']
})
export class CommandBarComponent implements OnInit, OnDestroy {
  promptInput: string = '';
  respuestaIA: string = '';
  cargando: boolean = false;
  errorMsg: string = '';
  statusMensaje: string = '';

  private subscriptions: Subscription[] = [];

  constructor(private agnuxService: AgnuxService) {}

  ngOnInit() {
    this.subscriptions.push(
      this.agnuxService.token$.subscribe(token => {
        this.respuestaIA += token;
      })
    );

    this.subscriptions.push(
      this.agnuxService.eventStatus$.subscribe(status => {
        switch (status.type) {
          case 'ROUTER_START':
            this.statusMensaje = '⚙️ Escaneando matriz local...';
            break;
          case 'INFERENCE_START':
            this.statusMensaje = '🧠 Ministral-es procesando...';
            break;
          case 'TOOL_EXECUTE':
            this.statusMensaje = status.msg || '🔧 Ejecutando herramienta...';
            break;
          case 'SCORE':
            this.statusMensaje = `📊 Score ${status.tool}: ${status.score}`;
            break;
          case 'RESULT':
            this.statusMensaje = '✅ Resultado de herramienta disponible.';
            break;
          case 'ERROR':
            this.statusMensaje = `❌ ${status.message}`;
            break;
          default:
            this.statusMensaje = '';
        }
      })
    );
  }

  ngOnDestroy() {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  async ejecutarComando() {
    if (!this.promptInput.trim()) return;

    this.cargando = true;
    this.respuestaIA = '';
    this.errorMsg = '';

    try {
      await this.agnuxService.enviarPromptStream(this.promptInput);
      this.statusMensaje = '🎯 Respuesta completa.';
    } catch (err) {
      this.errorMsg = 'No se pudo conectar con el backend de AGNUX.';
      console.error(err);
    } finally {
      this.cargando = false;
    }
  }
}