import { Component, Inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { PINQUARK_CONFIG, PinquarkConfig } from '@pinquark/integrations';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    MatSidenavModule,
    MatToolbarModule,
    MatListModule,
    MatIconModule,
    MatButtonModule,
    MatTooltipModule,
    MatSnackBarModule,
  ],
  template: `
    @if (isGatePage) {
      <router-outlet></router-outlet>
    } @else {
      <mat-sidenav-container class="app-container">
        <mat-sidenav mode="side" opened class="app-sidenav">
          <div class="app-sidenav__header">
            <h2>Open Integration</h2>
            <span class="app-sidenav__subtitle">Platform by Pinquark.com</span>
          </div>
          <mat-nav-list>
            <a mat-list-item routerLink="/connectors" routerLinkActive="active">
              <mat-icon matListItemIcon>extension</mat-icon>
              <span matListItemTitle>Connectors</span>
            </a>
            <a mat-list-item routerLink="/credentials" routerLinkActive="active">
              <mat-icon matListItemIcon>key</mat-icon>
              <span matListItemTitle>Credentials</span>
            </a>
            <a mat-list-item routerLink="/flows" routerLinkActive="active">
              <mat-icon matListItemIcon>account_tree</mat-icon>
              <span matListItemTitle>Flows & Workflows</span>
            </a>
            <a mat-list-item routerLink="/logs" routerLinkActive="active">
              <mat-icon matListItemIcon>receipt_long</mat-icon>
              <span matListItemTitle>Operation Log</span>
            </a>
            <a mat-list-item routerLink="/verification" routerLinkActive="active">
              <mat-icon matListItemIcon>verified</mat-icon>
              <span matListItemTitle>Verification</span>
            </a>
            <a mat-list-item routerLink="/settings" routerLinkActive="active">
              <mat-icon matListItemIcon>settings</mat-icon>
              <span matListItemTitle>Settings</span>
            </a>
          </mat-nav-list>

          @if (tenantName) {
            <div class="app-sidenav__footer">
              <div class="app-sidenav__tenant">
                <mat-icon class="app-sidenav__tenant-icon">business</mat-icon>
                <span class="app-sidenav__tenant-name">{{ tenantName }}</span>
              </div>
              <div class="app-sidenav__actions">
                <button
                  mat-icon-button
                  matTooltip="Copy API key"
                  (click)="copyApiKey()"
                >
                  <mat-icon>content_copy</mat-icon>
                </button>
                <button
                  mat-icon-button
                  matTooltip="Switch workspace"
                  (click)="switchWorkspace()"
                >
                  <mat-icon>logout</mat-icon>
                </button>
              </div>
            </div>
          }
        </mat-sidenav>

        <mat-sidenav-content class="app-content">
          <mat-toolbar color="primary">
            <span>{{ pageTitle }}</span>
          </mat-toolbar>
          <main class="app-main">
            <router-outlet></router-outlet>
          </main>
        </mat-sidenav-content>
      </mat-sidenav-container>
    }
  `,
  styles: [`
    .app-container { height: 100vh; }
    .app-sidenav { width: 260px; display: flex; flex-direction: column; }
    .app-sidenav__header { padding: 24px 16px 8px; }
    .app-sidenav__header h2 { margin: 0; font-size: 24px; }
    .app-sidenav__subtitle { font-size: 12px; opacity: 0.7; }
    .app-content { display: flex; flex-direction: column; }
    .app-main { padding: 24px; flex: 1; overflow: auto; }
    .active { background: rgba(0,0,0,0.04); }

    .app-sidenav__footer {
      margin-top: auto;
      padding: 12px 16px;
      border-top: 1px solid rgba(0, 0, 0, 0.08);
    }
    .app-sidenav__tenant {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 4px;
    }
    .app-sidenav__tenant-icon {
      font-size: 18px;
      width: 18px;
      height: 18px;
      opacity: 0.7;
    }
    .app-sidenav__tenant-name {
      font-size: 13px;
      font-weight: 500;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .app-sidenav__actions {
      display: flex;
      gap: 4px;
    }
  `],
})
export class AppComponent {
  pageTitle = 'Open Integration Platform by Pinquark.com';
  tenantName = '';

  get isGatePage(): boolean {
    return this.router.url === '/gate';
  }

  constructor(
    private readonly router: Router,
    private readonly snackBar: MatSnackBar,
    @Inject(PINQUARK_CONFIG) private readonly config: PinquarkConfig,
  ) {
    this.tenantName = sessionStorage.getItem('pinquark_tenant_name') || '';
  }

  copyApiKey(): void {
    const key = sessionStorage.getItem('pinquark_api_key') || this.config.apiKey;
    if (key) {
      navigator.clipboard.writeText(key).then(() => {
        this.snackBar.open('API key copied to clipboard', 'OK', { duration: 2000 });
      });
    }
  }

  switchWorkspace(): void {
    sessionStorage.removeItem('pinquark_api_key');
    sessionStorage.removeItem('pinquark_tenant_name');
    window.location.href = '/gate';
  }
}
