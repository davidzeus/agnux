import { Component, OnDestroy, OnInit, afterNextRender, ViewChild, ElementRef, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription, take } from 'rxjs';
import { AgnuxService } from '../../services/agnux.service';
import { Ventana } from '../../models/ventana.model';
import { Shortcut } from '../../models/shortcut.model';
import { VentanaComponent } from '../ventana/ventana.component';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { AuthService } from '../../services/auth.service';
import { PresenceService } from '../../services/presence.service';
import { NotificationService } from '../../services/notification.service';
import { HyperIslandComponent } from '../hyper-island/hyper-island.component';
import { ThemeService } from '../../services/theme.service';

@Component({
  selector: 'app-escritorio',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    VentanaComponent,
    HyperIslandComponent,
    MatIconModule,
    MatButtonModule
  ],
  templateUrl: './escritorio.component.html',
  styleUrls: ['./escritorio.component.css']
})
export class EscritorioComponent implements OnInit, OnDestroy {
  ventanas: Ventana[] = [];
  shortcuts: Shortcut[] = [];    // Accesos directos del escritorio
  promptInput: string = '';
  cargando: boolean = false;
  private idCounter = 0;
  private maxZIndex = 100;
  private subscriptions: Subscription[] = [];
  public currentHtmlWindowId: string | null = null;
  public horaActual: Date = new Date();
  private clockInterval: any;

  userId: string | null = null;
  terminalId: string = '';
  qrUrl: string = '';
  isLocked: boolean = true;
  private authSub!: Subscription;
  isGoogleConnected: boolean = false;

  // Local Biometric state
  tieneCamaraLocal: boolean = false;

