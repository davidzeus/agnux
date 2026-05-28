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

  async enviarPromptStream(promptTexto: string): Promise<void> {
    const userId = this.authService.getCurrentUser();
    
    if (!userId) {
      this.eventStatus$.next({ type: 'ERROR', message: 'ERROR: Terminal bloqueada. Inicie sesión.' });
      return;
    }

    try {
      const response = await fetch(this.apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: promptTexto, user_id: userId })
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

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lineas = buffer.split('\n');
        buffer = lineas.pop() || '';

        for (const linea of lineas) {
          if (!linea.trim()) continue;

          try {
            const dataObj = JSON.parse(linea);

            switch (dataObj.event) {
              case 'TOKEN':
                this.token$.next(dataObj.text);
                break;
              case 'ROUTER_START':
              case 'INFERENCE_START':
              case 'TOOL_EXECUTE':
                this.eventStatus$.next({ type: dataObj.event, msg: dataObj.message });
                break;
              case 'ROUTER_SCORE':
                this.eventStatus$.next({ type: 'SCORE', tool: dataObj.tool, score: dataObj.score });
                break;
              case 'TOOL_RESULT':
                this.eventStatus$.next({ type: 'RESULT', data: dataObj.response });
                break;
              default:
                this.eventStatus$.next({ type: 'UNKNOWN', payload: dataObj });
                break;
            }
          } catch (_error) {
            // Ignoramos fragmentos JSON mal formateados en el corte del chunk
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