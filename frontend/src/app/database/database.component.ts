import { Component, EventEmitter, inject, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { animate, style, transition, trigger } from '@angular/animations';
import { ApiService } from '../api.service';
import { CandidateProfile } from '../models';

@Component({
  selector: 'app-database',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './database.component.html',
  styleUrl: './database.component.css',
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
export class DatabaseComponent {
  private readonly api = inject(ApiService);

  @Input() candidates: CandidateProfile[] = [];
  @Input() selectedCandidate: CandidateProfile | null = null;
  @Input() isSearching = false;

  @Output() candidateSelected = new EventEmitter<CandidateProfile>();
  @Output() candidateDeleted = new EventEmitter<string>();
  @Output() recommendRefreshed = new EventEmitter<{ id: string; recommended_jobs: string[] }>();
  @Output() refreshAll = new EventEmitter<void>();
  @Output() searchBySkill = new EventEmitter<string>();
  @Output() navigateToUpload = new EventEmitter<void>();

  selectCandidate(candidate: CandidateProfile): void {
    this.candidateSelected.emit(candidate);
  }

  deleteCandidate(candidate: CandidateProfile): void {
    if (!confirm(`Delete ${candidate.name}?`)) return;
    this.api.deleteResume(candidate.id).subscribe({
      next: () => this.candidateDeleted.emit(candidate.id),
      error: () => console.error('Failed to delete candidate.')
    });
  }

  refreshRecommendations(candidate: CandidateProfile): void {
    this.api.refreshRecommendations(candidate.id).subscribe({
      next: (response) => this.recommendRefreshed.emit(response),
      error: () => console.error('Failed to refresh recommendations.')
    });
  }

  exportCSV(): void {
    window.open('http://127.0.0.1:8000/export/candidates', '_blank');
  }
}
