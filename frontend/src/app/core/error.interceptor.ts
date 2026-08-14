import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { catchError } from 'rxjs/operators';
import { throwError } from 'rxjs';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      let errorMessage = 'An unexpected error occurred.';
      
      if (error.error instanceof ErrorEvent) {
        // Client-side error
        errorMessage = error.error.message;
      } else {
        // Server-side error (FastAPI usually sends {"detail": "..."})
        if (error.error && error.error.detail) {
          errorMessage = typeof error.error.detail === 'string' ? error.error.detail : JSON.stringify(error.error.detail);
        } else {
          errorMessage = error.message;
        }
      }
      
      // Log to console for teammates/debugging
      console.error('[Global Interceptor] HTTP Error:', error);
      
      // Show native alert so users aren't left in the dark
      alert(`API Error: ${errorMessage}`);
      
      return throwError(() => error);
    })
  );
};
