import { Component, OnInit, OnDestroy, AfterViewInit, NgZone } from '@angular/core';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatDividerModule } from '@angular/material/divider';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';

import {
  CredentialFormComponent,
  PinquarkApiService,
  Connector,
  ConnectorInstance,
  CredentialInfo,
  CredentialValidationResult,
  COUNTRY_FLAG_MAP,
} from '@pinquark/integrations';

type ViewMode = 'list' | 'add' | 'edit';

const PAGE_SIZE = 20;

@Component({
  selector: 'app-credentials-page',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatSelectModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatChipsModule,
    MatDividerModule,
    MatSnackBarModule,
    MatTooltipModule,
    FormsModule,
    CredentialFormComponent,
  ],
  template: `
    <div class="cred-page">
      <div class="cred-page__header">
        <h2>Credentials</h2>
        @if (mode === 'list') {
          <button mat-raised-button color="primary" (click)="startAdd()" [disabled]="connectors.length === 0">
            <mat-icon>add</mat-icon> Add Credentials
          </button>
        }
      </div>

      <!-- SAVED CREDENTIALS LIST -->
      @if (mode === 'list') {
        @if (loading) {
          <p class="cred-page__hint">Loading...</p>
        } @else if (savedCredentials.length === 0) {
          <mat-card class="cred-page__empty">
            <mat-card-content>
              <mat-icon class="cred-page__empty-icon">vpn_key</mat-icon>
              <p>No saved credentials.</p>
              <p class="cred-page__hint">Click "Add Credentials" to configure a connector.</p>
            </mat-card-content>
          </mat-card>
        } @else {
          <div class="cred-grid" (scroll)="onScroll($event)">
            @for (cred of visibleCredentials; track credTrackBy($index, cred)) {
              <mat-card class="cred-card">
                <mat-card-content>
                  <div class="cred-card__header">
                    <div class="cred-card__title-row">
                      <div class="cred-card__logo">
                        @if (getLogoUrl(cred)) {
                          <img [src]="getLogoUrl(cred)" [alt]="cred.display_name" />
                        } @else {
                          <mat-icon class="cred-card__logo-fallback">{{ getCategoryIcon(cred.category) }}</mat-icon>
                        }
                      </div>
                      <div class="cred-card__name-block">
                        <span class="cred-card__name">
                          <span class="cred-card__status-dot"
                                [class.cred-card__status-dot--success]="getValidationStatus(credKey(cred)) === 'success'"
                                [class.cred-card__status-dot--failed]="getValidationStatus(credKey(cred)) === 'failed'"
                                [class.cred-card__status-dot--pending]="getValidationStatus(credKey(cred)) === 'pending'"
                                [class.cred-card__status-dot--pulse]="validatingConnectors.has(credKey(cred))"
                                [matTooltip]="getStatusTooltip(credKey(cred))">
                          </span>
                          <span class="cred-card__cred-label">{{ cred.credential_name }}</span>
                        </span>
                        <span class="cred-card__connector-label">
                          {{ getFlag(cred) }} {{ cred.display_name }}
                        </span>
                        <span class="cred-card__meta">
                          <span class="cred-card__category">{{ cred.category }}</span>
                          <span class="cred-card__connector">{{ cred.connector_name }}</span>
                        </span>
                      </div>
                    </div>
                    <div class="cred-card__actions">
                      <button mat-icon-button (click)="testConnection(cred)" matTooltip="Revalidate"
                              [disabled]="validatingConnectors.has(credKey(cred))">
                        <mat-icon [class.spin]="validatingConnectors.has(credKey(cred))">
                          {{ validatingConnectors.has(credKey(cred)) ? 'sync' : 'refresh' }}
                        </mat-icon>
                      </button>
                      <button mat-icon-button color="primary" (click)="startEdit(cred)" matTooltip="Edit">
                        <mat-icon>edit</mat-icon>
                      </button>
                      <button mat-icon-button color="warn" (click)="confirmDelete(cred)" matTooltip="Delete">
                        <mat-icon>delete</mat-icon>
                      </button>
                    </div>
                  </div>

                  <div class="cred-card__body">
                    @if (cred.token) {
                      <div class="cred-card__token-row">
                        <mat-icon class="cred-card__token-icon">token</mat-icon>
                        <code class="cred-card__token-value">{{ cred.token }}</code>
                        <button mat-icon-button class="cred-card__token-btn" (click)="copyToken(cred.token)" matTooltip="Copy token">
                          <mat-icon>content_copy</mat-icon>
                        </button>
                        <button mat-icon-button class="cred-card__token-btn" (click)="regenerateToken(cred)" matTooltip="Regenerate token"
                                [disabled]="regeneratingTokens.has(credKey(cred))">
                          <mat-icon [class.spin]="regeneratingTokens.has(credKey(cred))">autorenew</mat-icon>
                        </button>
                      </div>
                    }
                    <div class="cred-card__keys">
                      @for (key of cred.keys; track key) {
                        <mat-chip-set>
                          <mat-chip>
                            <mat-icon matChipAvatar>key</mat-icon>
                            {{ key }}
                          </mat-chip>
                        </mat-chip-set>
                      }
                    </div>
                    @if (cred.updated_at) {
                      <div class="cred-card__date">Updated: {{ cred.updated_at | date:'medium' }}</div>
                    }
                  </div>

                  @if (validationResults[credKey(cred)]; as result) {
                    <div class="cred-card__status-bar"
                         [class.cred-card__status-bar--success]="result.status === 'success'"
                         [class.cred-card__status-bar--failed]="result.status === 'failed'"
                         [class.cred-card__status-bar--unsupported]="result.status === 'unsupported'">
                      <mat-icon>{{ result.status === 'success' ? 'check_circle' : result.status === 'failed' ? 'error' : 'info' }}</mat-icon>
                      <span>{{ result.message }}</span>
                      @if (result.response_time_ms) {
                        <span class="cred-card__status-time">{{ result.response_time_ms }}ms</span>
                      }
                    </div>
                  }
                </mat-card-content>
              </mat-card>
            }
            @if (hasMore) {
              <div class="cred-grid__sentinel">Loading more...</div>
            }
          </div>
        }
      }

      <!-- ADD MODE -->
      @if (mode === 'add') {
        <mat-card class="cred-page__form-card">
          <mat-card-content>
            @if (availableConnectors.length === 0) {
              <p class="cred-page__hint" style="margin-bottom: 12px;">
                No active connectors. Activate connectors on the <strong>Connectors</strong> page.
              </p>
              <div style="text-align: right;">
                <button mat-button (click)="backToList()">Back</button>
              </div>
            } @else {
              <mat-form-field appearance="outline" style="width: 100%;">
                <mat-label>Select connector</mat-label>
                <mat-select [(ngModel)]="selectedConnector">
                  @for (c of availableConnectors; track c.name) {
                    <mat-option [value]="c">
                      @if (c.logo_url) {
                        <img [src]="c.logo_url" class="cred-page__option-logo" />
                      }
                      {{ c.display_name }} ({{ c.category }})
                    </mat-option>
                  }
                </mat-select>
              </mat-form-field>

              @if (selectedConnector) {
                <pinquark-credential-form
                  [connector]="selectedConnector"
                  [connectorName]="selectedConnector.name"
                  [credentialName]="newCredentialName"
                  (saved)="onSaved()"
                  (cancelled)="backToList()"
                ></pinquark-credential-form>
              } @else {
                <div style="text-align: right;">
                  <button mat-button (click)="backToList()">Cancel</button>
                </div>
              }
            }
          </mat-card-content>
        </mat-card>
      }

      <!-- EDIT MODE -->
      @if (mode === 'edit' && editConnector) {
        <mat-card class="cred-page__form-card">
          <mat-card-content>
            @if (loadingEdit) {
              <p class="cred-page__hint">Loading credentials...</p>
            } @else {
              <pinquark-credential-form
                [connector]="editConnector"
                [connectorName]="editConnector.name"
                [credentialName]="editCredentialName"
                [editMode]="true"
                [existingKeys]="editExistingKeys"
                [existingValues]="editExistingValues"
                (saved)="onSaved()"
                (cancelled)="backToList()"
              ></pinquark-credential-form>
            }
          </mat-card-content>
        </mat-card>
      }

      <!-- DELETE CONFIRMATION -->
      @if (deleteTarget) {
        <div class="cred-page__overlay" (click)="deleteTarget = null">
          <mat-card class="cred-page__dialog" (click)="$event.stopPropagation()">
            <mat-card-content>
              <h3>Delete Credentials</h3>
              <p>Are you sure you want to delete credentials <strong>"{{ deleteTarget.credential_name }}"</strong> for <strong>{{ deleteTarget.display_name }}</strong>?</p>
              <p class="cred-page__hint">Keys to remove: {{ deleteTarget.keys.join(', ') }}</p>
              <div class="cred-page__dialog-actions">
                <button mat-button (click)="deleteTarget = null">Cancel</button>
                <button mat-raised-button color="warn" (click)="doDelete()" [disabled]="deleting">
                  {{ deleting ? 'Deleting...' : 'Delete' }}
                </button>
              </div>
            </mat-card-content>
          </mat-card>
        </div>
      }
    </div>
  `,
  styles: [`
    .cred-page__header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
    .cred-page__header h2 { margin: 0; }
    .cred-page__hint { color: rgba(0,0,0,0.54); font-size: 13px; }
    .cred-page__empty { text-align: center; padding: 40px 16px; max-width: 600px; }
    .cred-page__empty-icon { font-size: 48px; width: 48px; height: 48px; color: rgba(0,0,0,0.2); margin-bottom: 8px; }
    .cred-page__form-card { max-width: 600px; margin-top: 16px; }
    .cred-page__overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 1000; }
    .cred-page__dialog { max-width: 440px; width: 100%; }
    .cred-page__dialog-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }
    .cred-page__option-logo { width: 20px; height: 20px; border-radius: 4px; vertical-align: middle; margin-right: 8px; }

    .cred-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
      gap: 16px;
      max-height: calc(100vh - 140px);
      overflow-y: auto;
      padding-right: 4px;
    }
    .cred-grid__sentinel {
      grid-column: 1 / -1;
      text-align: center;
      padding: 16px;
      color: rgba(0,0,0,0.38);
      font-size: 13px;
    }

    .cred-card { overflow: hidden; transition: box-shadow 0.2s; }
    .cred-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
    .cred-card__header { display: flex; justify-content: space-between; align-items: flex-start; }
    .cred-card__title-row { display: flex; align-items: center; gap: 12px; flex: 1; min-width: 0; }
    .cred-card__logo {
      width: 56px; height: 40px; border-radius: 8px;
      overflow: hidden; flex-shrink: 0;
      display: flex; align-items: center; justify-content: center;
      background: #f5f5f5;
    }
    .cred-card__logo img { max-width: 100%; max-height: 100%; object-fit: contain; }
    .cred-card__logo-fallback { font-size: 24px; color: rgba(0,0,0,0.3); }
    .cred-card__name-block { display: flex; flex-direction: column; min-width: 0; gap: 2px; }
    .cred-card__name { display: flex; align-items: center; gap: 6px; font-size: 15px; font-weight: 500; line-height: 1.3; }
    .cred-card__cred-label {
      background: #e3f2fd; color: #1565c0;
      padding: 2px 10px; border-radius: 4px; font-weight: 600; font-size: 13px;
    }
    .cred-card__connector-label { color: rgba(0,0,0,0.7); font-size: 13px; }
    .cred-card__meta { display: flex; gap: 8px; font-size: 11px; color: rgba(0,0,0,0.45); margin-top: 1px; }
    .cred-card__category { background: rgba(0,0,0,0.06); padding: 1px 6px; border-radius: 4px; }
    .cred-card__connector { font-family: monospace; }
    .cred-card__actions { display: flex; gap: 2px; flex-shrink: 0; }
    .cred-card__body { padding-top: 8px; }
    .cred-card__keys { display: flex; flex-wrap: wrap; gap: 4px; }
    .cred-card__date { font-size: 12px; color: rgba(0,0,0,0.4); margin-top: 6px; }

    .cred-card__token-row {
      display: flex; align-items: center; gap: 6px;
      background: #f5f5f5; border-radius: 6px;
      padding: 4px 8px; margin-bottom: 8px;
    }
    .cred-card__token-icon { font-size: 16px; width: 16px; height: 16px; color: rgba(0,0,0,0.4); flex-shrink: 0; }
    .cred-card__token-value {
      font-size: 12px; color: #333; font-family: 'Roboto Mono', monospace;
      overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; min-width: 0;
    }
    .cred-card__token-btn { width: 28px; height: 28px; flex-shrink: 0; }
    .cred-card__token-btn mat-icon { font-size: 16px; width: 16px; height: 16px; }

    .cred-card__status-dot {
      width: 10px; height: 10px; border-radius: 50%;
      background: #bdbdbd; flex-shrink: 0;
    }
    .cred-card__status-dot--success { background: #4caf50; }
    .cred-card__status-dot--failed { background: #f44336; }
    .cred-card__status-dot--pending { background: #bdbdbd; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
    .cred-card__status-dot--pulse { animation: pulse 1.2s ease-in-out infinite; }

    .cred-card__status-bar {
      display: flex; align-items: center; gap: 6px;
      margin: 10px -16px -16px; padding: 6px 16px;
      font-size: 12px; font-weight: 500;
    }
    .cred-card__status-bar mat-icon { font-size: 15px; height: 15px; width: 15px; }
    .cred-card__status-bar--success { background: #e8f5e9; color: #2e7d32; }
    .cred-card__status-bar--failed { background: #fbe9e7; color: #c62828; }
    .cred-card__status-bar--unsupported { background: #fff3e0; color: #e65100; }
    .cred-card__status-time { opacity: 0.6; }

    @keyframes spin { 100% { transform: rotate(360deg); } }
    .spin { animation: spin 1s linear infinite; }
  `],
})
export class CredentialsPage implements OnInit, OnDestroy, AfterViewInit {
  connectors: Connector[] = [];
  activeInstances: ConnectorInstance[] = [];
  savedCredentials: CredentialInfo[] = [];
  mode: ViewMode = 'list';
  loading = true;

