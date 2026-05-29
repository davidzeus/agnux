import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private styleElementId = 'agnux-ia-runtime-styles';

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
