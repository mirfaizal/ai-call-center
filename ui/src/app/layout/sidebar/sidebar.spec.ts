import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SidebarComponent } from './sidebar';
import { provideRouter } from '@angular/router';
import { vi } from 'vitest';

describe('SidebarComponent', () => {
  let component: SidebarComponent;
  let fixture: ComponentFixture<SidebarComponent>;

  beforeEach(async () => {
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: () => ({ matches: false })
    });
    try {
      Object.defineProperty(window, 'localStorage', {
        writable: true,
        value: { getItem: () => null, setItem: () => {}, removeItem: () => {} }
      });
    } catch(e) {}
    
    await TestBed.configureTestingModule({
      imports: [SidebarComponent],
      providers: [provideRouter([])]
    }).compileComponents();

    fixture = TestBed.createComponent(SidebarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should toggle theme', () => {
    const spy = vi.spyOn(component.themeService, 'toggleTheme');
    component.toggleTheme();
    expect(spy).toHaveBeenCalled();
  });
});