  selectedConnector: Connector | null = null;
  newCredentialName = 'default';
  editConnector: Connector | null = null;
  editCredentialName = 'default';
  editExistingKeys: string[] = [];
  editExistingValues: Record<string, string> = {};
  loadingEdit = false;

  deleteTarget: CredentialInfo | null = null;
  deleting = false;

  validatingConnectors = new Set<string>();
  regeneratingTokens = new Set<string>();
  validationResults: Record<string, CredentialValidationResult> = {};

  private connectorMap = new Map<string, Connector>();
  private displayCount = PAGE_SIZE;
  private scrollHandler?: () => void;
  private destroy$ = new Subject<void>();

  get visibleCredentials(): CredentialInfo[] {
    return this.savedCredentials.slice(0, this.displayCount);
  }

  get hasMore(): boolean {
    return this.displayCount < this.savedCredentials.length;
  }

  credKey(cred: CredentialInfo): string {
    return `${cred.connector_name}::${cred.credential_name}`;
  }

  credTrackBy(_index: number, cred: CredentialInfo): string {
    return this.credKey(cred);
  }

  constructor(
    private readonly api: PinquarkApiService,
    private readonly snackBar: MatSnackBar,
    private readonly zone: NgZone,
  ) {}

  ngOnInit(): void {
    this.loadData();
  }

