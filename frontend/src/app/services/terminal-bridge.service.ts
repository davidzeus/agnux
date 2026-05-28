import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject } from 'rxjs';
import { AuthService } from './auth.service';

@Injectable({ providedIn: 'root' })
export class TerminalBridgeService {
  private apiUrl = 'http://localhost:8000/api/auth';
  private eventSource: EventSource | null = null;
  private retryTimeout: any = null;

  constructor(private http: HttpClient, private authService: AuthService) {}

  escucharDesbloqueoRemoto(terminalId: string): Observable<any> {
    const subject = new Subject<any>();

    const connect = () => {
      if (this.eventSource) {
        this.eventSource.close();
      }

      this.eventSource = new EventSource(`${this.apiUrl}/terminal-stream?terminal_id=${terminalId}`);

      this.eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.event === 'HEARTBEAT') {
            subject.next({ type: 'HEARTBEAT' });
          } else if (data.event === 'AUTH_SUCCESS') {
            const userId = data.user_id;
            this.authService.currentUser.set(userId);
            this.authService.isAuthenticated.set(true);
            subject.next({ type: 'AUTH_SUCCESS', user_id: userId });
            
            // Cerrar el canal después de una autenticación exitosa
            if (this.eventSource) {
                this.eventSource.close();
                this.eventSource = null;
            }
          }
        } catch (err) {
          console.error('Error parseando evento SSE terminal:', err);
        }
      };

      this.eventSource.onerror = (err) => {
        console.warn('Conexión SSE terminal perdida. Reintentando en 3s...', err);
        if (this.eventSource) {
            this.eventSource.close();
        }
        
        clearTimeout(this.retryTimeout);
        this.retryTimeout = setTimeout(() => connect(), 3000);
      };
    };

    connect();

    return subject.asObservable();
  }

  autorizarTerminalRemota(terminalId: string, userId: string): Observable<any> {
    const payload = { terminal_id: terminalId, user_id: userId };
    return this.http.post<any>(`${this.apiUrl}/terminal-authorize`, payload);
  }

  detenerEscucha() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    clearTimeout(this.retryTimeout);
  }
}
