import { Component, Input, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatChipsModule } from '@angular/material/chips';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { MatTabsModule } from '@angular/material/tabs';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDividerModule } from '@angular/material/divider';
import { forkJoin, of, catchError } from 'rxjs';

import { Flow, FlowExecution, FlowExecutionDetail, WorkflowExecutionDetail, WorkflowNodeResultDetail } from '../../models';
import { Workflow, WorkflowExecution, WorkflowNode, WorkflowNodeResult } from '../../models/workflow.model';
import { PinquarkApiService } from '../../services/pinquark-api.service';
import { WorkflowCanvasComponent } from '../workflow-canvas/workflow-canvas.component';

interface UnifiedExecution {
  id: string;
  type: 'flow' | 'workflow';
  name: string;
  status: string;
  connectors: string;
  duration_ms: number | null;
  started_at: string;
  error: string | null;
  node_results?: unknown[];
}

@Component({
  selector: 'pinquark-operation-log',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatTableModule,
    MatChipsModule,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatSelectModule,
    MatInputModule,
    MatTabsModule,
    MatProgressSpinnerModule,
    MatTooltipModule,
    MatDividerModule,
    WorkflowCanvasComponent,
  ],
  template: `
    <div class="operation-log" [class.operation-log--detail-open]="!!selectedExecution">
      <!-- ─── List view ─── -->
      <div class="operation-log__list">
        <div class="operation-log__header">
          <h3>Operation Log</h3>
          <button mat-icon-button (click)="loadAll()" matTooltip="Refresh">
            <mat-icon>refresh</mat-icon>
          </button>
        </div>

        <div class="operation-log__filters">
          <mat-form-field appearance="outline" class="operation-log__search">
            <mat-label>Search</mat-label>
            <input matInput [(ngModel)]="searchQuery" (ngModelChange)="applyFilters()" placeholder="Search by name, error..." />
            <mat-icon matPrefix>search</mat-icon>
            @if (searchQuery) {
              <button matSuffix mat-icon-button (click)="searchQuery = ''; applyFilters()">
                <mat-icon>close</mat-icon>
              </button>
            }
          </mat-form-field>
          <mat-form-field appearance="outline" class="operation-log__filter">
            <mat-label>Status</mat-label>
            <mat-select [(ngModel)]="selectedStatus" (selectionChange)="applyFilters()">
              <mat-option value="all">All</mat-option>
              <mat-option value="success">Success</mat-option>
              <mat-option value="failed">Failed</mat-option>
              <mat-option value="running">Running</mat-option>
              <mat-option value="skipped">Skipped</mat-option>
            </mat-select>
          </mat-form-field>
          <mat-form-field appearance="outline" class="operation-log__filter">
            <mat-label>Type</mat-label>
            <mat-select [(ngModel)]="selectedType" (selectionChange)="applyFilters()">
              <mat-option value="all">All</mat-option>
              <mat-option value="flow">Quick Flows</mat-option>
              <mat-option value="workflow">Workflows</mat-option>
            </mat-select>
          </mat-form-field>
          <mat-form-field appearance="outline" class="operation-log__filter operation-log__filter--wide">
            <mat-label>Connector</mat-label>
            <mat-select [(ngModel)]="selectedConnector" (selectionChange)="applyFilters()">
              <mat-option value="">All connectors</mat-option>
              @for (c of connectorNames; track c) {
                <mat-option [value]="c">{{ c }}</mat-option>
              }
            </mat-select>
          </mat-form-field>
          <mat-form-field appearance="outline" class="operation-log__filter">
            <mat-label>From</mat-label>
            <input matInput type="datetime-local" [(ngModel)]="dateFrom" (ngModelChange)="onDateFilterChange()" />
            @if (dateFrom) {
              <button matSuffix mat-icon-button (click)="dateFrom = ''; onDateFilterChange()">
                <mat-icon>close</mat-icon>
              </button>
            }
          </mat-form-field>
          <mat-form-field appearance="outline" class="operation-log__filter">
            <mat-label>To</mat-label>
            <input matInput type="datetime-local" [(ngModel)]="dateTo" (ngModelChange)="onDateFilterChange()" />
            @if (dateTo) {
              <button matSuffix mat-icon-button (click)="dateTo = ''; onDateFilterChange()">
                <mat-icon>close</mat-icon>
              </button>
            }
          </mat-form-field>
        </div>

        @if (initialLoading) {
          <div class="operation-log__initial-loading">
            <mat-spinner diameter="40"></mat-spinner>
            <span>Loading operation log...</span>
          </div>
        }

        @if (loadError && !initialLoading) {
          <div class="operation-log__error-banner">
            <mat-icon>error_outline</mat-icon>
            <span>{{ loadError }}</span>
            <button mat-stroked-button (click)="loadAll()">
              <mat-icon>refresh</mat-icon> Retry
            </button>
          </div>
        }

        @if (!initialLoading) {
        <table mat-table [dataSource]="filteredUnified" class="operation-log__table">
          <ng-container matColumnDef="type">
            <th mat-header-cell *matHeaderCellDef>Type</th>
            <td mat-cell *matCellDef="let e">
              <mat-icon [style.font-size.px]="18" [style.color]="e.type === 'workflow' ? '#7b1fa2' : '#1565c0'">
                {{ e.type === 'workflow' ? 'account_tree' : 'swap_horiz' }}
              </mat-icon>
            </td>
          </ng-container>

          <ng-container matColumnDef="status">
            <th mat-header-cell *matHeaderCellDef>Status</th>
            <td mat-cell *matCellDef="let e">
              <mat-chip [class]="'status-' + e.status">{{ e.status }}</mat-chip>
            </td>
          </ng-container>

          <ng-container matColumnDef="name">
            <th mat-header-cell *matHeaderCellDef>Name</th>
            <td mat-cell *matCellDef="let e">{{ e.name }}</td>
          </ng-container>

          <ng-container matColumnDef="connectors">
            <th mat-header-cell *matHeaderCellDef>Connectors</th>
            <td mat-cell *matCellDef="let e">{{ e.connectors }}</td>
          </ng-container>

          <ng-container matColumnDef="duration">
            <th mat-header-cell *matHeaderCellDef>Duration</th>
            <td mat-cell *matCellDef="let e">{{ e.duration_ms ? e.duration_ms + 'ms' : '-' }}</td>
          </ng-container>

          <ng-container matColumnDef="started_at">
            <th mat-header-cell *matHeaderCellDef>Started</th>
            <td mat-cell *matCellDef="let e">{{ e.started_at | date:'short' }}</td>
          </ng-container>

          <ng-container matColumnDef="error">
            <th mat-header-cell *matHeaderCellDef>Error</th>
            <td mat-cell *matCellDef="let e" class="operation-log__error-cell">{{ e.error || '-' }}</td>
          </ng-container>

          <ng-container matColumnDef="actions">
            <th mat-header-cell *matHeaderCellDef></th>
            <td mat-cell *matCellDef="let e">
              <button mat-icon-button matTooltip="View details" (click)="openDetail(e); $event.stopPropagation()">
                <mat-icon>visibility</mat-icon>
              </button>
            </td>
          </ng-container>

          <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
          <tr mat-row *matRowDef="let row; columns: displayedColumns;"
              (click)="openDetail(row)"
              [class.operation-log__row--selected]="selectedExecution?.id === row.id"
              class="operation-log__row--clickable">
          </tr>
        </table>

        @if (filteredUnified.length === 0 && !loadingMore && !loadError) {
          <p class="operation-log__empty">No executions matching the selected filters.</p>
        }

        @if (loadingMore) {
          <div class="operation-log__loading-more">
            <mat-spinner diameter="24"></mat-spinner>
            <span>Loading more...</span>
          </div>
        }

        @if (!hasMore && filteredUnified.length > 0) {
          <p class="operation-log__end-of-list">All executions loaded</p>
        }
        }
      </div>

      <!-- ─── Detail panel ─── -->
      @if (selectedExecution) {
        <div class="operation-log__detail">
          <div class="detail__header">
            <div class="detail__header-left">
              <mat-icon [style.color]="selectedExecution.type === 'workflow' ? '#7b1fa2' : '#1565c0'">
                {{ selectedExecution.type === 'workflow' ? 'account_tree' : 'swap_horiz' }}
              </mat-icon>
              <div>
                <h3 class="detail__title">{{ selectedExecution.name }}</h3>
                <span class="detail__subtitle">{{ selectedExecution.type === 'workflow' ? 'Workflow' : 'Quick Flow' }} Execution</span>
              </div>
            </div>
            <button mat-icon-button class="detail__close-btn" (click)="closeDetail()" matTooltip="Close">
              <mat-icon>close</mat-icon>
            </button>
          </div>

          @if (detailLoading) {
            <div class="detail__loading">
              <mat-spinner diameter="32"></mat-spinner>
              <span>Loading execution details...</span>
            </div>
          }

          <!-- GDPR Banner -->
          @if (!detailLoading && (flowDetail || workflowDetail)) {
            <div class="detail__gdpr-banner">
              <mat-icon>security</mat-icon>
              <span>GDPR: Personal data (email addresses, phone numbers, names) has been masked to protect privacy.</span>
            </div>
          }

          <!-- Overview section -->
          @if (!detailLoading && (flowDetail || workflowDetail)) {
            <div class="detail__section">
              <h4 class="detail__section-title">
                <mat-icon>info</mat-icon> Overview
              </h4>
              <div class="detail__grid">
                <div class="detail__field">
                  <span class="detail__label">Status</span>
                  <mat-chip [class]="'status-' + selectedExecution.status">{{ selectedExecution.status }}</mat-chip>
                </div>
                <div class="detail__field">
                  <span class="detail__label">Started</span>
                  <span class="detail__value">{{ selectedExecution.started_at | date:'medium' }}</span>
                </div>
                <div class="detail__field">
                  <span class="detail__label">Duration</span>
                  <span class="detail__value">{{ selectedExecution.duration_ms ? selectedExecution.duration_ms + 'ms' : '-' }}</span>
                </div>
                <div class="detail__field">
                  <span class="detail__label">Connectors</span>
                  <span class="detail__value">{{ selectedExecution.connectors }}</span>
                </div>
              </div>
            </div>
          }

          <!-- Flow detail -->
          @if (!detailLoading && flowDetail) {
            <mat-divider></mat-divider>
            <div class="detail__section">
              <h4 class="detail__section-title">
                <mat-icon>input</mat-icon> Source Event Data
              </h4>
              <div class="detail__json-block">
                <pre>{{ formatJson(flowDetail.source_event_data) }}</pre>
              </div>
            </div>
            <div class="detail__section">
              <h4 class="detail__section-title">
                <mat-icon>output</mat-icon> Destination Action Data
              </h4>
              <div class="detail__json-block">
                <pre>{{ formatJson(flowDetail.destination_action_data) }}</pre>
              </div>
            </div>
            @if (flowDetail.result) {
              <div class="detail__section">
                <h4 class="detail__section-title">
                  <mat-icon>check_circle</mat-icon> Result
                </h4>
                <div class="detail__json-block">
                  <pre>{{ formatJson(flowDetail.result) }}</pre>
                </div>
              </div>
            }
            @if (flowDetail.error) {
              <div class="detail__section">
                <h4 class="detail__section-title detail__section-title--error">
                  <mat-icon>error</mat-icon> Error
                </h4>
                <div class="detail__error-block">{{ flowDetail.error }}</div>
              </div>
            }
          }

          <!-- Workflow detail -->
          @if (!detailLoading && workflowDetail) {
            @if (workflowDetail.workflow_description) {
              <div class="detail__section">
                <p class="detail__description">{{ workflowDetail.workflow_description }}</p>
              </div>
            }
            @if (workflowDetail.error) {
              <div class="detail__section">
                <h4 class="detail__section-title detail__section-title--error">
                  <mat-icon>error</mat-icon> Error
                </h4>
                <div class="detail__error-block">
                  {{ workflowDetail.error }}
                  @if (workflowDetail.error_node_id) {
                    <br/><strong>Failed at node:</strong> {{ workflowDetail.error_node_id }}
                  }
                </div>
              </div>
            }

            <!-- Workflow Graph Visualization -->
            @if (workflowNodes.length > 0) {
              <div class="detail__section">
                <h4 class="detail__section-title detail__section-title--collapsible" (click)="toggleSection('graph')">
                  <mat-icon>schema</mat-icon> Workflow Graph
                  <mat-icon class="detail__collapse-icon">{{ collapsedSections.has('graph') ? 'expand_more' : 'expand_less' }}</mat-icon>
                </h4>
                @if (!collapsedSections.has('graph')) {
                  <div class="detail__canvas-container">
                    <pinquark-workflow-canvas
                      [nodes]="workflowNodes"
                      [edges]="workflowEdges"
                      [nodeResults]="canvasNodeResults"
                      [readonly]="true"
                    ></pinquark-workflow-canvas>
                  </div>
                  <div class="detail__legend">
                    <span class="detail__legend-item"><span class="detail__legend-dot detail__legend-dot--success"></span> Success</span>
                    <span class="detail__legend-item"><span class="detail__legend-dot detail__legend-dot--failed"></span> Failed</span>
                    <span class="detail__legend-item"><span class="detail__legend-dot detail__legend-dot--filtered"></span> Filtered</span>
                    <span class="detail__legend-item"><span class="detail__legend-dot detail__legend-dot--unexecuted"></span> Not executed</span>
                  </div>
                }
              </div>
            }

            <mat-divider></mat-divider>

            <!-- Trigger data -->
            <div class="detail__section">
              <h4 class="detail__section-title detail__section-title--collapsible" (click)="toggleSection('trigger')">
                <mat-icon>bolt</mat-icon> Trigger Data
                @if (workflowDetail.trigger_connector) {
                  <span class="detail__connector-badge">{{ workflowDetail.trigger_connector }}</span>
                }
                <mat-icon class="detail__collapse-icon">{{ collapsedSections.has('trigger') ? 'expand_more' : 'expand_less' }}</mat-icon>
              </h4>
              @if (!collapsedSections.has('trigger')) {
                <div class="detail__json-block">
                  <pre>{{ formatJson(workflowDetail.trigger_data) }}</pre>
                </div>
              }
            </div>

            <mat-divider></mat-divider>

            <!-- Node-by-node execution timeline -->
            <div class="detail__section">
              <h4 class="detail__section-title detail__section-title--collapsible" (click)="toggleSection('timeline')">
                <mat-icon>timeline</mat-icon> Execution Timeline
                <span class="detail__node-count">({{ workflowDetail.node_results.length }} nodes)</span>
                <mat-icon class="detail__collapse-icon">{{ collapsedSections.has('timeline') ? 'expand_more' : 'expand_less' }}</mat-icon>
              </h4>

              @if (!collapsedSections.has('timeline')) {
              <div class="detail__timeline">
                @for (node of workflowDetail.node_results; track node.node_id; let idx = $index) {
                  <div class="timeline__node" [class]="'timeline__node--' + node.status">
                    <div class="timeline__connector">
                      <div class="timeline__dot" [class]="'timeline__dot--' + node.status">
                        <mat-icon>
                          @switch (node.status) {
                            @case ('success') { check }
                            @case ('failed') { close }
                            @case ('filtered') { filter_alt }
                            @case ('running') { hourglass_empty }
                          }
                        </mat-icon>
                      </div>
                      @if (idx < workflowDetail!.node_results.length - 1) {
                        <div class="timeline__line"></div>
                      }
                    </div>

                    <div class="timeline__content" (click)="toggleNodeExpand(node.node_id)">
                      <div class="timeline__node-header">
                        <div class="timeline__node-info">
                          <span class="timeline__node-label">{{ node.label || node.node_id }}</span>
                          <span class="timeline__node-type">{{ node.node_type }}</span>
                          @if (isEmailAction(node)) {
                            <span class="timeline__email-badge">
                              <mat-icon [style.font-size.px]="14">email</mat-icon> Email
                            </span>
                          }
                        </div>
                        <div class="timeline__node-meta">
                          @if (node.duration_ms !== undefined) {
                            <span class="timeline__duration">{{ node.duration_ms }}ms</span>
                          }
                          <mat-icon class="timeline__expand-icon">
                            {{ expandedNodes.has(node.node_id) ? 'expand_less' : 'expand_more' }}
                          </mat-icon>
                        </div>
                      </div>

                      @if (expandedNodes.has(node.node_id)) {
                        <div class="timeline__node-detail">
                          @if (node.error) {
                            <div class="detail__error-block">{{ node.error }}</div>
                          }

                          @if (isEmailAction(node) && node.output) {
                            <div class="timeline__email-detail">
                              <h5>Email Details</h5>
                              <div class="detail__grid">
                                @if (getEmailField(node, 'status')) {
                                  <div class="detail__field">
                                    <span class="detail__label">Status</span>
                                    <mat-chip [class]="'status-' + getEmailField(node, 'status')">{{ getEmailField(node, 'status') }}</mat-chip>
                                  </div>
                                }
                                @if (getEmailField(node, 'message_id')) {
                                  <div class="detail__field">
                                    <span class="detail__label">Message ID</span>
                                    <span class="detail__value detail__value--mono">{{ getEmailField(node, 'message_id') }}</span>
                                  </div>
                                }
                                @if (getEmailField(node, 'account_name')) {
                                  <div class="detail__field">
                                    <span class="detail__label">Account</span>
                                    <span class="detail__value">{{ getEmailField(node, 'account_name') }}</span>
                                  </div>
                                }
                                @if (getEmailField(node, 'to') || getEmailField(node, 'recipient')) {
                                  <div class="detail__field">
                                    <span class="detail__label">Recipient</span>
                                    <span class="detail__value detail__value--redacted">
                                      {{ getEmailField(node, 'to') || getEmailField(node, 'recipient') }}
                                      @if (isRedactedField(node.output, 'to') || isRedactedField(node.output, 'recipient')) {
                                        <mat-icon matTooltip="Masked for GDPR/RODO compliance" [style.font-size.px]="14">shield</mat-icon>
                                      }
                                    </span>
                                  </div>
                                }
                                @if (getEmailField(node, 'subject')) {
                                  <div class="detail__field detail__field--full">
                                    <span class="detail__label">Subject</span>
                                    <span class="detail__value">{{ getEmailField(node, 'subject') }}</span>
                                  </div>
                                }
                              </div>
                            </div>
                          } @else if (node.output) {
                            <div class="detail__json-block">
                              <pre>{{ formatJson(node.output) }}</pre>
                            </div>
                          }
                        </div>
                      }
                    </div>
                  </div>
                }
              </div>
              }
            </div>
          }
        </div>
      }
    </div>
  `,
  styles: [`
    :host {
      display: block;
      width: 100%;
      height: 100%;
    }
    .operation-log {
      display: flex;
      gap: 0;
      height: 100%;
      width: 100%;
      overflow: hidden;
    }
    .operation-log__list {
      flex: 1 1 auto;
      min-width: 0;
      overflow-y: auto;
      overflow-x: auto;
      transition: flex 0.3s ease;
    }
    .operation-log--detail-open .operation-log__list {
      flex: 0 0 42%;
      max-width: 42%;
    }
    .operation-log__header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .operation-log__filters {
      display: flex;
      gap: 12px;
      align-items: center;
      flex-wrap: wrap;
      margin-bottom: 8px;
    }
    .operation-log__search { width: 280px; }
    .operation-log--detail-open .operation-log__search { width: 100%; }
    .operation-log__filter { width: 180px; }
    .operation-log--detail-open .operation-log__filter { width: 120px; }
    .operation-log__filter--wide { width: 260px; }
    .operation-log--detail-open .operation-log__filter--wide { width: 160px; }
    .operation-log__table { width: 100%; }
    .operation-log--detail-open .operation-log__table {
      font-size: 13px;
    }
    .operation-log__initial-loading {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 16px;
      padding: 64px 0;
      color: rgba(0, 0, 0, 0.54);
      font-size: 14px;
    }
    .operation-log__error-banner {
      display: flex;
      align-items: center;
      gap: 12px;
      background: #fce4ec;
      border: 1px solid #ef9a9a;
      border-radius: 8px;
      padding: 12px 16px;
      margin-bottom: 16px;
      color: #c62828;
      font-size: 14px;
    }
    .operation-log__error-banner mat-icon {
      color: #c62828;
      flex-shrink: 0;
    }
    .operation-log__error-banner span {
      flex: 1;
    }
    .operation-log__empty {
      color: rgba(0, 0, 0, 0.54);
      font-style: italic;
      padding: 16px 0;
    }
    .operation-log__loading-more {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      padding: 16px 0;
      color: rgba(0, 0, 0, 0.54);
      font-size: 13px;
    }
    .operation-log__end-of-list {
      text-align: center;
      color: rgba(0, 0, 0, 0.3);
      font-size: 12px;
      padding: 12px 0;
      margin: 0;
    }
    .operation-log__error-cell {
      max-width: 200px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .operation-log__row--clickable {
      cursor: pointer;
      transition: background-color 0.15s;
    }
    .operation-log__row--clickable:hover {
      background-color: rgba(0, 0, 0, 0.04);
    }
    .operation-log__row--selected {
      background-color: rgba(25, 118, 210, 0.08) !important;
    }

    .status-success { background-color: #c8e6c9 !important; }
    .status-failed { background-color: #ffcdd2 !important; }
    .status-running { background-color: #fff9c4 !important; }
    .status-skipped { background-color: #e0e0e0 !important; }
    .status-filtered { background-color: #e0e0e0 !important; }
    .status-sent { background-color: #c8e6c9 !important; }

    /* ─── Detail panel ─── */
    .operation-log__detail {
      flex: 0 0 58%;
      max-width: 58%;
      border-left: 1px solid rgba(0, 0, 0, 0.12);
      overflow-y: auto;
      overflow-x: hidden;
      padding: 0 20px 24px 20px;
      box-sizing: border-box;
      animation: slideIn 0.25s ease;
    }
    @keyframes slideIn {
      from { opacity: 0; transform: translateX(20px); }
      to { opacity: 1; transform: translateX(0); }
    }

    .detail__header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 0;
      position: sticky;
      top: 0;
      background: white;
      z-index: 2;
      border-bottom: 1px solid rgba(0, 0, 0, 0.08);
      margin-bottom: 12px;
      gap: 8px;
    }
    .detail__header-left {
      display: flex;
      gap: 12px;
      align-items: center;
      min-width: 0;
      flex: 1;
    }
    .detail__close-btn {
      flex-shrink: 0;
    }
    .detail__title {
      margin: 0;
      font-size: 18px;
      font-weight: 500;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .detail__subtitle {
      font-size: 13px;
      color: rgba(0, 0, 0, 0.54);
    }
    .detail__loading {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 32px 0;
      color: rgba(0, 0, 0, 0.54);
    }

    .detail__gdpr-banner {
      display: flex;
      align-items: flex-start;
      gap: 10px;
      background: #e3f2fd;
      border: 1px solid #90caf9;
      border-radius: 8px;
      padding: 12px 16px;
      margin-bottom: 16px;
      font-size: 13px;
      color: #1565c0;
      line-height: 1.5;
    }
    .detail__gdpr-banner mat-icon {
      color: #1565c0;
      flex-shrink: 0;
      margin-top: 1px;
    }

    .detail__section {
      padding: 12px 0;
    }
    .detail__section-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;
      font-weight: 500;
      color: rgba(0, 0, 0, 0.7);
      margin: 0 0 12px;
    }
    .detail__section-title mat-icon { font-size: 20px; width: 20px; height: 20px; }
    .detail__section-title--collapsible {
      cursor: pointer;
      user-select: none;
      border-radius: 6px;
      padding: 6px 8px;
      margin-left: -8px;
      margin-right: -8px;
      transition: background-color 0.15s;
    }
    .detail__section-title--collapsible:hover {
      background-color: rgba(0, 0, 0, 0.04);
    }
    .detail__collapse-icon {
      margin-left: auto;
      color: rgba(0, 0, 0, 0.4);
    }
    .detail__section-title--error { color: #c62828; }
    .detail__section-title--error mat-icon { color: #c62828; }
    .detail__description {
      margin: 0;
      color: rgba(0, 0, 0, 0.6);
      font-size: 14px;
    }
    .detail__connector-badge {
      background: #e8eaf6;
      color: #3949ab;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 400;
    }
    .detail__node-count {
      font-weight: 400;
      color: rgba(0, 0, 0, 0.5);
      font-size: 13px;
    }

    .detail__grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    .detail__field {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .detail__field--full { grid-column: 1 / -1; }
    .detail__label {
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: rgba(0, 0, 0, 0.5);
      font-weight: 500;
    }
    .detail__value {
      font-size: 14px;
      color: rgba(0, 0, 0, 0.87);
      display: flex;
      align-items: center;
      gap: 4px;
    }
    .detail__value--mono { font-family: 'Roboto Mono', monospace; font-size: 12px; word-break: break-all; }
    .detail__value--redacted { color: #e65100; }
    .detail__value--redacted mat-icon { color: #e65100; }

    .detail__json-block {
      background: #fafafa;
      border: 1px solid rgba(0, 0, 0, 0.08);
      border-radius: 8px;
      padding: 12px 16px;
      overflow-x: auto;
      max-height: 300px;
      overflow-y: auto;
    }
    .detail__json-block pre {
      margin: 0;
      font-family: 'Roboto Mono', monospace;
      font-size: 12px;
      line-height: 1.6;
      white-space: pre-wrap;
      word-break: break-word;
    }
    .detail__error-block {
      background: #fce4ec;
      border: 1px solid #ef9a9a;
      border-radius: 8px;
      padding: 12px 16px;
      font-size: 13px;
      color: #b71c1c;
      line-height: 1.5;
    }

    /* ─── Canvas ─── */
    .detail__canvas-container {
      height: 350px;
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid rgba(0, 0, 0, 0.08);
    }
    .detail__legend {
      display: flex;
      gap: 16px;
      padding: 10px 0 0;
      flex-wrap: wrap;
    }
    .detail__legend-item {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      color: rgba(0, 0, 0, 0.6);
    }
    .detail__legend-dot {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      flex-shrink: 0;
    }
    .detail__legend-dot--success { background: #4caf50; }
    .detail__legend-dot--failed { background: #f44336; }
    .detail__legend-dot--filtered { background: #ff9800; }
    .detail__legend-dot--unexecuted { background: #9e9e9e; }

    /* ─── Timeline ─── */
    .detail__timeline {
      padding: 0 0 0 4px;
    }
    .timeline__node {
      display: flex;
      gap: 16px;
      min-height: 48px;
    }
    .timeline__connector {
      display: flex;
      flex-direction: column;
      align-items: center;
      flex-shrink: 0;
      width: 32px;
    }
    .timeline__dot {
      width: 28px;
      height: 28px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .timeline__dot mat-icon {
      font-size: 16px;
      width: 16px;
      height: 16px;
      color: white;
    }
    .timeline__dot--success { background: #43a047; }
    .timeline__dot--failed { background: #e53935; }
    .timeline__dot--filtered { background: #757575; }
    .timeline__dot--running { background: #fbc02d; }
    .timeline__line {
      width: 2px;
      flex: 1;
      background: rgba(0, 0, 0, 0.12);
      min-height: 16px;
    }

    .timeline__content {
      flex: 1;
      padding-bottom: 16px;
      cursor: pointer;
      min-width: 0;
    }
    .timeline__node-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 4px 8px;
      border-radius: 6px;
      transition: background-color 0.15s;
    }
    .timeline__content:hover .timeline__node-header {
      background: rgba(0, 0, 0, 0.04);
    }
    .timeline__node-info {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      min-width: 0;
    }
    .timeline__node-label {
      font-size: 14px;
      font-weight: 500;
      color: rgba(0, 0, 0, 0.87);
    }
    .timeline__node-type {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: rgba(0, 0, 0, 0.45);
      background: rgba(0, 0, 0, 0.06);
      padding: 1px 6px;
      border-radius: 4px;
    }
    .timeline__email-badge {
      display: inline-flex;
      align-items: center;
      gap: 3px;
      background: #e3f2fd;
      color: #1565c0;
      padding: 1px 8px;
      border-radius: 10px;
      font-size: 11px;
      font-weight: 500;
    }
    .timeline__node-meta {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-shrink: 0;
    }
    .timeline__duration {
      font-size: 12px;
      color: rgba(0, 0, 0, 0.45);
      font-family: 'Roboto Mono', monospace;
    }
    .timeline__expand-icon {
      color: rgba(0, 0, 0, 0.35);
    }
    .timeline__node-detail {
      padding: 8px;
      margin-top: 4px;
    }
    .timeline__email-detail h5 {
      margin: 0 0 8px;
      font-size: 13px;
      font-weight: 500;
      color: rgba(0, 0, 0, 0.6);
    }
  `],
})
export class OperationLogComponent implements OnInit, OnDestroy {
  @Input() filter?: { connector?: string; flow_id?: string; workflow_id?: string };
  unified: UnifiedExecution[] = [];
  filteredUnified: UnifiedExecution[] = [];
  flows: Flow[] = [];
  workflows: Workflow[] = [];
  connectorNames: string[] = [];
  displayedColumns = ['type', 'status', 'name', 'connectors', 'duration', 'started_at', 'error', 'actions'];