  ngAfterViewInit(): void {
    this.attachScrollListener();
  }

  ngOnDestroy(): void {
    this.detachScrollListener();
    this.destroy$.next();
    this.destroy$.complete();
  }

  private attachScrollListener(): void {
    setTimeout(() => {
      const gridEl = document.querySelector('.cred-grid');
      if (!gridEl) return;
      this.scrollHandler = () => this.onScroll(gridEl as HTMLElement);
      gridEl.addEventListener('scroll', this.scrollHandler, { passive: true });
    });
  }

  private detachScrollListener(): void {
    if (this.scrollHandler) {
      const gridEl = document.querySelector('.cred-grid');
      if (gridEl) gridEl.removeEventListener('scroll', this.scrollHandler);
      this.scrollHandler = undefined;
    }
  }

  onScroll(eventOrEl: Event | HTMLElement): void {
    const el = eventOrEl instanceof HTMLElement ? eventOrEl : eventOrEl.target as HTMLElement;
    if (!el) return;
    const threshold = 200;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < threshold;
    if (atBottom && this.hasMore) {
      this.zone.run(() => {
        this.displayCount = Math.min(this.displayCount + PAGE_SIZE, this.savedCredentials.length);
      });
    }
  }

  getLogoUrl(cred: CredentialInfo): string {
    const connector = this.connectorMap.get(cred.connector_name);
    return connector?.logo_url ?? '';
  }

