import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { SidebarComponent } from './layout/sidebar/sidebar';
import { TopbarComponent } from './layout/topbar/topbar';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, SidebarComponent, TopbarComponent],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  title = 'automated-call-dashboard';
}