  searchQuery = '';
  selectedStatus = 'all';
  selectedType = 'all';
  selectedConnector = '';
  dateFrom = '';
  dateTo = '';

  selectedExecution: UnifiedExecution | null = null;
  detailLoading = false;
  flowDetail: FlowExecutionDetail | null = null;
  workflowNodes: WorkflowNode[] = [];
  workflowEdges: { id: string; source: string; target: string; sourceHandle: string; label: string }[] = [];
  canvasNodeResults: WorkflowNodeResult[] = [];
  workflowDetail: WorkflowExecutionDetail | null = null;
  expandedNodes = new Set<string>();
  collapsedSections = new Set<string>();

  initialLoading = true;
  loadError: string | null = null;
  loadingMore = false;
  hasMore = true;
  private readonly PAGE_SIZE = 30;
  private flowExecOffset = 0;
  private wfExecOffset = 0;
  private flowExecHasMore = true;
  private wfExecHasMore = true;
  private scrollHandler?: () => void;
  private dateFilterTimer?: ReturnType<typeof setTimeout>;

  private flowMap = new Map<string, Flow>();
  private workflowMap = new Map<string, Workflow>();

  constructor(private readonly api: PinquarkApiService) {}

  ngOnInit(): void {
    this.loadAll();
  }

  ngOnDestroy(): void {
    this.detachScrollListener();
  }

