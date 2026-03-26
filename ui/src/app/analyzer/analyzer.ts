import { Component, ElementRef, ViewChild, ChangeDetectorRef, NgZone } from '@angular/core';
import { CommonModule, TitleCasePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AnalyzeService, AnalyzeResult } from './analyze.service';

@Component({
  selector: 'app-analyzer',
  standalone: true,
  imports: [CommonModule, FormsModule, TitleCasePipe],
  // RouterLink not needed – we use Router.navigate programmatically
  templateUrl: './analyzer.html',
  styleUrl: './analyzer.css'
})
export class AnalyzerComponent {
  transcriptText: string = '';
  callId: string = '';
  isAnalyzing: boolean = false;
  result: AnalyzeResult | null = null;
  errorMessage: string | null = null;

  @ViewChild('fileInput') fileInput!: ElementRef;
  selectedFile: File | null = null;
  fileDragOver: boolean = false;

  openSections: Record<string, boolean> = {
    metadata: true,
    transcript: false,
    summary: true,
    quality: true,
    json: false
  };

  constructor(
    private analyzeService: AnalyzeService,
    private router: Router,
    private cdr: ChangeDetectorRef,
    private ngZone: NgZone
  ) {}

  goToConversations() {
    this.router.navigate(['/conversations']);
  }

  toggleSection(key: string) {
    this.openSections[key] = !this.openSections[key];
  }

  triggerFileInput() {
    this.fileInput.nativeElement.click();
  }

  onFileSelected(event: any) {
    const files = event.target.files;
    if (files.length > 0) {
      this.selectedFile = files[0];
      this.result = null;
      this.errorMessage = null;
    }
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
    this.fileDragOver = true;
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    this.fileDragOver = false;
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    this.fileDragOver = false;
    if (event.dataTransfer && event.dataTransfer.files.length > 0) {
      this.selectedFile = event.dataTransfer.files[0];
      this.result = null;
      this.errorMessage = null;
    }
  }

  analyzeTextCall() {
    if (!this.transcriptText.trim()) return;
    this.isAnalyzing = true;
    this.errorMessage = null;
    this.result = null;

    this.analyzeService.analyzeText(this.transcriptText, this.callId || undefined)
      .subscribe({
        next: (res) => {
          this.ngZone.run(() => {
            this.result = res;
            this.isAnalyzing = false;
            this.cdr.detectChanges();
          });
        },
        error: (err) => {
          this.ngZone.run(() => {
            this.errorMessage = err?.error?.detail || err.message || 'An error occurred.';
            this.isAnalyzing = false;
            this.cdr.detectChanges();
          });
        }
      });
  }

  analyzeFileCall() {
    if (!this.selectedFile) return;
    this.isAnalyzing = true;
    this.errorMessage = null;
    this.result = null;

    this.analyzeService.analyzeFile(this.selectedFile, this.callId || undefined)
      .subscribe({
        next: (res) => {
          this.ngZone.run(() => {
            this.result = res;
            this.isAnalyzing = false;
            this.cdr.detectChanges();
          });
        },
        error: (err) => {
          this.ngZone.run(() => {
            this.errorMessage = err?.error?.detail || err.message || 'An error occurred during file analysis.';
            this.isAnalyzing = false;
            this.cdr.detectChanges();
          });
        }
      });
  }

  trySample() {
    this.transcriptText = `Agent: Thank you for calling technical support. My name is Alex. How can I assist you today?
Customer: Hi Alex, I'm having trouble logging into my account. It keeps saying 'Invalid Password' even though I just reset it.
Agent: I apologize for the inconvenience. Can I please have your email address?
Customer: Yes, it's john.doe@example.com.
Agent: I see the recent password reset. It appears the system might be caching your old credentials. Could you try clearing your browser cache and cookies, then attempt to log in again?
Customer: Okay, I just did that. Let me try logging in... Yes, that worked! I'm in.
Agent: Excellent! I'm glad we could get that resolved. Is there anything else I can help you with?
Customer: No, that was the main issue. Thanks for your help.
Agent: You're welcome. Have a great day!`;
  }

  getMetadataEntries(metadata: Record<string, any>): { key: string; value: string }[] {
    if (!metadata) return [];
    return Object.entries(metadata)
      .filter(([key]) => key !== 'audio_url')
      .map(([key, value]) => ({ key, value: String(value) }));
  }

  getScoreColor(score: number | undefined): string {
    if (score == null) return 'var(--text-secondary)';
    if (score >= 8) return 'var(--success-color)';
    if (score >= 6) return 'var(--warning-color)';
    return 'var(--danger-color)';
  }

  scoreClass(score: number | undefined): string {
    if (score == null) return 'badge-warning';
    if (score >= 7) return 'badge-success';
    if (score >= 5) return 'badge-warning';
    return 'badge-danger';
  }
}
