import { Component } from '@angular/core';
import { EscritorioComponent } from './components/escritorio/escritorio.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [EscritorioComponent], 
  template: '<app-escritorio></app-escritorio>', 
})

export class AppComponent {
  title = 'AGNUX OS';
}
