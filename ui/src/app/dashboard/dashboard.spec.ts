import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DashboardComponent } from './dashboard';
import { CallsService } from '../conversations/calls.service';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';

describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;
  let mockCallsService: any;

  beforeEach(async () => {
    mockCallsService = { listCalls: vi.fn().mockReturnValue(of([])) };

    await TestBed.configureTestingModule({
      imports: [DashboardComponent],
      providers: [{ provide: CallsService, useValue: mockCallsService }]
    }).compileComponents();

    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
  });

  it('should create and handle empty data', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
    expect(component.isLoading).toBe(false);
    expect(component.totalCalls).toBe(0);
  });

  it('should compute stats correctly', () => {
    const calls = [
      { overall_score: 9.5, resolution_status: 'resolved', sentiment: 'positive', tags: ['Account Setup'] },
      { overall_score: 8.0, resolution_status: 'unresolved', sentiment: 'neutral', tags: ['Billing & Payment'] },
      { overall_score: 6.5, resolution_status: 'unknown', sentiment: 'negative', tags: ['Account Setup', 'Technical Issue'] },
      { overall_score: 5.0, resolution_status: 'resolved', sentiment: 'positive', tags: ['Technical Issue'] },
    ];
    mockCallsService.listCalls.mockReturnValue(of(calls));
    
    fixture.detectChanges();
    
    expect(component.totalCalls).toBe(4);
    expect(component.resolvedCalls).toBe(2);
    expect(component.unresolvedCalls).toBe(2);
    expect(component.resolutionRate).toBe(50);
    expect(component.avgQaScore).toBe(73); 
    
    expect(component.sentiment.pos).toBe(2);
    expect(component.sentiment.neu).toBe(1);
    expect(component.sentiment.neg).toBe(1);
    
    expect(component.topCategory).toBe('Account Setup');
  });

  it('should handle error from api', () => {
    mockCallsService.listCalls.mockReturnValue(throwError(() => new Error('error')));
    fixture.detectChanges();
    expect(component.isLoading).toBe(false);
  });
});
