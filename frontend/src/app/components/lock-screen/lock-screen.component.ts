import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-lock-screen',
  templateUrl: './lock-screen.component.html',
  styleUrls: ['./lock-screen.component.css']
})
export class LockScreenComponent implements OnInit, OnDestroy {
  public terminalId: string = '';
  public qrUrl: string = '';
  private authSub: Subscription | null = null;

  constructor(private authService: AuthService, private router: Router) {}

  ngOnInit(): void {
    const currentUser = this.authService.getCurrentUser();
    
    if (currentUser) {
      // Si ya hay sesión en memoria, bypass directo al kernel
      this.router.navigate(['/']);
      return;
    }

    // Generar ID único para esta pantalla inerte
    this.terminalId = 'TERM_DESKTOP_' + Math.floor(Math.random() * 100000);
    this.qrUrl = `http://10.10.0.66:4200/authorize?terminal_id=${this.terminalId}`;
    
    console.log(`[AGNUX LOCK] Esperando validación remota para: ${this.terminalId}`);
    
    // Abrir canal de escucha SSE con el host
    this.authSub = this.authService.listenTerminal(this.terminalId).subscribe({
      next: (event) => {
        if (event.event === 'AUTH_SUCCESS') {
          console.log(`[AGNUX LOCK] Acceso concedido por el celular: ${event.user_id}`);
          this.router.navigate(['/']); // Redirección al entorno
        }
      },
      error: (err) => {
        console.error('[AGNUX LOCK] Error en el túnel de escucha', err);
      }
    });
  }

  ngOnDestroy(): void {
    if (this.authSub) {
      this.authSub.unsubscribe();
    }
  }
}
