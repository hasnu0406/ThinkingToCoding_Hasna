import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { CandidateProfile, SearchResponse, SearchHistory } from './models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = 'http://127.0.0.1:8000';

  getResumes(): Observable<CandidateProfile[]> {
    return this.http.get<CandidateProfile[] | { candidates: CandidateProfile[] }>(`${this.baseUrl}/resumes`).pipe(
      map((response) => Array.isArray(response) ? response : response.candidates)
    );
  }

  uploadResume(file: File): Observable<CandidateProfile> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<CandidateProfile>(`${this.baseUrl}/resume/upload`, formData);
  }

  searchCandidates(query: string): Observable<SearchResponse> {
    return this.http.post<SearchResponse>(`${this.baseUrl}/search`, { query });
  }

  botSearchCandidates(query: string, topN: number = 10): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/search/bot`, { query, top_n: topN });
  }

  refreshRecommendations(candidateId: string): Observable<{ candidate_id: string; recommended_jobs: string[] }> {
    return this.http.get<{ candidate_id: string; recommended_jobs: string[] }>(
      `${this.baseUrl}/resume/${candidateId}/recommend`
    );
  }

  deleteResume(candidateId: string): Observable<any> {
    return this.http.delete(`${this.baseUrl}/resume/${candidateId}`);
  }

  getSearchHistory(limit: number = 20): Observable<SearchHistory[]> {
    return this.http.get<SearchHistory[]>(`${this.baseUrl}/search/history?limit=${limit}`);
  }

  clearSearchHistory(): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.baseUrl}/search/history`);
  }
}
