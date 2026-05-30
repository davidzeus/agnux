import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private styleElementId = 'agnux-ia-runtime-styles';

  constructor(private http: HttpClient) {}

  loadBaseStyle(userId: string) {
    const finalUrl = `/api/theme/${userId}`;
    
    this.http.get(finalUrl, { responseType: 'text' }).subscribe({
      next: (css) => {
        if (css && !css.includes('default_theme')) {
          console.log(`💾 [THEME ENGINE] Estilo físico cargado para ${userId}`);
          this.injectRawCss(css);
        }
      },
      error: (err) => console.log('Sin estilo físico previo:', err)
    });
  }

  injectRawCss(cssCode: string) {
    console.log("🎨 [THEME ENGINE] Recibido bloque de CSS libre desde el Kernel. Inyectando...");

    // 1. Buscamos si ya existe el tag <style> de la IA en el <head>
    let styleElement = document.getElementById(this.styleElementId) as HTMLStyleElement;

    if (!styleElement) {
      // 2. Si es la primera vez que muta, creamos el elemento dinámicamente
      styleElement = document.createElement('style');
      styleElement.id = this.styleElementId;
      styleElement.type = 'text/css';
      document.head.appendChild(styleElement);
    }

    // 3. Clavamos el código CSS puro adentro del tag. El navegador recalcula todo al instante.
    // Hack de Anarquía: Inyectamos !important en todas las reglas para romper el ViewEncapsulation de Angular
    const cssWithImportant = cssCode.replace(/([^!])\s*;/g, '$1 !important;');
    styleElement.textContent = cssWithImportant;
  }
}
