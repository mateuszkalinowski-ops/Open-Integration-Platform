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
import { FormsModule } from '@angular/forms';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

declare const SwaggerUIBundle: any;

@Component({
  selector: 'pinquark-swagger-ui',
  standalone: true,
  imports: [CommonModule, FormsModule, MatProgressSpinnerModule, MatIconModule, MatFormFieldModule, MatInputModule],
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
      <div *ngIf="!loading && !error && rendered" class="swagger-filter">
        <mat-form-field appearance="outline" class="swagger-filter__field">
          <mat-icon matPrefix>search</mat-icon>
          <input matInput
                 [(ngModel)]="filterQuery"
                 (input)="onFilter()"
                 placeholder="Filter endpoints — type path or keyword, e.g. /orders, products, create..." />
          <button *ngIf="filterQuery" matSuffix mat-icon-button (click)="filterQuery = ''; onFilter()">
            <mat-icon>close</mat-icon>
          </button>
        </mat-form-field>
        <span class="swagger-filter__count" *ngIf="filterQuery">
          {{ visibleCount }} / {{ totalCount }} endpoints
        </span>
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
    .swagger-filter {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 8px 0;
    }
    .swagger-filter__field {
      flex: 1;
      max-width: 600px;
    }
    .swagger-filter__field mat-icon[matPrefix] {
      color: #999;
      margin-right: 4px;
    }
    .swagger-filter__count {
      font-size: 13px;
      color: var(--mat-sys-on-surface-variant, #666);
      white-space: nowrap;
    }
    .swagger-dom--hidden {
      display: none;
    }
    .swagger-dom .swagger-ui .topbar { display: none; }
    .swagger-dom .swagger-ui .filter-container { display: none; }
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
  rendered = false;
  filterQuery = '';
  visibleCount = 0;
  totalCount = 0;

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['specUrl'] || changes['spec']) {
      this.render();
    }
  }

  ngOnDestroy(): void {
    this.cleanup();
  }

  onFilter(): void {
    const dom = this.swaggerDomRef?.nativeElement;
    if (!dom) return;

    const q = this.filterQuery.trim().toLowerCase();
    const opblocks = dom.querySelectorAll<HTMLElement>('.opblock');
    this.totalCount = opblocks.length;
    let visible = 0;

    opblocks.forEach((block) => {
      if (!q) {
        block.style.display = '';
        visible++;
        return;
      }
      const path = block.querySelector('.opblock-summary-path, .opblock-summary-path__deprecated');
      const desc = block.querySelector('.opblock-summary-description');
      const method = block.querySelector('.opblock-summary-method');
      const text = [
        path?.textContent ?? '',
        desc?.textContent ?? '',
        method?.textContent ?? '',
      ].join(' ').toLowerCase();

      if (text.includes(q)) {
        block.style.display = '';
        visible++;
      } else {
        block.style.display = 'none';
      }
    });

    this.visibleCount = visible;

    const tagSections = dom.querySelectorAll<HTMLElement>('.opblock-tag-section');
    tagSections.forEach((section) => {
      const ops = section.querySelectorAll<HTMLElement>('.opblock');
      const anyVisible = Array.from(ops).some((op) => op.style.display !== 'none');
      section.style.display = anyVisible || !q ? '' : 'none';
    });
  }

  private cleanup(): void {
    if (this.swaggerDomRef?.nativeElement) {
      this.swaggerDomRef.nativeElement.innerHTML = '';
    }
    this.rendered = false;
    this.filterQuery = '';
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
        onComplete: () => {
          this.rendered = true;
          this.loading = false;
          const opblocks = this.swaggerDomRef?.nativeElement?.querySelectorAll('.opblock');
          this.totalCount = opblocks?.length ?? 0;
          this.visibleCount = this.totalCount;
        },
      };

      if (this.spec) {
        config['spec'] = this.spec;
      } else {
        config['url'] = this.specUrl;
      }

      SwaggerUIBundle(config);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      this.error = 'Failed to render Swagger UI: ' + msg;
      this.loading = false;
    }
  }
}
