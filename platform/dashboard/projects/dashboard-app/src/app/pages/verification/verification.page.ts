import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatSortModule, Sort } from '@angular/material/sort';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import {
  PinquarkApiService,
  SchedulerStatus,
  VerificationConnectorResult,
  VerificationLatestResponse,
  VerificationRunResponse,
} from '@pinquark/integrations';

@Component({
  selector: 'app-verification-page',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatTableModule,
    MatSortModule,
    MatIconModule,
    MatButtonModule,
    MatSlideToggleModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressSpinnerModule,
    MatChipsModule,
    MatTooltipModule,
    MatSnackBarModule,
  ],
  template: `
    <div class="page-header">
      <h2>Verification</h2>
      <div class="page-header__actions">
        <button mat-raised-button color="primary" [disabled]="isRunning" (click)="runAll()">
          <mat-icon>play_arrow</mat-icon>
          Run Now
        </button>
      </div>
    </div>

    <!-- Scheduler -->
    <mat-card class="scheduler-card">
      <mat-card-content>
        <div class="scheduler-row">
          <div class="scheduler-toggle">
            <mat-slide-toggle
              [checked]="scheduler.enabled"
              (change)="toggleScheduler($event.checked)"
              [disabled]="!canEditScheduler"
              color="primary"
            >Scheduler</mat-slide-toggle>
          </div>
          <div class="scheduler-interval">
            <span>Every</span>
            <mat-form-field appearance="outline" class="interval-field">
              <input matInput type="number" min="1" [(ngModel)]="scheduler.interval_days"
                     (blur)="updateInterval()" [disabled]="!canEditScheduler" />
            </mat-form-field>
            <span>days</span>
            @if (!canEditScheduler) {
              <span class="info-label" style="color: #999; font-size: 12px;">(admin only)</span>
            }
          </div>
          <div class="scheduler-info">
            @if (scheduler.next_run) {
              <span class="info-label">Next: {{ scheduler.next_run | date:'medium' }}</span>
            }
            @if (scheduler.last_run) {
              <span class="info-label">Last: {{ scheduler.last_run | date:'medium' }}</span>
            }
            @if (isRunning) {
              <mat-spinner diameter="20"></mat-spinner>
              <span class="info-label running">Running...</span>
            }
          </div>
        </div>
      </mat-card-content>
    </mat-card>

    <!-- Overview Cards -->
    @if (latest) {
      <div class="overview-cards">
        <mat-card class="overview-card pass">
          <mat-card-content>
            <div class="overview-value">{{ overviewPassed }}</div>
            <div class="overview-label">PASS</div>
          </mat-card-content>
        </mat-card>
        <mat-card class="overview-card fail">
          <mat-card-content>
            <div class="overview-value">{{ overviewFailed }}</div>
            <div class="overview-label">FAIL</div>
          </mat-card-content>
        </mat-card>
        <mat-card class="overview-card skip">
          <mat-card-content>
            <div class="overview-value">{{ overviewSkipped }}</div>
            <div class="overview-label">SKIP</div>
          </mat-card-content>
        </mat-card>
        <mat-card class="overview-card total">
          <mat-card-content>
            <div class="overview-value">{{ latestConnectors.length }}</div>
            <div class="overview-label">TOTAL</div>
          </mat-card-content>
        </mat-card>
      </div>
    }

    <!-- Connector Status Table -->
    <mat-card class="table-card">
      <mat-card-header>
        <mat-card-title>Connector Status</mat-card-title>
        @if (latest && latest.created_at) {
          <mat-card-subtitle>Run: {{ latest.created_at | date:'medium' }}</mat-card-subtitle>
        }
      </mat-card-header>
      <mat-card-content>
        <div class="table-filter">
          <mat-form-field appearance="outline" class="filter-field">
            <mat-label>Filter by name</mat-label>
            <input matInput [(ngModel)]="nameFilter" (input)="applyFilter()" />
            @if (nameFilter) {
              <button matSuffix mat-icon-button (click)="nameFilter = ''; applyFilter()">
                <mat-icon>close</mat-icon>
              </button>
            }
          </mat-form-field>
        </div>
        @if (latestConnectors.length === 0) {
          <p class="empty-message">No verification data yet. Click "Run Now" to start.</p>
        } @else {
          <table mat-table [dataSource]="sortedConnectors" matSort (matSortChange)="sortData($event)"
                 multiTemplateDataRows class="full-width connector-table">
            <ng-container matColumnDef="connector_name">
              <th mat-header-cell *matHeaderCellDef mat-sort-header>Connector</th>
              <td mat-cell *matCellDef="let row">
                @if (isChecking(rowKey(row))) {
                  <mat-icon class="checking-spinner">sync</mat-icon>
                }
                <strong>{{ row.connector_name }}</strong>
                <span class="version-badge">v{{ row.connector_version }}</span>
              </td>
            </ng-container>

            <ng-container matColumnDef="connector_category">
              <th mat-header-cell *matHeaderCellDef mat-sort-header>Category</th>
              <td mat-cell *matCellDef="let row">{{ row.connector_category }}</td>
            </ng-container>

            <ng-container matColumnDef="status">
              <th mat-header-cell *matHeaderCellDef mat-sort-header>Status</th>
              <td mat-cell *matCellDef="let row">
                <span class="status-chip" [class]="'status-' + row.status.toLowerCase()">
                  {{ row.status }}
                </span>
              </td>
            </ng-container>

            <ng-container matColumnDef="duration">
              <th mat-header-cell *matHeaderCellDef mat-sort-header>Time</th>
              <td mat-cell *matCellDef="let row">{{ row.summary?.duration_ms ?? 0 }}ms</td>
            </ng-container>

            <ng-container matColumnDef="created_at">
              <th mat-header-cell *matHeaderCellDef mat-sort-header>Last checked</th>
              <td mat-cell *matCellDef="let row">{{ row.created_at | date:'short' }}</td>
            </ng-container>

            <ng-container matColumnDef="actions">
              <th mat-header-cell *matHeaderCellDef></th>
              <td mat-cell *matCellDef="let row">
                <button mat-icon-button (click)="$event.stopPropagation(); runSingle(row.connector_name, row.connector_version)"
                        matTooltip="Run verification" [disabled]="isRunning">
                  <mat-icon>refresh</mat-icon>
                </button>
                <button mat-icon-button (click)="$event.stopPropagation(); toggleRowExpand(rowKey(row))"
                        matTooltip="Show checks">
                  <mat-icon>{{ expandedRow === rowKey(row) ? 'expand_less' : 'expand_more' }}</mat-icon>
                </button>
              </td>
            </ng-container>

            <!-- Expandable detail row spanning all columns -->
            <ng-container matColumnDef="expandedDetail">
              <td mat-cell *matCellDef="let row" [attr.colspan]="connectorColumns.length">
                <div class="detail-expand"
                     [class.detail-expand--collapsed]="expandedRow !== rowKey(row)"
                     [class.detail-expand--expanded]="expandedRow === rowKey(row)">
                  @if (expandedRow === rowKey(row) && row.checks?.length) {
                    <div class="detail-expand__content">
                      <table mat-table [dataSource]="row.checks" class="full-width checks-table">
                        <ng-container matColumnDef="name">
                          <th mat-header-cell *matHeaderCellDef>Check</th>
                          <td mat-cell *matCellDef="let c">{{ c.name }}</td>
                        </ng-container>
                        <ng-container matColumnDef="status">
                          <th mat-header-cell *matHeaderCellDef>Status</th>
                          <td mat-cell *matCellDef="let c">
                            <span class="status-chip" [class]="'status-' + c.status.toLowerCase()">{{ c.status }}</span>
                          </td>
                        </ng-container>
                        <ng-container matColumnDef="response_time_ms">
                          <th mat-header-cell *matHeaderCellDef>Time</th>
                          <td mat-cell *matCellDef="let c">{{ c.response_time_ms }}ms</td>
                        </ng-container>
                        <ng-container matColumnDef="error">
                          <th mat-header-cell *matHeaderCellDef>Error</th>
                          <td mat-cell *matCellDef="let c" class="error-cell">{{ c.error || '—' }}</td>
                        </ng-container>
                        <tr mat-header-row *matHeaderRowDef="checkColumns"></tr>
                        <tr mat-row *matRowDef="let row; columns: checkColumns;"></tr>
                      </table>
                    </div>
                  }
                </div>
              </td>
            </ng-container>

            <tr mat-header-row *matHeaderRowDef="connectorColumns"></tr>
            <tr mat-row *matRowDef="let row; columns: connectorColumns;"
                class="connector-row"
                [class.expanded-row]="expandedRow === rowKey(row)"
                (click)="toggleRowExpand(rowKey(row))"></tr>
            <tr mat-row *matRowDef="let row; columns: ['expandedDetail']"
                class="detail-row"></tr>
          </table>
        }
      </mat-card-content>
    </mat-card>

  
  `,
  styles: [`
    .page-header {
      display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;
    }
    .page-header h2 { margin: 0; }

    .scheduler-card { margin-bottom: 16px; }
    .scheduler-row {
      display: flex; align-items: center; gap: 24px; flex-wrap: wrap;
    }
    .scheduler-interval {
      display: flex; align-items: center; gap: 8px;
    }
    .interval-field { width: 70px; }
    .interval-field .mat-mdc-form-field-subscript-wrapper { display: none; }
    .scheduler-info {
      display: flex; align-items: center; gap: 12px; margin-left: auto;
    }
    .info-label { color: rgba(0,0,0,0.6); font-size: 13px; }
    .info-label.running { color: #1976d2; font-weight: 500; }

    .overview-cards {
      display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 16px;
    }
    .overview-card { text-align: center; }
    .overview-value { font-size: 32px; font-weight: 700; }
    .overview-label { font-size: 13px; text-transform: uppercase; color: rgba(0,0,0,0.6); }
    .overview-card.pass .overview-value { color: #4caf50; }
    .overview-card.fail .overview-value { color: #f44336; }
    .overview-card.skip .overview-value { color: #ff9800; }
    .overview-card.total .overview-value { color: #1976d2; }

    .table-card { margin-bottom: 16px; }
    .full-width { width: 100%; }

    .status-chip {
      display: inline-block; padding: 2px 10px; border-radius: 12px;
      font-size: 12px; font-weight: 600; text-transform: uppercase;
    }
    .status-pass { background: #e8f5e9; color: #2e7d32; }
    .status-fail { background: #ffebee; color: #c62828; }
    .status-partial { background: #fff3e0; color: #e65100; }
    .status-warn { background: #fff8e1; color: #f57f17; }
    .status-skip { background: #f5f5f5; color: #757575; }

    .version-badge {
      font-size: 11px; color: rgba(0,0,0,0.5); margin-left: 4px;
    }

    .connector-row { cursor: pointer; }
    .connector-row:hover { background: #f5f5f5; }
    .expanded-row { background: #e3f2fd !important; }

    .detail-row { height: 0; }
    .detail-row td { padding: 0 !important; border-bottom-width: 0; }

    .detail-expand {
      overflow: hidden;
      transition: height 200ms ease;
    }
    .detail-expand--collapsed { height: 0; }
    .detail-expand--expanded { height: auto; }

    .detail-expand__content {
      padding: 8px 16px 16px;
      background: #fafafa;
      border-bottom: 2px solid #e0e0e0;
    }

    .checks-table { font-size: 13px; }

    .error-cell { color: #c62828; font-size: 13px; max-width: 300px; word-break: break-word; }
    .suggestion-cell { color: #1565c0; font-size: 13px; max-width: 250px; word-break: break-word; }

    .table-filter { margin-bottom: 8px; }
    .filter-field { width: 280px; }
    .filter-field .mat-mdc-form-field-subscript-wrapper { display: none; }

    .checking-spinner {
      font-size: 18px; width: 18px; height: 18px;
      margin-right: 6px; vertical-align: middle;
      color: #1976d2;
      animation: spin 1s linear infinite;
    }
    @keyframes spin { 100% { transform: rotate(360deg); } }

    .empty-message { color: rgba(0,0,0,0.5); padding: 24px 0; text-align: center; }

    @media (max-width: 768px) {
      .overview-cards { grid-template-columns: repeat(2, 1fr); }
      .scheduler-row { flex-direction: column; align-items: flex-start; }
      .scheduler-info { margin-left: 0; }
    }
  `],
})
export class VerificationPage implements OnInit, OnDestroy {
  scheduler: SchedulerStatus = {
    enabled: false, interval_days: 7, last_run: null, next_run: null, currently_running: false,
  };
  isRunning = false;
  checkingConnector: string | null = null;
  canEditScheduler = false;
  private pollIntervalId: ReturnType<typeof setInterval> | null = null;