  constructor(
    private agnuxService: AgnuxService,
    private authService: AuthService,
    private presenceService: PresenceService,
    private notificationService: NotificationService,
    private themeService: ThemeService,
    private cdr: ChangeDetectorRef
  ) {
    afterNextRender(() => {
      this.clockInterval = setInterval(() => {
        this.horaActual = new Date();
      }, 1000);
    });

    this.subscriptions.push(
      this.agnuxService.eventStatus$.subscribe(status => {
        const event = status;

        // 🔥 EL EVENTO QUE FALTA: Capturar la orden de creación estructurada del Kernel
        if (event.type === 'CREATE_WINDOW' || event.event === 'CREATE_WINDOW' || (event.type === 'UNKNOWN' && event.payload?.event === 'CREATE_WINDOW')) {
          try {
            let rawData = event.data || event.payload?.data;
            const winData = typeof rawData === 'string' ? JSON.parse(rawData) : rawData;
            console.log("📺 [UI KERNEL] Orden de creación de ventana recibida:", winData);

            // Usamos la ventana actual anclada o generamos un ID único por seguridad
            const targetId = this.currentHtmlWindowId || `agnux-ai-window-${Date.now()}`;
            this.currentHtmlWindowId = targetId;

            // Verificamos si la ventana ya existe para no duplicarla
            let ventanaIA = this.ventanas.find(v => v.id === targetId);

            if (!ventanaIA) {
              // Respetamos la regla constitucional de no guiones bajos en el objeto de la interfaz
              ventanaIA = {
                id: targetId,
                titulo: winData.title || '🧠 AGNUX OS Core',
                tipo: 'html',
                htmlDinamico: winData.content || '',
                x: 150 + (this.ventanas.length * 20),
                y: 100 + (this.ventanas.length * 20),
                width: 550,
                height: 420,
                maximizada: false,
                zIndex: ++this.maxZIndex
              };

              // Forzamos la mutación inmutable para que Angular se entere
              this.ventanas = [...this.ventanas, ventanaIA];
            } else {
              // Si ya existía, actualizamos el contenido final consolidado
              ventanaIA.htmlDinamico = winData.content;
            }

            // 🔥 Forzamos el redibujado inmediato del DOM de Chrome
            this.cdr.detectChanges();
          } catch (parseError) {
            console.error("❌ Error crítico parseando el JSON de la ventana:", parseError);
          }
        } else if (status.type === 'TOOL_EXECUTE') {
          this.cargando = true;

        } else if (status.type === 'OPEN_MEDIA') {
          // ✅ El service ya normalizó el payload → { mediaPlatform, url }
          this.cargando = false;
          const targetUrl = status.payload?.url;
          if (targetUrl) {
            console.log(`🎵 [UI KERNEL] Abriendo pestaña externa: ${targetUrl}`);
            window.open(targetUrl, '_blank');
          }

        } else if (status.type === 'OPEN_LOCAL_MEDIA') {
          // ✅ Nuevo evento del backend Agno: media local o streaming
          this.cargando = false;
          const { mediaType, query } = status.payload || {};
          const mediaUrls: Record<string, string> = {
            'youtube':       `https://www.youtube.com/results?search_query=${encodeURIComponent(query || '')}`,
            'spotify':       'https://open.spotify.com',
            'netflix':       'https://www.netflix.com',
            'youtube-music': 'https://music.youtube.com',
          };
          const url = mediaUrls[mediaType] ?? `https://www.google.com/search?q=${encodeURIComponent(query || mediaType)}`;
          window.open(url, '_blank');

        } else if (status.type === 'OPEN_SYSTEM_APP') {
          // ✅ Nuevo evento: abrir app del sistema como ventana flotante
          this.cargando = false;
          const appId = status.payload?.appId ?? '';
          console.log(`🖥️ [UI KERNEL] Abriendo app del sistema: ${appId}`);
          const appTitles: Record<string, string> = {
            'calc':            '🧮 Calculadora',
            'terminal':        '💻 Terminal',
            'files':           '📁 Archivos',
            'settings':        '⚙️ Configuración',
            'hyper-island':    '📡 Hyper Island',
            'notes':           '📝 Notas',
            'network-monitor': '📊 Monitor de Red',
          };
          this.spawnVentana('html', appTitles[appId] ?? `🖥️ ${appId}`, `<p style="padding:1rem;color:var(--agnux-text-primary)">App: <strong>${appId}</strong></p>`);

        } else if (status.type === 'OPEN_IFRAME_APP') {
          // ✅ El service ya normalizó appService/appAction/appParams
          this.cargando = false;
          const { appService, appAction, appParams } = status.payload ?? {};
          if (!appService) return;
          const service = appService.toLowerCase();
          const urlMap: Record<string, string> = {
            'gmail':    'https://mail.google.com/',
            'calendar': 'https://calendar.google.com/',
            'docs':     'https://docs.google.com/',
            'sheets':   'https://docs.google.com/spreadsheets/',
            'slides':   'https://docs.google.com/presentation/',
          };
          window.open(urlMap[service] ?? 'https://workspace.google.com/', '_blank');

        } else if (status.type === 'SET_WALLPAPER') {
          // ✅ El service ya normalizó → { imageUrl } (sin importar si llegó 'image-url' o 'imageUrl')
          this.cargando = false;
          const imageUrl = status.payload?.imageUrl ?? '';
          if (imageUrl) {
            document.documentElement.style.setProperty('--agnux-bg-image', `url('${imageUrl}')`);
            console.log(`🖼️ [UI KERNEL] Wallpaper aplicado: ${imageUrl}`);
          }

        } else if (status.type === 'SET_THEME') {
          // ✅ El service ya normalizó → { cssCode } (sin importar si llegó 'css-code' o 'cssCode')
          this.cargando = false;
          const cssCode = status.payload?.cssCode ?? '';
          if (cssCode) {
            this.themeService.injectRawCss(cssCode);
            console.log(`🎨 [UI KERNEL] Tema CSS inyectado (${cssCode.length} chars)`);
          }

        } else if (status.type === 'SANDBOX_RUNNING') {
          // Notificación live: contenedor arrancando
          this.cargando = true;
          const lang = status.language || '?';
          console.log(`🐳 [SANDBOX] Lanzando contenedor para ${lang}...`);
          // Abrimos una ventana temporal de "evaluando..."
          this.currentHtmlWindowId = `sandbox-${Date.now()}`;
          const winPreview: any = {
            id:           this.currentHtmlWindowId,
            titulo:       `🐳 Sandbox [${lang.toUpperCase()}] — Evaluando...`,
            tipo:         'html',
            htmlDinamico: `<div style="padding:1.5rem;color:var(--agnux-text-secondary);font-family:monospace;">
              <span style="color:var(--agnux-accent)">▶</span>
              Lanzando contenedor Docker aislado para <strong style="color:var(--agnux-accent)">${lang}</strong>...
              <br/><br/>
              <span style="opacity:0.6;font-size:12px">🔒 Sin acceso a red · 💾 RAM 128MB máx · ⏱️ Timeout 20s</span>
            </div>`,
            x: 180, y: 120, width: 600, height: 300,
            maximizada: false, zIndex: ++this.maxZIndex
          };
          this.ventanas = [...this.ventanas, winPreview];
          this.cdr.detectChanges();

        } else if (status.type === 'SANDBOX_OK') {
          // ✅ Código validado: renderizar ventana con código + output
          this.cargando = false;
          const p = status.payload || {};
          const lang     = p.language     || 'code';
          const codigo   = this.escapeHtml(p.codigo   || '');
          const output   = this.escapeHtml(p.output   || '(sin output)');
          const execMs   = p.executionMs  || 0;

          // Construir HTML de la ventana con estilo cyberpunk
          const contenidoHtml = `
            <div style="font-family: 'Courier New', monospace; height: 100%; display: flex; flex-direction: column; gap: 0;">
              <!-- Header badge -->
              <div style="background: rgba(0,255,102,0.1); border-bottom: 1px solid var(--agnux-accent); padding: 6px 12px; font-size: 11px; color: var(--agnux-accent); display: flex; justify-content: space-between;">
                <span>✅ SANDBOX VALIDATED · ${lang.toUpperCase()} · ${execMs}ms</span>
                <span style="color: var(--agnux-text-secondary)">🔒 isolated · no-network · readonly-fs</span>
              </div>
              <!-- Código fuente -->
              <div style="flex:1; overflow: auto; background: rgba(0,0,0,0.5); padding: 12px;">
                <div style="font-size: 10px; color: var(--agnux-text-secondary); margin-bottom: 6px; text-transform: uppercase; letter-spacing: 1px;">Código Fuente</div>
                <pre style="margin:0; color: var(--agnux-accent); white-space: pre-wrap; font-size: 13px; line-height: 1.5;">${codigo}</pre>
              </div>
              <!-- Output terminal -->
              <div style="max-height: 160px; overflow: auto; background: rgba(0,0,0,0.8); border-top: 1px solid rgba(0,255,102,0.2); padding: 10px 12px;">
                <div style="font-size: 10px; color: var(--agnux-text-secondary); margin-bottom: 6px; text-transform: uppercase; letter-spacing: 1px;">Output del Proceso</div>
                <pre style="margin:0; color: #e0e0e0; white-space: pre-wrap; font-size: 12px; line-height: 1.4;">${output}</pre>
              </div>
            </div>`;

          // Reusar la ventana de sandbox si existe, sino crear una nueva
          const existente = this.ventanas.find(v => v.id === this.currentHtmlWindowId);
          if (existente) {
            existente.titulo       = p.title || `🐳 Sandbox [${lang.toUpperCase()}] — Validado ✅`;
            existente.htmlDinamico = contenidoHtml;
            existente.height       = 480;
          } else {
            this.spawnVentana('html', p.title || `🐳 Sandbox [${lang.toUpperCase()}]`, contenidoHtml);
          }
          this.cdr.detectChanges();

        } else if (status.type === 'SANDBOX_RETRY') {
          // 🔄 Código fallido: mostrar notificación sin cerrar la ventana
          const errorMsg = status.error || 'Error desconocido';
          console.warn(`⚠️ [SANDBOX] Reintentando... Error: ${errorMsg.slice(0, 150)}`);
          const existente = this.ventanas.find(v => v.id === this.currentHtmlWindowId);
          if (existente) {
            existente.titulo       = `🔄 Sandbox — Corrigiendo error...`;
            existente.htmlDinamico = `
              <div style="padding: 1.2rem; font-family: monospace;">
                <div style="color: #ff6b6b; margin-bottom: 8px; font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">Error detectado (corrigiendo automáticamente...)</div>
                <pre style="color: #ffaa44; font-size: 12px; white-space: pre-wrap; margin:0;">${this.escapeHtml(errorMsg)}</pre>
              </div>`;
            this.cdr.detectChanges();
          }

        } else if (status.type === 'ADD_SHORTCUT') {
          // 📌 Agregar acceso directo al escritorio
          const p = status.payload;
          if (p && p.id && !this.shortcuts.find(s => s.id === p.id)) {
            this.shortcuts = [...this.shortcuts, p as Shortcut];
            this.cdr.detectChanges();
            console.log(`📌 [SHORTCUT] Creado: '${p.nombre}' tipo=${p.tipo}`);
          }

        } else if (status.type === 'SHOW_SYSTEM_INFO') {
          // ℹ️ Mostrar manifiesto de capacidades del sistema como ventana flotante
          this.cargando = false;
          const man = status.manifiesto;
          const html = this._renderManifiesto(man);
          this.spawnVentana('html', 'ℹ️ AGNUX OS — Capacidades del Sistema', html);

        } else if (status.type === 'TOOL_END' || status.type === 'ERROR') {
          this.cargando = false;
          if (status.type === 'ERROR') {
            this.spawnVentana('html', '❌ Error de Sistema', status.message || 'Error desconocido');
          }

        } else if (status.type === 'INFERENCE_START') {
          this.currentHtmlWindowId = this.spawnVentana('html', '⚡ AGNUX OS Intelligence Output', null);

        } else if (status.type === 'TOOL_RESULT' || status.type === 'RESULT') {
          this.cargando = false;
          let output = status.data || status.payload;
          if (typeof output === 'object') {
            output = `<pre style="color: var(--agnux-text-primary); white-space: pre-wrap; font-size: 14px; margin: 0;">${JSON.stringify(output, null, 2)}</pre>`;
          }
          this.spawnVentana('html', '🛠️ AGNUX Tool Output', output);
        }
      })
    );
  }

