import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatTabsModule } from '@angular/material/tabs';
import { MatMenuModule } from '@angular/material/menu';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import {
  FlowDesignerComponent,
  PinquarkApiService,
  Flow,
  Workflow,
  WorkflowCreateRequest,
} from '@pinquark/integrations';

@Component({
  selector: 'app-flows-page',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatChipsModule,
    MatTabsModule,
    MatMenuModule,
    MatTooltipModule,
    MatExpansionModule,
    MatSnackBarModule,
    FlowDesignerComponent,
  ],
  template: `
    <div class="flows-page">
      <div class="flows-page__header">
        <div>
          <h2>Integration Flows & Workflows</h2>
          <p class="flows-page__subtitle">
            Connect systems, automate processes, and build complex integration scenarios
          </p>
        </div>
        <div class="flows-page__actions">
          <button mat-raised-button color="primary" (click)="createWorkflow()">
            <mat-icon>add</mat-icon> New Workflow
          </button>
          <button mat-stroked-button (click)="importFileInput.click()" matTooltip="Import workflow from JSON file">
            <mat-icon>upload_file</mat-icon> Import
          </button>
          <input
            #importFileInput
            type="file"
            accept=".json"
            hidden
            (change)="onImportFile($event)"
          />
          <button mat-stroked-button (click)="toggleSimpleDesigner()">
            <mat-icon>{{ showDesigner && !editingFlow ? 'close' : 'add' }}</mat-icon>
            {{ showDesigner && !editingFlow ? 'Cancel' : 'Quick Flow' }}
          </button>
        </div>
      </div>

      @if (showDesigner) {
        <mat-card style="margin-bottom: 24px;">
          <mat-card-content>
            <pinquark-flow-designer
              [editFlow]="editingFlow"
              (flowCreated)="onFlowCreated($event)"
              (flowUpdated)="onFlowUpdated($event)"
            ></pinquark-flow-designer>
          </mat-card-content>
        </mat-card>
      }

      @if (!showDesigner) {
      <mat-tab-group animationDuration="150ms" [selectedIndex]="selectedTabIndex" (selectedIndexChange)="selectedTabIndex = $event">
        <!-- Workflows Tab -->
        <mat-tab>
          <ng-template mat-tab-label>
            <mat-icon class="tab-icon">account_tree</mat-icon>
            Workflows ({{ workflows.length }})
          </ng-template>
          <div class="flows-page__tab-content">
            @if (workflows.length === 0) {
              <div class="flows-page__empty">
                <mat-icon>account_tree</mat-icon>
                <h3>No workflows yet</h3>
                <p>Create your first visual workflow to connect systems with conditions, transforms, and branching logic.</p>
                <button mat-raised-button color="primary" (click)="createWorkflow()">
                  <mat-icon>add</mat-icon> Create Workflow
                </button>
              </div>
            } @else {
              <div class="flows-page__grid">
                @for (wf of workflows; track wf.id) {
                  <mat-card class="wf-card" [class.wf-card--active]="wf.is_enabled" (click)="openWorkflow(wf)">
                    <mat-card-header>
                      <mat-icon mat-card-avatar class="wf-card__avatar" [class.wf-card__avatar--active]="wf.is_enabled">
                        account_tree
                      </mat-icon>
                      <mat-card-title>{{ wf.name }}</mat-card-title>
                      <mat-card-subtitle>
                        @if (wf.trigger_connector && wf.trigger_event) {
                          {{ wf.trigger_connector }} / {{ wf.trigger_event }}
                        } @else {
                          No trigger configured
                        }
                      </mat-card-subtitle>
                    </mat-card-header>
                    <mat-card-content>
                      @if (wf.description) {
                        <p class="wf-card__desc">{{ wf.description }}</p>
                      }
                      <div class="wf-card__chips">
                        <mat-chip [highlighted]="wf.is_enabled">{{ wf.is_enabled ? 'Active' : 'Inactive' }}</mat-chip>
                        <mat-chip>v{{ wf.version }}</mat-chip>
                        <mat-chip>{{ wf.nodes.length }} nodes</mat-chip>
                        <mat-chip>{{ wf.edges.length }} connections</mat-chip>
                      </div>
                    </mat-card-content>
                    <mat-card-actions>
                      <button mat-button color="primary" (click)="openWorkflow(wf); $event.stopPropagation()">
                        <mat-icon>edit</mat-icon> Edit
                      </button>
                      <button mat-button (click)="exportWorkflow(wf, $event)">
                        <mat-icon>download</mat-icon> Export
                      </button>
                      <button mat-button color="warn" (click)="deleteWorkflow(wf.id, $event)">
                        <mat-icon>delete</mat-icon> Delete
                      </button>
                    </mat-card-actions>
                  </mat-card>
                }
              </div>
            }
          </div>
        </mat-tab>

        <!-- Simple Flows Tab -->
        <mat-tab>
          <ng-template mat-tab-label>
            <mat-icon class="tab-icon">alt_route</mat-icon>
            Simple Flows ({{ flows.length }})
          </ng-template>
          <div class="flows-page__tab-content">
            <div class="flows-page__list">
              @for (flow of flows; track flow.id) {
                <mat-card class="flow-card">
                  <mat-card-header>
                    <mat-card-title>{{ flow.name }}</mat-card-title>
                    <mat-card-subtitle>
                      {{ flow.source_connector }} ({{ flow.source_event }})
                      &rarr;
                      {{ flow.destination_connector }} ({{ flow.destination_action }})
                    </mat-card-subtitle>
                  </mat-card-header>
                  <mat-card-content>
                    <mat-chip>{{ flow.is_enabled ? 'Active' : 'Disabled' }}</mat-chip>
                    <mat-chip>{{ flow.on_error }}</mat-chip>
                    <mat-chip>{{ flow.field_mapping.length }} mappings</mat-chip>
                  </mat-card-content>
                  <mat-card-actions>
                    <button mat-button color="primary" (click)="editFlow(flow)">
                      <mat-icon>edit</mat-icon> Edit
                    </button>
                    <button mat-button color="warn" (click)="deleteFlow(flow.id)">
                      <mat-icon>delete</mat-icon> Delete
                    </button>
                  </mat-card-actions>
                </mat-card>
              }
            </div>
          </div>
        </mat-tab>
      </mat-tab-group>
      }
    </div>
  `,
  styles: [`
    .flows-page__header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 20px;
      gap: 16px;
      flex-wrap: wrap;
    }
    .flows-page__header h2 { margin: 0; }
    .flows-page__subtitle { color: #666; margin: 4px 0 0; font-size: 14px; }
    .flows-page__actions { display: flex; gap: 10px; flex-shrink: 0; }
    .tab-icon { margin-right: 6px; }
    .flows-page__tab-content { padding-top: 16px; }
    .flows-page__list { display: flex; flex-direction: column; gap: 12px; }
    .flows-page__grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 16px;
    }
    .flows-page__empty {
      text-align: center;
      padding: 60px 20px;
      color: #888;
    }
    .flows-page__empty mat-icon { font-size: 64px; width: 64px; height: 64px; opacity: 0.3; }
    .flows-page__empty h3 { margin: 16px 0 8px; color: #555; }
    .flows-page__empty p { margin-bottom: 24px; max-width: 400px; margin-left: auto; margin-right: auto; }

    .wf-card {
      cursor: pointer;
      transition: box-shadow 0.2s, border-color 0.2s;
      border-left: 4px solid #ccc;
    }
    .wf-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.12); }
    .wf-card--active { border-left-color: #4caf50; }
    .wf-card__avatar {
      background: #e0e0e0;
      border-radius: 8px;
      padding: 8px;
      font-size: 24px;
      width: 24px;
      height: 24px;
      color: #666;
    }
    .wf-card__avatar--active { background: #e8f5e9; color: #4caf50; }
    .wf-card__desc { font-size: 13px; color: #666; margin: 8px 0; }
    .wf-card__chips { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
    .wf-card__chips mat-chip { font-size: 11px; }

    .flow-card mat-chip { margin-right: 8px; }
    .flow-card mat-card-actions { display: flex; gap: 8px; }
  `],
})
export class FlowsPage implements OnInit {
  @ViewChild('importFileInput') importFileInput!: ElementRef<HTMLInputElement>;

