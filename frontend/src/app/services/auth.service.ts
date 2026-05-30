import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private getInitialUserId(): string | null {
    if (typeof localStorage !== 'undefined') {
      return localStorage.getItem('agnux_user_id');
    }
    return null;
  }

  private currentUserSubject = new BehaviorSubject<string | null>(this.getInitialUserId());
  public currentUser$ = this.currentUserSubject.asObservable();
  private eventSource: EventSource | null = null;

  constructor(private http: HttpClient) {}

  getCurrentUser(): string | null {
    return this.currentUserSubject.value;
  }

  verifyCloudflareAuth(): Observable<any> {
    console.log('🛡️ [AGNUX KERNEL] Verificando cabeceras de Cloudflare Access...');

    // Bypass para entorno de desarrollo local
    if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
      console.log('⚠️ [MODO DEV] Ejecutando en localhost. Simulando acceso Cloudflare...');
      const devUser = 'dev-local-admin';
      this.currentUserSubject.next(devUser);
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem('agnux_user', devUser);
      }
      return new Observable(obs => {
        obs.next({ status: 'authenticated', user_id: devUser });
        obs.complete();
      });
    }

    // Usamos ruta relativa para que funcione tanto en local como a través de agnux.net.ar
    const req = this.http.get('/api/auth/cloudflare/verify');
    
    req.subscribe({
      next: (res: any) => {
        if (res.status === 'authenticated' && res.user_id) {
          console.log(`✅ [AGNUX KERNEL] Identidad Cloudflare confirmada: ${res.user_id} (${res.email})`);
          if (typeof localStorage !== 'undefined') {
            localStorage.setItem('agnux_user_id', res.user_id);
          }
          this.currentUserSubject.next(res.user_id);
        }
      },
      error: (err) => console.log('⚠️ Sin cabeceras de Cloudflare (Modo Local/Fallback)', err)
    });
    
    return req;
  }

  checkGoogleAuthStatus(userId: string): Observable<{connected: boolean, userId: string}> {
    return this.http.get<{connected: boolean, userId: string}>(`/api/auth/google/status?user_id=${userId}`);
  }

  listenTerminal(terminalId: string): Observable<string> {
    return new Observable<string>(observer => {
      console.log(`📡 [AGNUX KERNEL] Abriendo canal SSE para Terminal: ${terminalId}`);
      this.eventSource = new EventSource(`/api/auth/terminal-stream/${terminalId}`);

      // Escucha el evento personalizado que dispara FastAPI al aprobar desde el celular
      this.eventSource.addEventListener('AUTH-SUCCESS', (event: any) => {
        const data = JSON.parse(event.data);
        console.log('🟢 [AGNUX KERNEL] Autenticación remota exitosa:', data);

        if (typeof localStorage !== 'undefined') {
          localStorage.setItem('agnux_user_id', data.userId);
        }
        this.currentUserSubject.next(data.userId);
        
        // Cierre controlado posterior al impacto del estado
        this.closeConnection();
        observer.next(data.userId);
      });

      this.eventSource.addEventListener('HEARTBEAT', (event: any) => {
        console.log('💓 [AGNUX KERNEL] Heartbeat de terminal recibido...');
      });

      this.eventSource.onerror = (error) => {
        console.error('❌ [AGNUX KERNEL] Error en el bus SSE de la terminal:', error);
      };
    });
  }

  authorizeTerminal(terminalId: string, userId: string): Observable<any> {
    return this.http.post('/api/auth/terminal-authorize', {
      terminal_id: terminalId,
      user_id: userId
    });
  }

  loginFacial(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    const req = this.http.post('/api/auth/facial-login', formData);
    
    req.subscribe({
      next: (res: any) => {
        if (res.status === 'authenticated' && res.user_id) {
          console.log('🟢 [AGNUX BIOMETRICS] Reconocimiento local exitoso:', res.user_id);
          if (typeof localStorage !== 'undefined') {
            localStorage.setItem('agnux_user_id', res.user_id);
          }
          this.currentUserSubject.next(res.user_id);
          this.closeConnection();
        }
      },
      error: () => {} // Ignorar errores de reconocimiento continuo
    });
    return req;
  }

  loginVocal(file: Blob): Observable<any> {
    const formData = new FormData();
    formData.append('file', file, 'audio.webm');
    const req = this.http.post('/api/auth/vocal-login', formData);
    
    req.subscribe({
      next: (res: any) => {
        if (res.status === 'authenticated' && res.user_id) {
          console.log('🎤 [AGNUX BIOMETRICS] Reconocimiento vocal exitoso:', res.user_id);
          if (typeof localStorage !== 'undefined') {
            localStorage.setItem('agnux_user_id', res.user_id);
          }
          this.currentUserSubject.next(res.user_id);
          this.closeConnection();
        }
      },
      error: (err) => console.error('Error en autenticación vocal:', err)
    });
    return req;
  }

  logoutForzado() {
    console.warn('⚠️ [AGNUX KERNEL] Logout forzado emitido (Fallo de Presencia / Invalidación).');
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem('agnux_user_id');
    }
    this.currentUserSubject.next(null);
    this.closeConnection();
  }

  closeConnection() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }
}
