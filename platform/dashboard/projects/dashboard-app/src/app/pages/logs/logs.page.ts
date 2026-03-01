import { Component } from '@angular/core';
import { OperationLogComponent } from '@pinquark/integrations';

@Component({
  selector: 'app-logs-page',
  standalone: true,
  imports: [OperationLogComponent],
  template: `
    <div class="logs-page">
      <div class="logs-page__header">
        <h2>Operation Log</h2>
      </div>
      <div class="logs-page__content">
        <pinquark-operation-log></pinquark-operation-log>
      </div>
    </div>
  `,
  styles: [`
    .logs-page {
      display: flex;
      flex-direction: column;
      height: calc(100vh - 64px - 48px);
    }
    .logs-page__header {
      margin-bottom: 16px;
      flex-shrink: 0;
    }
    .logs-page__header h2 {
      margin: 0;
    }
    .logs-page__content {
      flex: 1;
      min-height: 0;
      overflow: hidden;
    }
  `],
})
export class LogsPage {}