  ngOnInit() {
    // 🛡️ [NUEVO FLUJO DE SEGURIDAD] Intentamos validación silenciosa por Cloudflare Access
    if (typeof window !== 'undefined') {
      this.authService.verifyCloudflareAuth();
    }

    this.authSub = this.authService.currentUser$.subscribe(user => {
      // Se ejecuta de forma asíncrona para evitar que choque con el proceso de Hidratación de Angular
      setTimeout(() => {
        console.log('🔄 [UI KERNEL] Cambio de estado de usuario detectado:', user);

        if (user) {
          // 🔓 Si hay usuario, limpiamos CUALQUIER conexión residual primero
          this.authService.closeConnection();
          this.userId = user;
          this.isLocked = false;
          console.log(`🔓 [UI KERNEL] Terminal liberada con éxito para: ${user}`);
          this.cdr.detectChanges();

          // Consultar estado de Google Workspace
          this.authService.checkGoogleAuthStatus(user).subscribe({
            next: status => {
              this.isGoogleConnected = status.connected;
            },
            error: err => {
              console.warn('⚠️ [UI KERNEL] No se pudo verificar estado de Google Workspace', err);
            }
          });

          // Conectar WebSocket de Notificaciones
          if (this.terminalId) {
            this.notificationService.connect(this.terminalId, user);
          }

          // Cargar estilo físico persistente
          this.themeService.loadBaseStyle(user);
        } else {
          this.isLocked = true;
          this.cdr.detectChanges();
          // Evita disparar el bloqueo si ya hay un ID de terminal inicializado escuchando
          if (!this.terminalId) {
            this.iniciarFlujoBloqueo();
          }
        }
      }, 0);
    });

    this.subscriptions.push(
    );

    this.subscriptions.push(
      this.agnuxService.token$.subscribe({
        next: (tokenLimpio) => {
          try {
            console.log("🔥 [UI KERNEL] Token recibido en UI:", tokenLimpio);
            // Si no hay ventana actual, forzamos un ID nuevo para este flujo de inferencia
            if (!this.currentHtmlWindowId) {
              this.currentHtmlWindowId = `agnux-ai-window-${Date.now()}`;
            }

            // 1. Buscamos la ventana ACTUAL de inferencia
            let ventanaIA: Ventana | undefined = this.ventanas.find(v => v.id === this.currentHtmlWindowId);

            if (!ventanaIA) {
              // 2. SI NO EXISTE, LA CREAMOS AL VUELO CON SUS COORDENADAS Y FOCO
              console.log(`📺 [UI DESKTOP] Abriendo nueva ventana flotante reactiva para la IA: ${this.currentHtmlWindowId}`);
              ventanaIA = {
                id: this.currentHtmlWindowId,
                titulo: '🧠 AGNUX OS Core - Ministral IA',
                tipo: 'html',
                htmlDinamico: '',
                x: 150 + (this.ventanas.length * 20),
                y: 100 + (this.ventanas.length * 20),
                width: 500,
                height: 400,
                maximizada: false,
                zIndex: ++this.maxZIndex
              };
              // Usamos el operador de propagación para asegurar que Angular detecte la mutación del array
              this.ventanas = [...this.ventanas, ventanaIA];
            }

            // 3. CONCATENAMOS EL TOKEN EN VIVO (Efecto máquina de escribir)
            const htmlPrevio = ventanaIA.htmlDinamico || '';
            ventanaIA.htmlDinamico = htmlPrevio + tokenLimpio;

            // Clonamos y embellecemos al vuelo para que el usuario no vea JSON feo
            ventanaIA.htmlDinamico = this.formatStreamText(ventanaIA.htmlDinamico);

            // 🔥 OBLIGAMOS A ANGULAR A REDIBUJAR LA PANTALLA EN ESTE MICROSEGUNDO
            this.cdr.detectChanges();
          } catch (e) {
            console.error("❌ Error procesando token$ en UI:", e);
          }
        },
        error: (err) => console.error("❌ Stream token$ abortado:", err)
      })
    );
  }

