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
}