  private attachScrollListener(): void {
    this.detachScrollListener();
    setTimeout(() => {
      const listEl = document.querySelector('.operation-log__list');
      if (!listEl) return;
      this.scrollHandler = () => this.onListScroll(listEl as HTMLElement);
      listEl.addEventListener('scroll', this.scrollHandler, { passive: true });
    });
  }

  private detachScrollListener(): void {
    if (this.scrollHandler) {
      const listEl = document.querySelector('.operation-log__list');
      if (listEl) listEl.removeEventListener('scroll', this.scrollHandler);
      this.scrollHandler = undefined;
    }
  }

  private onListScroll(el: HTMLElement): void {
    const threshold = 200;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < threshold;
    if (atBottom && !this.loadingMore && this.hasMore) {
      this.loadMore();
    }
  }

  private getDateParams(): { date_from?: string; date_to?: string } {
    const params: { date_from?: string; date_to?: string } = {};
    if (this.dateFrom) {
      const d = new Date(this.dateFrom);
      params.date_from = d.toISOString();
    }
    if (this.dateTo) {
      const d = new Date(this.dateTo);
      params.date_to = d.toISOString();
    }
    return params;
  }

  onDateFilterChange(): void {
    if (this.dateFilterTimer) clearTimeout(this.dateFilterTimer);
    this.dateFilterTimer = setTimeout(() => this.resetAndReload(), 500);
  }

