import {
  Component,
  ElementRef,
  EventEmitter,
  Input,
  Output,
  ViewChild,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { PinquarkApiService } from '../../services/pinquark-api.service';
import {
  AiChatMessage,
  AiModelType,
  AiGenerateResponse,
  AI_MODELS,
  Connector,
  WorkflowNode,
  WorkflowEdge,
} from '../../models';

interface ChatEntry {
  role: 'user' | 'assistant';
  content: string;
  nodes?: WorkflowNode[];
  edges?: WorkflowEdge[];
  name?: string;
  description?: string;
  timestamp: Date;
}

@Component({
  selector: 'pinquark-workflow-ai-chat',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressSpinnerModule,
    MatTooltipModule,
    MatSnackBarModule,
  ],
  template: `
    <div class="ai-chat">
      <div class="ai-chat__header">
        <div class="ai-chat__header-left">
          <div class="ai-chat__avatar">
            <mat-icon>psychology</mat-icon>
          </div>
          <div>
            <div class="ai-chat__title">AI Workflow Agent</div>
            <div class="ai-chat__model">{{ getModelLabel() }}</div>
          </div>
        </div>
        @if (messages.length > 0) {
          <button
            mat-icon-button
            matTooltip="Clear conversation"
            (click)="clearChat()"
            class="ai-chat__clear"
          >
            <mat-icon>delete_sweep</mat-icon>
          </button>
        }
      </div>

      <div class="ai-chat__messages" #messagesContainer>
        @if (messages.length === 0) {
          <div class="ai-chat__empty">
            <mat-icon class="ai-chat__empty-icon">auto_awesome</mat-icon>
            <p class="ai-chat__empty-title">Describe the workflow you need</p>
            <p class="ai-chat__empty-hint">For example:</p>
            <div class="ai-chat__suggestions">
              @for (s of suggestions; track s) {
                <button class="ai-chat__suggestion" (click)="useSuggestion(s)">{{ s }}</button>
              }
            </div>
          </div>
        }

        @for (msg of messages; track msg.timestamp) {
          <div class="ai-chat__msg" [class.ai-chat__msg--user]="msg.role === 'user'" [class.ai-chat__msg--assistant]="msg.role === 'assistant'">
            <div class="ai-chat__msg-avatar">
              <mat-icon>{{ msg.role === 'user' ? 'person' : 'psychology' }}</mat-icon>
            </div>
            <div class="ai-chat__msg-body">
              <div class="ai-chat__msg-content">{{ msg.content }}</div>
              @if (msg.nodes && msg.nodes.length > 0) {
                <div class="ai-chat__msg-workflow">
                  <div class="ai-chat__msg-workflow-header">
                    <mat-icon>account_tree</mat-icon>
                    <span>{{ msg.name || 'Generated Workflow' }} &mdash; {{ msg.nodes.length }} nodes</span>
                  </div>
                  <div class="ai-chat__msg-workflow-actions">
                    <button
                      mat-raised-button
                      color="primary"
                      (click)="applyWorkflow(msg)"
                      matTooltip="Replace current workflow with this one"
                    >
                      <mat-icon>check</mat-icon> Apply Workflow
                    </button>
                  </div>
                </div>
              }
              <span class="ai-chat__msg-time">{{ msg.timestamp | date:'HH:mm' }}</span>
            </div>
          </div>
        }

        @if (loading) {
          <div class="ai-chat__msg ai-chat__msg--assistant">
            <div class="ai-chat__msg-avatar">
              <mat-icon>psychology</mat-icon>
            </div>
            <div class="ai-chat__msg-body">
              <div class="ai-chat__typing">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        }
      </div>

      <div class="ai-chat__input-area">
        @if (!isConfigured) {
          <div class="ai-chat__no-config">
            <mat-icon>warning</mat-icon>
            <span>Configure AI model and API key in <a class="ai-chat__settings-link" (click)="goToSettings()">Settings</a> first</span>
          </div>
        } @else {
          <div class="ai-chat__input-row">
            <textarea
              class="ai-chat__textarea"
              [(ngModel)]="userInput"
              placeholder="Describe the workflow you want to create..."
              (keydown.enter)="onEnterKey($event)"
              [disabled]="loading"
              rows="1"
              #inputEl
            ></textarea>
            <button
              mat-icon-button
              color="primary"
              (click)="send()"
              [disabled]="loading || !userInput.trim()"
              class="ai-chat__send"
            >
              <mat-icon>send</mat-icon>
            </button>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    .ai-chat {
      display: flex;
      flex-direction: column;
      height: 100%;
      background: #f8f9fa;
    }

    .ai-chat__header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 16px;
      background: linear-gradient(135deg, #6a1b9a, #1565c0);
      color: #fff;
    }
    .ai-chat__header-left {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .ai-chat__avatar {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: rgba(255,255,255,0.2);
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .ai-chat__avatar mat-icon { font-size: 22px; }
    .ai-chat__title { font-weight: 600; font-size: 14px; }
    .ai-chat__model { font-size: 11px; opacity: 0.8; }
    .ai-chat__clear { color: rgba(255,255,255,0.7); }

    .ai-chat__messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .ai-chat__empty {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: 32px 16px;
      color: #666;
      flex: 1;
    }
    .ai-chat__empty-icon {
      font-size: 48px;
      width: 48px;
      height: 48px;
      color: #9c27b0;
      margin-bottom: 12px;
    }
    .ai-chat__empty-title { font-size: 16px; font-weight: 600; margin: 0 0 4px; color: #333; }
    .ai-chat__empty-hint { font-size: 13px; margin: 0 0 16px; }

    .ai-chat__suggestions {
      display: flex;
      flex-direction: column;
      gap: 8px;
      width: 100%;
      max-width: 360px;
    }
    .ai-chat__suggestion {
      border: 1px solid #e0e0e0;
      background: #fff;
      border-radius: 8px;
      padding: 10px 14px;
      font-size: 13px;
      color: #333;
      cursor: pointer;
      text-align: left;
      transition: all 0.15s;
    }
    .ai-chat__suggestion:hover {
      border-color: #1976d2;
      background: #e3f2fd;
      color: #1565c0;
    }

    .ai-chat__msg {
      display: flex;
      gap: 8px;
      max-width: 90%;
    }
    .ai-chat__msg--user { align-self: flex-end; flex-direction: row-reverse; }
    .ai-chat__msg--assistant { align-self: flex-start; }

    .ai-chat__msg-avatar {
      width: 28px;
      height: 28px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .ai-chat__msg-avatar mat-icon { font-size: 16px; width: 16px; height: 16px; }
    .ai-chat__msg--user .ai-chat__msg-avatar { background: #1976d2; color: #fff; }
    .ai-chat__msg--assistant .ai-chat__msg-avatar { background: #6a1b9a; color: #fff; }

    .ai-chat__msg-body {
      background: #fff;
      border-radius: 12px;
      padding: 10px 14px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
      position: relative;
    }
    .ai-chat__msg--user .ai-chat__msg-body {
      background: #1976d2;
      color: #fff;
      border-bottom-right-radius: 4px;
    }
    .ai-chat__msg--assistant .ai-chat__msg-body {
      border-bottom-left-radius: 4px;
    }

    .ai-chat__msg-content {
      font-size: 13px;
      line-height: 1.5;
      white-space: pre-wrap;
      word-break: break-word;
    }

    .ai-chat__msg-time {
      font-size: 10px;
      opacity: 0.5;
      display: block;
      margin-top: 4px;
    }
    .ai-chat__msg--user .ai-chat__msg-time { text-align: right; }

    .ai-chat__msg-workflow {
      margin-top: 10px;
      padding-top: 10px;
      border-top: 1px solid #e0e0e0;
    }
    .ai-chat__msg-workflow-header {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      font-weight: 600;
      color: #6a1b9a;
      margin-bottom: 8px;
    }
    .ai-chat__msg-workflow-header mat-icon { font-size: 18px; width: 18px; height: 18px; }
    .ai-chat__msg-workflow-actions {
      display: flex;
      gap: 8px;
    }
    .ai-chat__msg-workflow-actions button { font-size: 12px; }

    .ai-chat__typing {
      display: flex;
      gap: 4px;
      padding: 4px 0;
    }
    .ai-chat__typing span {
      width: 8px;
      height: 8px;
      background: #999;
      border-radius: 50%;
      animation: typing 1.2s ease-in-out infinite;
    }
    .ai-chat__typing span:nth-child(2) { animation-delay: 0.2s; }
    .ai-chat__typing span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes typing {
      0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
      30% { transform: translateY(-6px); opacity: 1; }
    }

    .ai-chat__input-area {
      padding: 12px 16px;
      background: #fff;
      border-top: 1px solid #e0e0e0;
    }
    .ai-chat__input-row {
      display: flex;
      align-items: flex-end;
      gap: 8px;
      background: #f5f5f5;
      border-radius: 12px;
      padding: 6px 6px 6px 14px;
    }
    .ai-chat__textarea {
      flex: 1;
      border: none;
      outline: none;
      background: transparent;
      font-size: 13px;
      line-height: 1.5;
      resize: none;
      min-height: 24px;
      max-height: 120px;
      font-family: inherit;
      padding: 4px 0;
    }
    .ai-chat__send {
      flex-shrink: 0;
    }

    .ai-chat__no-config {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px;
      background: #fff3e0;
      border-radius: 8px;
      font-size: 13px;
      color: #e65100;
    }
    .ai-chat__no-config mat-icon { font-size: 20px; color: #ff9800; }
    .ai-chat__settings-link {
      color: #1976d2;
      cursor: pointer;
      font-weight: 600;
      text-decoration: underline;
    }
    .ai-chat__settings-link:hover { color: #0d47a1; }
  `],
})
export class WorkflowAiChatComponent {
  @Input() nodes: WorkflowNode[] = [];
  @Input() edges: WorkflowEdge[] = [];
  @Input() connectors: Connector[] = [];

