import { TestBed } from '@angular/core/testing';
import { ThemeService } from './theme';
import { vi } from 'vitest';

describe('ThemeService', () => {
  let service: ThemeService;
  let setItemSpy: any;
  let getItemSpy: any;
  let addClassSpy: any;
  let removeClassSpy: any;

  beforeEach(() => {
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: (query: any) => ({ matches: false })
    });
    
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn(),
        setItem: vi.fn(),
        removeItem: vi.fn(),
      },
      writable: true
    });
    setItemSpy = window.localStorage.setItem;
    getItemSpy = window.localStorage.getItem;
    getItemSpy.mockReturnValue(null);
    addClassSpy = vi.spyOn(document.body.classList, 'add');
    removeClassSpy = vi.spyOn(document.body.classList, 'remove');
    
    TestBed.configureTestingModule({});
    service = TestBed.inject(ThemeService);
  });

  it('should be created and default to light theme', () => {
    expect(service).toBeTruthy();
    expect(service.isDarkMode()).toBe(false);
    expect(removeClassSpy).toHaveBeenCalledWith('dark-theme');
  });

  it('should set dark theme if stored', () => {
    getItemSpy.mockReturnValue('dark');
    service.initTheme();
    expect(service.isDarkMode()).toBe(true);
    expect(addClassSpy).toHaveBeenCalledWith('dark-theme');
  });

  it('should toggle theme', () => {
    service.toggleTheme();
    expect(service.isDarkMode()).toBe(true);
    service.toggleTheme();
    expect(service.isDarkMode()).toBe(false);
  });
});