  flows: Flow[] = [];
  workflows: Workflow[] = [];
  showDesigner = false;
  editingFlow: Flow | null = null;
  selectedTabIndex = 0;

  constructor(
    private readonly api: PinquarkApiService,
    private readonly router: Router,
    private readonly snackBar: MatSnackBar,
  ) {}

  ngOnInit(): void {
    this.loadFlows();
    this.loadWorkflows();
  }

  loadFlows(): void {
    this.api.listFlows().subscribe({
      next: data => (this.flows = data),
      error: () => this.snackBar.open('Failed to load flows', 'OK', { duration: 4000 }),
    });
  }

  loadWorkflows(): void {
    this.api.listWorkflows().subscribe({
      next: data => (this.workflows = data),
      error: () => this.snackBar.open('Failed to load workflows', 'OK', { duration: 4000 }),
    });
  }

  createWorkflow(): void {
    this.router.navigate(['/workflows', 'new']);
  }

  openWorkflow(wf: Workflow): void {
    this.router.navigate(['/workflows', wf.id]);
  }

  deleteWorkflow(id: string, event: MouseEvent): void {
    event.stopPropagation();
    this.api.deleteWorkflow(id).subscribe({
      next: () => this.loadWorkflows(),
      error: () => this.snackBar.open('Failed to delete workflow', 'OK', { duration: 4000 }),
    });
  }

