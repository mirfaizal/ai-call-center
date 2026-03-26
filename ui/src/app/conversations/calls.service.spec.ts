import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { CallsService } from './calls.service';

describe('CallsService', () => {
  let service: CallsService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [CallsService]
    });
    service = TestBed.inject(CallsService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should fetch list of calls', () => {
    const mockCalls = [{ call_id: '123', overall_score: 9 }];
    service.listCalls().subscribe(res => {
      expect(res).toEqual(mockCalls as any);
    });

    const req = httpMock.expectOne('/api/calls');
    expect(req.request.method).toBe('GET');
    req.flush(mockCalls);
  });
});
