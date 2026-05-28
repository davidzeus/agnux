import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  // Gestiona el estado del usuario activo
  private currentUserSubject = new BehaviorSubject<string | null>(localStorage.getItem('agnux_user_id'));
  public currentUser$ = this.currentUserSubject.asObservable();

  private backendUrl = 'http://10.10.0.66:8000/api/auth';

  constructor(private http: HttpClient) {}

  /**
   * Devuelve el ID del usuario en foco actualmente.
   */
  public getCurrentUser(): string | null {
    return this.currentUserSubject.value;
  }

  /**
   * Abre un canal SSE para escuchar cuando el celular autoriza el ingreso.
   */
  public listenTerminal(terminalId: string): Observable<any> {
    return new Observable((observer) => {
      const eventSource = new EventSource(`${this.backendUrl}/terminal-stream/${terminalId}`);

      eventSource.addEventListener('message', (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.event === 'AUTH_SUCCESS') {
            const userId = data.user_id;
            this.currentUserSubject.next(userId);
            localStorage.setItem('agnux_user_id', userId);
            
            observer.next(data);
            observer.complete();
            eventSource.close();
          } else if (data.event === 'HEARTBEAT') {
            console.log('[VPN BYPASS] Heartbeat recibido: Canal físico vivo.');
            observer.next(data);
          }
        } catch (error) {
          console.error('Error parseando evento SSE:', error);
        }
      });

      eventSource.onerror = (error) => {
        console.error('Error de red en el EventSource de la terminal', error);
        observer.error(error);
        eventSource.close();
      };

      return () => {
        eventSource.close();
      };
    });
  }

  /**
   * Es invocado por el dispositivo móvil vía WireGuard para destrabar la PC.
   */
  public authorizeTerminal(terminalId: string, userId: string): Observable<any> {
    return this.http.post(`${this.backendUrl}/terminal-authorize`, {
      terminal_id: terminalId,
      user_id: userId
    });
  }
}
