import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root'
})
export class PresenceService {
  private isRunning = false;
  private timeoutId: any;

  constructor(private authService: AuthService, private http: HttpClient) {
    this.authService.currentUser$.subscribe(userId => {
      if (userId) {
        this.startPresenceDaemon();
      } else {
        this.stopPresenceDaemon();
      }
    });
  }

  private startPresenceDaemon() {
    if (this.isRunning) return;
    this.isRunning = true;
    console.log('🛡️ [AGNUX DAEMON] Servicio de presencia en segundo plano activado.');
    this.scheduleNextCheck();
  }

  private stopPresenceDaemon() {
    this.isRunning = false;
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
      this.timeoutId = null;
    }
    console.log('🛡️ [AGNUX DAEMON] Servicio de presencia detenido.');
  }

  private scheduleNextCheck() {
    if (!this.isRunning) return;
    
    // Muestreo aleatorio entre 3 y 8 minutos (180000ms a 480000ms)
    const delay = Math.floor(Math.random() * (480000 - 180000 + 1)) + 180000;
    console.log(`⏱️ [AGNUX DAEMON] Próximo chequeo programado en ${Math.floor(delay / 1000)}s`);
    
    this.timeoutId = setTimeout(() => {
      this.performSilentCheck();
    }, delay);
  }

  private performSilentCheck() {
    if (typeof navigator === 'undefined' || !navigator.mediaDevices) {
      this.scheduleNextCheck();
      return;
    }

    navigator.mediaDevices.getUserMedia({ video: true }).then(stream => {
      const video = document.createElement('video');
      video.srcObject = stream;
      video.play();
      
      video.onloadeddata = () => {
        setTimeout(() => {
          const canvas = document.createElement('canvas');
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          const context = canvas.getContext('2d');
          
          if (context) {
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            canvas.toBlob(blob => {
              if (blob) {
                const file = new File([blob], 'presence_frame.jpg', { type: 'image/jpeg' });
                const formData = new FormData();
                formData.append('file', file);
                
                this.http.post('http://10.10.0.66:8000/api/system/validate-presence', formData)
                  .subscribe({
                    next: (res: any) => {
                      if (res.status === 'valid') {
                        // Presencia confirmada, seguir muestreando
                        this.scheduleNextCheck();
                      } else {
                        // Respuesta del backend indica que no coincide o no hay humano
                        console.warn('⚠️ [AGNUX DAEMON] Presencia invalida detectada por el backend.');
                        this.authService.logoutForzado();
                      }
                    },
                    error: (err) => {
                      console.warn('⚠️ [AGNUX DAEMON] Falla en conexión de presencia. Se reintentará luego.', err);
                      this.scheduleNextCheck();
                    }
                  });
              }
              stream.getTracks().forEach(track => track.stop());
            }, 'image/jpeg');
          } else {
            stream.getTracks().forEach(track => track.stop());
            this.scheduleNextCheck();
          }
        }, 800); // Dar tiempo al foco de la cámara
      };
    }).catch(err => {
      console.warn('⚠️ [AGNUX DAEMON] No se pudo acceder a la cámara silenciosamente.', err);
      // Si la cámara fue desconectada físicamente o bloqueada, agendamos otro chequeo
      this.scheduleNextCheck();
    });
  }
}
