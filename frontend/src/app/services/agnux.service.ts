import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';
import { AuthService } from './auth.service';

export interface AgnuxResponse {
  status: string;
  user: string;
  response: string;
  detail?: string;
}

// =====================================================================
// 🔑 TABLA DE ALIASES DE EVENTOS SSE
// Mapea los nombres históricos (guiones bajos) y los nuevos (guiones medios)
// al tipo canónico interno que consume el EscritorioComponent.
// Esto garantiza compatibilidad total sin importar qué versión del backend
// emite el evento.
// =====================================================================
const EVENT_ALIAS_MAP: Record<string, string> = {
  // --- Eventos con guión bajo (backend legacy) ---
  'CREATE_WINDOW':    'CREATE_WINDOW',
  'TOKEN':            'TOKEN',
  'ROUTER_START':     'ROUTER_START',
  'ROUTER_SCORE':     'ROUTER_SCORE',
  'INFERENCE_START':  'INFERENCE_START',
  'TOOL_EXECUTE':     'TOOL_EXECUTE',
  'TOOL_RESULT':      'TOOL_RESULT',
  'TOOL_END':         'TOOL_END',
  'ERROR':            'ERROR',
  'QUEUE_WAIT':       'QUEUE_WAIT',
  'SET_WALLPAPER':    'SET_WALLPAPER',
  'SET_THEME':        'SET_THEME',
  'OPEN_MEDIA':       'OPEN_MEDIA',
  'OPEN_IFRAME_APP':  'OPEN_IFRAME_APP',
  'OPEN_LOCAL_MEDIA': 'OPEN_LOCAL_MEDIA',

  // --- Eventos con guión medio (backend Agno refactorizado) ---
  'CREATE-WINDOW':    'CREATE_WINDOW',
  'ROUTER-START':     'ROUTER_START',
  'ROUTER-SCORE':     'ROUTER_SCORE',
  'QUEUE-WAIT':       'QUEUE_WAIT',
  'TOOL-EXECUTE':     'TOOL_EXECUTE',
  'TOOL-RESULT':      'TOOL_RESULT',
  'TOOL-END':         'TOOL_END',
  'SET-WALLPAPER':    'SET_WALLPAPER',
  'SET-THEME':        'SET_THEME',
  'OPEN-MEDIA':       'OPEN_MEDIA',
  'OPEN-IFRAME-APP':  'OPEN_IFRAME_APP',
  'OPEN-LOCAL-MEDIA': 'OPEN_LOCAL_MEDIA',
  'OPEN-SYSTEM-APP':  'OPEN_SYSTEM_APP',

  // --- Eventos del Sandbox Docker ---
  'SANDBOX-RUNNING':  'SANDBOX_RUNNING',
  'SANDBOX-OK':       'SANDBOX_OK',
  'SANDBOX-RETRY':    'SANDBOX_RETRY',
  'SANDBOX_RUNNING':  'SANDBOX_RUNNING',
  'SANDBOX_OK':       'SANDBOX_OK',
  'SANDBOX_RETRY':    'SANDBOX_RETRY',

  // --- Streaming de texto (Backend Agno) ---
  'TEXT-CHUNK':       'TOKEN',
  'TEXT_CHUNK':       'TOKEN',

  // --- Accesos directos y sistema ---
  'ADD-SHORTCUT':     'ADD_SHORTCUT',
  'ADD_SHORTCUT':     'ADD_SHORTCUT',
  'SHOW-SYSTEM-INFO': 'SHOW_SYSTEM_INFO',
  'SHOW_SYSTEM_INFO': 'SHOW_SYSTEM_INFO',
};

function normalizeEventType(raw: string): string {
  return EVENT_ALIAS_MAP[raw] ?? raw.toUpperCase().replace(/-/g, '_');
}

@Injectable({
  providedIn: 'root'
})
export class AgnuxService {
  private apiUrl = '/api/system/intent';

  public token$ = new Subject<string>();
  public eventStatus$ = new Subject<any>();

  constructor(private authService: AuthService) {}

