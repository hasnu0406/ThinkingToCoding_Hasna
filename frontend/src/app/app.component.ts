import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { animate, style, transition, trigger } from '@angular/animations';
import { BackendApiClientService } from './core/backend-api-client.service';
import { CandidateProfile } from './core/data-type-definitions.model';
import { InteractiveParticleBackgroundComponent } from './shared/components/interactive-particle-background/interactive-particle-background.component';
import { ConversationalCvSearchComponent } from './features/conversational-cv-search/conversational-cv-search.component';
import { UserAccessControlComponent } from './features/user-access-control/user-access-control.component';
import { RecruitmentAnalyticsDashboardComponent } from './features/recruitment-analytics-dashboard/recruitment-analytics-dashboard.component';
import { ResumeFileParserComponent } from './features/resume-file-parser/resume-file-parser.component';
import { CandidateProfileDatabaseComponent } from './features/candidate-profile-database/candidate-profile-database.component';
import { PastSearchesLogComponent } from './features/past-searches-log/past-searches-log.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    InteractiveParticleBackgroundComponent,
    ConversationalCvSearchComponent,
    UserAccessControlComponent,
    RecruitmentAnalyticsDashboardComponent,
    ResumeFileParserComponent,
    CandidateProfileDatabaseComponent,
    PastSearchesLogComponent
  ],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
  animations: [
    trigger('fadeInOut', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate('300ms ease-in', style({ opacity: 1 }))
      ]),
      transition(':leave', [
        animate('300ms ease-out', style({ opacity: 0 }))
      ])
    ])
  ]
})
export class AppComponent {
  private readonly api = inject(BackendApiClientService);

  // ── Auth State ────────────────────────────────────────────────────
  currentUser: { name: string; email: string; token: string } | null = null;



  // ── Navigation State ──────────────────────────────────────────────
  activeView: 'dashboard' | 'database' | 'upload' | 'search' | 'history' | 'chatbot' = 'dashboard';

  // ── Shared Candidate State ────────────────────────────────────────
  candidates: CandidateProfile[] = [];
  selectedCandidate: CandidateProfile | null = null;
  isSearching = false;
  hasActiveSearch = false;

  // ── Notification State ────────────────────────────────────────────
  errorMessage = '';
  messageType: 'error' | 'notice' = 'error';

  // ── Chat State ────────────────────────────────────────────────────
  chatSessions: any[] = [];
  chatSessionId: string | null = null;
  isLoadingHistory = false;

  constructor() {
    document.documentElement.setAttribute('data-theme', 'light');

    const savedUser = localStorage.getItem('currentUser');
    if (savedUser) {
      try {
        this.currentUser = JSON.parse(savedUser);
        this.loadCandidates();
      } catch (e) {
        localStorage.removeItem('currentUser');
      }
    }
  }



  // ── Auth Handlers ─────────────────────────────────────────────────
  onLoginSuccess(user: { name: string; email: string; token: string }): void {
    this.currentUser = user;
    localStorage.setItem('currentUser', JSON.stringify(user));
    this.loadCandidates();
  }

  logout(): void {
    localStorage.removeItem('currentUser');
    this.currentUser = null;
    this.candidates = [];
    this.selectedCandidate = null;
    this.chatSessions = [];
    this.chatSessionId = null;
    this.activeView = 'dashboard';
  }

  // ── Navigation ────────────────────────────────────────────────────
  setView(view: 'dashboard' | 'database' | 'upload' | 'search' | 'history' | 'chatbot'): void {
    this.activeView = view;
    if (view === 'history') this.loadSearchHistory();
  }

  // ── Candidates ────────────────────────────────────────────────────
  loadCandidates(): void {
    this.api.getResumes().subscribe({
      next: (candidates) => {
        this.errorMessage = '';
        this.candidates = candidates.map(c => ({ ...c, rank_score: c.rank_score || 0 }));
        if (!this.selectedCandidate && this.candidates.length > 0) {
          this.selectedCandidate = this.candidates[0];
        }
      },
      error: () => {
        this.messageType = 'error';
        this.errorMessage = 'Failed to load candidates. Start the backend and retry.';
      }
    });
  }

  selectCandidate(candidate: CandidateProfile): void {
    this.selectedCandidate = candidate;
  }

  inspectCandidate(candidate: CandidateProfile): void {
    this.selectedCandidate = candidate;
    this.activeView = 'database';
  }

