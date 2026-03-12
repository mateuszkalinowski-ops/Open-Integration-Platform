import { Component, OnDestroy, OnInit, ViewChild, Inject } from '@angular/core';
import { CommonModule, DOCUMENT } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { Clipboard, ClipboardModule } from '@angular/cdk/clipboard';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatTabsModule } from '@angular/material/tabs';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatMenuModule } from '@angular/material/menu';
import { forkJoin } from 'rxjs';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';

import {
  PinquarkApiService,
  WorkflowCanvasComponent,
  WorkflowNodeConfigComponent,
  WorkflowAiChatComponent,
  VisualFieldMapperDialogComponent,
  VisualFieldMapperDialogData,
  Connector,
  Workflow,
  WorkflowNode,
  WorkflowEdge,
  WorkflowExecution as WorkflowExecutionModel,
  WorkflowNodeResult,
  SyncConfig,
  AiExplainErrorResponse,
  ConnectorFieldDef,
  FieldMapping,
} from '@pinquark/integrations';

@Component({
  selector: 'app-workflow-builder-page',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatToolbarModule,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatSnackBarModule,
    MatSlideToggleModule,
    MatTabsModule,
    MatChipsModule,
    MatTooltipModule,
    MatProgressSpinnerModule,
    MatMenuModule,
    MatDialogModule,
    ClipboardModule,
    WorkflowCanvasComponent,
    WorkflowNodeConfigComponent,
    WorkflowAiChatComponent,
  ],
  template: `
    <div class="wb">
      <!-- Top Bar -->
      <div class="wb__topbar">
        <div class="wb__topbar-left">
          <button mat-icon-button matTooltip="Back to Flows" (click)="goBack()">
            <mat-icon>arrow_back</mat-icon>
          </button>
          <div class="wb__name-area">
            <input
              class="wb__name-input"
              [(ngModel)]="workflowName"
              placeholder="Workflow name..."
            />
            <span class="wb__version" *ngIf="workflow">v{{ workflow.version }}</span>
          </div>
        </div>
        <div class="wb__topbar-right">
          @if (workflow) {
            <mat-slide-toggle
              [checked]="workflow.is_enabled"
              (change)="toggleEnabled()"
              [matTooltip]="workflow.is_enabled ? 'Active' : 'Inactive'"
            >
              {{ workflow.is_enabled ? 'Active' : 'Inactive' }}
            </mat-slide-toggle>
          }
          <button mat-stroked-button (click)="openAiChat()" matTooltip="AI workflow generator" class="wb__ai-btn">
            <mat-icon>psychology</mat-icon> AI Agent
          </button>
          <button mat-stroked-button (click)="openTestPanel()" matTooltip="Test workflow with sample data">
            <mat-icon>science</mat-icon> Test
          </button>
          <button mat-icon-button [matMenuTriggerFor]="importExportMenu" matTooltip="Import / Export">
            <mat-icon>swap_vert</mat-icon>
          </button>
          <mat-menu #importExportMenu="matMenu">
            <button mat-menu-item (click)="exportWorkflow()">
              <mat-icon>download</mat-icon> Export as JSON
            </button>
            <button mat-menu-item (click)="builderImportInput.click()">
              <mat-icon>upload_file</mat-icon> Import from JSON
            </button>
          </mat-menu>
          <input
            #builderImportInput
            type="file"
            accept=".json"
            hidden
            (change)="onImportFile($event)"
          />
          <button mat-raised-button color="primary" (click)="save()" [disabled]="saving">
            <mat-icon>save</mat-icon> {{ saving ? 'Saving...' : 'Save' }}
          </button>
        </div>
      </div>

      <!-- Main Area -->
      <div class="wb__main">
        <!-- Canvas -->
        <div class="wb__canvas-area">
          <pinquark-workflow-canvas
            #canvas
            [nodes]="nodes"
            [edges]="edges"
            [nodeResults]="testNodeResults"
            [connectors]="connectors"
            (nodesChange)="nodes = $event"
            (edgesChange)="edges = $event"
            (nodeSelected)="onNodeSelected($event)"
            (nodeDoubleClicked)="onNodeDoubleClicked($event)"
            (openNodeMapper)="onOpenNodeMapper($event)"
          ></pinquark-workflow-canvas>
        </div>

        <!-- Right Panel -->
        @if (showRightPanel) {
          <div
            class="wb__right-panel"
            [style.width.px]="panelWidth"
            [style.min-width.px]="panelWidth"
          >
            <!-- Resize handle -->
            <div
              class="wb__resize-handle"
              (mousedown)="onResizeStart($event)"
            ></div>
            <!-- Panel toolbar -->
            <div class="wb__panel-toolbar">
              <button
                mat-icon-button
                (click)="togglePanelExpand()"
                [matTooltip]="panelExpanded ? 'Zwez panel' : 'Rozszerz panel'"
              >
                <mat-icon>{{ panelExpanded ? 'chevron_right' : 'chevron_left' }}</mat-icon>
              </button>
              <button
                mat-icon-button
                (click)="showRightPanel = false"
                matTooltip="Zamknij panel"
              >
                <mat-icon>close</mat-icon>
              </button>
            </div>
            <mat-tab-group [(selectedIndex)]="rightTabIndex" animationDuration="0ms">
              <!-- Config Tab -->
              <mat-tab label="Configure">
                <div class="wb__config-tab">
                  @if (selectedNode) {
                    <pinquark-workflow-node-config
                      [node]="selectedNode"
                      [connectors]="connectors"
                      [allNodes]="nodes"
                      [allEdges]="edges"
                      (nodeChange)="onNodeConfigChange($event)"
                      (close)="closeRightPanel()"
                    ></pinquark-workflow-node-config>
                  } @else {
                    <div class="wb__empty-config">
                      <mat-icon>touch_app</mat-icon>
                      <p>Select a node to configure it</p>
                      <p class="wb__hint">Double-click a node to open its settings</p>
                    </div>
                  }
                </div>
              </mat-tab>

              <!-- Test Tab -->
              <mat-tab label="Test">
                <div class="wb__test-tab">
                  <mat-form-field appearance="outline" class="wb__test-input">
                    <mat-label>Trigger Data (JSON)</mat-label>
                    <textarea
                      matInput
                      [(ngModel)]="testDataJson"
                      rows="8"
                      placeholder='{"order_id": "123", "status": "created"}'
                    ></textarea>
                  </mat-form-field>
                  <button
                    mat-raised-button
                    color="accent"
                    (click)="runTest()"
                    [disabled]="testing"
                    class="wb__test-btn"
                  >
                    @if (testing) {
                      <mat-spinner diameter="18" class="wb__spinner"></mat-spinner>
                    } @else {
                      <mat-icon>play_arrow</mat-icon>
                    }
                    {{ testing ? 'Running...' : 'Run Test' }}
                  </button>

                  @if (testExecution) {
                    <div class="wb__test-results">
                      <div class="wb__test-status" [class]="'wb__test-status--' + testExecution.status">
                        <mat-icon>{{ testExecution.status === 'success' ? 'check_circle' : testExecution.status === 'failed' ? 'error' : 'pending' }}</mat-icon>
                        <span>{{ testExecution.status | uppercase }}</span>
                        <span class="wb__test-duration" *ngIf="testExecution.duration_ms">{{ testExecution.duration_ms }}ms</span>
                      </div>
                      @if (testExecution.error) {
                        <div class="wb__test-error">
                          <strong>Error:</strong> {{ testExecution.error }}
                          @if (testExecution.error_node_id) {
                            <br/><strong>Node:</strong> {{ testExecution.error_node_id }}
                          }
                        </div>
                        <button
                          mat-stroked-button
                          color="primary"
                          (click)="explainTestError()"
                          [disabled]="aiExplaining"
                          class="wb__ai-explain-btn"
                        >
                          <mat-icon>{{ aiExplaining ? 'hourglass_top' : 'psychology' }}</mat-icon>
                          {{ aiExplaining ? 'Explaining...' : 'Explain with AI' }}
                        </button>
                        @if (aiErrorExplanation) {
                          <div class="wb__ai-explain">
                            <h4>AI explanation</h4>
                            <p>{{ aiErrorExplanation.summary }}</p>
                            @if (aiErrorExplanation.likely_causes.length > 0) {
                              <div class="wb__ai-explain-list">
                                <strong>Likely causes</strong>
                                <ul>
                                  @for (item of aiErrorExplanation.likely_causes; track item) {
                                    <li>{{ item }}</li>
                                  }
                                </ul>
                              </div>
                            }
                            @if (aiErrorExplanation.suggested_fixes.length > 0) {
                              <div class="wb__ai-explain-list">
                                <strong>Suggested fixes</strong>
                                <ul>
                                  @for (item of aiErrorExplanation.suggested_fixes; track item) {
                                    <li>{{ item }}</li>
                                  }
                                </ul>
                              </div>
                            }
                          </div>
                        }
                      }
                      <div class="wb__test-nodes">
                        <h4>Node Results</h4>
                        @for (nr of testExecution.node_results; track nr.node_id) {
                          <div class="wb__test-node" [class]="'wb__test-node--' + nr.status">
                            <div class="wb__test-node-header">
                              <mat-icon [style.font-size.px]="16">{{ getNodeResultIcon(nr) }}</mat-icon>
                              <span>{{ nr.label || nr.node_id }}</span>
                              <mat-chip class="wb__test-node-status">{{ nr.status }}</mat-chip>
                              @if (nr.duration_ms != null) {
                                <span class="wb__test-node-time">{{ nr.duration_ms }}ms</span>
                              }
                            </div>
                            @if (nr.error) {
                              <pre class="wb__test-node-error">{{ nr.error }}</pre>
                            }
                            @if (nr.output != null) {
                              <pre class="wb__test-node-output">{{ formatOutput(nr.output) }}</pre>
                            }
                          </div>
                        }
                      </div>
                    </div>
                  }
                </div>
              </mat-tab>

              <!-- Settings Tab -->
              <mat-tab label="Settings">
                <div class="wb__settings-tab">
                  <mat-form-field appearance="outline" class="wb__field">
                    <mat-label>Description</mat-label>
                    <textarea matInput [(ngModel)]="workflowDescription" rows="3" placeholder="What does this workflow do?"></textarea>
                  </mat-form-field>
                  <mat-form-field appearance="outline" class="wb__field">
                    <mat-label>On Error</mat-label>
                    <mat-select [(ngModel)]="workflowOnError">
                      <mat-option value="stop">Stop Workflow</mat-option>
                      <mat-option value="continue">Continue Execution</mat-option>
                    </mat-select>
                  </mat-form-field>
                  <mat-form-field appearance="outline" class="wb__field">
                    <mat-label>Max Retries</mat-label>
                    <input matInput type="number" [(ngModel)]="workflowMaxRetries" />
                  </mat-form-field>
                  <mat-form-field appearance="outline" class="wb__field">
                    <mat-label>Timeout (seconds)</mat-label>
                    <input matInput type="number" [(ngModel)]="workflowTimeout" />
                  </mat-form-field>

                  @if (workflowId && workflowId !== 'new') {
                    <div class="wb__api-section">
                      <div class="wb__api-header">
                        <mat-icon>code</mat-icon>
                        <span>API — Execute this workflow</span>
                      </div>

                      <div class="wb__api-block">
                        <div class="wb__api-label">
                          <span class="wb__api-method">POST</span>
                          Endpoint
                          <button mat-icon-button class="wb__api-copy" (click)="copyToClipboard(executeEndpoint)" matTooltip="Copy endpoint">
                            <mat-icon>content_copy</mat-icon>
                          </button>
                        </div>
                        <code class="wb__api-code">{{ executeEndpoint }}</code>
                      </div>

                      <div class="wb__api-block">
                        <div class="wb__api-label">
                          curl
                          <button mat-icon-button class="wb__api-copy" (click)="copyToClipboard(curlExample)" matTooltip="Copy curl">
                            <mat-icon>content_copy</mat-icon>
                          </button>
                        </div>
                        <pre class="wb__api-code wb__api-curl">{{ curlExample }}</pre>
                      </div>

                      <div class="wb__api-block">
                        <div class="wb__api-label">Response</div>
                        <pre class="wb__api-code wb__api-response">{{ responseExample }}</pre>
                      </div>

                      <div class="wb__api-hint">
                        The workflow executes synchronously — the response contains
                        <strong>node_results</strong> with each step's output and
                        <strong>context_snapshot</strong> with the merged final data.
                      </div>

                      <div class="wb__api-divider"></div>

                      <div class="wb__api-block">
                        <div class="wb__api-label">
                          <span class="wb__api-method wb__api-method--get">GET</span>
                          Call via URL
                          <button mat-icon-button class="wb__api-copy" (click)="copyToClipboard(callEndpoint)" matTooltip="Copy endpoint">
                            <mat-icon>content_copy</mat-icon>
                          </button>
                        </div>
                        <code class="wb__api-code">{{ callEndpoint }}</code>
                      </div>

                      <div class="wb__api-block">
                        <div class="wb__api-label">
                          Example
                          <button mat-icon-button class="wb__api-copy" (click)="copyToClipboard(callExample)" matTooltip="Copy URL">
                            <mat-icon>content_copy</mat-icon>
                          </button>
                        </div>
                        <code class="wb__api-code">{{ callExample }}</code>
                      </div>

                      <div class="wb__api-hint">
                        Pass <strong>trigger_data</strong> as query parameters.
                        If the workflow output contains a <strong>url</strong> field,
                        the endpoint returns a <strong>302 redirect</strong> — the
                        browser follows it automatically (e.g. to download a file from S3).
                      </div>
                    </div>
                  }
                </div>
              </mat-tab>

              <!-- AI Agent Tab -->
              <mat-tab>
                <ng-template mat-tab-label>
                  <mat-icon class="wb__ai-tab-icon">psychology</mat-icon>
                  AI Agent
                </ng-template>
                <div class="wb__ai-tab">
                  <pinquark-workflow-ai-chat
                    [nodes]="nodes"
                    [edges]="edges"
                    [connectors]="connectors"
                    (workflowGenerated)="onAiWorkflowGenerated($event)"
                  ></pinquark-workflow-ai-chat>
                </div>
              </mat-tab>

              <!-- Sync Status Tab -->
              @if (workflow?.sync_config) {
                <mat-tab>
                  <ng-template mat-tab-label>
                    <mat-icon>sync</mat-icon>
                    Sync
                    @if (syncStats && syncStats.failed > 0) {
                      <span class="wb__sync-badge wb__sync-badge--fail">{{ syncStats.failed }}</span>
                    }
                  </ng-template>
                  <div class="wb__sync-tab">
                    @if (syncLoading) {
                      <mat-progress-spinner mode="indeterminate" diameter="32"></mat-progress-spinner>
                    } @else if (syncStats) {
                      <div class="wb__sync-stats">
                        <div class="wb__sync-stat wb__sync-stat--synced">
                          <span class="wb__sync-num">{{ syncStats.synced }}</span>
                          <span class="wb__sync-label">Synced</span>
                        </div>
                        <div class="wb__sync-stat wb__sync-stat--failed">
                          <span class="wb__sync-num">{{ syncStats.failed }}</span>
                          <span class="wb__sync-label">Failed</span>
                        </div>
                        <div class="wb__sync-stat wb__sync-stat--pending">
                          <span class="wb__sync-num">{{ syncStats.pending }}</span>
                          <span class="wb__sync-label">Pending</span>
                        </div>
                        <div class="wb__sync-stat wb__sync-stat--stale">
                          <span class="wb__sync-num">{{ syncStats.stale }}</span>
                          <span class="wb__sync-label">Stale</span>
                        </div>
                      </div>
                      <div class="wb__sync-actions">
                        <button mat-stroked-button (click)="retrySyncs()" [disabled]="syncStats.failed === 0">
                          <mat-icon>replay</mat-icon> Retry Failed ({{ syncStats.failed }})
                        </button>
                        <button mat-stroked-button color="warn" (click)="clearSyncLedger()">
                          <mat-icon>delete_sweep</mat-icon> Force Full Re-sync
                        </button>
                        <button mat-stroked-button (click)="loadSyncStats()">
                          <mat-icon>refresh</mat-icon> Refresh
                        </button>
                      </div>
                      @if (syncFailedEntries.length > 0) {
                        <div class="wb__sync-failed-list">
                          <h4>Failed Entries</h4>
                          @for (entry of syncFailedEntries; track entry.id) {
                            <div class="wb__sync-failed-item">
                              <span class="wb__sync-key">{{ entry.entity_key }}</span>
                              <span class="wb__sync-attempts">{{ entry.attempt_count }} attempts</span>
                              @if (entry.last_error) {
                                <span class="wb__sync-error">{{ entry.last_error }}</span>
                              }
                            </div>
                          }
                        </div>
                      }
                    } @else {
                      <p>No sync data available. Enable sync tracking in the trigger node.</p>
                    }
                  </div>
                </mat-tab>
              }
            </mat-tab-group>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    .wb {
      display: flex;
      flex-direction: column;
      height: calc(100vh - 64px - 48px);
      margin: -24px;
    }
    .wb__topbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 16px;
      background: #fff;
      border-bottom: 1px solid #e0e0e0;
      z-index: 10;
    }
    .wb__topbar-left, .wb__topbar-right { display: flex; align-items: center; gap: 10px; }
    .wb__name-area { display: flex; align-items: baseline; gap: 8px; }
    .wb__name-input {
      border: none;
      outline: none;
      font-size: 18px;
      font-weight: 600;
      background: transparent;
      width: 320px;
      padding: 4px 0;
    }
    .wb__name-input:focus { border-bottom: 2px solid #1976d2; }
    .wb__version { font-size: 12px; color: #999; }
    .wb__main {
      flex: 1;
      display: flex;
      overflow: hidden;
    }
    .wb__canvas-area { flex: 1; min-width: 0; }
    .wb__right-panel {
      border-left: 1px solid #e0e0e0;
      background: #fff;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      position: relative;
      transition: none;
    }
    .wb__right-panel mat-tab-group {
      flex: 1;
      display: flex;
      flex-direction: column;
    }
    .wb__resize-handle {
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 5px;
      cursor: col-resize;
      z-index: 20;
      background: transparent;
      transition: background 0.15s;
    }
    .wb__resize-handle:hover,
    .wb__resize-handle:active {
      background: #1976d2;
    }
    .wb__panel-toolbar {
      display: flex;
      justify-content: flex-end;
      align-items: center;
      padding: 2px 4px;
      border-bottom: 1px solid #e0e0e0;
      background: #fafafa;
      gap: 2px;
    }
    .wb__panel-toolbar button { width: 32px; height: 32px; }
    .wb__panel-toolbar mat-icon { font-size: 20px; width: 20px; height: 20px; }
    .wb__config-tab, .wb__test-tab, .wb__settings-tab {
      height: calc(100vh - 240px);
      overflow-y: auto;
    }
    .wb__settings-tab { padding: 16px; }
    .wb__field { width: 100%; margin-bottom: 8px; }
    .wb__empty-config {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 300px;
      color: #999;
      text-align: center;
    }
    .wb__empty-config mat-icon { font-size: 48px; width: 48px; height: 48px; margin-bottom: 16px; }
    .wb__hint { font-size: 12px; opacity: 0.7; }
    .wb__test-tab { padding: 16px; }
    .wb__test-input { width: 100%; }
    .wb__test-btn { width: 100%; margin-bottom: 16px; }
    .wb__spinner { display: inline-block; margin-right: 8px; }
    .wb__test-results { margin-top: 8px; }
    .wb__test-status {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 14px;
      border-radius: 6px;
      font-weight: 600;
      margin-bottom: 12px;
    }
    .wb__test-status--success { background: #e8f5e9; color: #2e7d32; }
    .wb__test-status--failed { background: #ffebee; color: #c62828; }
    .wb__test-status--running { background: #e3f2fd; color: #1565c0; }
    .wb__test-duration { margin-left: auto; font-size: 12px; font-weight: 400; }
    .wb__test-error {
      background: #fff3e0;
      padding: 10px;
      border-radius: 6px;
      font-size: 12px;
      margin-bottom: 12px;
      border-left: 3px solid #ff9800;
    }
    .wb__ai-explain-btn { margin-bottom: 12px; }
    .wb__ai-explain {
      background: #f3e5f5;
      border-left: 3px solid #7b1fa2;
      border-radius: 6px;
      padding: 12px;
      margin-bottom: 12px;
      font-size: 12px;
      color: #4a148c;
    }
    .wb__ai-explain h4 { margin: 0 0 8px; font-size: 13px; }
    .wb__ai-explain p { margin: 0 0 8px; line-height: 1.5; }
    .wb__ai-explain-list strong { display: block; margin-bottom: 4px; }
    .wb__ai-explain-list ul { margin: 0 0 8px 18px; padding: 0; }
    .wb__test-nodes h4 { margin: 0 0 8px; font-size: 13px; color: #666; }
    .wb__test-node {
      border: 1px solid #e0e0e0;
      border-radius: 6px;
      margin-bottom: 8px;
      overflow: hidden;
    }
    .wb__test-node--success { border-left: 3px solid #4caf50; }
    .wb__test-node--failed { border-left: 3px solid #f44336; }
    .wb__test-node--filtered { border-left: 3px solid #ff9800; }
    .wb__test-node-header {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 8px 10px;
      font-size: 13px;
    }
    .wb__test-node-status { font-size: 10px !important; min-height: 22px !important; padding: 0 8px !important; }
    .wb__test-node-time { margin-left: auto; font-size: 11px; color: #999; }
    .wb__test-node-output, .wb__test-node-error {
      font-size: 11px;
      padding: 6px 10px;
      margin: 0;
      background: #f5f5f5;
      max-height: 120px;
      overflow: auto;
      white-space: pre-wrap;
      word-break: break-all;
    }
    .wb__test-node-error { background: #ffebee; color: #c62828; }

    .wb__api-section {
      margin-top: 16px;
      border-top: 1px solid #e0e0e0;
      padding-top: 16px;
    }
    .wb__api-header {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
      font-size: 14px;
      margin-bottom: 16px;
      color: #333;
    }
    .wb__api-header mat-icon { font-size: 20px; width: 20px; height: 20px; color: #1976d2; }
    .wb__api-block { margin-bottom: 12px; }
    .wb__api-label {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      font-weight: 500;
      color: #666;
      margin-bottom: 4px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .wb__api-method {
      background: #1976d2;
      color: #fff;
      font-size: 10px;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 3px;
      letter-spacing: 0;
    }
    .wb__api-copy {
      width: 24px !important;
      height: 24px !important;
      line-height: 24px !important;
      margin-left: auto;
    }
    .wb__api-copy mat-icon { font-size: 16px; width: 16px; height: 16px; }
    .wb__api-code {
      display: block;
      background: #1e1e1e;
      color: #d4d4d4;
      padding: 12px;
      border-radius: 6px;
      font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
      font-size: 12px;
      line-height: 1.5;
      overflow-x: auto;
      word-break: break-all;
    }
    .wb__api-curl { white-space: pre-wrap; }
    .wb__api-response { white-space: pre-wrap; max-height: 160px; overflow-y: auto; }
    .wb__api-hint {
      font-size: 12px;
      color: #666;
      line-height: 1.5;
      margin-top: 8px;
    }
    .wb__api-hint strong { color: #1976d2; font-family: 'JetBrains Mono', 'Fira Code', monospace; font-size: 11px; }
    .wb__api-divider { border-top: 1px solid #e0e0e0; margin: 16px 0; }
    .wb__api-method--get { background: #2e7d32; }

    .wb__ai-btn {
      background: linear-gradient(135deg, #6a1b9a, #1565c0) !important;
      color: #fff !important;
      border: none !important;
    }
    .wb__ai-tab-icon {
      margin-right: 4px;
      font-size: 18px;
      width: 18px;
      height: 18px;
      vertical-align: middle;
      color: #6a1b9a;
    }
    .wb__ai-tab {
      height: calc(100vh - 240px);
      display: flex;
      flex-direction: column;
    }

    .wb__sync-tab { padding: 16px; }
    .wb__sync-stats { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
    .wb__sync-stat { display: flex; flex-direction: column; align-items: center; padding: 12px 16px; border-radius: 8px; min-width: 80px; }
    .wb__sync-stat--synced { background: #e8f5e9; }
    .wb__sync-stat--failed { background: #ffebee; }
    .wb__sync-stat--pending { background: #fff3e0; }
    .wb__sync-stat--stale { background: #f3e5f5; }
    .wb__sync-num { font-size: 24px; font-weight: 700; line-height: 1; }
    .wb__sync-stat--synced .wb__sync-num { color: #2e7d32; }
    .wb__sync-stat--failed .wb__sync-num { color: #c62828; }
    .wb__sync-stat--pending .wb__sync-num { color: #e65100; }
    .wb__sync-stat--stale .wb__sync-num { color: #7b1fa2; }
    .wb__sync-label { font-size: 11px; color: #666; margin-top: 4px; }
    .wb__sync-actions { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
    .wb__sync-badge { font-size: 10px; padding: 1px 6px; border-radius: 10px; font-weight: 700; margin-left: 6px; }
    .wb__sync-badge--fail { background: #c62828; color: #fff; }
    .wb__sync-failed-list { margin-top: 12px; }
    .wb__sync-failed-list h4 { margin: 0 0 8px; font-size: 13px; font-weight: 600; }
    .wb__sync-failed-item { padding: 8px 12px; border: 1px solid #ffcdd2; border-radius: 6px; margin-bottom: 6px; background: #fff5f5; }
    .wb__sync-key { font-weight: 600; font-size: 13px; display: block; }
    .wb__sync-attempts { font-size: 11px; color: #888; }
    .wb__sync-error { display: block; font-size: 11px; color: #c62828; margin-top: 4px; word-break: break-word; }
  `],
})
export class WorkflowBuilderPage implements OnInit, OnDestroy {
  @ViewChild('canvas') canvas!: WorkflowCanvasComponent;

