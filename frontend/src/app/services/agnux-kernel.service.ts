import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';
import { AuthService } from './auth.service';

export interface AgUiEvent {
  type: string;
  message?: string;
  text?: string;
  tool?: string;
  score?: number;
  data?: any;
}

@Injectable({ providedIn: 'root' })
export class AgnuxKernelService {
  private apiUrl = 'http://localhost:8000/api/system/intent';
  private eventSubject = new Subject<AgUiEvent>();
  
  public events$ = this.eventSubject.asObservable();
  
  constructor(private authService: AuthService) {}

  async procesarIntencionStream(prompt: string): Promise<void> {
    const userId = this.authService.getCurrentUser();
    
    if (!userId) {
      this.eventSubject.next({ type: 'ERROR', message: 'Usuario no autenticado en el Kernel' });
      return;
    }

    try {
      const response = await fetch(this.apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, user_id: userId })
      });

      if (!response.body) throw new Error('ReadableStream no soportado.');

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const parsed = JSON.parse(line);
            this.eventSubject.next({
              type: parsed.event,
              message: parsed.message,
              text: parsed.text,
              tool: parsed.tool,
              score: parsed.score,
              data: parsed.data
            });
          } catch (e) {
            console.warn('Error parseando chunk JSON en stream:', line);
          }
        }
      }
    } catch (err: any) {
      console.error('Error en bus de streaming AGNUX:', err);
      this.eventSubject.next({ type: 'ERROR', message: err.message || 'Error de red en Kernel' });
    }
  }
}