  latest: VerificationLatestResponse | null = null;
  latestConnectors: VerificationConnectorResult[] = [];
  sortedConnectors: VerificationConnectorResult[] = [];

  overviewPassed = 0;
  overviewFailed = 0;
  overviewSkipped = 0;

  expandedRow: string | null = null;
  nameFilter = '';

  connectorColumns = ['connector_name', 'connector_category', 'status', 'duration', 'created_at', 'actions'];
  checkColumns = ['name', 'status', 'response_time_ms', 'error'];

  constructor(
    private readonly api: PinquarkApiService,
    private readonly snackBar: MatSnackBar,
  ) {}

  ngOnInit(): void {
    this.canEditScheduler = this.api.isAdmin;
    this.loadScheduler();
    this.loadLatest();
  }

  loadScheduler(): void {
    this.api.verificationSchedulerStatus().subscribe({
      next: (s: SchedulerStatus) => {
        this.scheduler = s;
        this.isRunning = s.currently_running;
      },
      error: () => {},
    });
  }

  loadLatest(): void {
    this.api.verificationLatest().subscribe({
      next: (data: VerificationLatestResponse) => {
        this.latest = data;
        this.latestConnectors = data.connectors || [];
        this.overviewPassed = this.latestConnectors.filter(c => c.status === 'PASS').length;
        this.overviewFailed = this.latestConnectors.filter(c => c.status === 'FAIL' || c.status === 'PARTIAL').length;
        this.overviewSkipped = this.latestConnectors.filter(c => c.status === 'SKIP').length;
        this.applyFilter();
      },
      error: (err: { status?: number }) => {
        if (err.status === 403) {
          this.snackBar.open('Verification data requires admin access', 'OK', { duration: 5000 });
        }
      },
    });
  }