  workflow: Workflow | null = null;
  workflowId: string | null = null;
  workflowName = 'New Workflow';
  workflowDescription = '';
  workflowOnError = 'stop';
  workflowMaxRetries = 3;
  workflowTimeout = 300;

  nodes: WorkflowNode[] = [];
  edges: WorkflowEdge[] = [];
  connectors: Connector[] = [];

  selectedNode: WorkflowNode | null = null;
  showRightPanel = true;
  rightTabIndex = 0;

  panelWidth = 380;
  panelExpanded = false;
  private readonly PANEL_MIN = 320;
  private readonly PANEL_DEFAULT = 380;
  private readonly PANEL_EXPANDED_RATIO = 0.55;
  private resizing = false;
  private resizeStartX = 0;
  private resizeStartWidth = 0;
  private boundResizeMove: ((e: MouseEvent) => void) | null = null;
  private boundResizeEnd: ((e: MouseEvent) => void) | null = null;

  saving = false;
  testing = false;

  syncStats: { synced: number; failed: number; pending: number; stale: number; total: number } | null = null;
  syncFailedEntries: { id: string; entity_key: string; attempt_count: number; last_error: string | null; updated_at: string | null }[] = [];
  syncLoading = false;

  testDataJson = '{}';
  testExecution: WorkflowExecutionModel | null = null;
  testNodeResults: WorkflowNodeResult[] = [];
  aiExplaining = false;
  aiErrorExplanation: AiExplainErrorResponse | null = null;

