import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private socket: WebSocket | null = null;
  public notifications$ = new Subject<any>();

  constructor() {}

  public connect(terminalId: string, userId: string) {
    if (this.socket) {
      this.socket.close();
    }

    const wsUrl = `ws://10.10.0.66:8000/api/system/notifications/ws/${terminalId}/${userId}`;
    this.socket = new WebSocket(wsUrl);

    this.socket.onopen = () => {
      console.log(`🟢 [NOTIF BUS] WebSocket conectado exitosamente a ${wsUrl}`);
    };

    this.socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        console.log(`📩 [NOTIF BUS] Notificación recibida:`, payload);
        if (payload.type === 'notification') {
          this.notifications$.next(payload.data);
        } else if (payload.type === 'theme_update') {
          console.log(`🎨 [THEME ENGINE] Aplicando nuevo estilo dinámico...`);
          const variables = payload.data;
          for (const key in variables) {
            if (Object.prototype.hasOwnProperty.call(variables, key)) {
              document.documentElement.style.setProperty(key, variables[key]);
            }
          }
        }
      } catch (e) {
        console.error(`❌ [NOTIF BUS] Error parseando mensaje WS:`, e);
      }
    };

    this.socket.onerror = (error) => {
      console.error(`❌ [NOTIF BUS] Error en WebSocket:`, error);
    };

    this.socket.onclose = () => {
      console.warn(`🔴 [NOTIF BUS] WebSocket desconectado.`);
      this.socket = null;
    };
  }

  public disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }
}
