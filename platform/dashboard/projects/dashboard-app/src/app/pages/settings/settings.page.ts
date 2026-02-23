import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';

import { PinquarkApiService, HealthResponse } from '@pinquark/integrations';

@Component({
  selector: 'app-settings-page',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatListModule, MatIconModule],
  template: `
    <h2>Settings</h2>

    <mat-card>
      <mat-card-header>
        <mat-card-title>Platform Status</mat-card-title>
      </mat-card-header>
      <mat-card-content>
        @if (health) {
          <mat-list>
            <mat-list-item>
              <mat-icon matListItemIcon [class]="health.status === 'healthy' ? 'text-green' : 'text-red'">
                {{ health.status === 'healthy' ? 'check_circle' : 'error' }}
              </mat-icon>
              <span matListItemTitle>Status: {{ health.status }}</span>
            </mat-list-item>
            <mat-list-item>
              <mat-icon matListItemIcon>info</mat-icon>
              <span matListItemTitle>Version: {{ health.version }}</span>
            </mat-list-item>
            <mat-list-item>
              <mat-icon matListItemIcon>schedule</mat-icon>
              <span matListItemTitle>Uptime: {{ health.uptime_seconds | number:'1.0-0' }}s</span>
            </mat-list-item>
          </mat-list>
        }
      </mat-card-content>
    </mat-card>
  `,
  styles: [`
    .text-green { color: #4caf50; }
    .text-red { color: #f44336; }
  `],
})
export class SettingsPage implements OnInit {
  health: HealthResponse | null = null;

  constructor(private readonly api: PinquarkApiService) {}

  ngOnInit(): void {
    this.api.health().subscribe(data => this.health = data);
  }
}