  constructor(
    private readonly api: PinquarkApiService,
    private readonly route: ActivatedRoute,
    private readonly router: Router,
    private readonly snackBar: MatSnackBar,
    private readonly clipboard: Clipboard,
    private readonly dialog: MatDialog,
    @Inject(DOCUMENT) private readonly doc: Document,
  ) {}

  get executeEndpoint(): string {
    const base = this.getApiBaseUrl();
    return `${base}/api/v1/workflows/${this.workflowId}/execute`;
  }

  get curlExample(): string {
    const base = this.getApiBaseUrl();
    return `curl -X POST "${base}/api/v1/workflows/${this.workflowId}/execute" \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -d '{
    "trigger_data": {
      "your_field": "value"
    }
  }'`;
  }

  get callEndpoint(): string {
    const base = this.getApiBaseUrl();
    return `${base}/api/v1/workflows/${this.workflowId}/call?api_key=YOUR_API_KEY&key=FILENAME`;
  }

  get callExample(): string {
    const base = this.getApiBaseUrl();
    return `${base}/api/v1/workflows/${this.workflowId}/call?api_key=local-dev-key&key=example-file.pdf`;
  }

  get responseExample(): string {
    return `{
  "status": "success",
  "node_results": [
    { "node_id": "action-1", "status": "success",
      "output": { ... } }
  ],
  "context_snapshot": { ... },
  "duration_ms": 1200
}`;
  }

