import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ConversationDetailsComponent } from './conversation-details';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ActivatedRoute } from '@angular/router';

describe('ConversationDetailsComponent', () => {
  let component: ConversationDetailsComponent;
  let fixture: ComponentFixture<ConversationDetailsComponent>;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ConversationDetailsComponent, HttpClientTestingModule],
      providers: [
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: { get: () => '123' } } }
        }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ConversationDetailsComponent);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should load call details on init', () => {
    fixture.detectChanges();
    const mockCall = {
      call_id: '123',
      final_transcript: 'System Event\nAgent: Hello\nCustomer: Hi',
      metadata: { customer: 'Bob', audio_url: 'http', agent: 'Alice', duration: '5m', category: 'Cat' },
      summary: { resolution_status: 'resolved', customer_sentiment: 'positive', tags: ['a', 'b'] },
      quality_scores: { overall_score: 9.5 }
    };

    const req = httpMock.expectOne('/api/calls/123');
    req.flush(mockCall);

    expect(component.call).toEqual(mockCall as any);
    expect(component.customerName).toBe('Bob');
    expect(component.audioUrl).toBe('http');
    expect(component.agentName).toBe('Alice');
    expect(component.duration).toBe('5m');
    expect(component.status).toBe('Resolved');
    expect(component.qaScore).toBe(95);
    expect(component.qaHighlightClass).toBe('highlight-success');
    expect(component.qaTextClass).toBe('text-success');
    expect(component.statusIconColor).toBe('var(--success-color)');
    
    expect(component.transcriptLines.length).toBe(3);
    expect(component.transcriptLines[0].speaker).toBe('System');
    expect(component.transcriptLines[1].speaker).toBe('Agent');
    expect(component.transcriptLines[2].speaker).toBe('Customer');

    expect(component.allTags.length).toBe(4); // cat, pos, a, b
  });

  it('should parse continued lines', () => {
    fixture.detectChanges();
    const req = httpMock.expectOne('/api/calls/123');
    req.flush({ final_transcript: 'Agent: Hello\n   continued' });
    expect(component.transcriptLines.length).toBe(1);
    expect(component.transcriptLines[0].text).toBe('Hello continued');
  });

  it('should handle load error', () => {
    fixture.detectChanges();
    const req = httpMock.expectOne('/api/calls/123');
    req.error(new ProgressEvent('error'));
    expect(component.error).toBe('Could not load call details.');
  });

  it('should change tabs', () => {
    component.setTab('qa');
    expect(component.activeTab).toBe('qa');
  });

  it('should return score widths and displays', () => {
    expect(component.scoreWidth(5, 10)).toBe('50%');
    expect(component.scoreDisplay(5, 10)).toBe('50/100');
  });

  it('should return fallback missing properties', () => {
    component.call = { summary: null, metadata: null, quality_scores: null, call_id: '' } as any;
    expect(component.customerName).toBe('—');
    expect(component.audioUrl).toBeNull();
    expect(component.agentName).toBe('AI Agent');
    expect(component.duration).toBe('—');
    expect(component.status).toBe('Unknown');
    expect(component.qaScore).toBe(0);
    expect(component.qaHighlightClass).toBe('');
    expect(component.qaTextClass).toBe('text-danger');
  });

  it('should return tag classes', () => {
    expect(component.getTagClass('positive')).toContain('success');
    expect(component.getTagClass('NEGATIVE')).toContain('danger');
    expect(component.getTagClass('neutral')).toContain('warning');
    expect(component.getTagClass('other')).toContain('primary');
  });
});

describe('ConversationDetailsComponent No ID', () => {
  it('should display error when no ID is provided', () => {
    TestBed.configureTestingModule({
      imports: [ConversationDetailsComponent, HttpClientTestingModule],
      providers: [
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: { get: () => null } } }
        }
      ]
    });
    const fixture = TestBed.createComponent(ConversationDetailsComponent);
    const component = fixture.componentInstance;
    fixture.detectChanges();
    
    expect(component.error).toBe('No call ID provided.');
  });
});
