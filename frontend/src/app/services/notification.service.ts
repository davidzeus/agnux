import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';
import { ThemeService } from './theme.service';

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private socket: WebSocket | null = null;
  public notifications$ = new Subject<any>();

  constructor(private themeService: ThemeService) {}

  public connect(terminalId: string, userId: string) {
    if (this.socket) {
      this.socket.close();
    }

    // Detectar si usamos HTTPS para usar WSS (WebSocket Seguro)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/system/notifications/ws/${terminalId}/${userId}`;
    
    console.log(`[NOTIF BUS] Conectando a ${wsUrl}`);
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
          // Si recibimos texto o un bloque de CSS crudo
          const cssRaw = typeof payload.data === 'string' ? payload.data : payload.data.css;
          if (cssRaw) {
            this.themeService.injectRawCss(cssRaw);
          } else {
            console.error("❌ Formato CSS crudo inválido recibido del backend.");
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