  iniciarFlujoBloqueo() {
    this.terminalId = 'TERM-' + Math.floor(Math.random() * 100000);
    console.warn(`🔒 [UI] Terminal Bloqueada. ID Asignado: ${this.terminalId}`);
    // El flujo de biometría y SSE fue delegado a Cloudflare Access.
  }



  ngOnDestroy() {
    this.subscriptions.forEach(sub => sub.unsubscribe());
    if (this.clockInterval) {
      clearInterval(this.clockInterval);
    }
    if (this.authSub) {
      this.authSub.unsubscribe();
    }
    this.authService.closeConnection();
    this.notificationService.disconnect();
  }

  // =====================================================================
  // 📌 LAUNCHER DE ACCESOS DIRECTOS
  // =====================================================================
  lanzarShortcut(s: Shortcut): void {
    console.log(`📌 [SHORTCUT] Lanzando: '${s.nombre}' tipo=${s.tipo}`);
    switch (s.tipo) {
      case 'app':
        // Dispara open-system-app como si el agente lo hubiera ordenado
        this.agnuxService.enviarPromptStream(`abrí la app ${s.destino}`, this.terminalId);
        break;
      case 'url':
        window.open(s.destino, '_blank');
        break;
      case 'command':
        // Ejecuta el comando directamente en la barra del kernel
        this.promptInput = s.destino;
        this.ejecutarComando();
        break;
    }
  }

