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

  listenTerminal(terminalId: string): Observable<string> {
    return new Observable<string>(observer => {
      console.log(`📡 [AGNUX KERNEL] Abriendo canal SSE para Terminal: ${terminalId}`);
      this.eventSource = new EventSource(`http://10.10.0.66:8000/api/auth/terminal-stream/${terminalId}`);

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
    return this.http.post('http://10.10.0.66:8000/api/auth/terminal-authorize', {
      terminal_id: terminalId,
      user_id: userId
    });
  }

  loginFacial(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    const req = this.http.post('http://10.10.0.66:8000/api/auth/facial-login', formData);
    
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
    const req = this.http.post('http://10.10.0.66:8000/api/auth/vocal-login', formData);
    
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