  copyToClipboard(text: string): void {
    this.clipboard.copy(text);
    this.snackBar.open('Copied to clipboard', '', { duration: 2000 });
  }

  private getApiBaseUrl(): string {
    const cfg = (this.doc.defaultView as any)?.['__PINQUARK_CONFIG__'];
    if (cfg?.apiUrl) return cfg.apiUrl;
    return `${this.doc.location.protocol}//${this.doc.location.hostname}:8080`;
  }

  ngOnInit(): void {
    this.workflowId = this.route.snapshot.paramMap.get('id');

    forkJoin({
      connectors: this.api.listConnectors(),
      instances: this.api.listConnectorInstances(),
    }).subscribe(({ connectors, instances }) => {
      const activeKeys = new Set(
        instances.filter(i => i.is_enabled).map(i => `${i.connector_name}:${i.connector_version}`)
      );
      this.connectors = connectors.filter(c => activeKeys.has(`${c.name}:${c.version}`));
    });

    if (this.workflowId && this.workflowId !== 'new') {
      this.api.getWorkflow(this.workflowId).subscribe(wf => {
        this.workflow = wf;
        this.workflowName = wf.name;
        this.workflowDescription = wf.description;
        this.workflowOnError = wf.on_error;
        this.workflowMaxRetries = wf.max_retries;
        this.workflowTimeout = wf.timeout_seconds;
        this.nodes = wf.nodes;
        this.edges = wf.edges;
        this.applySyncConfigToTrigger(wf);
        if (wf.sync_config) {
          this.loadSyncStats();
        }
        setTimeout(() => this.canvas?.fitView(), 100);
      });
    }
  }