  toggleScheduler(enabled: boolean): void {
    this.api.verificationSchedulerUpdate({ enabled }).subscribe({
      next: () => {
        this.scheduler.enabled = enabled;
        this.snackBar.open(`Scheduler ${enabled ? 'enabled' : 'disabled'}`, 'OK', { duration: 3000 });
      },
      error: (err: { status?: number }) => {
        this.scheduler.enabled = !enabled;
        if (err.status === 403) {
          this.canEditScheduler = false;
        }
        const msg = err.status === 403 ? 'Admin access required to modify scheduler' : 'Failed to update scheduler';
        this.snackBar.open(msg, 'OK', { duration: 4000 });
      },
    });
  }

  updateInterval(): void {
    if (this.scheduler.interval_days < 1) return;
    this.api.verificationSchedulerUpdate({ interval_days: this.scheduler.interval_days }).subscribe({
      next: () => this.snackBar.open('Interval updated', 'OK', { duration: 2000 }),
      error: (err: { status?: number }) => {
        if (err.status === 403) {
          this.canEditScheduler = false;
        }
        const msg = err.status === 403 ? 'Admin access required to modify scheduler' : 'Failed to update interval';
        this.snackBar.open(msg, 'OK', { duration: 4000 });
      },
    });
  }

  runAll(): void {
    this.isRunning = true;
    this.checkingConnector = null;
    this.api.verificationRunAll().subscribe({
      next: (res: VerificationRunResponse) => {
        this.snackBar.open(`Verification started (${res.run_id.slice(0, 8)}...)`, 'OK', { duration: 5000 });
        this.pollUntilDone();
      },
      error: (err: { error?: { detail?: string } }) => {
        this.isRunning = false;
        this.snackBar.open(err.error?.detail || 'Failed to start', 'OK', { duration: 3000 });
      },
    });
  }