  async getSystemStatus(): Promise<any> {
    try {
      const response = await fetch('/api/system/status');
      if (response.ok) {
        return await response.json();
      }
    } catch (e) {
      console.warn("Error obteniendo estado del sistema:", e);
    }
    return null;
  }

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
        throw new Error(`Backend respondió con ${response.status}: ${text}`);
      }

      if (!response.body) {
        throw new Error('El Kernel no envió un flujo de datos válido.');
      }

      const reader  = response.body.getReader();
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
            // Guardamos el nombre de evento RAW; se normaliza al consumir
            eventoActual = lineaLimpia.substring(7).trim();

          } else if (lineaLimpia.startsWith('data: ')) {
            const dataRaw = lineaLimpia.substring(6);
            console.log(`🔥 [AGNUX SERVICE] Evento='${eventoActual}' raw=`, dataRaw);

            try {
              const dataObj = JSON.parse(dataRaw);

              // Normalización: convierte guiones medios → guiones bajos para el
              // consumo interno en EscritorioComponent (sin romper los listeners).
              const tipoNorm = normalizeEventType(eventoActual);

              switch (tipoNorm) {
                case 'TOKEN':
                  this.token$.next(typeof dataObj === 'string' ? dataObj : (dataObj?.content ?? JSON.stringify(dataObj)));
                  break;

                case 'CREATE_WINDOW':
                  // El payload puede venir directo en dataObj o anidado en .data
                  this.eventStatus$.next({ type: 'CREATE_WINDOW', data: dataObj });
                  break;

                case 'SET_WALLPAPER':
                  // Backend nuevo envía 'image-url', legacy enviaba 'imageUrl'
                  this.eventStatus$.next({
                    type: 'SET_WALLPAPER',
                    payload: {
                      imageUrl: dataObj['image-url'] ?? dataObj['imageUrl'] ?? ''
                    }
                  });
                  break;

                case 'SET_THEME':
                  // Backend nuevo envía 'css-code', legacy enviaba 'cssCode'
                  this.eventStatus$.next({
                    type: 'SET_THEME',
                    payload: {
                      cssCode: dataObj['css-code'] ?? dataObj['cssCode'] ?? ''
                    }
                  });
                  break;

                case 'OPEN_MEDIA':
                  this.eventStatus$.next({
                    type: 'OPEN_MEDIA',
                    payload: {
                      // Normaliza 'media-platform' (nuevo) y 'mediaPlatform' (legacy)
                      mediaPlatform: dataObj['media-platform'] ?? dataObj['mediaPlatform'] ?? '',
                      url:           dataObj['url'] ?? '',
                    }
                  });
                  break;

                case 'OPEN_LOCAL_MEDIA':
                  this.eventStatus$.next({
                    type: 'OPEN_LOCAL_MEDIA',
                    payload: {
                      mediaType: dataObj['media-type'] ?? dataObj['mediaType'] ?? '',
                      query:     dataObj['query'] ?? '',
                    }
                  });
                  break;

                case 'OPEN_IFRAME_APP':
                  this.eventStatus$.next({
                    type: 'OPEN_IFRAME_APP',
                    payload: {
                      // Normaliza 'app-service' (nuevo) y 'appService' (legacy)
                      appService: dataObj['app-service'] ?? dataObj['appService'] ?? '',
                      appAction:  dataObj['app-action']  ?? dataObj['appAction']  ?? '',
                      appParams:  dataObj['app-params']  ?? dataObj['appParams']  ?? {},
                    }
                  });
                  break;

                case 'OPEN_SYSTEM_APP':
                  this.eventStatus$.next({
                    type: 'OPEN_SYSTEM_APP',
                    payload: { appId: dataObj['app-id'] ?? dataObj['appId'] ?? '' }
                  });
                  break;

                case 'TOOL_EXECUTE':
                  this.eventStatus$.next({ type: 'TOOL_EXECUTE', msg: dataObj['message'] ?? dataObj });
                  break;

                case 'TOOL_RESULT':
                case 'RESULT':
                  this.eventStatus$.next({ type: 'TOOL_RESULT', data: dataObj['data'] ?? dataObj['response'] ?? dataObj });
                  break;

                case 'ROUTER_START':
                case 'INFERENCE_START':
                  this.eventStatus$.next({ type: tipoNorm, msg: dataObj['message'] ?? dataObj });
                  break;

                case 'ROUTER_SCORE':
                  this.eventStatus$.next({ type: 'ROUTER_SCORE', tool: dataObj['tool'], score: dataObj['score'] });
                  break;

                case 'QUEUE_WAIT':
                  this.eventStatus$.next({ type: 'QUEUE_WAIT', message: dataObj['message'] ?? dataObj });
                  break;

                case 'SANDBOX_RUNNING':
                  this.eventStatus$.next({
                    type:     'SANDBOX_RUNNING',
                    message:  dataObj['message'] ?? '🐳 Evaluando código en sandbox...',
                    language: dataObj['language'] ?? '',
                  });
                  break;

                case 'SANDBOX_OK':
                  // Código validado: entregamos el payload completo al escritorio
                  this.eventStatus$.next({
                    type:    'SANDBOX_OK',
                    payload: {
                      windowId:    dataObj['window-id']    ?? 'sandbox-output',
                      title:       dataObj['title']        ?? '🐳 Sandbox Output',
                      language:    dataObj['language']     ?? '',
                      codigo:      dataObj['codigo']       ?? '',
                      output:      dataObj['output']       ?? '',
                      executionMs: dataObj['execution-ms'] ?? 0,
                      validated:   dataObj['validated']    ?? true,
                    }
                  });
                  break;

                case 'SANDBOX_RETRY':
                  this.eventStatus$.next({
                    type:     'SANDBOX_RETRY',
                    message:  dataObj['message'] ?? '🔄 Corrigiendo código...',
                    exitCode: dataObj['exit-code'] ?? -1,
                    error:    dataObj['error']     ?? '',
                  });
                  break;

                case 'ADD_SHORTCUT':
                  this.eventStatus$.next({
                    type:    'ADD_SHORTCUT',
                    payload: {
                      id:          dataObj['id']          ?? '',
                      nombre:      dataObj['nombre']      ?? '',
                      icono:       dataObj['icono']       ?? '📌',
                      tipo:        dataObj['tipo']        ?? 'command',
                      destino:     dataObj['destino']     ?? '',
                      descripcion: dataObj['descripcion'] ?? '',
                    }
                  });
                  break;

                case 'SHOW_SYSTEM_INFO':
                  this.eventStatus$.next({
                    type:      'SHOW_SYSTEM_INFO',
                    manifiesto: dataObj['manifiesto'] ?? dataObj,
                  });
                  break;

                case 'ERROR':
                  this.eventStatus$.next({ type: 'ERROR', message: dataObj['message'] ?? String(dataObj) });
                  break;

                default:
                  console.warn(`[AGNUX SERVICE] Evento desconocido '${eventoActual}' → normalizado='${tipoNorm}'`, dataObj);
                  this.eventStatus$.next({ type: 'UNKNOWN', payload: { event: eventoActual, data: dataObj } });
              }

            } catch (e) {
              console.error('[AGNUX SERVICE] Error parseando data payload:', e, '→ raw:', dataRaw);
            }

            eventoActual = ''; // Resetear tras consumir el par event/data

          } else if (lineaLimpia.startsWith('{')) {
            // Soporte para raw JSON sin formato SSE (fallback de compatibilidad)
            try {
              const rawParsed = JSON.parse(lineaLimpia);
              if (rawParsed.event) {
                const tipoNorm = normalizeEventType(rawParsed.event);
                this.eventStatus$.next({ type: tipoNorm, payload: rawParsed });
              }
            } catch (e) {
              console.error('[AGNUX SERVICE] Error parseando raw JSON event:', e);
            }
          }
        }
      }

    } catch (error) {
      console.error('[AGNUX SERVICE] Falla en el bus de streaming local:', error);
      this.eventStatus$.next({
        type: 'ERROR',
        message: (error as Error).message || 'Error de streaming desconocido'
      });
      throw error;
    }
  }
}