  private resetAndReload(): void {
    this.unified = [];
    this.filteredUnified = [];
    this.flowExecOffset = 0;
    this.wfExecOffset = 0;
    this.flowExecHasMore = true;
    this.wfExecHasMore = true;
    this.hasMore = true;
    this.loadError = null;
    this.loadExecutions();
  }

  loadAll(): void {
    this.unified = [];
    this.filteredUnified = [];
    this.flowExecOffset = 0;
    this.wfExecOffset = 0;
    this.flowExecHasMore = true;
    this.wfExecHasMore = true;
    this.hasMore = true;
    this.initialLoading = true;
    this.loadError = null;

    forkJoin({
      flows: this.api.listFlows().pipe(catchError(() => of([] as Flow[]))),
      workflows: this.api.listWorkflows().pipe(catchError(() => of([] as Workflow[]))),
    }).subscribe(({ flows, workflows }: { flows: Flow[]; workflows: Workflow[] }) => {
      this.flows = flows;
      this.workflows = workflows;
      this.flowMap = new Map(flows.map(f => [f.id, f]));
      this.workflowMap = new Map(workflows.map(w => [w.id, w]));

      const names = new Set<string>();
      for (const f of flows) {
        names.add(f.source_connector);
        names.add(f.destination_connector);
      }
      for (const w of workflows) {
        if (w.trigger_connector) names.add(w.trigger_connector);
        for (const node of (w.nodes || [])) {
          if (node.type === 'action' && node.config?.['connector_name']) {
            names.add(node.config['connector_name'] as string);
          }
        }
      }
      this.connectorNames = [...names].sort();
      this.loadExecutions();
    });
  }

