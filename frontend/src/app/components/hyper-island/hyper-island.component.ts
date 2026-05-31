import { Component, OnInit, ChangeDetectorRef, HostListener, ElementRef, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { NotificationService } from '../../services/notification.service';
import { AgnuxService } from '../../services/agnux.service';

export type IslandState = 'compact' | 'expanded-notif' | 'expanded-widget';

interface BackgroundTask {
  id: string;
  type: 'player' | 'system' | 'network';
  title: string;
  subtitle: string;
  icon: string;
}

@Component({
  selector: 'app-hyper-island',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './hyper-island.component.html',
  styleUrls: ['./hyper-island.component.css']
})
export class HyperIslandComponent implements OnInit, OnDestroy {
  currentState: IslandState = 'compact';
  currentNotification: string | null = null;
  private notifSub!: Subscription;
  private agnuxSub!: Subscription;
  
  // Estado para monitores del sistema
  hoveredMonitor: 'wifi' | 'battery' | 'hardware' | null = null;
  monitorData: any = null;
  private hoverTimeout: any = null;
  
  // Tarea del reproductor mockeada por defecto en el bus del sistema
  activeTasks: BackgroundTask[] = [
    { id: 'track-player', type: 'player', title: 'Cyberpunk Synth', subtitle: 'Loop Station', icon: '📻' }
  ];

  constructor(
    private cdr: ChangeDetectorRef,
    private el: ElementRef,
    private notificationService: NotificationService,
    private agnuxService: AgnuxService
  ) {}

  ngOnInit() {
    console.log("🏝️ [HYPER ISLAND] Bus de notificaciones inicializado en el tope del DOM.");
    
    this.notifSub = this.notificationService.notifications$.subscribe(notif => {
      this.showNotification(notif.message || 'Notificación del Sistema');
    });

    this.agnuxSub = this.agnuxService.eventStatus$.subscribe(event => {
      if (event.type === 'OPEN_MEDIA') {
        this.currentState = 'expanded-widget';
        this.activeTasks = [{
            id: 'media-kiosk',
            type: 'player',
            title: `Reproduciendo en ${event.payload?.mediaPlatform || 'Kiosco'}`,
            subtitle: 'Kiosco Activo',
            icon: '🎵'
        }];
        this.cdr.detectChanges();
      }
    });
  }

  ngOnDestroy() {
    if (this.notifSub) this.notifSub.unsubscribe();
    if (this.agnuxSub) this.agnuxSub.unsubscribe();
  }

  showNotification(message: string) {
    this.currentNotification = message;
    this.currentState = 'expanded-notif';
    this.cdr.detectChanges();

    // Vuelve a estado compacto después de 4 segundos
    setTimeout(() => {
      this.currentNotification = null;
      this.currentState = 'compact';
      this.cdr.detectChanges();
    }, 4000);
  }

  toggleWidget(event?: Event) {
    if (event) {
      event.stopPropagation();
    }
    if (this.currentState === 'expanded-widget') {
      this.currentState = 'compact';
    } else {
      this.currentState = 'expanded-widget';
    }
    this.cdr.detectChanges();
  }

  cerrarWidget(event: Event) {
    event.stopPropagation();
    this.currentState = 'compact';
    this.cdr.detectChanges();
  }

  // --- MONITORES DE SISTEMA ---
  onMonitorHover(type: 'wifi' | 'battery' | 'hardware') {
    // Evitar parpadeos o peticiones spam si ya estamos sobre el mismo
    if (this.hoveredMonitor === type) return;
    
    // Limpiar timeout previo
    if (this.hoverTimeout) {
      clearTimeout(this.hoverTimeout);
    }

    this.hoveredMonitor = type;
    this.monitorData = null; // Mostrar loading state (opcional)
    this.cdr.detectChanges();

    // Debounce para hacer la petición HTTP
    this.hoverTimeout = setTimeout(async () => {
      if (this.hoveredMonitor === type) { // doble chequeo de que seguimos acá
        const status = await this.agnuxService.getSystemStatus();
        if (status && this.hoveredMonitor === type) {
          this.monitorData = status;
          this.cdr.detectChanges();
        }
      }
    }, 250);
  }

  onMonitorLeave() {
    if (this.hoverTimeout) {
      clearTimeout(this.hoverTimeout);
      this.hoverTimeout = null;
    }
    // Pequeño retardo para no ocultar de golpe si mueve rápido el mouse
    this.hoverTimeout = setTimeout(() => {
      this.hoveredMonitor = null;
      this.monitorData = null;
      this.cdr.detectChanges();
    }, 200);
  }

  @HostListener('document:click', ['$event'])
  onClickOutside(event: Event) {
    // Si el clic ocurrió fuera de la isla y está expandida, la cerramos
    if (this.currentState === 'expanded-widget' && !this.el.nativeElement.contains(event.target)) {
      this.currentState = 'compact';
      this.cdr.detectChanges();
    }
  }
}
