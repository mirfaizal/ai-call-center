import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration } from 'chart.js';
import { CallsService, CallSummaryRecord } from '../conversations/calls.service';



@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [BaseChartDirective, CommonModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css'
})
export class DashboardComponent implements OnInit {
  isLoading = true;
  totalCalls = 0;
  avgQaScore = 0;
  resolutionRate = 0;
  resolvedCalls = 0;
  unresolvedCalls = 0;
  topCategory = '—';

  sentiment = { pos: 0, neu: 0, neg: 0, posPCT: 0, neuPCT: 0, negPCT: 0 };

  qaHigh = 0; qaHighPCT = 0;    // 90–100
  qaMid  = 0; qaMidPCT  = 0;    // 75–89
  qaLow  = 0; qaLowPCT  = 0;    // 60–74
  qaVLow = 0; qaVLowPCT = 0;    // <60

  pieGradient = 'conic-gradient(var(--text-tertiary) 0% 100%)';

  public barChartData: ChartConfiguration<'bar'>['data'] = {
    labels: [],
    datasets: [{
      data: [0, 0, 0, 0, 0, 0, 0],
      backgroundColor: '#3b82f6',
      borderRadius: 2,
      barPercentage: 0.8,
      categoryPercentage: 0.9
    }]
  };

  public barChartOptions: ChartConfiguration<'bar'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: { enabled: true } },
    scales: {
      y: {
        beginAtZero: true,
        ticks: { stepSize: 1, font: { size: 11, family: 'Inter' } },
        grid: { color: 'rgba(0,0,0,0.05)', drawTicks: false }
      },
      x: {
        grid: { display: false },
        ticks: { font: { size: 10, family: 'Inter' } }
      }
    }
  };

  constructor(private callsService: CallsService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.callsService.listCalls().subscribe({
      next: calls => { this.computeStats(calls); },
      error: () => { this.isLoading = false; this.cdr.detectChanges(); }
    });
  }

  private computeStats(calls: CallSummaryRecord[]): void {
    this.totalCalls = calls.length;

    if (calls.length === 0) { this.isLoading = false; this.cdr.detectChanges(); return; }

    // QA (overall_score is 0–10; ×10 gives 0–100 display)
    const scored = calls.filter(c => c.overall_score != null);
    if (scored.length) {
      this.avgQaScore = Math.round(
        scored.reduce((s, c) => s + c.overall_score! * 10, 0) / scored.length
      );
    }

    // Resolution
    this.resolvedCalls   = calls.filter(c => c.resolution_status === 'resolved').length;
    this.unresolvedCalls = this.totalCalls - this.resolvedCalls;
    this.resolutionRate  = Math.round((this.resolvedCalls / this.totalCalls) * 100);

    // Sentiment
    const n = this.totalCalls;
    const pos = calls.filter(c => c.sentiment?.toLowerCase() === 'positive').length;
    const neu = calls.filter(c => c.sentiment?.toLowerCase() === 'neutral').length;
    const neg = calls.filter(c => c.sentiment?.toLowerCase() === 'negative').length;
    this.sentiment = {
      pos, neu, neg,
      posPCT: Math.round(pos / n * 100),
      neuPCT: Math.round(neu / n * 100),
      negPCT: Math.round(neg / n * 100)
    };

    // QA distribution buckets
    const sn = scored.length;
    this.qaHigh  = scored.filter(c => c.overall_score! >= 9).length;
    this.qaMid   = scored.filter(c => c.overall_score! >= 7.5 && c.overall_score! < 9).length;
    this.qaLow   = scored.filter(c => c.overall_score! >= 6   && c.overall_score! < 7.5).length;
    this.qaVLow  = scored.filter(c => c.overall_score! < 6).length;
    this.qaHighPCT = sn ? Math.round(this.qaHigh / sn * 100) : 0;
    this.qaMidPCT  = sn ? Math.round(this.qaMid  / sn * 100) : 0;
    this.qaLowPCT  = sn ? Math.round(this.qaLow  / sn * 100) : 0;
    this.qaVLowPCT = sn ? Math.round(this.qaVLow / sn * 100) : 0;
    const hi = this.qaHighPCT, mi = hi + this.qaMidPCT, lo = mi + this.qaLowPCT;
    this.pieGradient = `conic-gradient(
      var(--success-color) 0% ${hi}%,
      var(--primary-color) ${hi}% ${mi}%,
      var(--warning-color) ${mi}% ${lo}%,
      var(--danger-color)  ${lo}% 100%)`;

    // Category bar chart
    const uniqueCats = Array.from(
      new Set(calls.flatMap(c => c.tags || []))
    ).sort();

    if (uniqueCats.length === 0) {
      this.topCategory = '—';
      this.barChartData = {
        ...this.barChartData,
        labels: [],
        datasets: [{ ...this.barChartData.datasets[0], data: [] }]
      };
    } else {
      const catCounts = uniqueCats.map(
        cat => calls.filter(c => (c.tags || []).includes(cat)).length
      );
      const topIdx = catCounts.indexOf(Math.max(...catCounts));
      this.topCategory = catCounts[topIdx] > 0 ? uniqueCats[topIdx] : '—';
      
      this.barChartData = {
        ...this.barChartData,
        labels: uniqueCats.map(c => {
          const parts = c.split(' ');
          if (parts.length > 2) {
             return [parts.slice(0, 2).join(' '), parts.slice(2).join(' ')];
          } else if (parts.length === 2 && c.length > 12) {
             return parts;
          }
          return c;
        }),
        datasets: [{ ...this.barChartData.datasets[0], data: catCounts }]
      };
    }

    this.isLoading = false;
    this.cdr.detectChanges();
  }
}
