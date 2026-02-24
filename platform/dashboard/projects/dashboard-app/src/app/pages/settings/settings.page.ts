import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { PinquarkApiService, HealthResponse, AI_MODELS, AiModelType } from '@pinquark/integrations';

@Component({
  selector: 'app-settings-page',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatListModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatSnackBarModule,
  ],
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

    <mat-card class="ai-card">
      <mat-card-header>
        <mat-icon mat-card-avatar class="ai-card__icon">psychology</mat-icon>
        <mat-card-title>AI Workflow Agent</mat-card-title>
        <mat-card-subtitle>Configure the AI model used by the workflow chat agent</mat-card-subtitle>
      </mat-card-header>
      <mat-card-content>
        <mat-form-field appearance="outline" class="ai-field">
          <mat-label>AI Model</mat-label>
          <mat-select [(ngModel)]="aiModel">
            @for (m of aiModels; track m.value) {
              <mat-option [value]="m.value">{{ m.label }}</mat-option>
            }
          </mat-select>
        </mat-form-field>

        <mat-form-field appearance="outline" class="ai-field">
          <mat-label>{{ aiModel === 'gemini' ? 'Gemini API Key' : 'Anthropic API Key' }}</mat-label>
          <input
            matInput
            [type]="showApiKey ? 'text' : 'password'"
            [(ngModel)]="aiApiKey"
            [placeholder]="aiModel === 'gemini' ? 'AIza...' : 'sk-ant-...'"
          />
          <button mat-icon-button matSuffix (click)="showApiKey = !showApiKey" type="button">
            <mat-icon>{{ showApiKey ? 'visibility_off' : 'visibility' }}</mat-icon>
          </button>
        </mat-form-field>

        <div class="ai-actions">
          <button mat-raised-button color="primary" (click)="saveAiSettings()">
            <mat-icon>save</mat-icon> Save AI Settings
          </button>
        </div>
      </mat-card-content>
    </mat-card>
  `,
  styles: [`
    .text-green { color: #4caf50; }
    .text-red { color: #f44336; }
    .ai-card { margin-top: 24px; }
    .ai-card__icon {
      background: linear-gradient(135deg, #6a1b9a, #1976d2);
      color: #fff;
      border-radius: 50%;
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
    }
    .ai-field { width: 100%; margin-top: 16px; }
    .ai-actions { margin-top: 8px; display: flex; gap: 12px; }
  `],
})
export class SettingsPage implements OnInit {
  health: HealthResponse | null = null;

  aiModels = AI_MODELS;
  aiModel: AiModelType = 'gemini';
  aiApiKey = '';
  showApiKey = false;

  constructor(
    private readonly api: PinquarkApiService,
    private readonly snackBar: MatSnackBar,
  ) {}

  ngOnInit(): void {
    this.api.health().subscribe(data => this.health = data);
    this.loadAiSettings();
  }

  private loadAiSettings(): void {
    try {
      const stored = localStorage.getItem('pinquark_ai_settings');
      if (stored) {
        const parsed = JSON.parse(stored);
        this.aiModel = parsed.model || 'gemini';
        this.aiApiKey = parsed.apiKey || '';
      }
    } catch { /* ignore */ }
  }

  saveAiSettings(): void {
    localStorage.setItem('pinquark_ai_settings', JSON.stringify({
      model: this.aiModel,
      apiKey: this.aiApiKey,
    }));
    this.snackBar.open('AI settings saved', 'OK', { duration: 3000 });
  }
}
