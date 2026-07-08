import { Component, EventEmitter, inject, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { animate, style, transition, trigger } from '@angular/animations';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-auth',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './auth.component.html',
  styleUrl: './auth.component.css',
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
export class AuthComponent {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(ApiService);

  @Output() loginSuccess = new EventEmitter<{ name: string; email: string; token: string }>();

  authMode: 'login' | 'register' = 'login';
  isAuthLoading = false;
  authError = '';

  readonly authForm = this.fb.group({
    name: [''],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(6)]]
  });

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
    if (this.authForm.invalid) return;
    const { name, email, password } = this.authForm.value;
    if (!email || !password) return;

    this.isAuthLoading = true;
    this.authError = '';

    if (this.authMode === 'login') {
      this.api.login(email, password).subscribe({
        next: (response) => {
          this.isAuthLoading = false;
          this.authForm.reset();
          this.loginSuccess.emit({
            name: response.name,
            email: response.email,
            token: response.access_token
          });
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
        next: () => {
          this.authMode = 'login';
          this.isAuthLoading = false;
          this.authError = '';
          this.api.login(email, password).subscribe({
            next: (response) => {
              this.loginSuccess.emit({
                name: response.name,
                email: response.email,
                token: response.access_token
              });
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
}
