import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface AnalyzeResult {
  call_id?: string;
  success?: boolean;
  errors?: string[];
  final_transcript?: string;
  summary?: {
    success: boolean;
    summary: string;
    key_points: string[];
    action_items: string[];
    customer_sentiment: string;
    resolution_status: string;
    tags: string[];
    error?: string;
  };
  quality_scores?: {
    success: boolean;
    empathy_score: number;
    professionalism_score: number;
    resolution_score: number;
    communication_score: number;
    overall_score: number;
    strengths: string[];
    improvements: string[];
    compliance_flags: string[];
    tone_assessment: string;
    error?: string;
  };
  call_record?: {
    call_id: string;
    input_type: string;
    metadata?: Record<string, any>;
  };
}

@Injectable({
  providedIn: 'root'
})
export class AnalyzeService {
  private apiUrl = '/api/analyze';

  constructor(private http: HttpClient) { }

  analyzeText(transcript: string, callId?: string): Observable<AnalyzeResult> {
    return this.http.post<AnalyzeResult>(`${this.apiUrl}/text`, {
      transcript_text: transcript,
      call_id: callId
    });
  }

  analyzeFile(file: File, callId?: string): Observable<AnalyzeResult> {
    const formData = new FormData();
    formData.append('file', file);
    if (callId) {
      formData.append('call_id', callId);
    }
    
    return this.http.post<AnalyzeResult>(`${this.apiUrl}/file`, formData);
  }
}
