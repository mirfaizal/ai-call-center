import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface CallSummaryRecord {
  call_id: string;
  analyzed_at: string;
  metadata: Record<string, any>;
  overall_score: number | null;
  sentiment: string | null;
  resolution_status: string | null;
  summary_text: string | null;
  tags?: string[];
}

@Injectable({ providedIn: 'root' })
export class CallsService {
  constructor(private http: HttpClient) {}

  listCalls(): Observable<CallSummaryRecord[]> {
    return this.http.get<CallSummaryRecord[]>('/api/calls');
  }
}
