import {
  Component,
  ElementRef,
  Input,
  OnChanges,
  OnDestroy,
  SimpleChanges,
  ViewChild,
  ViewEncapsulation,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatIconModule } from '@angular/material/icon';

declare const SwaggerUIBundle: any;

@Component({
  selector: 'pinquark-swagger-ui',
  standalone: true,
  imports: [CommonModule, MatProgressSpinnerModule, MatIconModule],
  template: `
    <div class="swagger-container">
      <div *ngIf="loading" class="swagger-loading">
        <mat-spinner diameter="40"></mat-spinner>
        <span>Loading API documentation...</span>
      </div>
      <div *ngIf="error" class="swagger-error">
        <mat-icon>error_outline</mat-icon>
        <span>{{ error }}</span>
      </div>
      <div #swaggerDom class="swagger-dom" [class.swagger-dom--hidden]="loading || error"></div>
    </div>
  `,
  styles: [`
    .swagger-container {
      min-height: 400px;
      position: relative;
    }
    .swagger-loading {
      display: flex;
      align-items: center;
      gap: 16px;
      justify-content: center;
      padding: 48px 0;
      color: var(--mat-sys-on-surface-variant, #666);
    }
    .swagger-error {
      display: flex;
      align-items: center;
      gap: 8px;
      justify-content: center;
      padding: 48px 0;
      color: #c62828;
    }
    .swagger-dom--hidden {
      display: none;
    }
    .swagger-dom .swagger-ui .topbar { display: none; }
    .swagger-dom .swagger-ui .info { margin: 16px 0; }
    .swagger-dom .swagger-ui .scheme-container { display: none; }
  `],
  encapsulation: ViewEncapsulation.None,
})
export class SwaggerUiComponent implements OnChanges, OnDestroy {
  @Input() specUrl = '';
  @Input() spec: object | null = null;
  @ViewChild('swaggerDom', { static: true }) swaggerDomRef!: ElementRef<HTMLDivElement>;

  loading = false;
  error = '';

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['specUrl'] || changes['spec']) {
      this.render();
    }
  }

  ngOnDestroy(): void {
    this.cleanup();
  }

  private cleanup(): void {
    if (this.swaggerDomRef?.nativeElement) {
      this.swaggerDomRef.nativeElement.innerHTML = '';
    }
  }

  private render(): void {
    this.cleanup();
    this.error = '';

    if (!this.specUrl && !this.spec) {
      return;
    }

    if (typeof SwaggerUIBundle === 'undefined') {
      this.error = 'Swagger UI library not loaded.';
      return;
    }

    this.loading = true;

    try {
      const config: Record<string, unknown> = {
        domNode: this.swaggerDomRef.nativeElement,
        deepLinking: false,
        layout: 'BaseLayout',
        defaultModelsExpandDepth: 1,
        defaultModelExpandDepth: 1,
        docExpansion: 'list',
        filter: true,
        tryItOutEnabled: false,
      };

      if (this.spec) {
        config['spec'] = this.spec;
      } else {
        config['url'] = this.specUrl;
      }

      SwaggerUIBundle(config);
      this.loading = false;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      this.error = 'Failed to render Swagger UI: ' + msg;
      this.loading = false;
    }
  }
}