  @Output() workflowGenerated = new EventEmitter<{
    nodes: WorkflowNode[];
    edges: WorkflowEdge[];
    name?: string;
    description?: string;
  }>();

  @ViewChild('messagesContainer') messagesContainer!: ElementRef<HTMLDivElement>;
  @ViewChild('inputEl') inputEl!: ElementRef<HTMLTextAreaElement>;

  messages: ChatEntry[] = [];
  userInput = '';
  loading = false;
  isConfigured = false;

  private aiModel: AiModelType = 'gemini';
  private aiApiKey = '';

  readonly suggestions = [
    'When a new order arrives from Allegro, create a shipment in InPost',
    'Monitor email inbox and extract invoice data using AI',
    'Compare shipping prices from DHL, InPost and DPD, pick the cheapest',
    'When WMS updates stock levels, sync to Shopify and BaseLinker',
  ];

  constructor(
    private readonly api: PinquarkApiService,
    private readonly snackBar: MatSnackBar,
    private readonly router: Router,
  ) {
    this.loadSettings();
  }

  private loadSettings(): void {
    try {
      const stored = localStorage.getItem('pinquark_ai_settings');
      if (stored) {
        const parsed = JSON.parse(stored);
        this.aiModel = parsed.model || 'gemini';
        this.aiApiKey = parsed.apiKey || '';
        this.isConfigured = !!this.aiApiKey;
      }
    } catch { /* ignore */ }
  }

