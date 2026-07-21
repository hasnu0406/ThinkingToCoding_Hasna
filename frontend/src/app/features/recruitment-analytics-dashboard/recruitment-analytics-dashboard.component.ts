import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CandidateProfile } from '../../core/data-type-definitions.model';

@Component({
  selector: 'app-recruitment-analytics-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './recruitment-analytics-dashboard.component.html',
  styleUrl: './recruitment-analytics-dashboard.component.css'
})
export class RecruitmentAnalyticsDashboardComponent {
  @Input() candidates: CandidateProfile[] = [];

  @Output() searchBySkill = new EventEmitter<string>();
  @Output() inspectCandidate = new EventEmitter<CandidateProfile>();
  @Output() navigateTo = new EventEmitter<string>();

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
}