  private loadExecutions(): void {
    this.loadingMore = true;
    const dateParams = this.getDateParams();

    forkJoin({
      flowExecs: this.flowExecHasMore
        ? this.api.listFlowExecutions({ flow_id: this.filter?.flow_id, limit: this.PAGE_SIZE, offset: this.flowExecOffset, ...dateParams }).pipe(catchError(() => of([] as FlowExecution[])))
        : of([] as FlowExecution[]),
      wfExecs: this.wfExecHasMore
        ? this.api.listWorkflowExecutions({ workflow_id: this.filter?.workflow_id, limit: this.PAGE_SIZE, offset: this.wfExecOffset, ...dateParams }).pipe(catchError(() => of([] as WorkflowExecution[])))
        : of([] as WorkflowExecution[]),
    }).subscribe({
      next: ({ flowExecs, wfExecs }: { flowExecs: FlowExecution[]; wfExecs: WorkflowExecution[] }) => {
        if (flowExecs.length < this.PAGE_SIZE) this.flowExecHasMore = false;
        if (wfExecs.length < this.PAGE_SIZE) this.wfExecHasMore = false;
        this.flowExecOffset += flowExecs.length;
        this.wfExecOffset += wfExecs.length;
        this.hasMore = this.flowExecHasMore || this.wfExecHasMore;

        const flowEntries = this.mapFlowExecutions(flowExecs);
        const wfEntries = this.mapWorkflowExecutions(wfExecs);

        const newEntries = [...flowEntries, ...wfEntries].sort(
          (a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
        );

        const existingIds = new Set(this.unified.map(e => e.id));
        const deduped = newEntries.filter(e => !existingIds.has(e.id));
        this.unified = [...this.unified, ...deduped].sort(
          (a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
        );

        this.applyFilters();
        this.loadingMore = false;
        this.initialLoading = false;
        this.attachScrollListener();
      },
      error: () => {
        this.loadingMore = false;
        this.initialLoading = false;
        this.hasMore = false;
        this.loadError = 'Failed to load executions. Check the API connection and try again.';
      },
    });
  }

  loadMore(): void {
    if (this.loadingMore || !this.hasMore) return;
    this.loadExecutions();
  }

  private mapFlowExecutions(execs: FlowExecution[]): UnifiedExecution[] {
    return execs.map(e => {
      const flow = this.flowMap.get(e.flow_id);
      return {
        id: e.id,
        type: 'flow' as const,
        name: flow?.name ?? e.flow_id.slice(0, 8) + '...',
        status: e.status,
        connectors: flow ? `${flow.source_connector} → ${flow.destination_connector}` : '-',
        duration_ms: e.duration_ms,
        started_at: e.started_at,
        error: e.error,
      };
    });
  }

  private mapWorkflowExecutions(execs: WorkflowExecution[]): UnifiedExecution[] {
    return execs.map(e => {
      const wf = this.workflowMap.get(e.workflow_id);
      const actionConnectors = (wf?.nodes || [])
        .filter((n: WorkflowNode) => n.type === 'action' && n.config?.['connector_name'])
        .map((n: WorkflowNode) => n.config?.['connector_name'])
        .filter((v: unknown, i: number, arr: unknown[]) => arr.indexOf(v) === i);
      const connStr = wf?.trigger_connector
        ? `${wf.trigger_connector} → ${actionConnectors.join(', ') || '?'}`
        : '-';
      return {
        id: e.id,
        type: 'workflow' as const,
        name: wf?.name ?? e.workflow_id.slice(0, 8) + '...',
        status: e.status,
        connectors: connStr,
        duration_ms: e.duration_ms,
        started_at: e.started_at,
        error: e.error,
        node_results: e.node_results,
      };
    });
  }

  applyFilters(): void {
    let result = this.unified;

    if (this.selectedStatus !== 'all') {
      result = result.filter(e => e.status === this.selectedStatus);
    }

    if (this.selectedType !== 'all') {
      result = result.filter(e => e.type === this.selectedType);
    }

    if (this.selectedConnector) {
      result = result.filter(e => e.connectors.includes(this.selectedConnector));
    }

    if (this.searchQuery.trim()) {
      const q = this.searchQuery.trim().toLowerCase();
      result = result.filter(e =>
        e.name.toLowerCase().includes(q) ||
        (e.error && e.error.toLowerCase().includes(q)) ||
        e.connectors.toLowerCase().includes(q) ||
        e.status.toLowerCase().includes(q)
      );
    }

    this.filteredUnified = result;
  }

  openDetail(execution: UnifiedExecution): void {
    this.selectedExecution = execution;
    this.flowDetail = null;
    this.workflowDetail = null;
    this.workflowNodes = [];
    this.workflowEdges = [];
    this.canvasNodeResults = [];
    this.expandedNodes = new Set<string>();
    this.detailLoading = true;

    if (execution.type === 'flow') {
      this.api.getFlowExecutionDetail(execution.id).subscribe({
        next: (detail: FlowExecutionDetail) => {
          this.flowDetail = detail;
          this.detailLoading = false;
        },
        error: () => {
          this.detailLoading = false;
        },
      });
    } else {
      this.api.getWorkflowExecutionDetail(execution.id).subscribe({
        next: (detail: WorkflowExecutionDetail) => {
          this.workflowDetail = detail;
          this.detailLoading = false;
          if (detail.node_results.length <= 10) {
            for (const nr of detail.node_results) {
              this.expandedNodes.add(nr.node_id);
            }
          }
          this.canvasNodeResults = detail.node_results.map((nr: WorkflowNodeResultDetail) => ({
            node_id: nr.node_id,
            node_type: nr.node_type,
            label: nr.label,
            status: nr.status,
            output: nr.output,
            error: nr.error,
            duration_ms: nr.duration_ms,
          }));
          if (detail.workflow_nodes_snapshot && detail.workflow_nodes_snapshot.length > 0) {
            this.workflowNodes = detail.workflow_nodes_snapshot as unknown as WorkflowNode[];
            this.workflowEdges = (detail.workflow_edges_snapshot || []) as unknown as { id: string; source: string; target: string; sourceHandle: string; label: string }[];
            this.patchTriggerNodeResult(this.workflowNodes);
          } else {
            this.loadWorkflowDefinition(detail.workflow_id);
          }
        },
        error: () => {
          this.detailLoading = false;
        },
      });
    }
  }

  private loadWorkflowDefinition(workflowId: string): void {
    const applyNodes = (nodes: WorkflowNode[], edges: { id: string; source: string; target: string; sourceHandle: string; label: string }[]) => {
      this.workflowNodes = nodes;
      this.workflowEdges = edges;
      this.patchTriggerNodeResult(nodes);
    };

    const wf = this.workflowMap.get(workflowId);
    if (wf) {
      applyNodes(wf.nodes || [], wf.edges || []);
      return;
    }
    this.api.getWorkflow(workflowId).subscribe({
      next: (wf: Workflow) => applyNodes(wf.nodes || [], wf.edges || []),
      error: () => {},
    });
  }

  private patchTriggerNodeResult(nodes: WorkflowNode[]): void {
    const triggerNode = nodes.find(n => n.type === 'trigger');
    if (!triggerNode) return;
    const alreadyInResults = this.canvasNodeResults.some(r => r.node_id === triggerNode.id);
    if (alreadyInResults) return;
    const hasDownstreamResults = this.canvasNodeResults.length > 0;
    if (hasDownstreamResults) {
      this.canvasNodeResults = [
        { node_id: triggerNode.id, node_type: 'trigger', label: triggerNode.label || triggerNode.id, status: 'success', duration_ms: 0 },
        ...this.canvasNodeResults,
      ];
    }
  }

  closeDetail(): void {
    this.selectedExecution = null;
    this.flowDetail = null;
    this.workflowDetail = null;
    this.collapsedSections.clear();
  }

  toggleSection(section: string): void {
    if (this.collapsedSections.has(section)) {
      this.collapsedSections.delete(section);
    } else {
      this.collapsedSections.add(section);
    }
  }

  toggleNodeExpand(nodeId: string): void {
    if (this.expandedNodes.has(nodeId)) {
      this.expandedNodes.delete(nodeId);
    } else {
      this.expandedNodes.add(nodeId);
    }
  }

  isEmailAction(node: WorkflowNodeResultDetail): boolean {
    if (node.node_type !== 'action') return false;
    const output = node.output;
    if (!output || typeof output !== 'object') return false;
    return 'message_id' in output || 'account_name' in output;
  }

  getEmailField(node: WorkflowNodeResultDetail, field: string): string | null {
    const output = node.output as Record<string, unknown> | undefined;
    if (!output) return null;
    const val = output[field];
    return val != null ? String(val) : null;
  }

  isRedactedField(output: unknown, field: string): boolean {
    if (!output || typeof output !== 'object') return false;
    return (`__${field}_redacted` in (output as Record<string, unknown>));
  }

  formatJson(data: unknown): string {
    if (data == null) return '-';
    try {
      return JSON.stringify(data, null, 2);
    } catch {
      return String(data);
    }
  }
}