  goToSettings(): void {
    this.router.navigate(['/settings']);
  }

  getModelLabel(): string {
    const model = AI_MODELS.find(m => m.value === this.aiModel);
    return model?.label ?? this.aiModel;
  }

  useSuggestion(text: string): void {
    this.userInput = text;
    this.send();
  }

  onEnterKey(event: Event): void {
    const ke = event as KeyboardEvent;
    if (!ke.shiftKey) {
      ke.preventDefault();
      this.send();
    }
  }

  send(): void {
    const prompt = this.userInput.trim();
    if (!prompt || this.loading) return;

    this.loadSettings();
    if (!this.isConfigured) {
      this.snackBar.open('Configure AI settings first (Settings page)', 'OK', { duration: 4000 });
      return;
    }

    this.messages.push({
      role: 'user',
      content: prompt,
      timestamp: new Date(),
    });
    this.userInput = '';
    this.loading = true;
    this.scrollToBottom();

    const conversation: AiChatMessage[] = this.messages
      .filter(m => !m.nodes)
      .map(m => ({ role: m.role, content: m.content }));

    const connectorSummaries = this.connectors.map(c => ({
      name: c.name,
      display_name: c.display_name,
      category: c.category,
      events: c.events,
      actions: c.actions,
    }));

    this.api.aiGenerateWorkflow({
      prompt,
      model: this.aiModel,
      api_key: this.aiApiKey,
      conversation: conversation.slice(0, -1),
      current_nodes: this.nodes as unknown as Record<string, unknown>[],
      current_edges: this.edges as unknown as Record<string, unknown>[],
      connectors: connectorSummaries as unknown as Record<string, unknown>[],
    }).subscribe({
      next: (resp: AiGenerateResponse) => {
        this.messages.push({
          role: 'assistant',
          content: resp.message,
          nodes: resp.nodes,
          edges: resp.edges,
          name: resp.name ?? undefined,
          description: resp.description ?? undefined,
          timestamp: new Date(),
        });
        this.loading = false;
        this.scrollToBottom();
      },
      error: (err) => {
        const detail = err.error?.detail || err.message || 'Unknown error';
        this.messages.push({
          role: 'assistant',
          content: `Error: ${detail}`,
          timestamp: new Date(),
        });
        this.loading = false;
        this.scrollToBottom();
      },
    });
  }

  applyWorkflow(msg: ChatEntry): void {
    if (!msg.nodes || !msg.edges) return;
    this.workflowGenerated.emit({
      nodes: msg.nodes,
      edges: msg.edges,
      name: msg.name,
      description: msg.description,
    });
    this.snackBar.open('Workflow applied to canvas', 'OK', { duration: 3000 });
  }

  clearChat(): void {
    this.messages = [];
  }

  private scrollToBottom(): void {
    setTimeout(() => {
      if (this.messagesContainer) {
        const el = this.messagesContainer.nativeElement;
        el.scrollTop = el.scrollHeight;
      }
    }, 50);
  }
}
