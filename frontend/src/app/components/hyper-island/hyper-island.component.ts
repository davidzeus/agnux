import { Component, OnInit, ChangeDetectorRef, HostListener, ElementRef, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { NotificationService } from '../../services/notification.service';

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
  
  // Tarea del reproductor mockeada por defecto en el bus del sistema
  activeTasks: BackgroundTask[] = [
    { id: 'track-player', type: 'player', title: 'Cyberpunk Synth', subtitle: 'Loop Station', icon: '📻' }
  ];

  constructor(
    private cdr: ChangeDetectorRef,
    private el: ElementRef,
    private notificationService: NotificationService
  ) {}

  ngOnInit() {
    console.log("🏝️ [HYPER ISLAND] Bus de notificaciones inicializado en el tope del DOM.");
    
    this.notifSub = this.notificationService.notifications$.subscribe(notif => {
      this.showNotification(notif.message || 'Notificación del Sistema');
    });
  }

  ngOnDestroy() {
    if (this.notifSub) {
      this.notifSub.unsubscribe();
    }
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

  @HostListener('document:click', ['$event'])
  onClickOutside(event: Event) {
    // Si el clic ocurrió fuera de la isla y está expandida, la cerramos
    if (this.currentState === 'expanded-widget' && !this.el.nativeElement.contains(event.target)) {
      this.currentState = 'compact';
      this.cdr.detectChanges();
    }
  }
}