  getFlag(cred: CredentialInfo): string {
    const connector = this.connectorMap.get(cred.connector_name);
    if (!connector?.country) return '';
    return COUNTRY_FLAG_MAP[connector.country] ?? '';
  }

  getCategoryIcon(category: string): string {
    switch (category) {
      case 'courier': return 'local_shipping';
      case 'ecommerce': return 'shopping_cart';
      case 'wms': return 'warehouse';
      case 'erp': return 'business';
      case 'ai': return 'psychology';
      case 'other': return 'extension';
      default: return 'settings';
    }
  }

  get availableConnectors(): Connector[] {
    const activeNames = new Set(this.activeInstances.map(i => i.connector_name));
    const latestByName = new Map<string, Connector>();
    for (const c of this.connectors) {
      if (!activeNames.has(c.name)) continue;
      const existing = latestByName.get(c.name);
      if (!existing || c.version.localeCompare(existing.version, undefined, { numeric: true }) > 0) {
        latestByName.set(c.name, c);
      }
    }
    return Array.from(latestByName.values());
  }

  loadData(): void {
    this.loading = true;
    this.displayCount = PAGE_SIZE;
    forkJoin({
      connectors: this.api.listConnectors(),
      instances: this.api.listConnectorInstances(),
      credentials: this.api.listCredentials(),
    }).pipe(takeUntil(this.destroy$)).subscribe({
      next: ({ connectors, instances, credentials }) => {
        this.connectors = connectors;
        this.connectorMap.clear();
        for (const c of connectors) {
          this.connectorMap.set(c.name, c);
        }
        this.activeInstances = instances.filter(i => i.is_enabled);
        this.savedCredentials = credentials;
        this.loading = false;
        this.validateAll();
        setTimeout(() => this.attachScrollListener());
      },
      error: () => {
        this.loading = false;
      },
    });
  }