  ngOnDestroy(): void {
    this.onResizeEnd();
  }

  goBack(): void {
    this.router.navigate(['/flows']);
  }

  onNodeSelected(node: WorkflowNode | null): void {
    this.selectedNode = node;
    if (node) {
      this.showRightPanel = true;
      this.rightTabIndex = 0;
    }
  }

  onNodeDoubleClicked(node: WorkflowNode): void {
    this.selectedNode = node;
    this.showRightPanel = true;
    this.rightTabIndex = 0;
  }

  onOpenNodeMapper(node: WorkflowNode): void {
    const cfg = node.config || {};
    const sourceFields = this.getSourceFieldsForNode(node);
    const destFields = this.getDestFieldsForNode(node);
    const effectiveDest = destFields.length > 0 ? destFields : sourceFields;

    const isTransform = node.type === 'transform';
    const mappingKey = isTransform ? 'mappings' : 'field_mapping';
    const rawMappings = cfg[mappingKey];
    const mappings: FieldMapping[] = Array.isArray(rawMappings) ? rawMappings.map((m: FieldMapping) => ({ ...m })) : [];

    const data: VisualFieldMapperDialogData = {
      title: isTransform ? 'Transform Mapper' : 'Action Mapper',
      description: `${node.label || node.type}`,
      sourceFields,
      destinationFields: effectiveDest,
      mappings,
      sourceLabel: 'Available inputs',
      destinationLabel: isTransform ? 'Output fields' : 'Action payload',
      contextHint: '',
    };

    const dialogRef = this.dialog.open(VisualFieldMapperDialogComponent, {
      data,
      maxWidth: '95vw',
      width: '1280px',
      panelClass: 'pinquark-visual-mapper-dialog-panel',
      autoFocus: false,
    });

    dialogRef.afterClosed().subscribe((result?: FieldMapping[]) => {
      if (!result) return;
      const updated = { ...node, config: { ...cfg, [mappingKey]: result } };
      this.canvas.updateNode(updated);
      this.selectedNode = updated;
    });
  }

