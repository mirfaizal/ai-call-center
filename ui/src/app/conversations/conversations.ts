import { Component, OnInit, ChangeDetectorRef, NgZone } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CallsService } from './calls.service';


const SENTIMENTS = ['positive', 'neutral', 'negative'];

interface ConversationCard {
  id: string | number;
  customerName: string;
  agentName: string;
  date: string;
  duration: string;
  qaScore: number;
  category: string;
  sentiment: string;
  description: string;
  tags: string[];
  generatedTags: string[];
  fromApi?: boolean;
}

@Component({
  selector: 'app-conversations',
  standalone: true,
  imports: [RouterLink, CommonModule, FormsModule],
  templateUrl: './conversations.html',
  styleUrl: './conversations.css'
})
export class ConversationsComponent implements OnInit {
  searchQuery = '';
  selectedCategory = '';
  selectedSentiment = '';
  isLoading = false;
  apiError = false;

  categories: string[] = [];
  readonly sentiments = SENTIMENTS;

  allConversations: ConversationCard[] = [];

  constructor(
    private callsService: CallsService,
    private cdr: ChangeDetectorRef,
    private ngZone: NgZone
  ) {}

  ngOnInit(): void {
    this.loadApiCalls();
  }

  loadApiCalls(): void {
    this.isLoading = true;
    this.apiError = false;
    this.callsService.listCalls().subscribe({
      next: (apiCalls) => {
        this.ngZone.run(() => {
          this.allConversations = apiCalls.map(c => {
            const meta = c.metadata || {};
            const score = c.overall_score ?? 0;
            const sentiment = (c.sentiment || 'neutral').toLowerCase();
            const aiTags = c.tags || [];
            const tags: string[] = [sentiment, ...aiTags];
            if (meta['category']) tags.unshift(meta['category']);
            if (meta['department']) tags.push(meta['department']);

            return {
              id: c.call_id,
              customerName: meta['customer'] || c.call_id,
              agentName: meta['agent'] || 'AI Agent',
              date: new Date(c.analyzed_at).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }),
              duration: meta['duration'] || '—',
              qaScore: Math.round(score * 10),
              category: aiTags.length ? aiTags[0] : (meta['category'] || 'Uncategorized'),
              sentiment,
              description: c.summary_text || 'No summary available.',
              tags,
              generatedTags: aiTags,
              fromApi: true
            };
          });
          
          const genTagsSet = new Set<string>();
          this.allConversations.forEach(c => c.generatedTags.forEach(t => genTagsSet.add(t)));
          this.categories = Array.from(genTagsSet).sort();
          this.isLoading = false;
          this.cdr.detectChanges();
        });
      },
      error: () => {
        this.ngZone.run(() => {
          this.apiError = true;
          this.isLoading = false;
          this.cdr.detectChanges();
        });
      }
    });
  }

  get filteredConversations(): ConversationCard[] {
    return this.allConversations.filter(c => {
      const matchText = !this.searchQuery ||
        c.customerName.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
        c.agentName.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
        c.description.toLowerCase().includes(this.searchQuery.toLowerCase());
      const matchCat = !this.selectedCategory || c.generatedTags.includes(this.selectedCategory);
      const matchSent = !this.selectedSentiment || c.sentiment === this.selectedSentiment;
      return matchText && matchCat && matchSent;
    });
  }

  getTagClass(tag: string): string {
    const lowerTag = tag.toLowerCase();
    if (lowerTag === 'positive') return 'badge badge-success';
    if (lowerTag === 'negative') return 'badge badge-danger';
    if (lowerTag === 'neutral') return 'badge badge-warning';
    return 'badge badge-primary';
  }
}