  searchBySkill(skill: string): void {
    const targetSkill = skill.toLowerCase().trim();
    this.isSearching = true;
    this.errorMessage = '';

    this.api.getResumes().subscribe({
      next: (allCandidates) => {
        const filtered = allCandidates.filter(c =>
          (c.skills || []).some(s => s.toLowerCase().trim() === targetSkill)
        );
        this.candidates = filtered.map(c => ({ ...c, rank_score: c.rank_score || 0 }));
        if (this.candidates.length > 0) {
          this.selectedCandidate = this.candidates[0];
        } else {
          this.selectedCandidate = null;
          this.messageType = 'notice';
          this.errorMessage = `No candidates found with the skill "${skill}".`;
        }
        this.hasActiveSearch = true;
        this.isSearching = false;
        this.activeView = 'database';
      },
      error: () => {
        this.messageType = 'error';
        this.errorMessage = `Failed to filter candidates by skill "${skill}".`;
        this.isSearching = false;
      }
    });
  }

  onCandidateDeleted(id: string): void {
    this.candidates = this.candidates.filter(c => c.id !== id);
    if (this.selectedCandidate?.id === id) {
      this.selectedCandidate = this.candidates[0] ?? null;
    }
  }

  onRecommendRefreshed(response: { id: string; recommended_jobs: string[] }): void {
    this.candidates = this.candidates.map(c =>
      c.id === response.id ? { ...c, recommended_jobs: response.recommended_jobs } : c
    );
    if (this.selectedCandidate?.id === response.id) {
      this.selectedCandidate = { ...this.selectedCandidate, recommended_jobs: response.recommended_jobs };
    }
  }

  // ── Upload Handlers ───────────────────────────────────────────────
  onUploadComplete(result: {
    uploaded: CandidateProfile[];
    duplicates: CandidateProfile[];
    errors: string[];
    notices: string[];
  }): void {
    const { uploaded, duplicates, errors, notices } = result;

    if (uploaded.length > 0) {
      this.candidates = [...uploaded, ...this.candidates];
      this.selectedCandidate = uploaded[0];
      this.activeView = 'database';
    }

    const newDuplicates = duplicates.filter(d => !this.candidates.some(c => c.id === d.id));
    if (newDuplicates.length > 0) {
      this.candidates = [...newDuplicates, ...this.candidates];
      if (uploaded.length === 0) {
        this.selectedCandidate = newDuplicates[0];
        this.activeView = 'database';
      }
    }

    const messages: string[] = [];
    if (notices.length > 0) messages.push(`Already uploaded: ${notices.join(', ')}`);
    if (errors.length > 0) messages.push(`Could not upload: ${errors.join(', ')}`);
    if (messages.length > 0) {
      this.messageType = errors.length > 0 ? 'error' : 'notice';
      this.errorMessage = messages.join(' ');
    }
  }

  // ── Chat History Handlers ─────────────────────────────────────────
  loadSearchHistory(): void {
    if (!this.currentUser) return;
    this.isLoadingHistory = true;
    this.errorMessage = '';

    this.api.getChatSessions(this.currentUser.email).subscribe({
      next: (sessions) => {
        this.chatSessions = sessions;
        this.isLoadingHistory = false;
      },
      error: () => {
        this.messageType = 'error';
        this.errorMessage = 'Failed to load chat history.';
        this.isLoadingHistory = false;
      }
    });
  }

  viewHistorySession(session: any): void {
    this.chatSessionId = session.id;
    this.activeView = 'chatbot';
  }

  deleteChatSession(sessionId: string): void {
    if (!confirm('Are you sure you want to delete this chat session?')) return;
    this.api.deleteChatSession(sessionId).subscribe({
      next: () => {
        this.chatSessions = this.chatSessions.filter(s => s.id !== sessionId);
        if (this.chatSessionId === sessionId) this.chatSessionId = null;
      },
      error: () => {
        this.messageType = 'error';
        this.errorMessage = 'Failed to delete chat session.';
      }
    });
  }

  clearAllChatSessions(): void {
    if (!confirm('Clear all chat sessions? This cannot be undone.')) return;
    if (!this.currentUser) return;
    this.isLoadingHistory = true;

    this.api.clearChatSessions(this.currentUser.email).subscribe({
      next: () => {
        this.chatSessions = [];
        this.chatSessionId = null;
        this.isLoadingHistory = false;
        this.messageType = 'notice';
        this.errorMessage = 'History cleared successfully.';
      },
      error: () => {
        this.messageType = 'error';
        this.errorMessage = 'Failed to clear chat sessions.';
        this.isLoadingHistory = false;
      }
    });
  }
}