  runSingle(connectorName: string, version?: string): void {
    this.isRunning = true;
    this.checkingConnector = version ? `${connectorName}@${version}` : connectorName;
    this.api.verificationRunSingle(connectorName, version).subscribe({
      next: (_res: VerificationRunResponse) => {
        const label = version ? `${connectorName} v${version}` : connectorName;
        this.snackBar.open(`Verifying ${label}...`, 'OK', { duration: 3000 });
        this.pollUntilDone();
      },
      error: (err: { error?: { detail?: string } }) => {
        this.isRunning = false;
        this.checkingConnector = null;
        this.snackBar.open(err.error?.detail || 'Failed to start', 'OK', { duration: 3000 });
      },
    });
  }

  isChecking(key: string): boolean {
    if (!this.isRunning) return false;
    if (this.checkingConnector === null) return true;
    return this.checkingConnector === key;
  }

  ngOnDestroy(): void {
    this.clearPollInterval();
  }

  private clearPollInterval(): void {
    if (this.pollIntervalId !== null) {
      clearInterval(this.pollIntervalId);
      this.pollIntervalId = null;
    }
  }

  private pollUntilDone(): void {
    this.clearPollInterval();
    this.pollIntervalId = setInterval(() => {
      this.api.verificationSchedulerStatus().subscribe({
        next: (s: SchedulerStatus) => {
          this.isRunning = s.currently_running;
          if (!s.currently_running) {
            this.clearPollInterval();
            this.checkingConnector = null;
            this.loadLatest();
            this.loadScheduler();
            this.snackBar.open('Verification complete', 'OK', { duration: 3000 });
          }
        },
        error: () => {
          this.clearPollInterval();
          this.isRunning = false;
          this.checkingConnector = null;
          this.snackBar.open('Verification polling failed', 'OK', { duration: 3000 });
        },
      });
    }, 5000);
  }

