import { Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';
import { MatTabsModule } from '@angular/material/tabs';
import { MatListModule } from '@angular/material/list';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatTableModule } from '@angular/material/table';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';

import {
  Connector,
  ConnectorGroup,
  ConnectorInstance,
  ApiEndpoint,
  COUNTRY_FLAG_MAP,
  COUNTRY_NAME_MAP,
} from '../../models';
import { PinquarkApiService } from '../../services/pinquark-api.service';
import { SwaggerUiComponent } from '../swagger-ui/swagger-ui.component';

@Component({
  selector: 'pinquark-connector-detail',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatChipsModule,
    MatButtonModule,
    MatIconModule,
    MatDividerModule,
    MatTabsModule,
    MatListModule,
    MatExpansionModule,
    MatTableModule,
    MatFormFieldModule,
    MatSelectModule,
    SwaggerUiComponent,
  ],
  template: `
    <div class="connector-detail" *ngIf="connector">
      <!-- Header -->
      <div class="connector-detail__header">
        <button mat-icon-button (click)="goBack.emit()">
          <mat-icon>arrow_back</mat-icon>
        </button>
        <div class="connector-detail__logo-wrap" *ngIf="connector.logo_url">
          <img [src]="connector.logo_url" [alt]="connector.display_name" class="connector-detail__logo" />
        </div>
        <div class="connector-detail__title">
          <h2>
            <span class="connector-detail__flag" *ngIf="connector.country">{{ getFlag(connector.country) }}</span>
            {{ connector.display_name }}
            <span class="connector-detail__badge connector-detail__badge--status">{{ formatStatusLabel(connector.status) }}</span>
            <span class="connector-detail__badge" *ngIf="activeInstance">Active (v{{ activeInstance.connector_version }})</span>
          </h2>
          <p class="connector-detail__subtitle">
            {{ connector.category | titlecase }} &middot; Interface: {{ connector.interface }}
            <span *ngIf="connector.country"> &middot; {{ getCountryName(connector.country) }}</span>
          </p>
        </div>
        <div class="connector-detail__header-actions">
          <button
            *ngIf="activeInstance"
            mat-raised-button
            color="warn"
            (click)="onDeactivate()"
          >
            <mat-icon>remove_circle</mat-icon> Deactivate
          </button>
          <button
            *ngIf="!activeInstance"
            mat-raised-button
            color="primary"
            (click)="onActivateClick()"
          >
            <mat-icon>add_circle</mat-icon> Activate
          </button>
        </div>
      </div>

      <mat-divider></mat-divider>

      <!-- Version selector -->
      <div class="connector-detail__version-bar">
        <mat-form-field appearance="outline" class="connector-detail__version-select">
          <mat-label>Version</mat-label>
          <mat-select [(ngModel)]="selectedVersion" (selectionChange)="onVersionChange()">
            <mat-option *ngFor="let v of availableVersions" [value]="v.version">
              v{{ v.version }}
              <span *ngIf="v.display_name !== group?.display_name"> &mdash; {{ v.display_name }}</span>
              <span *ngIf="isVersionActive(v.version)"> (active)</span>
              <span *ngIf="v === group?.latest"> (latest)</span>
            </mat-option>
          </mat-select>
        </mat-form-field>
        <span class="connector-detail__version-count" *ngIf="availableVersions.length > 1">
          {{ availableVersions.length }} versions available
        </span>
      </div>

      <!-- Description -->
      <div class="connector-detail__section">
        <p class="connector-detail__description">{{ connector.description }}</p>
        <div class="connector-detail__meta">
          <mat-chip-set>
            <mat-chip>{{ formatStatusLabel(connector.status) }}</mat-chip>
            <mat-chip>{{ formatAuthType(connector.auth_type) }}</mat-chip>
            <mat-chip *ngIf="connector.supports_oauth2">OAuth2</mat-chip>
            <mat-chip *ngIf="connector.sandbox_available">Sandbox</mat-chip>
            <mat-chip *ngIf="connector.has_webhooks">Webhooks</mat-chip>
            <mat-chip *ngIf="connector.health" [highlighted]="true" [color]="getHealthColor(connector.health.status)">
              {{ formatHealthLabel(connector.health.status) }}
            </mat-chip>
          </mat-chip-set>
          <p class="connector-detail__health" *ngIf="connector.health">
            Live health:
            <strong>{{ formatHealthLabel(connector.health.status) }}</strong>
            <span *ngIf="connector.health.latency_ms"> &middot; {{ connector.health.latency_ms }}ms</span>
            <span *ngIf="connector.health.last_error"> &middot; {{ connector.health.last_error }}</span>
          </p>
        </div>
      </div>

      <!-- On-premise Agent Banner -->
      <div class="onpremise-banner" *ngIf="connector.requires_onpremise_agent && connector.onpremise_agent">
        <div class="onpremise-banner__icon">
          <mat-icon>dns</mat-icon>
        </div>
        <div class="onpremise-banner__content">
          <h3 class="onpremise-banner__title">
            {{ connector.onpremise_agent.display_name }}
            <span class="onpremise-banner__platform" *ngIf="connector.onpremise_agent.platform">
              <mat-icon>desktop_windows</mat-icon> {{ connector.onpremise_agent.platform | titlecase }}
            </span>
          </h3>
          <p class="onpremise-banner__desc">{{ connector.onpremise_agent.description }}</p>
          <div class="onpremise-banner__actions">
            <button mat-raised-button color="primary" (click)="onDownloadAgent()">
              <mat-icon>download</mat-icon> Download Agent Package
            </button>
            <span class="onpremise-banner__version">v{{ connector.version }}</span>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <mat-tab-group class="connector-detail__tabs" animationDuration="200ms">

        <!-- Swagger UI -->
        <mat-tab>
          <ng-template mat-tab-label>
            <mat-icon>api</mat-icon>&nbsp;Swagger UI
          </ng-template>
          <div class="connector-detail__tab-content">
            <p class="connector-detail__tab-hint">
              Interactive API documentation powered by Swagger UI. Loaded directly from the connector service.
            </p>
            <pinquark-swagger-ui
              *ngIf="openApiSpec"
              [spec]="openApiSpec"
            ></pinquark-swagger-ui>
            <div *ngIf="swaggerLoading" class="swagger-status">
              Loading Swagger UI...
            </div>
            <div *ngIf="swaggerError" class="swagger-status swagger-status--error">
              <mat-icon>cloud_off</mat-icon>
              {{ swaggerError }}
            </div>
          </div>
        </mat-tab>

        <!-- API Reference -->
        <mat-tab *ngIf="connector.api_endpoints && connector.api_endpoints.length > 0">
          <ng-template mat-tab-label>
            <mat-icon>description</mat-icon>&nbsp;API Reference ({{ connector.api_endpoints.length }})
          </ng-template>
          <div class="connector-detail__tab-content">
            <p class="connector-detail__tab-hint">
              Endpoint overview from connector manifest.
            </p>

            <div *ngFor="let group of endpointGroups" class="api-group">
              <h4 class="api-group__title">{{ group.name }}</h4>

              <mat-accordion multi>
                <mat-expansion-panel *ngFor="let ep of group.endpoints" class="api-endpoint">
                  <mat-expansion-panel-header>
                    <mat-panel-title>
                      <span class="api-method" [ngClass]="'api-method--' + ep.method.toLowerCase()">
                        {{ ep.method }}
                      </span>
                      <code class="api-path">{{ ep.path }}</code>
                    </mat-panel-title>
                    <mat-panel-description>
                      {{ ep.summary }}
                    </mat-panel-description>
                  </mat-expansion-panel-header>

                  <div class="api-endpoint__body">
                    <p class="api-endpoint__desc" *ngIf="ep.description">{{ ep.description }}</p>

                    <!-- Request Body -->
                    <div *ngIf="ep.request_body && ep.request_body.length > 0" class="api-fields">
                      <h5>Request Body</h5>
                      <table mat-table [dataSource]="ep.request_body" class="api-fields__table">
                        <ng-container matColumnDef="field">
                          <th mat-header-cell *matHeaderCellDef>Field</th>
                          <td mat-cell *matCellDef="let f">
                            <code>{{ f.field }}</code>
                            <span class="api-required" *ngIf="f.required">*</span>
                          </td>
                        </ng-container>
                        <ng-container matColumnDef="type">
                          <th mat-header-cell *matHeaderCellDef>Type</th>
                          <td mat-cell *matCellDef="let f"><code class="api-type">{{ f.type }}</code></td>
                        </ng-container>
                        <ng-container matColumnDef="description">
                          <th mat-header-cell *matHeaderCellDef>Description</th>
                          <td mat-cell *matCellDef="let f">{{ f.description }}</td>
                        </ng-container>
                        <tr mat-header-row *matHeaderRowDef="fieldColumns"></tr>
                        <tr mat-row *matRowDef="let row; columns: fieldColumns;"></tr>
                      </table>
                    </div>

                    <!-- Response Body -->
                    <div *ngIf="ep.response_body && ep.response_body.length > 0" class="api-fields">
                      <h5>Response Body</h5>
                      <table mat-table [dataSource]="ep.response_body" class="api-fields__table">
                        <ng-container matColumnDef="field">
                          <th mat-header-cell *matHeaderCellDef>Field</th>
                          <td mat-cell *matCellDef="let f"><code>{{ f.field }}</code></td>
                        </ng-container>
                        <ng-container matColumnDef="type">
                          <th mat-header-cell *matHeaderCellDef>Type</th>
                          <td mat-cell *matCellDef="let f"><code class="api-type">{{ f.type }}</code></td>
                        </ng-container>
                        <ng-container matColumnDef="description">
                          <th mat-header-cell *matHeaderCellDef>Description</th>
                          <td mat-cell *matCellDef="let f">{{ f.description }}</td>
                        </ng-container>
                        <tr mat-header-row *matHeaderRowDef="fieldColumns"></tr>
                        <tr mat-row *matRowDef="let row; columns: fieldColumns;"></tr>
                      </table>
                    </div>
                  </div>
                </mat-expansion-panel>
              </mat-accordion>
            </div>
          </div>
        </mat-tab>

        <!-- Capabilities -->
        <mat-tab>
          <ng-template mat-tab-label>
            <mat-icon>settings</mat-icon>&nbsp;Capabilities ({{ connector.capabilities.length }})
          </ng-template>
          <div class="connector-detail__tab-content">
            <mat-list>
              <mat-list-item *ngFor="let cap of connector.capabilities">
                <mat-icon matListItemIcon>check_circle</mat-icon>
                <span matListItemTitle>{{ formatName(cap) }}</span>
                <span matListItemLine class="connector-detail__code">{{ cap }}</span>
              </mat-list-item>
            </mat-list>
          </div>
        </mat-tab>

        <!-- Events -->
        <mat-tab>
          <ng-template mat-tab-label>
            <mat-icon>sensors</mat-icon>&nbsp;Events ({{ connector.events.length }})
          </ng-template>
          <div class="connector-detail__tab-content">
            <p class="connector-detail__tab-hint">Events emitted by this connector that can trigger flows.</p>
            <mat-list>
              <mat-list-item *ngFor="let ev of connector.events">
                <mat-icon matListItemIcon>bolt</mat-icon>
                <span matListItemTitle>{{ formatName(ev) }}</span>
                <span matListItemLine class="connector-detail__code">{{ ev }}</span>
              </mat-list-item>
            </mat-list>
            <p *ngIf="connector.events.length === 0" class="connector-detail__empty">No events defined.</p>
          </div>
        </mat-tab>

        <!-- Actions -->
        <mat-tab>
          <ng-template mat-tab-label>
            <mat-icon>play_arrow</mat-icon>&nbsp;Actions ({{ connector.actions.length }})
          </ng-template>
          <div class="connector-detail__tab-content">
            <p class="connector-detail__tab-hint">Actions that can be executed on this connector as flow destinations.</p>
            <mat-list>
              <mat-list-item *ngFor="let act of connector.actions">
                <mat-icon matListItemIcon>send</mat-icon>
                <span matListItemTitle>{{ getActionDisplayLabel(act) }}</span>
                <span matListItemLine class="connector-detail__code">{{ act }}</span>
                <span *ngIf="getActionDescription(act)" matListItemLine>{{ getActionDescription(act) }}</span>
              </mat-list-item>
            </mat-list>
            <p *ngIf="connector.actions.length === 0" class="connector-detail__empty">No actions defined.</p>
          </div>
        </mat-tab>

        <!-- Config Schema -->
        <mat-tab>
          <ng-template mat-tab-label>
            <mat-icon>tune</mat-icon>&nbsp;Configuration
          </ng-template>
          <div class="connector-detail__tab-content">
            <h4>Required fields</h4>
            <mat-list>
              <mat-list-item *ngFor="let field of connector.config_schema.required">
                <mat-icon matListItemIcon color="warn">label_important</mat-icon>
                <span matListItemTitle>{{ field }}</span>
              </mat-list-item>
            </mat-list>
            <p *ngIf="connector.config_schema.required.length === 0" class="connector-detail__empty">No required fields.</p>

            <h4 style="margin-top:16px">Optional fields</h4>
            <mat-list>
              <mat-list-item *ngFor="let field of connector.config_schema.optional">
                <mat-icon matListItemIcon>label</mat-icon>
                <span matListItemTitle>{{ field }}</span>
              </mat-list-item>
            </mat-list>
            <p *ngIf="connector.config_schema.optional.length === 0" class="connector-detail__empty">No optional fields.</p>
          </div>
        </mat-tab>

        <!-- On-Premise Agent -->
        <mat-tab *ngIf="connector.requires_onpremise_agent && connector.onpremise_agent">
          <ng-template mat-tab-label>
            <mat-icon>dns</mat-icon>&nbsp;On-Premise Agent
          </ng-template>
          <div class="connector-detail__tab-content">
            <p class="connector-detail__tab-hint">
              This connector requires an on-premise agent installed at the client site.
            </p>

            <div class="onpremise-details">
              <div class="onpremise-details__section">
                <h4><mat-icon>checklist</mat-icon> System Requirements</h4>
                <mat-list>
                  <mat-list-item *ngFor="let req of connector.onpremise_agent.requirements">
                    <mat-icon matListItemIcon>check_circle_outline</mat-icon>
                    <span matListItemTitle>{{ req }}</span>
                  </mat-list-item>
                </mat-list>
              </div>

              <div class="onpremise-details__section">
                <h4><mat-icon>format_list_numbered</mat-icon> Installation Steps</h4>
                <mat-list>
                  <mat-list-item *ngFor="let step of connector.onpremise_agent.install_steps; let i = index">
                    <span matListItemIcon class="onpremise-step-number">{{ i + 1 }}</span>
                    <span matListItemTitle>{{ step }}</span>
                  </mat-list-item>
                </mat-list>
              </div>

              <div class="onpremise-details__download">
                <button mat-raised-button color="primary" (click)="onDownloadAgent()">
                  <mat-icon>download</mat-icon> Download Agent Package (ZIP)
                </button>
              </div>
            </div>
          </div>
        </mat-tab>
      </mat-tab-group>
    </div>
  `,
  styles: [`
    .connector-detail__header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
    }
    .connector-detail__title { flex: 1; }
    .connector-detail__title h2 { margin: 0; }
    .connector-detail__subtitle {
      color: var(--mat-sys-on-surface-variant, #666);
      margin: 4px 0 0;
    }
    .connector-detail__logo-wrap {
      flex-shrink: 0;
      width: 64px;
      height: 48px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 8px;
      background: #f8f8f8;
      border: 1px solid #eee;
      padding: 6px;
      overflow: hidden;
    }
    .connector-detail__logo {
      max-width: 100%;
      max-height: 100%;
      object-fit: contain;
    }
    .connector-detail__flag {
      font-size: 24px;
      vertical-align: middle;
      margin-right: 6px;
    }
    .connector-detail__badge {
      display: inline-block;
      font-size: 11px;
      font-weight: 500;
      padding: 2px 8px;
      border-radius: 12px;
      background: var(--mat-sys-primary, #005cbb);
      color: var(--mat-sys-on-primary, #fff);
      vertical-align: middle;
      margin-left: 8px;
    }
    .connector-detail__badge--status {
      background: #e8f5e9;
      color: #2e7d32;
    }
    .connector-detail__header-actions { display: flex; gap: 8px; }
    .connector-detail__version-bar {
      display: flex;
      align-items: center;
      gap: 16px;
      margin: 16px 0 0;
    }
    .connector-detail__version-select { width: 200px; }
    .connector-detail__version-count {
      font-size: 13px;
      color: var(--mat-sys-on-surface-variant, #666);
    }
    .connector-detail__description {
      font-size: 15px;
      line-height: 1.6;
      margin: 16px 0;
    }
    .connector-detail__meta {
      display: flex;
      flex-direction: column;
      gap: 8px;
      margin-bottom: 16px;
    }
    .connector-detail__health {
      margin: 0;
      font-size: 13px;
      color: var(--mat-sys-on-surface-variant, #555);
    }
    .connector-detail__section { }
    .connector-detail__tabs { margin-top: 8px; }
    .connector-detail__tab-content { padding: 16px 0; }
    .connector-detail__tab-hint {
      font-size: 13px;
      color: var(--mat-sys-on-surface-variant, #666);
      margin-bottom: 12px;
    }
    .connector-detail__code {
      font-family: monospace;
      font-size: 12px;
      color: var(--mat-sys-on-surface-variant, #888);
    }
    .connector-detail__empty {
      color: var(--mat-sys-on-surface-variant, #999);
      font-style: italic;
      padding: 8px 16px;
    }

    /* API Reference styles */
    .api-group { margin-bottom: 24px; }
    .api-group__title {
      font-size: 16px;
      font-weight: 500;
      margin: 16px 0 8px;
      padding-bottom: 4px;
      border-bottom: 1px solid var(--mat-sys-outline-variant, #ddd);
    }

    .api-method {
      display: inline-block;
      font-family: monospace;
      font-size: 12px;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 4px;
      margin-right: 8px;
      min-width: 48px;
      text-align: center;
    }
    .api-method--get { background: #e8f5e9; color: #2e7d32; }
    .api-method--post { background: #e3f2fd; color: #1565c0; }
    .api-method--put { background: #fff3e0; color: #e65100; }
    .api-method--patch { background: #fff8e1; color: #f57f17; }
    .api-method--delete { background: #fce4ec; color: #c62828; }

    .api-path {
      font-family: monospace;
      font-size: 13px;
      color: var(--mat-sys-on-surface, #333);
    }

    .api-endpoint { margin-bottom: 4px; }
    .api-endpoint__body { padding: 8px 0; }
    .api-endpoint__desc {
      font-size: 14px;
      line-height: 1.5;
      color: var(--mat-sys-on-surface-variant, #555);
      margin-bottom: 16px;
    }

    .api-fields { margin-bottom: 16px; }
    .api-fields h5 {
      font-size: 13px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--mat-sys-on-surface-variant, #666);
      margin: 12px 0 8px;
    }
    .api-fields__table { width: 100%; }
    .api-fields__table code {
      font-size: 12px;
      background: var(--mat-sys-surface-variant, #f5f5f5);
      padding: 1px 6px;
      border-radius: 3px;
    }
    .api-type { color: var(--mat-sys-primary, #005cbb); }
    .api-required {
      color: #c62828;
      font-weight: bold;
      margin-left: 4px;
    }

    .swagger-status {
      display: flex;
      align-items: center;
      gap: 8px;
      justify-content: center;
      padding: 32px 0;
      color: var(--mat-sys-on-surface-variant, #666);
    }
    .swagger-status--error {
      color: #c62828;
    }

    /* On-premise agent banner */
    .onpremise-banner {
      display: flex;
      gap: 16px;
      padding: 20px;
      margin: 16px 0;
      border-radius: 12px;
      background: linear-gradient(135deg, #e8eaf6 0%, #e3f2fd 100%);
      border: 1px solid #c5cae9;
    }
    .onpremise-banner__icon {
      flex-shrink: 0;
      width: 48px;
      height: 48px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 12px;
      background: var(--mat-sys-primary, #005cbb);
      color: #fff;
    }
    .onpremise-banner__icon mat-icon { font-size: 28px; width: 28px; height: 28px; }
    .onpremise-banner__content { flex: 1; }
    .onpremise-banner__title {
      margin: 0 0 6px;
      font-size: 16px;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .onpremise-banner__platform {
      display: inline-flex;
      align-items: center;
      gap: 3px;
      font-size: 12px;
      font-weight: 500;
      padding: 2px 10px;
      border-radius: 12px;
      background: rgba(0,0,0,0.06);
      color: var(--mat-sys-on-surface-variant, #555);
    }
    .onpremise-banner__platform mat-icon { font-size: 14px; width: 14px; height: 14px; }
    .onpremise-banner__desc {
      font-size: 13px;
      line-height: 1.5;
      color: var(--mat-sys-on-surface-variant, #555);
      margin: 0 0 12px;
    }
    .onpremise-banner__actions {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .onpremise-banner__version {
      font-size: 12px;
      color: var(--mat-sys-on-surface-variant, #888);
    }

    /* On-premise agent tab details */
    .onpremise-details__section { margin-bottom: 20px; }
    .onpremise-details__section h4 {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 15px;
      font-weight: 600;
      margin: 0 0 8px;
      color: var(--mat-sys-on-surface, #1a1a1a);
    }
    .onpremise-details__section h4 mat-icon {
      font-size: 20px; width: 20px; height: 20px;
      color: var(--mat-sys-primary, #005cbb);
    }
    .onpremise-step-number {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background: var(--mat-sys-primary, #005cbb);
      color: #fff;
      font-size: 12px;
      font-weight: 700;
    }
    .onpremise-details__download {
      margin-top: 24px;
      padding-top: 16px;
      border-top: 1px solid var(--mat-sys-outline-variant, #ddd);
    }
  `],
})
export class ConnectorDetailComponent implements OnInit, OnChanges {
  @Input() group: ConnectorGroup | null = null;
  @Output() goBack = new EventEmitter<void>();
  @Output() activate = new EventEmitter<Connector>();
  @Output() deactivated = new EventEmitter<void>();

