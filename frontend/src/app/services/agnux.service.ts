import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface AgnuxResponse {
  status: string;
  user: string;
  response: string;
  detail?: string;
}

@Injectable({
  providedIn: 'root'
})
export class AgnuxService {
private apiUrl = 'http://10.10.0.66:8000/api/system/intent';

  constructor(private http: HttpClient) {}

  enviarPrompt(promptTexto: string): Observable<AgnuxResponse> {
    return this.http.post<AgnuxResponse>(this.apiUrl, { prompt: promptTexto });
  }
}