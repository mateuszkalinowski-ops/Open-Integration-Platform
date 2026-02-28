import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-logs-page',
  standalone: true,
  imports: [CommonModule, MatToolbarModule, MatIconModule],
  template: `
    <mat-toolbar color="primary">
      <mat-icon>description</mat-icon>
      <span style="margin-left: 8px">Logs</span>
    </mat-toolbar>
    <div style="padding: 24px; text-align: center; color: #666">
      <mat-icon style="font-size: 64px; width: 64px; height: 64px">construction</mat-icon>
      <h2>Logs — Coming Soon</h2>
      <p>Workflow execution logs and audit trail will appear here.</p>
    </div>
  `,
})
export class LogsPage {}
