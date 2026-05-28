import { Pipe, PipeTransform } from '@angular/core';
import { DomSanitizer, SafeHtml, SafeResourceUrl } from '@angular/platform-browser';

@Pipe({
  name: 'safeHtml',
  standalone: true
})
export class SafeHtmlPipe implements PipeTransform {
  constructor(private sanitizer: DomSanitizer) {}
  transform(value: string | undefined): SafeHtml {
    return value ? this.sanitizer.bypassSecurityTrustHtml(value) : '';
  }
}

@Pipe({
  name: 'safeUrl',
  standalone: true
})
export class SafeUrlPipe implements PipeTransform {
  constructor(private sanitizer: DomSanitizer) {}
  transform(value: string | undefined): SafeResourceUrl {
    return value ? this.sanitizer.bypassSecurityTrustResourceUrl(value) : '';
  }
}
