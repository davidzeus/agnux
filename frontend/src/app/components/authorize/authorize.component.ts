import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-authorize',
  templateUrl: './authorize.component.html',
  styleUrls: ['./authorize.component.css']
})
export class AuthorizeComponent implements OnInit {
  public terminalId: string | null = null;
  public usernameInput: string = '';
  public statusMessage: string = '';
  public isSuccess: boolean = false;
  private currentUser: string | null = null;

  constructor(
    private route: ActivatedRoute,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    // 1. Extraer ID de la terminal desde la URL
    this.terminalId = this.route.snapshot.queryParamMap.get('terminal_id');
    
    // 2. Comprobar identidad local del celular
    this.currentUser = this.authService.getCurrentUser();

    // Si ya estamos logueados y escaneamos un QR, autorizamos de inmediato
    if (this.currentUser && this.terminalId) {
      this.procesarAutorizacion(this.terminalId, this.currentUser);
    }
  }

  // Se ejecuta al darle Enter al input de identidad
  public registrarEIngresar(): void {
    if (!this.usernameInput.trim() || !this.terminalId) return;
    
    // Formatear: Cristian -> user_cristian
    const cleanUser = 'user_' + this.usernameInput.trim().toLowerCase().replace(/\s+/g, '_');
    this.procesarAutorizacion(this.terminalId, cleanUser);
  }

  private procesarAutorizacion(termId: string, userId: string): void {
    this.statusMessage = 'Estableciendo enlace de red VPN...';
    
    this.authService.authorizeTerminal(termId, userId).subscribe({
      next: (res) => {
        this.isSuccess = true;
        this.statusMessage = 'Terminal autorizada. Puedes mirar la pantalla grande.';
        // Opcionalmente podemos guardar la sesión en el celular si fue manual
        if (!this.currentUser) {
          localStorage.setItem('agnux_user_id', userId);
        }
      },
      error: (err) => {
        this.isSuccess = false;
        this.statusMessage = 'ERROR DE ENLACE: La terminal caducó o no fue encontrada.';
        console.error('Falla autorizando', err);
      }
    });
  }
}
