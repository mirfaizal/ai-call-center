import { Component, OnInit, ChangeDetectorRef, NgZone } from '@angular/core';
import { RouterLink, ActivatedRoute } from '@angular/router';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';

interface CallDetail {
  call_id: string;
  analyzed_at: string;
  metadata: Record<string, any>;
  summary: {
    summary: string;
    key_points: string[];
    action_items: string[];
    customer_sentiment: string;
    resolution_status: string;
    tags: string[];
  } | null;
  quality_scores: {
    empathy_score: number;
    professionalism_score: number;
    resolution_score: number;
    communication_score: number;
    overall_score: number;
    strengths: string[];
    improvements: string[];
    compliance_flags: string[];
    tone_assessment: string;
  } | null;
  final_transcript: string;
}

interface TranscriptLine {
  speaker: 'Agent' | 'Customer' | 'System';
  text: string;
}

@Component({
  selector: 'app-conversation-details',
  standalone: true,
  imports: [RouterLink, CommonModule],
  templateUrl: './conversation-details.html',
  styleUrl: './conversation-details.css'
})
export class ConversationDetailsComponent implements OnInit {
  activeTab = 'summary';
  isLoading = true;
  error: string | null = null;
  call: CallDetail | null = null;
  transcriptLines: TranscriptLine[] = [];

  constructor(
    private route: ActivatedRoute,
    private http: HttpClient,
    private cdr: ChangeDetectorRef,
    private ngZone: NgZone
  ) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (!id) { this.error = 'No call ID provided.'; this.isLoading = false; return; }
    this.http.get<CallDetail>(`/api/calls/${encodeURIComponent(id)}`).subscribe({
      next: data => {
        this.ngZone.run(() => {
          this.call = data;
          this.transcriptLines = this.parseTranscript(data.final_transcript);
          this.isLoading = false;
          this.cdr.detectChanges();
        });
      },
      error: () => {
        this.ngZone.run(() => {
          this.error = 'Could not load call details.';
          this.isLoading = false;
          this.cdr.detectChanges();
        });
      }
    });
  }

  setTab(tab: string): void { this.activeTab = tab; }

  get customerName(): string {
    return this.call?.metadata?.['customer'] || this.call?.call_id || '—';
  }
  get audioUrl(): string | null {
    return this.call?.metadata?.['audio_url'] || null;
  }
  get agentName(): string {
    return this.call?.metadata?.['agent'] || 'AI Agent';
  }
  get duration(): string {
    return this.call?.metadata?.['duration'] || '—';
  }
  get status(): string {
    const s = this.call?.summary?.resolution_status || 'unknown';
    return s.charAt(0).toUpperCase() + s.slice(1);
  }
  get qaScore(): number {
    if (!this.call?.quality_scores) return 0;
    return Math.round(this.call.quality_scores.overall_score * 10);
  }
  get qaHighlightClass(): string {
    return this.qaScore >= 85 ? 'highlight-success' : '';
  }
  get qaTextClass(): string {
    if (this.qaScore >= 85) return 'text-success';
    if (this.qaScore < 70) return 'text-danger';
    return '';
  }
  get statusIconColor(): string {
    return this.call?.summary?.resolution_status === 'resolved'
      ? 'var(--success-color)' : 'var(--text-tertiary)';
  }
  get allTags(): string[] {
    const tags: string[] = [];
    const meta = this.call?.metadata || {};
    if (meta['category']) tags.push(meta['category']);
    const sentiment = this.call?.summary?.customer_sentiment;
    if (sentiment) tags.push(sentiment);
    for (const t of (this.call?.summary?.tags || [])) {
      if (!tags.includes(t)) tags.push(t);
    }
    return tags;
  }

  scoreWidth(val: number, max = 10): string {
    return Math.round((val / max) * 100) + '%';
  }
  scoreDisplay(val: number, max = 10): string {
    return Math.round((val / max) * 100) + '/100';
  }
  getTagClass(tag: string): string {
    const t = tag.toLowerCase();
    if (t === 'positive') return 'badge badge-success';
    if (t === 'negative') return 'badge badge-danger';
    if (t === 'neutral')  return 'badge badge-warning';
    return 'badge badge-primary';
  }

  private parseTranscript(text: string): TranscriptLine[] {
    if (!text) return [];
    const lines: TranscriptLine[] = [];
    for (const raw of text.split('\n')) {
      const line = raw.trim();
      if (!line) continue;
      if (/^agent:/i.test(line)) {
        lines.push({ speaker: 'Agent', text: line.replace(/^agent:\s*/i, '') });
      } else if (/^customer:/i.test(line)) {
        lines.push({ speaker: 'Customer', text: line.replace(/^customer:\s*/i, '') });
      } else if (lines.length > 0) {
        lines[lines.length - 1].text += ' ' + line;
      } else {
        lines.push({ speaker: 'System', text: line });
      }
    }
    return lines;
  }
}
