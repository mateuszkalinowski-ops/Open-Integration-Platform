import { Component } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    MatSidenavModule,
    MatToolbarModule,
    MatListModule,
    MatIconModule,
    MatButtonModule,
  ],
  template: `
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
          <a mat-list-item routerLink="/settings" routerLinkActive="active">
            <mat-icon matListItemIcon>settings</mat-icon>
            <span matListItemTitle>Settings</span>
          </a>
        </mat-nav-list>
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
  `,
  styles: [`
    .app-container { height: 100vh; }
    .app-sidenav { width: 260px; }
    .app-sidenav__header { padding: 24px 16px 8px; }
    .app-sidenav__header h2 { margin: 0; font-size: 24px; }
    .app-sidenav__subtitle { font-size: 12px; opacity: 0.7; }
    .app-content { display: flex; flex-direction: column; }
    .app-main { padding: 24px; flex: 1; overflow: auto; }
    .active { background: rgba(0,0,0,0.04); }
  `],
})
export class AppComponent {
  pageTitle = 'Open Integration Platform by Pinquark.com';
}
