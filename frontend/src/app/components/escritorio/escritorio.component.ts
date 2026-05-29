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

@Component({
  selector: 'app-escritorio',
  standalone: true,
  imports: [
    CommonModule, 
    FormsModule, 
    VentanaComponent,
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

  // Local Biometric state
  tieneCamaraLocal: boolean = false;

  constructor(
    private agnuxService: AgnuxService, 
    private authService: AuthService, 
    private presenceService: PresenceService,
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
        } else if (status.type === 'TOOL_END' || status.type === 'ERROR') {
          this.cargando = false;
        } else if (status.type === 'INFERENCE_START') {
          this.currentHtmlWindowId = this.spawnVentana('html', '⚡ AGNUX OS Intelligence Output', null);
        } else if (status.type === 'ERROR') {
          this.spawnVentana('texto', '❌ Error de Sistema', { error: status.message });
        }
      })
    );
  }

  ngOnInit() {
    this.authSub = this.authService.currentUser$.subscribe(user => {
      console.log('🔄 [UI KERNEL] Cambio de estado de usuario detectado:', user);
      
      if (user) {
        // 🔓 Si hay usuario, limpiamos CUALQUIER conexión residual primero
        this.authService.closeConnection();
        this.userId = user;
        this.isLocked = false;
        console.log(`🔓 [UI KERNEL] Terminal liberada con éxito para: ${user}`);
      } else {
        this.isLocked = true;
        // Evita disparar el bloqueo si ya hay un ID de terminal inicializado escuchando
        if (!this.terminalId) {
          this.iniciarFlujoBloqueo();
        }
      }
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
    this.terminalId = 'TERM-DESKTOP-' + Math.floor(Math.random() * 100000);
    this.qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodeURIComponent('http://10.10.0.66:4200/authorize?terminal-id=' + this.terminalId)}`;
    console.warn(`🔒 [UI] Terminal Bloqueada. ID Asignado: ${this.terminalId}`);
    
    // Evitar ejecutar SSE en SSR Node.js
    if (typeof window !== 'undefined') {
      this.authService.listenTerminal(this.terminalId).pipe(take(1)).subscribe();

      // Sondeo silencioso de periféricos para habilitar los botones
      navigator.mediaDevices.enumerateDevices().then(devices => {
        const camara = devices.some(device => device.kind === 'videoinput');
        this.tieneCamaraLocal = camara;
      });
    }
  }

  ejecutarCapturaFacialDemanda() {
    if (typeof navigator === 'undefined' || !navigator.mediaDevices) return;
    
    console.log("📸 [KERNEL UI] Iniciando captura facial a demanda...");
    navigator.mediaDevices.getUserMedia({ video: true }).then(stream => {
      const video = document.createElement('video');
      video.srcObject = stream;
      video.play();
      
      video.onloadeddata = () => {
        // Pequeño delay para permitir que la cámara aclare el foco y la luz
        setTimeout(() => {
          const canvas = document.createElement('canvas');
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          const context = canvas.getContext('2d');
          if (context) {
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            canvas.toBlob(blob => {
              if (blob) {
                const file = new File([blob], 'frame.jpg', { type: 'image/jpeg' });
                this.authService.loginFacial(file).subscribe();
              }
              stream.getTracks().forEach(track => track.stop());
            }, 'image/jpeg');
          } else {
            stream.getTracks().forEach(track => track.stop());
          }
        }, 800);
      };
    }).catch(err => console.error("⚠️ [KERNEL UI] Error bloqueando cámara local:", err));
  }

  ejecutarCapturaVocalDemanda() {
    if (typeof navigator === 'undefined' || !navigator.mediaDevices) return;

    console.log("🎙️ [KERNEL UI] Grabando 2 segundos de audio...");
    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
      const mediaRecorder = new MediaRecorder(stream);
      const audioChunks: Blob[] = [];

      mediaRecorder.addEventListener("dataavailable", event => {
        audioChunks.push(event.data);
      });

      mediaRecorder.addEventListener("stop", () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        this.authService.loginVocal(audioBlob).subscribe();
        stream.getTracks().forEach(track => track.stop());
      });

      mediaRecorder.start();
      setTimeout(() => {
        mediaRecorder.stop();
      }, 2000);
    }).catch(err => console.error("⚠️ [KERNEL UI] Error capturando audio:", err));
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
  }

  spawnVentana(tipo: 'html' | 'musica' | 'video' | 'texto', titulo: string, datos: any): string {
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
      maximizada: false,
      x: 50 + (this.idCounter * 20),
      y: 50 + (this.idCounter * 20),
      zIndex: this.maxZIndex + 1,
      width: tipo === 'video' ? 680 : 480,
      height: 400
    };
    this.ventanas.push(nuevaVentana);
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
      await this.agnuxService.enviarPromptStream(this.promptInput);
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
      await this.agnuxService.enviarPromptStream(promptFinal);
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
    clean = clean.replace(/"([a-zA-Z0-9_]+)":/g, '<span style="color: #00e5ff;">"$1"</span>:');
    
    // Colorea valores string: : "valor"
    clean = clean.replace(/: \s*"([^"]*)"/g, ': <span style="color: #ffaa00;">"$1"</span>');
    
    // Colorea palabras reservadas
    clean = clean.replace(/: \s*(true|false|null)/g, ': <span style="color: #ff3366;">$1</span>');

    // Colorea llaves y corchetes (Solo si están sueltos en el formato de JSON)
    clean = clean.replace(/(\{|\}|\[|\])/g, '<span style="color: #ff3366; font-weight: bold;">$1</span>');
    
    // Limpieza de span corruptos (por si reemplazó corchetes de CSS)
    clean = clean.replace(/<span style="color: #ff3366; font-weight: bold;">\{<\/span>/g, '{');
    clean = clean.replace(/<span style="color: #ff3366; font-weight: bold;">\}<\/span>/g, '}');

    // Ocultar palabra inicial json {
    clean = clean.replace(/^json\s*\{/gmi, '{');

    return clean;
  }
}
