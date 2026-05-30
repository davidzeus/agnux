import { Component, OnDestroy, OnInit, afterNextRender, ViewChild, ElementRef, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription, take } from 'rxjs';
import { AgnuxService } from '../../services/agnux.service';
import { Ventana } from '../../models/ventana.model';
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
          const msg = status.msg || '';
          if (msg.includes('reproducir_musica')) {
            this.spawnVentana('musica', '🎵 AGNUX Media Player', { status: 'Playing...' });
          } else if (msg.includes('tool_reproductor_video')) {
            this.spawnVentana('video', '🎬 AGNUX Video Core', { url: '' });
          }
        } else if (status.type === 'OPEN_MEDIA') {
          this.cargando = false;
          const targetUrl = status.payload?.url;
          const platformName = status.payload?.mediaPlatform || 'Media';

          if (targetUrl) {
            console.log(`🎵 [UI KERNEL] Abriendo pestaña externa para: ${targetUrl}`);
            window.open(targetUrl, '_blank');
          }
          // Evento propagado a hyper-island a través de un bus o servicio (lo gestionaremos en app-hyper-island)
        } else if (status.type === 'OPEN_IFRAME_APP') {
          this.cargando = false;
          const { appService, appAction, appParams } = status.payload;
          const service = appService.toLowerCase();
          let targetUrl = 'https://workspace.google.com/';
          if (service === 'gmail') targetUrl = 'https://mail.google.com/';
          else if (service === 'calendar') targetUrl = 'https://calendar.google.com/';
          else if (service === 'docs') targetUrl = 'https://docs.google.com/';
          else if (service === 'sheets') targetUrl = 'https://docs.google.com/spreadsheets/';
          else if (service === 'slides') targetUrl = 'https://docs.google.com/presentation/';
          
          window.open(targetUrl, '_blank');
        } else if (status.type === 'SET_WALLPAPER') {
          this.cargando = false;
          const imageUrl = status.payload.imageUrl;
          document.documentElement.style.setProperty('--agnux-bg-image', `url('${imageUrl}')`);
        } else if (status.type === 'SET_THEME') {
          this.cargando = false;
          const cssCode = status.payload.cssCode;
          this.themeService.injectRawCss(cssCode);
        } else if (status.type === 'TOOL_END' || status.type === 'ERROR') {
          this.cargando = false;
        } else if (status.type === 'INFERENCE_START') {
          this.currentHtmlWindowId = this.spawnVentana('html', '⚡ AGNUX OS Intelligence Output', null);
        } else if (status.type === 'TOOL_RESULT' || status.type === 'RESULT') {
          this.cargando = false;
          let output = status.data || status.payload;
          if (typeof output === 'object') {
            output = `<pre style="color: var(--agnux-text-primary); white-space: pre-wrap; font-size: 14px; margin: 0;">${JSON.stringify(output, null, 2)}</pre>`;
          }
          this.spawnVentana('html', '🛠️ AGNUX Tool Output', output);
        } else if (status.type === 'ERROR') {
          this.spawnVentana('html', '❌ Error de Sistema', status.message || 'Error desconocido');
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
