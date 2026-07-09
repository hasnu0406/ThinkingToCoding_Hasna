import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { animate, style, transition, trigger } from '@angular/animations';
import { catchError, forkJoin, map, of } from 'rxjs';
import { ApiService } from './api.service';
import { CandidateProfile, SearchHistory } from './models';
import { ThreeBgComponent } from './three-bg.component';
import { ChatbotComponent } from './chatbot/chatbot.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, ThreeBgComponent, ChatbotComponent],
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
    ]),
    trigger('slideIn', [
      transition(':enter', [
        style({ transform: 'translateX(-20px)', opacity: 0 }),
        animate('400ms ease-out', style({ transform: 'translateX(0)', opacity: 1 }))
      ])
    ])
  ]
})
export class AppComponent {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(ApiService);

  readonly uploadForm = this.fb.group({
    resumes: [[] as File[], Validators.required]
  });

  readonly searchForm = this.fb.group({
    query: ['', Validators.required]
  });

  readonly authForm = this.fb.group({
    name: [''],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(6)]]
  });

  authMode: 'login' | 'register' = 'login';
  currentUser: { name: string; email: string; token: string } | null = null;
  isAuthLoading = false;
  authError = '';

  activeView: 'dashboard' | 'database' | 'upload' | 'search' | 'history' | 'chatbot' = 'dashboard';
  candidates: CandidateProfile[] = [];
  selectedCandidate: CandidateProfile | null = null;
  isUploading = false;
  isSearching = false;
  isLoadingHistory = false;
  errorMessage = '';
  messageType: 'error' | 'notice' = 'error';
  selectedFiles: File[] = [];
  hasActiveSearch = false;
  searchHistory: SearchHistory[] = [];
  chatSessions: any[] = [];
  chatSessionId: string | null = null;


  get totalUniqueSkillsCount(): number {
    const allSkills = this.candidates.flatMap(c => c.skills || []);
    return new Set(allSkills).size;
  }

  get topSkillsList(): { name: string; count: number }[] {
    const counts: { [key: string]: number } = {};
    this.candidates.flatMap(c => c.skills || []).forEach(skill => {
      counts[skill] = (counts[skill] || 0) + 1;
    });
    return Object.entries(counts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 12);
  }

  get recentCandidates(): CandidateProfile[] {
    return this.candidates.slice(0, 5);
  }

  setView(view: 'dashboard' | 'database' | 'upload' | 'search' | 'history' | 'chatbot'): void {
    this.activeView = view;
    if (view === 'history') {
      this.loadSearchHistory();
    }
  }

  inspectCandidate(candidate: CandidateProfile): void {
    this.selectCandidate(candidate);
    this.activeView = 'database';
  }

  get selectedFileSummary(): string {
    if (this.selectedFiles.length === 0) {
      return 'Choose Files';
    }
    if (this.selectedFiles.length === 1) {
      return this.selectedFiles[0].name;
    }
    return `${this.selectedFiles.length} resumes selected`;
  }

  constructor() {
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

  toggleAuthMode(): void {
    this.authMode = this.authMode === 'login' ? 'register' : 'login';
    this.authError = '';
    this.authForm.reset();

    const nameControl = this.authForm.get('name');
    if (this.authMode === 'register') {
      nameControl?.setValidators([Validators.required, Validators.minLength(2)]);
    } else {
      nameControl?.clearValidators();
    }
    nameControl?.updateValueAndValidity();
  }

  handleAuthSubmit(): void {
    if (this.authForm.invalid) {
      return;
    }
    const { name, email, password } = this.authForm.value;
    if (!email || !password) {
      return;
    }

    this.isAuthLoading = true;
    this.authError = '';

    if (this.authMode === 'login') {
      this.api.login(email, password).subscribe({
        next: (response) => {
          this.currentUser = {
            name: response.name,
            email: response.email,
            token: response.access_token
          };
          localStorage.setItem('currentUser', JSON.stringify(this.currentUser));
          this.isAuthLoading = false;
          this.authForm.reset();
          this.loadCandidates();
        },
        error: (err) => {
          this.isAuthLoading = false;
          this.authError = err?.error?.detail || 'Login failed. Please check your credentials.';
        }
      });
    } else {
      if (!name) {
        this.isAuthLoading = false;
        this.authError = 'Name is required for registration.';
        return;
      }
      this.api.register(name, email, password).subscribe({
        next: (regRes) => {
          this.authMode = 'login';
          this.isAuthLoading = false;
          this.authError = '';
          // Auto login
          this.api.login(email, password).subscribe({
            next: (response) => {
              this.currentUser = {
                name: response.name,
                email: response.email,
                token: response.access_token
              };
              localStorage.setItem('currentUser', JSON.stringify(this.currentUser));
              this.loadCandidates();
            }
          });
        },
        error: (err) => {
          this.isAuthLoading = false;
          this.authError = err?.error?.detail || 'Registration failed. Email might already be registered.';
        }
      });
    }
  }

  logout(): void {
    localStorage.removeItem('currentUser');
    this.currentUser = null;
    this.candidates = [];
    this.selectedCandidate = null;
    this.searchHistory = [];
    this.chatSessions = [];
    this.chatSessionId = null;
    this.activeView = 'dashboard';
  }

  loadCandidates(): void {
    this.api.getResumes().subscribe({
      next: (candidates) => {
        this.errorMessage = '';
        // Initialize rank_score for all candidates
        this.candidates = candidates.map(c => ({
          ...c,
          rank_score: c.rank_score || 0
        }));
        if (!this.selectedCandidate && this.candidates.length > 0) {
          this.selectCandidate(this.candidates[0]);
        }
      },
      error: (err) => {
        this.messageType = 'error';
        this.errorMessage =
          'Failed to load candidates. Start the backend with ".venv\\Scripts\\python.exe main.py" and retry.';
        console.error(err);
      }
    });
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const files = Array.from(input.files ?? []);
    this.selectedFiles = files;
    this.uploadForm.patchValue({ resumes: files });
  }

  clearSelectedFile(): void {
    this.uploadForm.reset();
    this.selectedFiles = [];
  }

  uploadResume(): void {
    const files = this.selectedFiles;
    if (files.length === 0) {
      return;
    }

    this.isUploading = true;
    this.errorMessage = '';
    this.messageType = 'error';

    const uploads = files.map((file) =>
      this.api.uploadResume(file).pipe(
        map((candidate) => ({
          fileName: file.name,
          candidate: candidate.duplicate ? null : candidate,
          duplicate: candidate.duplicate ? candidate : null,
          error: null as string | null
        })),
        catchError((err) =>
          of({
            fileName: file.name,
            candidate: null as CandidateProfile | null,
            duplicate: null as CandidateProfile | null,
            error: err?.error?.detail ?? 'Upload failed.'
          })
        )
      )
    );

    forkJoin(uploads).subscribe({
      next: (results) => {
        const uploadedCandidates = results.reduce<CandidateProfile[]>((items, result) => {
          if (result.candidate) {
            items.push({
              ...result.candidate,
              rank_score: result.candidate.rank_score || 0
            });
          }
          return items;
        }, []);

        if (uploadedCandidates.length > 0) {
          this.candidates = [...uploadedCandidates, ...this.candidates];
          this.selectCandidate(uploadedCandidates[0]);
          this.activeView = 'database';
        }

        const duplicateCandidates = results.reduce<CandidateProfile[]>((items, result) => {
          if (result.duplicate) {
            items.push({
              ...result.duplicate,
              rank_score: result.duplicate.rank_score || 0
            });
          }
          return items;
        }, []);
        const newDuplicateCandidates = duplicateCandidates.filter(
          (duplicate) => !this.candidates.some((candidate) => candidate.id === duplicate.id)
        );
        if (newDuplicateCandidates.length > 0) {
          this.candidates = [...newDuplicateCandidates, ...this.candidates];
          if (uploadedCandidates.length === 0) {
            this.selectCandidate(newDuplicateCandidates[0]);
            this.activeView = 'database';
          }
        }

        const duplicateFiles = results.filter((result) => result.duplicate).map((result) => result.fileName);
        const failedFiles = results.filter((result) => result.error).map((result) => result.fileName);
        const messages = [];
        if (duplicateFiles.length > 0) {
          messages.push(`Already uploaded: ${duplicateFiles.join(', ')}`);
        }
        if (failedFiles.length > 0) {
          messages.push(`Could not upload: ${failedFiles.join(', ')}`);
        }
        if (messages.length > 0) {
          this.messageType = failedFiles.length > 0 ? 'error' : 'notice';
          this.errorMessage = messages.join(' ');
        }

        this.clearSelectedFile();
        this.isUploading = false;
      },
      error: (err) => {
        this.messageType = 'error';
        this.errorMessage = err?.error?.detail ?? 'Upload failed. Check file formats and try again.';
        this.isUploading = false;
      }
    });
  }

  selectCandidate(candidate: CandidateProfile): void {
    this.selectedCandidate = candidate;
  }

  searchCandidates(): void {
    const query = this.searchForm.value.query?.trim();
    if (!query) {
      return;
    }

    this.isSearching = true;
    this.errorMessage = '';
    this.messageType = 'error';

    // Use the new bot search endpoint for AI-powered natural language search
    this.api.botSearchCandidates(query, 10).subscribe({
      next: (response) => {
        // Ensure all candidates have rank_score
        this.candidates = (response.candidates || []).map((c: any) => ({
          ...c,
          rank_score: c.rank_score || 0
        }));
        if (this.candidates.length > 0) {
          this.selectCandidate(this.candidates[0]);
        } else {
          this.selectedCandidate = null;
          this.messageType = 'notice';
          this.errorMessage = `No candidates found matching your search. Searched ${response.total_results} profiles with filters: ${JSON.stringify(response.filters_used)}`;
        }
        this.hasActiveSearch = true;
        this.isSearching = false;
      },
      error: (err) => {
        this.messageType = 'error';
        this.errorMessage = 'Search failed. Please try again.';
        this.isSearching = false;
        console.error(err);
      }
    });
  }

  clearSearch(): void {
    this.searchForm.reset();
    this.hasActiveSearch = false;
    this.errorMessage = '';
    this.messageType = 'error';
    this.loadCandidates();
  }

  searchBySkill(skill: string): void {
    const targetSkill = skill.toLowerCase().trim();
    this.isSearching = true;
    this.errorMessage = '';

    this.api.getResumes().subscribe({
      next: (allCandidates) => {
        // Filter candidates that have the target skill (case-insensitive)
        const filtered = allCandidates.filter(c => 
          (c.skills || []).some(s => s.toLowerCase().trim() === targetSkill)
        );

        this.candidates = filtered.map(c => ({
          ...c,
          rank_score: c.rank_score || 0
        }));

        if (this.candidates.length > 0) {
          this.selectCandidate(this.candidates[0]);
        } else {
          this.selectedCandidate = null;
          this.messageType = 'notice';
          this.errorMessage = `No candidates found with the skill "${skill}".`;
        }

        this.searchForm.patchValue({ query: skill });
        this.hasActiveSearch = true;
        this.isSearching = false;
        this.activeView = 'database';
      },
      error: (err) => {
        this.messageType = 'error';
        this.errorMessage = `Failed to filter candidates by skill "${skill}".`;
        this.isSearching = false;
        console.error(err);
      }
    });
  }

  refreshRecommendations(candidate: CandidateProfile): void {
    this.api.refreshRecommendations(candidate.id).subscribe({
      next: (response) => {
        this.candidates = this.candidates.map((item) =>
          item.id === candidate.id
            ? { ...item, recommended_jobs: response.recommended_jobs }
            : item
        );

        if (this.selectedCandidate?.id === candidate.id) {
          this.selectedCandidate = {
            ...this.selectedCandidate,
            recommended_jobs: response.recommended_jobs
          };
        }
      },
      error: (err) => {
        this.messageType = 'error';
        this.errorMessage = 'Failed to refresh recommendations.';
        console.error(err);
      }
    });
  }

  downloadResumePdf(candidate: CandidateProfile): void {
    if (!candidate || !candidate.id) {
      return;
    }
    this.api.downloadResumePdf(candidate.id);
  }

  deleteCandidate(candidate: CandidateProfile): void {
    if (!confirm(`Delete ${candidate.name}?`)) {
      return;
    }

    this.api.deleteResume(candidate.id).subscribe({
      next: () => {
        this.candidates = this.candidates.filter((item) => item.id !== candidate.id);
        if (this.selectedCandidate?.id === candidate.id) {
          this.selectedCandidate = this.candidates[0] ?? null;
        }
      },
      error: (err) => {
        this.messageType = 'error';
        this.errorMessage = 'Failed to delete candidate.';
        console.error(err);
      }
    });
  }

  loadSearchHistory(): void {
    this.isLoadingHistory = true;
    this.errorMessage = '';
    this.messageType = 'error';

    if (!this.currentUser) {
      this.isLoadingHistory = false;
      return;
    }

    this.api.getChatSessions(this.currentUser.email).subscribe({
      next: (sessions) => {
        this.chatSessions = sessions;
        this.isLoadingHistory = false;
      },
      error: (err) => {
        this.messageType = 'error';
        this.errorMessage = 'Failed to load chat history.';
        this.isLoadingHistory = false;
        console.error(err);
      }
    });
  }

  viewHistorySearch(session: any): void {
    this.chatSessionId = session.id;
    this.activeView = 'chatbot';
  }

  deleteChatSession(sessionId: string): void {
    if (!confirm('Are you sure you want to delete this chat session?')) {
      return;
    }
    this.api.deleteChatSession(sessionId).subscribe({
      next: () => {
        this.chatSessions = this.chatSessions.filter(s => s.id !== sessionId);
        if (this.chatSessionId === sessionId) {
          this.chatSessionId = null;
        }
      },
      error: (err) => {
        this.messageType = 'error';
        this.errorMessage = 'Failed to delete chat session.';
        console.error(err);
      }
    });
  }

  clearAllSearchHistory(): void {
    if (!confirm('Are you sure you want to clear all chat sessions? This action cannot be undone.')) {
      return;
    }
    if (!this.currentUser) return;
    this.isLoadingHistory = true;

    this.api.clearChatSessions(this.currentUser.email).subscribe({
      next: () => {
        this.chatSessions = [];
        this.chatSessionId = null;
        this.isLoadingHistory = false;
        this.messageType = 'notice';
        this.errorMessage = 'history cleared successfully.';
      },
      error: (err) => {
        this.messageType = 'error';
        this.errorMessage = 'Failed to clear chat sessions.';
        this.isLoadingHistory = false;
        console.error(err);
      }
    });
  }


  exportCSV(): void {
    window.open('http://127.0.0.1:8000/export/candidates', '_blank');
  }

}
