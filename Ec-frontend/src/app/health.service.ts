import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface HealthResponse {
  status: string;
  service?: string;
  timestamp?: string;
}

@Injectable({
  providedIn: 'root'
})
export class HealthService {
  private readonly http = inject(HttpClient);
  private readonly healthUrl = '/api/v1/health';

  /**
   * Consulta el estado de salud del backend FastAPI a través del proxy de desarrollo (/api)
   */
  getHealth(): Observable<HealthResponse> {
    return this.http.get<HealthResponse>(this.healthUrl);
  }
}
