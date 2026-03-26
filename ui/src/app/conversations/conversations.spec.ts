import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ConversationsComponent } from './conversations';
import { CallsService } from './calls.service';
import { of, throwError } from 'rxjs';
import { provideRouter } from '@angular/router';
import { vi } from 'vitest';

describe('ConversationsComponent', () => {
  let component: ConversationsComponent;
  let fixture: ComponentFixture<ConversationsComponent>;
  let mockCallsService: any;

  beforeEach(async () => {
    mockCallsService = { listCalls: vi.fn() };

    await TestBed.configureTestingModule({
      imports: [ConversationsComponent],
      providers: [
        { provide: CallsService, useValue: mockCallsService },
        provideRouter([])
      ]
    }).compileComponents();
  });

  it('should load calls on init', () => {
    mockCallsService.listCalls.mockReturnValue(of([
      { call_id: '1', analyzed_at: '2026-01-01T00:00:00Z', overall_score: 8.5, sentiment: 'positive', summary_text: 'test', metadata: {}, tags: ['Account Setup'] },
      { call_id: '2', analyzed_at: '2026-01-01T00:00:00Z', overall_score: null, sentiment: null, summary_text: null, metadata: {}, tags: [] }
    ]));
    fixture = TestBed.createComponent(ConversationsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    expect(component.allConversations.length).toBe(2);
    expect(component.filteredConversations.length).toBe(2);
    expect(component.allConversations[0].qaScore).toBe(85);
    expect(component.allConversations[1].description).toBe('No summary available.');
  });

  it('should handle error', () => {
    mockCallsService.listCalls.mockReturnValue(throwError(() => new Error('err')));
    fixture = TestBed.createComponent(ConversationsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    expect(component.apiError).toBe(true);
  });

  it('should filter conversations correctly', () => {
    mockCallsService.listCalls.mockReturnValue(of([]));
    fixture = TestBed.createComponent(ConversationsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    component.allConversations = [
      { id: '1', customerName: 'Alice', agentName: 'Bob', category: 'Support', sentiment: 'positive', description: 'desc1', date: '', duration: '', qaScore: 10, tags: [], generatedTags: ['Support'] },
      { id: '2', customerName: 'Charlie', agentName: 'Dan', category: 'Sales', sentiment: 'negative', description: 'desc2', date: '', duration: '', qaScore: 10, tags: [], generatedTags: ['Sales'] }
    ];

    component.searchQuery = 'alice';
    expect(component.filteredConversations.length).toBe(1);
    
    component.searchQuery = '';
    component.selectedCategory = 'Sales';
    expect(component.filteredConversations.length).toBe(1);

    component.selectedCategory = '';
    component.selectedSentiment = 'negative';
    expect(component.filteredConversations.length).toBe(1);
  });

  it('should return correct badge class', () => {
    mockCallsService.listCalls.mockReturnValue(of([]));
    fixture = TestBed.createComponent(ConversationsComponent);
    component = fixture.componentInstance;

    expect(component.getTagClass('positive')).toContain('badge-success');
    expect(component.getTagClass('negative')).toContain('badge-danger');
    expect(component.getTagClass('neutral')).toContain('badge-warning');
  });
});
