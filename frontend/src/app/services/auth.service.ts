import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private apiUrl = 'http://localhost:8000/api/auth';
  
  // Estado global reactivo con Signals
  public currentUser = signal<string | null>(null);
  public isAuthenticated = signal<boolean>(false);
  public enrolmentId = signal<string | null>(null);
  
  constructor(private http: HttpClient) {}
  
  loginFacial(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    
    return new Observable(observer => {
      this.http.post<any>(`${this.apiUrl}/facial-login`, formData).subscribe({
        next: (res) => {
          if (res.status === 'authenticated') {
            this.currentUser.set(res.user_id);
            this.isAuthenticated.set(true);
            this.enrolmentId.set(null);
          } else if (res.status === 'unknown_face') {
            // Pasamos a estado de inscripción en la UI
            this.enrolmentId.set(res.enrolment_id);
          }
          observer.next(res);
          observer.complete();
        },
        error: (err) => observer.error(err)
      });
    });
  }

  registrarPerfil(enrolmentId: string, nombre: string): Observable<any> {
    const payload = { enrolment_id: enrolmentId, nombre_usuario: nombre };
    
    return new Observable(observer => {
      this.http.post<any>(`${this.apiUrl}/register-profile`, payload).subscribe({
        next: (res) => {
          if (res.status === 'profile_created') {
             this.currentUser.set(res.user_id);
             this.isAuthenticated.set(true);
             this.enrolmentId.set(null);
          }
          observer.next(res);
          observer.complete();
        },
        error: (err) => observer.error(err)
      });
    });
  }
}
