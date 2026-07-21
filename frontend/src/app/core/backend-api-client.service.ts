import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { CandidateProfile, SearchResponse, SearchHistory } from './data-type-definitions.model';

@Injectable({ providedIn: 'root' })
export class BackendApiClientService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = 'http://127.0.0.1:8000';

  login(email: string, password: string): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/auth/login`, { email, password });
  }

  register(name: string, email: string, password: string): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/auth/register`, { name, email, password });
  }

  getResumes(): Observable<CandidateProfile[]> {
    return this.http.get<CandidateProfile[] | { candidates: CandidateProfile[] }>(`${this.baseUrl}/resumes`).pipe(
      map((response) => Array.isArray(response) ? response : response.candidates)
    );
  }

  sendChatMessage(sessionId: string | null, email: string, message: string): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/chat`, {
      session_id: sessionId,
      user_email: email,
      message: message
    });
  }

  getChatSessions(email: string): Observable<any[]> {
    return this.http.get<any[]>(`${this.baseUrl}/chat/sessions?user_email=${encodeURIComponent(email)}`);
  }

  getChatSession(sessionId: string): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/chat/sessions/${sessionId}`);
  }

  deleteChatSession(sessionId: string): Observable<any> {
    return this.http.delete<any>(`${this.baseUrl}/chat/sessions/${sessionId}`);
  }

  clearChatSessions(email: string): Observable<any> {
    return this.http.delete<any>(`${this.baseUrl}/chat/sessions?user_email=${encodeURIComponent(email)}`);
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

  refreshRecommendations(candidateId: string): Observable<{ id: string; recommended_jobs: string[] }> {
    return this.http.get<{ id: string; recommended_jobs: string[] }>(
      `${this.baseUrl}/resume/${candidateId}/recommend`
    );
  }

  deleteResume(candidateId: string): Observable<any> {
    return this.http.delete<any>(`${this.baseUrl}/resume/${candidateId}`);
  }

  downloadResumePdf(candidateId: string): void {
    window.open(`${this.baseUrl}/resume/${candidateId}/download`, '_blank');
  }

  getSearchHistory(limit: number = 20): Observable<SearchHistory[]> {
    return this.http.get<SearchHistory[]>(`${this.baseUrl}/search/history?limit=${limit}`);
  }

  clearSearchHistory(): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.baseUrl}/search/history`);
  }
}
