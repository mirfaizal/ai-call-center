import { Injectable, signal } from '@angular/core';

@Injectable({
  providedIn: 'root',
})
export class ThemeService {
  isDarkMode = signal<boolean>(false);

  constructor() {
    this.initTheme();
  }

  initTheme() {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const storedTheme = localStorage.getItem('theme');
    
    if (storedTheme === 'dark' || (!storedTheme && prefersDark)) {
      this.setDarkTheme();
    } else {
      this.setLightTheme();
    }
  }

  toggleTheme() {
    if (this.isDarkMode()) {
      this.setLightTheme();
    } else {
      this.setDarkTheme();
    }
  }

  private setDarkTheme() {
    document.body.classList.add('dark-theme');
    localStorage.setItem('theme', 'dark');
    this.isDarkMode.set(true);
  }

  private setLightTheme() {
    document.body.classList.remove('dark-theme');
    localStorage.setItem('theme', 'light');
    this.isDarkMode.set(false);
  }
}