  getValidationStatus(key: string): string {
    if (this.validatingConnectors.has(key)) return 'pending';
    const r = this.validationResults[key];
    return r ? r.status : 'pending';
  }

  getStatusTooltip(key: string): string {
    if (this.validatingConnectors.has(key)) return 'Validating...';
    const result = this.validationResults[key];
    if (!result) return 'Not validated';
    if (result.status === 'success') return 'Connected' + (result.response_time_ms ? ` (${result.response_time_ms}ms)` : '');
    if (result.status === 'failed') return result.message;
    return result.message;
  }

  private validateAll(): void {
    for (const cred of this.savedCredentials) {
      this.validateOne(cred);
    }
  }

  private validateOne(cred: CredentialInfo): void {
    const key = this.credKey(cred);
    this.validatingConnectors.add(key);
    this.api.validateCredentials(cred.connector_name, cred.credential_name).pipe(takeUntil(this.destroy$)).subscribe({
      next: (result) => {
        this.validatingConnectors.delete(key);
        this.validationResults[key] = result;
      },
      error: () => {
        this.validatingConnectors.delete(key);
        this.validationResults[key] = { status: 'failed', message: 'Validation request failed' };
      },
    });
  }

  startAdd(): void {
    this.mode = 'add';
    this.selectedConnector = null;
    this.newCredentialName = 'default';
  }

