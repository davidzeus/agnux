import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Ventana } from '../../models/ventana.model';
import { SafeHtmlPipe, SafeUrlPipe } from '../../pipes/safe.pipe';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { DragDropModule } from '@angular/cdk/drag-drop';

@Component({
  selector: 'app-ventana',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    SafeHtmlPipe,
    SafeUrlPipe,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatInputModule,
    MatFormFieldModule,
    DragDropModule
  ],
  templateUrl: './ventana.component.html',
  styleUrls: ['./ventana.component.css']
})
export class VentanaComponent {
  @Input() win!: Ventana;
  @Output() onCerrar = new EventEmitter<string>();
  @Output() onMaximizar = new EventEmitter<Ventana>();
  @Output() onEnfocar = new EventEmitter<Ventana>();
  @Output() onResponder = new EventEmitter<Ventana>();

  isResizing = false;
  resizeDirection = '';
  startX = 0;
  startY = 0;
  startWidth = 0;
  startHeight = 0;

  initResize(event: MouseEvent, direction: string) {
    if (this.win.maximizada) return;
    
    event.stopPropagation();
    event.preventDefault();
    this.isResizing = true;
    this.resizeDirection = direction;
    this.startX = event.clientX;
    this.startY = event.clientY;
    
    this.startWidth = this.win.width || 480;
    this.startHeight = this.win.height || 400;

    const mouseMoveHandler = (e: MouseEvent) => this.onMouseMove(e);
    const mouseUpHandler = () => {
      this.isResizing = false;
      document.removeEventListener('mousemove', mouseMoveHandler);
      document.removeEventListener('mouseup', mouseUpHandler);
    };

    document.addEventListener('mousemove', mouseMoveHandler);
    document.addEventListener('mouseup', mouseUpHandler);
  }

  onMouseMove(event: MouseEvent) {
    if (!this.isResizing) return;

    if (this.resizeDirection === 'right' || this.resizeDirection === 'both') {
      const newWidth = this.startWidth + (event.clientX - this.startX);
      this.win.width = Math.max(300, newWidth); // Ancho mínimo 300px
    }
    
    if (this.resizeDirection === 'bottom' || this.resizeDirection === 'both') {
      const newHeight = this.startHeight + (event.clientY - this.startY);
      this.win.height = Math.max(200, newHeight); // Alto mínimo 200px
    }
  }
}
