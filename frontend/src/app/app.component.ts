import { Component } from '@angular/core';
import { CommandBarComponent } from './components/command-bar/command-bar.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommandBarComponent], 
  template: '<app-command-bar></app-command-bar>', 
})

export class AppComponent {
  title = 'frontend';
}