  startEdit(cred: CredentialInfo): void {
    const connector = this.connectors.find(c => c.name === cred.connector_name);
    if (!connector) {
      this.snackBar.open('Connector definition not found', 'OK', { duration: 3000 });
      return;
    }
    this.editConnector = connector;
    this.editCredentialName = cred.credential_name;
    this.editExistingKeys = cred.keys;
    this.editExistingValues = {};
    this.loadingEdit = true;
    this.mode = 'edit';

    this.api.getCredentials(cred.connector_name, cred.credential_name).pipe(takeUntil(this.destroy$)).subscribe({
      next: (detail) => {
        this.editExistingValues = detail.values ?? {};
        this.loadingEdit = false;
      },
      error: () => {
        this.loadingEdit = false;
      },
    });
  }

  backToList(): void {
    this.mode = 'list';
    this.selectedConnector = null;
    this.newCredentialName = 'default';
    this.editConnector = null;
    this.editCredentialName = 'default';
    this.editExistingKeys = [];
    this.editExistingValues = {};
    setTimeout(() => this.attachScrollListener());
  }

  onSaved(): void {
    this.validationResults = {};
    this.backToList();
    this.loadData();
  }

  confirmDelete(cred: CredentialInfo): void {
    this.deleteTarget = cred;
  }

  doDelete(): void {
    if (!this.deleteTarget) return;
    this.deleting = true;
    this.api.deleteCredentials(this.deleteTarget.connector_name, this.deleteTarget.credential_name).pipe(takeUntil(this.destroy$)).subscribe({
      next: () => {
        this.deleting = false;
        this.snackBar.open('Credentials deleted', 'OK', { duration: 3000 });
        this.deleteTarget = null;
        this.loadData();
      },
      error: () => {
        this.deleting = false;
        this.snackBar.open('Failed to delete credentials', 'Retry', { duration: 5000 });
      },
    });
  }

  testConnection(cred: CredentialInfo): void {
    const key = this.credKey(cred);
    delete this.validationResults[key];
    this.validateOne(cred);
  }

  copyToken(token: string): void {
    navigator.clipboard.writeText(token).then(() => {
      this.snackBar.open('Token copied to clipboard', 'OK', { duration: 2000 });
    });
  }

  regenerateToken(cred: CredentialInfo): void {
    const key = this.credKey(cred);
    this.regeneratingTokens.add(key);
    this.api.regenerateCredentialToken(cred.connector_name, cred.credential_name).subscribe({
      next: (result) => {
        this.regeneratingTokens.delete(key);
        cred.token = result.token;
        this.snackBar.open('Token regenerated', 'OK', { duration: 3000 });
      },
      error: () => {
        this.regeneratingTokens.delete(key);
        this.snackBar.open('Failed to regenerate token', 'Retry', { duration: 5000 });
      },
    });
  }
}
