import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AgnuxService } from '../../services/agnux.service';

@Component({
  selector: 'app-command-bar',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './command-bar.component.html',
  styleUrls: ['./command-bar.component.css']
})
export class CommandBarComponent {
  promptInput: string = '';
  respuestaIA: string = '';
  cargando: boolean = false;
  errorMsg: string = '';

  constructor(private agnuxService: AgnuxService) {}

  ejecutarComando() {
    if (!this.promptInput.trim()) return;

    this.cargando = true;
    this.respuestaIA = '';
    this.errorMsg = '';

    this.agnuxService.enviarPrompt(this.promptInput).subscribe({
      next: (res) => {
        if (res.status === 'success') {
          this.respuestaIA = res.response;
        } else {
          this.errorMsg = res.detail || 'Ocurrió un error inesperado.';
        }
        this.cargando = false;
      },
      error: (err) => {
        this.errorMsg = 'No se pudo conectar con el backend de AGNUX.';
        this.cargando = false;
        console.error(err);
      }
    });
  }
}