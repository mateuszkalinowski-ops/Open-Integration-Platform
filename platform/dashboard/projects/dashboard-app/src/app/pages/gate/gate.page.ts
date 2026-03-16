import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTabsModule } from '@angular/material/tabs';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';

@Component({
  selector: 'app-gate-page',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatTabsModule,
    MatSnackBarModule,
    MatProgressSpinnerModule,
    MatTooltipModule,
  ],
  template: `
    <div class="gate">
      <div class="gate__card">
        <div class="gate__logo">
          <mat-icon class="gate__logo-icon">hub</mat-icon>
        </div>
        <h1 class="gate__title">Open Integration Platform</h1>
        <p class="gate__subtitle">by Pinquark.com</p>

        <mat-tab-group class="gate__tabs" animationDuration="200ms">
          <!-- Create workspace -->
          <mat-tab label="Create Workspace">
            <div class="gate__form">
              <p class="gate__hint">
                Create a new workspace to manage your integrations.
                You'll receive an API key to access your workspace later.
              </p>
              <mat-form-field appearance="outline" class="gate__field">
                <mat-label>Workspace name</mat-label>
                <input
                  matInput
                  [(ngModel)]="workspaceName"
                  placeholder="e.g. My Company"
                  (keyup.enter)="register()"
                  [disabled]="loading"
                />
                <mat-icon matSuffix>business</mat-icon>
              </mat-form-field>
              <button
                mat-raised-button
                color="primary"
                class="gate__btn"
                (click)="register()"
                [disabled]="!workspaceName.trim() || loading"
              >
                @if (loading) {
                  <mat-spinner diameter="20"></mat-spinner>
                } @else {
                  <mat-icon>add</mat-icon> Create workspace
                }
              </button>
            </div>
          </mat-tab>

          <!-- Enter existing key -->
          <mat-tab label="I Have a Key">
            <div class="gate__form">
              <p class="gate__hint">
                Enter your existing API key to access your workspace.
              </p>
              <mat-form-field appearance="outline" class="gate__field">
                <mat-label>API Key</mat-label>
                <input
                  matInput
                  [(ngModel)]="existingKey"
                  placeholder="pk_demo_..."
                  (keyup.enter)="validateKey()"
                  [disabled]="loading"
                />
                <mat-icon matSuffix>vpn_key</mat-icon>
              </mat-form-field>
              <button
                mat-raised-button
                color="primary"
                class="gate__btn"
                (click)="validateKey()"
                [disabled]="!existingKey.trim() || loading"
              >
                @if (loading) {
                  <mat-spinner diameter="20"></mat-spinner>
                } @else {
                  <mat-icon>login</mat-icon> Enter workspace
                }
              </button>
            </div>
          </mat-tab>
        </mat-tab-group>

        @if (generatedKey) {
          <div class="gate__key-display">
            <mat-icon class="gate__key-display-icon">check_circle</mat-icon>
            <p class="gate__key-display-label">
              Workspace <strong>{{ generatedTenantName }}</strong> created! Save your API key:
            </p>
            <div class="gate__key-row">
              <code class="gate__key-code">{{ generatedKey }}</code>
              <button mat-icon-button (click)="copyKey(generatedKey)" matTooltip="Copy">
                <mat-icon>content_copy</mat-icon>
              </button>
            </div>
            <button
              mat-raised-button
              color="accent"
              class="gate__btn"
              (click)="enterWithKey(generatedKey)"
            >
              <mat-icon>arrow_forward</mat-icon> Enter workspace
            </button>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    .gate {
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      background: linear-gradient(135deg, #1a237e 0%, #283593 50%, #3949ab 100%);
      padding: 24px;
    }
    .gate__card {
      background: #fff;
      border-radius: 16px;
      padding: 48px 40px;
      max-width: 480px;
      width: 100%;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
      text-align: center;
    }
    .gate__logo {
      margin-bottom: 16px;
    }
    .gate__logo-icon {
      font-size: 56px;
      width: 56px;
      height: 56px;
      color: #1a237e;
    }
    .gate__title {
      margin: 0;
      font-size: 24px;
      font-weight: 500;
      color: #212121;
    }
    .gate__subtitle {
      margin: 4px 0 24px;
      color: #757575;
      font-size: 14px;
    }
    .gate__tabs {
      text-align: left;
    }
    .gate__form {
      padding: 24px 0 8px;
    }
    .gate__hint {
      font-size: 13px;
      color: #616161;
      margin: 0 0 16px;
    }
    .gate__field {
      width: 100%;
    }
    .gate__btn {
      width: 100%;
      height: 48px;
      font-size: 15px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }
    .gate__key-display {
      margin-top: 24px;
      padding: 20px;
      background: #e8f5e9;
      border-radius: 12px;
      text-align: center;
    }
    .gate__key-display-icon {
      color: #2e7d32;
      font-size: 36px;
      width: 36px;
      height: 36px;
    }
    .gate__key-display-label {
      margin: 8px 0 12px;
      font-size: 14px;
      color: #424242;
    }
    .gate__key-row {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 4px;
      margin-bottom: 16px;
    }
    .gate__key-code {
      background: #fff;
      border: 1px solid #c8e6c9;
      border-radius: 6px;
      padding: 8px 12px;
      font-size: 13px;
      word-break: break-all;
      color: #1b5e20;
    }
  `],
})
export class GatePage {
  workspaceName = '';
  existingKey = '';
  loading = false;
  generatedKey = '';
  generatedTenantName = '';