  connector: Connector | null = null;
  selectedVersion = '';
  availableVersions: Connector[] = [];
  activeInstance: ConnectorInstance | null = null;
  allInstances: ConnectorInstance[] = [];
  endpointGroups: { name: string; endpoints: ApiEndpoint[] }[] = [];
  fieldColumns = ['field', 'type', 'description'];
  openApiSpec: object | null = null;
  swaggerLoading = false;
  swaggerError = '';

  constructor(private readonly api: PinquarkApiService) {}

  ngOnInit(): void {
    this.initFromGroup();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['group']) {
      this.initFromGroup();
    }
  }

  private initFromGroup(): void {
    if (!this.group) {
      this.connector = null;
      this.availableVersions = [];
      return;
    }

    this.availableVersions = this.group.versions;
    this.selectedVersion = this.group.latest.version;
    this.connector = this.group.latest;
    this.loadActiveState();
    this.buildEndpointGroups();
    this.loadSwaggerSpec();
  }

  onVersionChange(): void {
    this.connector = this.availableVersions.find(v => v.version === this.selectedVersion) ?? null;
    this.loadActiveInstance();
    this.buildEndpointGroups();
    this.loadSwaggerSpec();
  }

  onActivateClick(): void {
    if (this.connector) {
      this.activate.emit(this.connector);
    }
  }

  isVersionActive(version: string): boolean {
    return this.allInstances.some(
      i => i.is_enabled && i.connector_name === this.group?.name && i.connector_version === version
    );
  }

  private loadSwaggerSpec(): void {
    if (!this.connector) {
      this.openApiSpec = null;
      return;
    }
    this.swaggerLoading = true;
    this.swaggerError = '';
    this.openApiSpec = null;

    this.api.getConnectorOpenApiSpec(this.connector.name).subscribe({
      next: (spec) => {
        this.openApiSpec = spec;
        this.swaggerLoading = false;
      },
      error: () => {
        this.swaggerError = 'Connector is not running or Swagger spec is unavailable. Start the connector to see interactive API docs.';
        this.swaggerLoading = false;
      },
    });
  }

  private buildEndpointGroups(): void {
    if (!this.connector?.api_endpoints?.length) {
      this.endpointGroups = [];
      return;
    }

    const groupMap = new Map<string, ApiEndpoint[]>();
    for (const ep of this.connector.api_endpoints) {
      const groupName = ep.group || 'General';
      if (!groupMap.has(groupName)) {
        groupMap.set(groupName, []);
      }
      groupMap.get(groupName)!.push(ep);
    }

    this.endpointGroups = Array.from(groupMap.entries()).map(([name, endpoints]) => ({
      name,
      endpoints,
    }));
  }

  private loadActiveState(): void {
    this.api.listConnectorInstances().subscribe(instances => {
      this.allInstances = instances.filter(i => i.is_enabled);
      this.loadActiveInstance();
    });
  }

  private loadActiveInstance(): void {
    if (!this.connector) {
      this.activeInstance = null;
      return;
    }
    this.activeInstance = this.allInstances.find(
      i => i.connector_name === this.connector!.name
        && i.connector_version === this.connector!.version
    ) ?? null;
  }

  formatName(key: string): string {
    return key
      .replace(/[._]/g, ' ')
      .replace(/\b\w/g, c => c.toUpperCase());
  }

  getActionDisplayLabel(action: string): string {
    return this.connector?.action_metadata?.[action]?.label?.trim() || this.formatName(action);
  }

  getActionDescription(action: string): string {
    return this.connector?.action_metadata?.[action]?.description?.trim() || '';
  }

  formatAuthType(authType: string): string {
    return authType
      .split('_')
      .map(part => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' ');
  }

  formatStatusLabel(status: string): string {
    return status
      .split('_')
      .map(part => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' ');
  }

  formatHealthLabel(status?: string): string {
    switch (status) {
      case 'healthy': return 'Healthy';
      case 'degraded': return 'Degraded';
      case 'unhealthy': return 'Unhealthy';
      default: return 'Unknown';
    }
  }

  getHealthColor(status?: string): 'primary' | 'accent' | 'warn' | undefined {
    switch (status) {
      case 'healthy': return 'primary';
      case 'degraded': return 'accent';
      case 'unhealthy': return 'warn';
      default: return undefined;
    }
  }

  getFlag(code: string): string {
    return COUNTRY_FLAG_MAP[code] ?? code;
  }

  getCountryName(code: string): string {
    return COUNTRY_NAME_MAP[code] ?? code;
  }

  onDownloadAgent(): void {
    if (this.connector) {
      this.api.downloadOnPremiseAgent(this.connector.name);
    }
  }

  onDeactivate(): void {
    if (!this.activeInstance) return;
    this.api.deactivateConnector(this.activeInstance.id).subscribe(() => {
      this.activeInstance = null;
      this.deactivated.emit();
    });
  }
}