  private getSourceFieldsForNode(node: WorkflowNode): ConnectorFieldDef[] {
    const fields: ConnectorFieldDef[] = [];
    const seen = new Set<string>();
    const upstreamIds = this.getUpstreamNodeIds(node.id);

    for (const tn of this.nodes.filter(n => n.type === 'trigger')) {
      const c = this.connectors.find(cn => cn.name === tn.config['connector_name']);
      const eventFields = c?.event_fields?.[tn.config['event'] as string] ?? [];
      for (const f of eventFields) {
        if (!seen.has(f.field)) { seen.add(f.field); fields.push(f); }
      }
    }

    for (const an of this.nodes.filter(n => n.type === 'action' && n.id !== node.id && upstreamIds.has(n.id))) {
      const c = this.connectors.find(cn => cn.name === an.config['connector_name']);
      const outFields = c?.output_fields?.[an.config['action'] as string] ?? [];
      for (const f of outFields) {
        if (!seen.has(f.field)) { seen.add(f.field); fields.push(f); }
      }
    }

    return fields;
  }

  private getDestFieldsForNode(node: WorkflowNode): ConnectorFieldDef[] {
    if (node.type !== 'action') return [];
    const c = this.connectors.find(cn => cn.name === node.config['connector_name']);
    return c?.action_fields?.[node.config['action'] as string] ?? [];
  }

  private getUpstreamNodeIds(nodeId: string): Set<string> {
    const upstream = new Set<string>();
    const queue = [nodeId];
    while (queue.length > 0) {
      const current = queue.shift()!;
      for (const edge of this.edges) {
        if (edge.target === current && !upstream.has(edge.source)) {
          upstream.add(edge.source);
          queue.push(edge.source);
        }
      }
    }
    return upstream;
  }