  borrarShortcut(id: string): void {
    this.shortcuts = this.shortcuts.filter(s => s.id !== id);
    this.cdr.detectChanges();
  }

  // =====================================================================
  // 🛠️ UTILIDADES INTERNAS
  // =====================================================================

  /** Escapa HTML para mostrar código fuente de forma segura en ventanas. */
  escapeHtml(text: string): string {
    return text
      .replace(/&/g,  '&amp;')
      .replace(/</g,  '&lt;')
      .replace(/>/g,  '&gt;')
      .replace(/"/g,  '&quot;')
      .replace(/'/g,  '&#039;');
  }

  /** Renderiza el manifiesto de capacidades como HTML estructurado con diseño cyberpunk. */
  private _renderManifiesto(man: any): string {
    if (!man || !man.capacidades) {
      return '<p style="padding:1rem;color:var(--agnux-text-secondary)">Sin información de capacidades disponible.</p>';
    }
    const categorias = man.capacidades as any[];
    const sections = categorias.map(cat => {
      const tools = (cat.herramientas as any[]).map(t => `
        <div style="margin-bottom:10px; padding: 8px 10px; border-left: 2px solid var(--agnux-accent-border); background: rgba(0,0,0,0.3);">
          <div style="color: var(--agnux-accent); font-weight: bold; font-size: 13px;">${this.escapeHtml(t.nombre)}</div>
          <div style="color: var(--agnux-text-secondary); font-size: 11px; margin: 2px 0 4px;">${this.escapeHtml(t.comando)}</div>
          <div style="color: var(--agnux-text-primary); font-size: 12px; line-height: 1.4;">${this.escapeHtml(t.descripcion)}</div>
        </div>`).join('');
      return `
        <div style="margin-bottom: 18px;">
          <div style="font-size: 13px; font-weight: bold; color: var(--agnux-accent); letter-spacing: 1px; padding: 4px 0; border-bottom: 1px solid var(--agnux-accent-border); margin-bottom: 8px;">
            ${this.escapeHtml(cat.categoria)}
          </div>
          ${tools}
        </div>`;
    }).join('');

    return `
      <div style="padding: 16px; font-family: var(--agnux-font-main); height: 100%; overflow-y: auto; box-sizing: border-box;">
        <div style="font-size: 11px; color: var(--agnux-text-secondary); margin-bottom: 14px; letter-spacing: 1px;">
          ${this.escapeHtml(man.sistema ?? 'AGNUX OS')} &nbsp;·&nbsp; ${this.escapeHtml(man.version ?? '')}
        </div>
        ${sections}
        <div style="margin-top:12px; font-size: 11px; color: var(--agnux-text-secondary); text-align: center; opacity: 0.6;">
          Podés hablarme en lenguaje natural — ejecutaré la acción correcta automáticamente.
        </div>
      </div>`;
  }



  spawnVentana(tipo: 'html' | 'musica' | 'video' | 'texto' | 'iframe', titulo: string, datos: any): string {
    this.maxZIndex++;
    const id = `win_${this.idCounter++}`;
    // Si ya existe una ventana HTML, podemos reusarla, o crear una nueva
    if (tipo === 'html' && this.currentHtmlWindowId) {
      const existing = this.ventanas.find(v => v.id === this.currentHtmlWindowId);
      if (existing) {
        existing.htmlDinamico = ''; // Reset for new output
        this.enfocarVentana(existing);
        return existing.id;
      }
    }

    const nuevaVentana: Ventana = {
      id: `win_${Date.now()}`,
      titulo,
      tipo,
      datos,
      htmlDinamico: tipo === 'html' ? datos : '',
      urlDinamica: (tipo === 'video' || tipo === 'iframe') ? datos.url : '',
      maximizada: false,
      x: 50 + (this.idCounter * 20),
      y: 50 + (this.idCounter * 20),
      zIndex: this.maxZIndex + 1,
      width: tipo === 'video' ? 680 : 480,
      height: 400
    };
    this.ventanas = [...this.ventanas, nuevaVentana];
    this.cdr.detectChanges();
    return nuevaVentana.id;
  }

  cerrarVentana(id: string) {
    this.ventanas = this.ventanas.filter(v => v.id !== id);
    if (this.currentHtmlWindowId === id) {
      this.currentHtmlWindowId = null;
    }
  }

  toggleMaximizar(win: Ventana) {
    win.maximizada = !win.maximizada;
    this.enfocarVentana(win);
  }

  enfocarVentana(win: Ventana) {
    this.maxZIndex++;
    win.zIndex = this.maxZIndex;
  }

  async ejecutarComando() {
    if (!this.promptInput.trim()) return;
    this.cargando = true;

    // Forzamos a abrir una ventana nueva por cada comando, desligando la actual
    this.currentHtmlWindowId = null;

    try {
      await this.agnuxService.enviarPromptStream(this.promptInput, this.terminalId);
    } catch (err) {
      console.error(err);
      this.spawnVentana('texto', '❌ Error Local', { error: 'No se pudo conectar con AGNUX' });
    } finally {
      this.cargando = false;
      this.promptInput = ''; // Limpiar input
    }
  }

  async responderVentana(win: Ventana) {
    if (!win.replyInput?.trim()) return;
    win.cargandoRespuesta = true;

    const userText = win.replyInput;
    win.replyInput = '';

    // Mostrar visualmente la entrada del usuario en la consola
    win.htmlDinamico = (win.htmlDinamico || '') + `<br><br><span style="color: #fff; background: rgba(0,255,102,0.2); padding: 2px 4px; border-radius: 4px;">> ${userText}</span><br><br>`;

    // Reasignamos esta ventana como objetivo para el próximo stream
    this.currentHtmlWindowId = win.id;

    // Extraer texto limpio para el contexto
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = win.htmlDinamico;
    const contextText = tempDiv.innerText || tempDiv.textContent || '';

    // Regla de Oro AGNUX: Limpieza para el Router Semántico
    const esComandoDirecto = /^[0-9+\-*/().\s]+$/.test(userText) ||
      userText.toLowerCase().includes('resta') ||
      userText.toLowerCase().includes('suma') ||
      userText.toLowerCase().includes('calcula') ||
      userText.toLowerCase().includes('crea') ||
      userText.toLowerCase().includes('genera');

    let promptFinal = userText;

    if (!esComandoDirecto) {
      promptFinal = `[CONTEXTO PREVIO DE LA CONVERSACIÓN]:
${contextText.slice(-1000)}

[NUEVA ENTRADA DEL USUARIO CONTINUANDO EL TEMA]:
${userText}`;
    }

    try {
      await this.agnuxService.enviarPromptStream(promptFinal, this.terminalId);
    } catch (err) {
      console.error(err);
      win.htmlDinamico += `<br><span style="color: #ff3366;">[Error Local]</span>`;
    } finally {
      win.cargandoRespuesta = false;
    }
  }

  private formatStreamText(text: string): string {
    // 1. Limpieza base de markdown
    let clean = text.replace(/\*\*/g, '').replace(/```[a-zA-Z]*\n?/gi, '').replace(/```/g, '');

    // Si detectamos un JSON literal colado, le aplicamos sintaxis cyberpunk
    // Colorea claves de JSON: "clave":
    clean = clean.replace(/"([a-zA-Z0-9_]+)":/g, '<span style="color: var(--agnux-accent);">"$1"</span>:');

    // Colorea valores string: : "valor"
    clean = clean.replace(/: \s*"([^"]*)"/g, ': <span style="color: var(--agnux-text-primary);">"$1"</span>');

    // Colorea palabras reservadas
    clean = clean.replace(/: \s*(true|false|null)/g, ': <span style="color: var(--agnux-text-secondary); font-weight: bold;">$1</span>');

    // Colorea llaves y corchetes (Solo si están sueltos en el formato de JSON)
    clean = clean.replace(/(\{|\}|\[|\])/g, '<span style="color: var(--agnux-text-secondary); font-weight: bold;">$1</span>');

    // Limpieza de span corruptos (por si reemplazó corchetes de CSS)
    clean = clean.replace(/<span style="color: var(--agnux-text-secondary); font-weight: bold;">\{<\/span>/g, '{');
    clean = clean.replace(/<span style="color: var(--agnux-text-secondary); font-weight: bold;">\}<\/span>/g, '}');

    // Ocultar palabra inicial json {
    clean = clean.replace(/^json\s*\{/gmi, '{');

    return clean;
  }
}
