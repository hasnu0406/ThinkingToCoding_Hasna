import { Component, EventEmitter, inject, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { catchError, forkJoin, map, of } from 'rxjs';
import { ApiService } from '../api.service';
import { CandidateProfile } from '../models';

@Component({
  selector: 'app-upload',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './upload.component.html',
  styleUrl: './upload.component.css'
})
export class UploadComponent {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(ApiService);

  @Output() uploadComplete = new EventEmitter<{
    uploaded: CandidateProfile[];
    duplicates: CandidateProfile[];
    errors: string[];
    notices: string[];
  }>();

  readonly uploadForm = this.fb.group({
    resumes: [[] as File[], Validators.required]
  });

  isUploading = false;
  selectedFiles: File[] = [];

  get selectedFileSummary(): string {
    if (this.selectedFiles.length === 0) return 'Choose Files';
    if (this.selectedFiles.length === 1) return this.selectedFiles[0].name;
    return `${this.selectedFiles.length} resumes selected`;
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
    if (files.length === 0) return;

    this.isUploading = true;

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
        const uploaded = results.reduce<CandidateProfile[]>((items, result) => {
          if (result.candidate) items.push({ ...result.candidate, rank_score: result.candidate.rank_score || 0 });
          return items;
        }, []);

        const duplicates = results.reduce<CandidateProfile[]>((items, result) => {
          if (result.duplicate) items.push({ ...result.duplicate, rank_score: result.duplicate.rank_score || 0 });
          return items;
        }, []);

        const errors = results.filter(r => r.error).map(r => r.fileName);
        const notices = results.filter(r => r.duplicate).map(r => r.fileName);

        this.clearSelectedFile();
        this.isUploading = false;
        this.uploadComplete.emit({ uploaded, duplicates, errors, notices });
      },
      error: (err) => {
        this.isUploading = false;
        this.uploadComplete.emit({
          uploaded: [],
          duplicates: [],
          errors: [err?.error?.detail ?? 'Upload failed. Check file formats and try again.'],
          notices: []
        });
      }
    });
  }
}