  toggleSimpleDesigner(): void {
    if (this.showDesigner && !this.editingFlow) {
      this.showDesigner = false;
    } else {
      this.editingFlow = null;
      this.showDesigner = true;
    }
  }

  editFlow(flow: Flow): void {
    this.editingFlow = flow;
    this.showDesigner = true;
  }

  onFlowCreated(_flow: Flow): void {
    this.showDesigner = false;
    this.editingFlow = null;
    this.loadFlows();
  }

  onFlowUpdated(_flow: Flow): void {
    this.showDesigner = false;
    this.editingFlow = null;
    this.loadFlows();
  }

  deleteFlow(flowId: string): void {
    this.api.deleteFlow(flowId).subscribe({
      next: () => this.loadFlows(),
      error: () => this.snackBar.open('Failed to delete flow', 'OK', { duration: 4000 }),
    });
  }

  exportWorkflow(wf: Workflow, event: MouseEvent): void {
    event.stopPropagation();
    const exportData: WorkflowCreateRequest = {
      name: wf.name,
      description: wf.description,
      nodes: wf.nodes,
      edges: wf.edges,
      variables: wf.variables,
      on_error: wf.on_error,
      max_retries: wf.max_retries,
      timeout_seconds: wf.timeout_seconds,
    };
    if (wf.sync_config) {
      exportData.sync_config = wf.sync_config;
    }
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${wf.name.replace(/[^a-zA-Z0-9_-]/g, '_').toLowerCase()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  onImportFile(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      try {
        const data = JSON.parse(reader.result as string);
        if (!data.name || !Array.isArray(data.nodes) || !Array.isArray(data.edges)) {
          this.snackBar.open('Invalid workflow file — missing name, nodes, or edges', 'OK', { duration: 5000 });
          return;
        }
        const body: WorkflowCreateRequest = {
          name: data.name,
          description: data.description ?? '',
          nodes: data.nodes,
          edges: data.edges,
          variables: data.variables ?? {},
          sync_config: data.sync_config ?? null,
          on_error: data.on_error ?? 'stop',
          max_retries: data.max_retries ?? 3,
          timeout_seconds: data.timeout_seconds ?? 300,
        };
        this.api.createWorkflow(body).subscribe({
          next: (wf) => {
            this.snackBar.open(`Workflow "${wf.name}" imported`, 'Open', { duration: 5000 })
              .onAction()
              .subscribe(() => this.router.navigate(['/workflows', wf.id]));
            this.loadWorkflows();
          },
          error: (err) => {
            this.snackBar.open('Import failed: ' + (err.error?.detail || 'Unknown error'), 'OK', { duration: 5000 });
          },
        });
      } catch {
        this.snackBar.open('Invalid JSON file', 'OK', { duration: 5000 });
      }
      input.value = '';
    };
    reader.readAsText(file);
  }
}