  private readonly apiUrl: string;

  constructor(
    private readonly http: HttpClient,
    private readonly snackBar: MatSnackBar,
  ) {
    const cfg = (window as any).__PINQUARK_CONFIG__;
    this.apiUrl = cfg?.apiUrl || '';
  }

  register(): void {
    const name = this.workspaceName.trim();
    if (!name || this.loading) return;

    this.loading = true;
    this.http.post<{ api_key: string; tenant_name: string; tenant_slug: string }>(
      `${this.apiUrl}/api/v1/demo/register`,
      { workspace_name: name },
    ).subscribe({
      next: (res) => {
        this.loading = false;
        this.generatedKey = res.api_key;
        this.generatedTenantName = res.tenant_name;
      },
      error: (err) => {
        this.loading = false;
        const msg = err.status === 404
          ? 'Self-service registration is disabled. Contact your administrator for an API key.'
          : (err.error?.detail || 'Registration failed');
        this.snackBar.open(msg, 'OK', { duration: 6000 });
      },
    });
  }

  validateKey(): void {
    const key = this.existingKey.trim();
    if (!key || this.loading) return;

    this.loading = true;
    this.http.get<{ tenant_name?: string }>(`${this.apiUrl}/api/v1/me`, {
      headers: { 'X-API-Key': key },
    }).subscribe({
      next: (res) => {
        this.loading = false;
        if (res.tenant_name) {
          sessionStorage.setItem('pinquark_tenant_name', res.tenant_name);
        }
        this.enterWithKey(key);
      },
      error: (err) => {
        this.loading = false;
        if (err.status === 401 || err.status === 403) {
          this.snackBar.open('Invalid API key', 'OK', { duration: 4000 });
        } else {
          this.snackBar.open('Could not validate key', 'OK', { duration: 4000 });
        }
      },
    });
  }

  enterWithKey(key: string): void {
    sessionStorage.setItem('pinquark_api_key', key);
    if (this.generatedTenantName) {
      sessionStorage.setItem('pinquark_tenant_name', this.generatedTenantName);
    }
    window.location.href = '/connectors';
  }

  copyKey(key: string): void {
    if (!navigator.clipboard?.writeText) {
      this.snackBar.open('Clipboard not available — use HTTPS', 'OK', { duration: 3000 });
      return;
    }
    navigator.clipboard.writeText(key).then(
      () => this.snackBar.open('API key copied to clipboard', 'OK', { duration: 2000 }),
      () => this.snackBar.open('Failed to copy to clipboard', 'OK', { duration: 2000 }),
    );
  }
}
