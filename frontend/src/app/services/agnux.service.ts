import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';
import { AuthService } from './auth.service';

export interface AgnuxResponse {
  status: string;
  user: string;
  response: string;
  detail?: string;
}

@Injectable({
  providedIn: 'root'
})
export class AgnuxService {
  private apiUrl = 'http://10.10.0.66:8000/api/system/intent';

  public token$ = new Subject<string>();
  public eventStatus$ = new Subject<any>();

  constructor(private authService: AuthService) {}

  async enviarPromptStream(promptTexto: string, terminalId: string): Promise<void> {
    const userId = this.authService.getCurrentUser();
    
    if (!userId) {
      this.eventStatus$.next({ type: 'ERROR', message: 'ERROR: Terminal bloqueada. Inicie sesión.' });
      return;
    }

    try {
      const response = await fetch(this.apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: promptTexto, user_id: userId, terminal_id: terminalId })
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(`Backend responded with ${response.status}: ${text}`);
      }

      if (!response.body) {
        throw new Error('El Kernel no envió un flujo de datos válido.');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      let eventoActual = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lineas = buffer.split('\n');
        buffer = lineas.pop() || '';

        for (const linea of lineas) {
          const lineaLimpia = linea.trim();
          if (!lineaLimpia) continue;

          if (lineaLimpia.startsWith('event: ')) {
            eventoActual = lineaLimpia.substring(7).trim();
          } else if (lineaLimpia.startsWith('data: ')) {
            const dataRaw = lineaLimpia.substring(6);
            console.log("🔥 [AGNUX SERVICE] Raw data string recibido:", dataRaw, "para evento:", eventoActual);
            
            try {
              const dataObj = JSON.parse(dataRaw);
              console.log("🔥 [AGNUX SERVICE] Data parseada con éxito:", dataObj);
              
              if (eventoActual === 'CREATE_WINDOW' || (typeof dataObj === 'object' && (dataObj.window_id || dataObj.windowId))) {
                this.eventStatus$.next({ type: 'CREATE_WINDOW', data: dataObj });
              } else if (eventoActual === 'TOKEN') {
                this.token$.next(dataObj);
              } else if (eventoActual === 'ROUTER_START' || eventoActual === 'INFERENCE_START' || eventoActual === 'TOOL_EXECUTE') {
                this.eventStatus$.next({ type: eventoActual, msg: dataObj.message || dataObj });
              } else if (eventoActual === 'ROUTER_SCORE') {
                this.eventStatus$.next({ type: 'SCORE', tool: dataObj.tool, score: dataObj.score });
              } else if (eventoActual === 'TOOL_RESULT') {
                this.eventStatus$.next({ type: 'RESULT', data: dataObj.response || dataObj.data });
              } else if (eventoActual === 'ERROR') {
                this.eventStatus$.next({ type: 'ERROR', message: dataObj.message });
              } else {
                this.eventStatus$.next({ type: 'UNKNOWN', payload: { event: eventoActual, data: dataObj } });
              }
            } catch (e) {
              console.error("Error parsing data payload:", e);
            }
            eventoActual = ''; // Limpiar el estado tras consumir la data
          }
        }
      }
    } catch (error) {
      console.error('Falla en el bus de streaming local:', error);
      this.eventStatus$.next({ type: 'ERROR', message: (error as Error).message || 'Error de streaming' });
      throw error;
    }
  }
}