  onNodeConfigChange(updated: WorkflowNode): void {
    this.canvas.updateNode(updated);
    this.selectedNode = updated;
  }

  closeRightPanel(): void {
    this.selectedNode = null;
  }

  onResizeStart(event: MouseEvent): void {
    event.preventDefault();
    this.resizing = true;
    this.resizeStartX = event.clientX;
    this.resizeStartWidth = this.panelWidth;

    this.boundResizeMove = (e: MouseEvent) => this.onResizeMove(e);
    this.boundResizeEnd = () => this.onResizeEnd();
    document.addEventListener('mousemove', this.boundResizeMove);
    document.addEventListener('mouseup', this.boundResizeEnd);
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  }

  private onResizeMove(event: MouseEvent): void {
    if (!this.resizing) return;
    const delta = this.resizeStartX - event.clientX;
    const maxWidth = window.innerWidth * 0.75;
    this.panelWidth = Math.max(this.PANEL_MIN, Math.min(maxWidth, this.resizeStartWidth + delta));
    this.panelExpanded = this.panelWidth > this.PANEL_DEFAULT + 100;
  }

  private onResizeEnd(): void {
    this.resizing = false;
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
    if (this.boundResizeMove) {
      document.removeEventListener('mousemove', this.boundResizeMove);
      this.boundResizeMove = null;
    }
    if (this.boundResizeEnd) {
      document.removeEventListener('mouseup', this.boundResizeEnd);
      this.boundResizeEnd = null;
    }
  }

  togglePanelExpand(): void {
    if (this.panelExpanded) {
      this.panelWidth = this.PANEL_DEFAULT;
      this.panelExpanded = false;
    } else {
      this.panelWidth = Math.round(window.innerWidth * this.PANEL_EXPANDED_RATIO);
      this.panelExpanded = true;
    }
  }

  openTestPanel(): void {
    this.showRightPanel = true;
    this.rightTabIndex = 1;
  }

  openAiChat(): void {
    this.showRightPanel = true;
    this.rightTabIndex = 3;
    if (this.panelWidth < 420) {
      this.panelWidth = 420;
    }
  }

  onAiWorkflowGenerated(event: {
    nodes: WorkflowNode[];
    edges: WorkflowEdge[];
    name?: string;
    description?: string;
  }): void {
    this.nodes = event.nodes;
    this.edges = event.edges;
    if (event.name) {
      this.workflowName = event.name;
    }
    if (event.description) {
      this.workflowDescription = event.description;
    }
    setTimeout(() => this.canvas?.fitView(), 100);
  }

  private applySyncConfigToTrigger(wf: Workflow): void {
    if (!wf.sync_config) return;
    const triggerNode = this.nodes.find(n => n.type === 'trigger');
    if (!triggerNode) return;
    const sc = wf.sync_config;
    triggerNode.config['sync_enabled'] = sc.enabled ?? false;
    triggerNode.config['sync_entity_key'] = sc.entity_key_field ?? '';
    triggerNode.config['sync_mode'] = sc.mode ?? 'incremental';
    triggerNode.config['sync_on_duplicate'] = sc.on_duplicate ?? 'update';
    triggerNode.config['sync_max_retries'] = sc.max_retries ?? 3;
  }

  private buildSyncConfig(): SyncConfig | null {
    const triggerNode = this.nodes.find(n => n.type === 'trigger');
    const cfg = triggerNode?.config ?? {};
    if (!cfg['sync_enabled']) return null;
    return {
      enabled: true,
      entity_key_field: (cfg['sync_entity_key'] as string) || undefined,
      content_hash_fields: ['*'],
      mode: (cfg['sync_mode'] as SyncConfig['mode']) || 'incremental',
      on_duplicate: (cfg['sync_on_duplicate'] as SyncConfig['on_duplicate']) || 'update',
      max_retries: (cfg['sync_max_retries'] as number) ?? 3,
    };
  }

  save(): void {
    this.saving = true;
    const body = {
      name: this.workflowName,
      description: this.workflowDescription,
      nodes: this.nodes,
      edges: this.edges,
      sync_config: this.buildSyncConfig(),
      on_error: this.workflowOnError,
      max_retries: this.workflowMaxRetries,
      timeout_seconds: this.workflowTimeout,
    };

    if (this.workflow) {
      this.api.updateWorkflow(this.workflow.id, body).subscribe({
        next: (wf) => {
          this.workflow = wf;
          this.saving = false;
          this.snackBar.open('Workflow saved', 'OK', { duration: 3000 });
        },
        error: () => {
          this.saving = false;
          this.snackBar.open('Failed to save workflow', 'Retry', { duration: 5000 });
        },
      });
    } else {
      this.api.createWorkflow(body).subscribe({
        next: (wf) => {
          this.workflow = wf;
          this.workflowId = wf.id;
          this.saving = false;
          this.snackBar.open('Workflow created', 'OK', { duration: 3000 });
          this.router.navigate(['/workflows', wf.id], { replaceUrl: true });
        },
        error: () => {
          this.saving = false;
          this.snackBar.open('Failed to create workflow', 'Retry', { duration: 5000 });
        },
      });
    }
  }

  toggleEnabled(): void {
    if (!this.workflow) return;
    this.api.toggleWorkflow(this.workflow.id).subscribe({
      next: (res) => {
        if (this.workflow) {
          this.workflow = { ...this.workflow, is_enabled: res.is_enabled };
        }
        this.snackBar.open(`Workflow ${res.is_enabled ? 'enabled' : 'disabled'}`, 'OK', { duration: 3000 });
      },
    });
  }