  applyFilter(): void {
    const q = this.nameFilter.trim().toLowerCase();
    const filtered = q
      ? this.latestConnectors.filter(c => c.connector_name.toLowerCase().includes(q))
      : [...this.latestConnectors];
    this.sortedConnectors = filtered;
  }

  rowKey(row: VerificationConnectorResult): string {
    return `${row.connector_name}@${row.connector_version}`;
  }

  toggleRowExpand(key: string): void {
    this.expandedRow = this.expandedRow === key ? null : key;
  }

  sortData(sort: Sort): void {
    const base = this.nameFilter.trim().toLowerCase()
      ? this.latestConnectors.filter(c => c.connector_name.toLowerCase().includes(this.nameFilter.trim().toLowerCase()))
      : [...this.latestConnectors];
    if (!sort.active || sort.direction === '') {
      this.sortedConnectors = base;
      return;
    }
    this.sortedConnectors = base.sort((a, b) => {
      const dir = sort.direction === 'asc' ? 1 : -1;
      switch (sort.active) {
        case 'connector_name': return a.connector_name.localeCompare(b.connector_name) * dir;
        case 'connector_category': return a.connector_category.localeCompare(b.connector_category) * dir;
        case 'status': return a.status.localeCompare(b.status) * dir;
        case 'duration': return ((a.summary?.duration_ms ?? 0) - (b.summary?.duration_ms ?? 0)) * dir;
        case 'created_at': return (new Date(a.created_at).getTime() - new Date(b.created_at).getTime()) * dir;
        default: return 0;
      }
    });
  }

}
