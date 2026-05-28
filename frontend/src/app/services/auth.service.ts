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
      this.eventSource.addEventListener('AUTH_SUCCESS', (event: any) => {
        const data = JSON.parse(event.data);
        console.log('🟢 [AGNUX KERNEL] Autenticación remota exitosa:', data);
        
        if (typeof localStorage !== 'undefined') {
          localStorage.setItem('agnux_user_id', data.user_id);
        }
        this.currentUserSubject.next(data.user_id);
        
        observer.next(data.user_id);
        this.closeConnection();
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

  closeConnection() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }
}