  runTest(): void {
    if (!this.workflow) {
      this.snackBar.open('Save the workflow first', 'OK', { duration: 3000 });
      return;
    }

    let triggerData: Record<string, unknown>;
    try {
      triggerData = JSON.parse(this.testDataJson);
    } catch {
      this.snackBar.open('Invalid JSON', 'OK', { duration: 3000 });
      return;
    }

    this.testing = true;
    this.testExecution = null;
    this.testNodeResults = [];
    this.aiErrorExplanation = null;

    this.api.testWorkflow(this.workflow.id, triggerData).subscribe({
      next: (exec) => {
        this.testExecution = exec;
        this.testNodeResults = exec.node_results;
        this.testing = false;
      },
      error: (err) => {
        this.testing = false;
        this.snackBar.open('Test failed: ' + (err.error?.detail || 'Unknown error'), 'OK', { duration: 5000 });
      },
    });
  }

  getNodeResultIcon(nr: WorkflowNodeResult): string {
    switch (nr.status) {
      case 'success': return 'check_circle';
      case 'failed': return 'error';
      case 'filtered': return 'filter_alt';
      default: return 'pending';
    }
  }

  formatOutput(output: unknown): string {
    if (output == null) return '';
    if (typeof output === 'string') return output;
    try {
      return JSON.stringify(output, null, 2);
    } catch {
      return String(output);
    }
  }

  explainTestError(): void {
    if (!this.testExecution?.error) {
      return;
    }
    const settings = this.loadAiSettings();
    if (!settings?.apiKey) {
      this.snackBar.open('Save AI settings first on the Settings page', 'OK', { duration: 4000 });
      return;
    }
    const failedNode = this.testExecution.node_results.find(node => node.node_id === this.testExecution?.error_node_id);
    this.aiExplaining = true;
    this.aiErrorExplanation = null;
    this.api.aiExplainError({
      model: settings.model,
      api_key: settings.apiKey,
      workflow_name: this.workflowName,
      node_label: failedNode?.label,
      node_type: failedNode?.node_type,
      error: this.testExecution.error,
      trigger_data: this.testExecution.trigger_data,
      node_results: this.testExecution.node_results,
    }).subscribe({
      next: (response) => {
        this.aiExplaining = false;
        this.aiErrorExplanation = response;
      },
      error: (err) => {
        this.aiExplaining = false;
        const detail = err?.error?.detail || 'Failed to explain error';
        this.snackBar.open(detail, 'OK', { duration: 5000 });
      },
    });
  }

  private loadAiSettings(): { model: 'gemini' | 'opus'; apiKey: string } | null {
    try {
      const stored = localStorage.getItem('pinquark_ai_settings');
      if (!stored) {
        return null;
      }
      const parsed = JSON.parse(stored);
      return {
        model: parsed.model || 'gemini',
        apiKey: parsed.apiKey || '',
      };
    } catch {
      return null;
    }
  }

  // ── Import / Export ──

  exportWorkflow(): void {
    const exportData = {
      name: this.workflowName,
      description: this.workflowDescription,
      nodes: this.nodes,
      edges: this.edges,
      variables: this.workflow?.variables ?? {},
      sync_config: this.buildSyncConfig(),
      on_error: this.workflowOnError,
      max_retries: this.workflowMaxRetries,
      timeout_seconds: this.workflowTimeout,
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = this.doc.createElement('a');
    a.href = url;
    a.download = `${this.workflowName.replace(/[^a-zA-Z0-9_-]/g, '_').toLowerCase()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    this.snackBar.open('Workflow exported', '', { duration: 2000 });
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
        this.workflowName = data.name;
        this.workflowDescription = data.description ?? '';
        this.nodes = data.nodes;
        this.edges = data.edges;
        this.workflowOnError = data.on_error ?? 'stop';
        this.workflowMaxRetries = data.max_retries ?? 3;
        this.workflowTimeout = data.timeout_seconds ?? 300;
        setTimeout(() => this.canvas?.fitView(), 100);
        this.snackBar.open('Workflow loaded from file — click Save to persist', 'OK', { duration: 5000 });
      } catch {
        this.snackBar.open('Invalid JSON file', 'OK', { duration: 5000 });
      }
      input.value = '';
    };
    reader.readAsText(file);
  }

  // ── Sync Status ──

  loadSyncStats(): void {
    if (!this.workflow) return;
    this.syncLoading = true;
    this.api.getSyncStats(this.workflow.id).subscribe({
      next: (data: { stats: { synced: number; failed: number; pending: number; stale: number; total: number } }) => {
        this.syncStats = data.stats;
        this.syncLoading = false;
        if (data.stats.failed > 0) {
          this.loadSyncFailed();
        } else {
          this.syncFailedEntries = [];
        }
      },
      error: () => {
        this.syncLoading = false;
      },
    });
  }

  private loadSyncFailed(): void {
    if (!this.workflow) return;
    this.api.getSyncFailed(this.workflow.id).subscribe({
      next: (entries: { id: string; entity_key: string; attempt_count: number; last_error: string | null; updated_at: string | null }[]) => {
        this.syncFailedEntries = entries;
      },
    });
  }

  retrySyncs(): void {
    if (!this.workflow) return;
    this.api.retrySyncs(this.workflow.id).subscribe({
      next: () => {
        this.snackBar.open('Failed entries reset for retry', 'OK', { duration: 3000 });
        this.loadSyncStats();
      },
      error: () => {
        this.snackBar.open('Failed to retry syncs', 'OK', { duration: 3000 });
      },
    });
  }

  clearSyncLedger(): void {
    if (!this.workflow) return;
    this.api.clearSyncLedger(this.workflow.id).subscribe({
      next: () => {
        this.snackBar.open('Sync ledger cleared — next poll will re-sync everything', 'OK', { duration: 5000 });
        this.loadSyncStats();
      },
      error: () => {
        this.snackBar.open('Failed to clear sync ledger', 'OK', { duration: 3000 });
      },
    });
  }
}
