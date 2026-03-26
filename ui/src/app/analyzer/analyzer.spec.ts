import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AnalyzerComponent } from './analyzer';
import { AnalyzeService } from './analyze.service';
import { of, throwError } from 'rxjs';
import { provideRouter } from '@angular/router';
import { Router } from '@angular/router';
import { vi } from 'vitest';

describe('AnalyzerComponent', () => {
  let component: AnalyzerComponent;
  let fixture: ComponentFixture<AnalyzerComponent>;
  let analyzeServiceSpy: any;
  let routerSpy: any;

  beforeEach(async () => {
    analyzeServiceSpy = { analyzeText: vi.fn(), analyzeFile: vi.fn() };
    routerSpy = { navigate: vi.fn() };

    await TestBed.configureTestingModule({
      imports: [AnalyzerComponent],
      providers: [
        { provide: AnalyzeService, useValue: analyzeServiceSpy },
        { provide: Router, useValue: routerSpy },
        provideRouter([])
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(AnalyzerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should navigate to conversations', () => {
    component.goToConversations();
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/conversations']);
  });

  it('should toggle sections', () => {
    expect(component.openSections['metadata']).toBe(true);
    component.toggleSection('metadata');
    expect(component.openSections['metadata']).toBe(false);
  });

  it('should analyze text successfully', () => {
    const mockRes = { call_id: '123' };
    analyzeServiceSpy.analyzeText.mockReturnValue(of(mockRes));
    
    component.transcriptText = 'hello world';
    component.analyzeTextCall();
    
    expect(component.isAnalyzing).toBe(false);
    expect(component.result).toEqual(mockRes);
  });

  it('should handle analyze text error', () => {
    analyzeServiceSpy.analyzeText.mockReturnValue(throwError(() => new Error('text error')));
    
    component.transcriptText = 'hello world';
    component.analyzeTextCall();
    
    expect(component.isAnalyzing).toBe(false);
    expect(component.errorMessage).toBe('text error');
  });

  it('should skip analyzeTextCall if empty', () => {
    component.transcriptText = '   ';
    component.analyzeTextCall();
    expect(analyzeServiceSpy.analyzeText).not.toHaveBeenCalled();
  });

  it('should handle file selection and drag-drop', () => {
    component.onDragOver(new Event('dragover') as DragEvent);
    expect(component.fileDragOver).toBe(true);
    
    component.onDragLeave(new Event('dragleave') as DragEvent);
    expect(component.fileDragOver).toBe(false);

    const mockFile = new File([''], 'test.mp3');
    component.onFileSelected({ target: { files: [mockFile] } });
    expect(component.selectedFile).toBe(mockFile);

    const mockDropEvent = new Event('drop') as any;
    mockDropEvent.dataTransfer = { files: [mockFile] };
    component.onDrop(mockDropEvent);
    expect(component.selectedFile).toBe(mockFile);
  });

  it('should trigger file input', () => {
    const spy = vi.spyOn(component.fileInput.nativeElement, 'click');
    component.triggerFileInput();
    expect(spy).toHaveBeenCalled();
  });

  it('should analyze file successfully', () => {
    const mockFile = new File([''], 'test.mp3');
    component.selectedFile = mockFile;
    const mockRes = { call_id: '123' };
    analyzeServiceSpy.analyzeFile.mockReturnValue(of(mockRes));
    
    component.analyzeFileCall();
    
    expect(component.isAnalyzing).toBe(false);
    expect(component.result).toEqual(mockRes);
  });

  it('should handle analyze file error', () => {
    const mockFile = new File([''], 'test.mp3');
    component.selectedFile = mockFile;
    analyzeServiceSpy.analyzeFile.mockReturnValue(throwError(() => ({ error: { detail: 'file error' } })));
    
    component.analyzeFileCall();
    
    expect(component.isAnalyzing).toBe(false);
    expect(component.errorMessage).toBe('file error');
  });

  it('should skip analyzeFileCall if no file', () => {
    component.selectedFile = null;
    component.analyzeFileCall();
    expect(analyzeServiceSpy.analyzeFile).not.toHaveBeenCalled();
  });

  it('should load trySample', () => {
    component.trySample();
    expect(component.transcriptText.length).toBeGreaterThan(0);
  });

  it('should get metadata entries', () => {
    const entries = component.getMetadataEntries({ a: 1, audio_url: 'b', c: 2 });
    expect(entries).toEqual([{key: 'a', value: '1'}, {key: 'c', value: '2'}]);
    expect(component.getMetadataEntries(null as any)).toEqual([]);
  });

  it('should return score color', () => {
    expect(component.getScoreColor(undefined)).toBe('var(--text-secondary)');
    expect(component.getScoreColor(9)).toBe('var(--success-color)');
  });

  it('should return score class', () => {
    expect(component.scoreClass(undefined)).toBe('badge-warning');
  });
});
