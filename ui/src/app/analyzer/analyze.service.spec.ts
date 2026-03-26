import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { AnalyzeService } from './analyze.service';

describe('AnalyzeService', () => {
  let service: AnalyzeService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [AnalyzeService]
    });
    service = TestBed.inject(AnalyzeService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should call analyzeText endpoint', () => {
    const mockRes = { call_id: '123' };
    service.analyzeText('test transcript', 'call1').subscribe(res => {
      expect(res).toEqual(mockRes);
    });

    const req = httpMock.expectOne('/api/analyze/text');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ transcript_text: 'test transcript', call_id: 'call1' });
    req.flush(mockRes);
  });

  it('should call analyzeFile endpoint', () => {
    const mockRes = { call_id: '123' };
    const mockFile = new File(['mock content'], 'test.txt', { type: 'text/plain' });
    
    service.analyzeFile(mockFile, 'call1').subscribe(res => {
      expect(res).toEqual(mockRes);
    });

    const req = httpMock.expectOne('/api/analyze/file');
    expect(req.request.method).toBe('POST');
    expect(req.request.body instanceof FormData).toBeTruthy();
    req.flush(mockRes);
  });

  it('should call analyzeFile without callId', () => {
    const mockRes = { call_id: '123' };
    const mockFile = new File(['mock content'], 'test.txt', { type: 'text/plain' });
    
    service.analyzeFile(mockFile).subscribe();

    const req = httpMock.expectOne('/api/analyze/file');
    expect(req.request.method).toBe('POST');
    expect(req.request.body instanceof FormData).toBeTruthy();
    req.flush(mockRes);
  });
});
