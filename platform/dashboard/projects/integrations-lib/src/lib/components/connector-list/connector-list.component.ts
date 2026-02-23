import {
  AfterViewInit, Component, ElementRef, EventEmitter,
  Input, OnDestroy, OnInit, Output, ViewChild,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatBadgeModule } from '@angular/material/badge';
import { MatInputModule } from '@angular/material/input';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDividerModule } from '@angular/material/divider';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';

import {
  Connector, ConnectorGroup, ConnectorInstance,
  CategorySection, CredentialInfo, CredentialValidationResult,
  COUNTRY_FLAG_MAP, COUNTRY_NAME_MAP,
  CATEGORY_ORDER, CATEGORY_DISPLAY,
} from '../../models';
import { PinquarkApiService } from '../../services/pinquark-api.service';

const BATCH_SIZE = 12;

@Component({
  selector: 'pinquark-connector-list',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatChipsModule,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatSelectModule,
    MatBadgeModule,
    MatInputModule,
    MatTooltipModule,
    MatDividerModule,
    MatProgressSpinnerModule,
    FormsModule,
  ],
  template: `
    <div class="connector-list">
      <div class="connector-list__header">
        <h2>Connectors</h2>
        <div class="connector-list__filters">
          <mat-form-field appearance="outline" class="connector-list__search">
            <mat-label>Search</mat-label>
            <input matInput [(ngModel)]="searchQuery" (ngModelChange)="applyFilters()" placeholder="Search connectors..." />
            <mat-icon matPrefix>search</mat-icon>
            @if (searchQuery) {
              <button matSuffix mat-icon-button (click)="searchQuery = ''; applyFilters()">
                <mat-icon>close</mat-icon>
              </button>
            }
          </mat-form-field>
          <mat-form-field appearance="outline" class="connector-list__filter">
            <mat-label>Status</mat-label>
            <mat-select [(ngModel)]="selectedStatus" (selectionChange)="applyFilters()">
              <mat-option value="all">All</mat-option>
              <mat-option value="active">Active</mat-option>
              <mat-option value="inactive">Inactive</mat-option>
            </mat-select>
          </mat-form-field>
          <mat-form-field appearance="outline" class="connector-list__filter">
            <mat-label>Category</mat-label>
            <mat-select [(ngModel)]="selectedCategory" (selectionChange)="loadAll()">
              <mat-option [value]="''">All</mat-option>
              <mat-option value="courier">Courier</mat-option>
              <mat-option value="ecommerce">E-commerce</mat-option>
              <mat-option value="erp">ERP</mat-option>
              <mat-option value="wms">WMS</mat-option>
              <mat-option value="automation">Automation</mat-option>
              <mat-option value="other">Other</mat-option>
            </mat-select>
          </mat-form-field>
          <mat-form-field appearance="outline" class="connector-list__filter">
            <mat-label>Country</mat-label>
            <mat-select [(ngModel)]="selectedCountry" (selectionChange)="applyFilters()">
              <mat-option [value]="''">All</mat-option>
              @for (country of availableCountries; track country.code) {
                <mat-option [value]="country.code">{{ country.flag }} {{ country.name }}</mat-option>
              }
            </mat-select>
          </mat-form-field>
        </div>
      </div>

      <div class="connector-list__body">
        @for (section of visibleSections; track section.category; let isFirst = $first) {
          @if (!isFirst) {
            <div class="category-divider"></div>
          }
          <div class="category-section">
            <div class="category-section__header">
              <mat-icon class="category-section__icon">{{ section.icon }}</mat-icon>
              <h3 class="category-section__title">{{ section.displayName }}</h3>
              <span class="category-section__count">{{ section.totalCount }}</span>
            </div>

            <div class="connector-list__grid">
              @for (group of section.groups; track group.name) {
                <mat-card
                  class="connector-card"
                  [class.connector-card--active]="group.activeVersions.length > 0"
                  (click)="onSelect.emit(group)"
                >
                  <mat-card-header>
                    <div mat-card-avatar class="connector-card__logo-container">
                      @if (group.logo_url) {
                        <img [src]="group.logo_url" [alt]="group.display_name" class="connector-card__logo" />
                      } @else {
                        <span class="connector-card__logo-fallback">{{ group.display_name.charAt(0) }}</span>
                      }
                    </div>
                    <mat-card-title>
                      @if (group.country) {
                        <span class="connector-card__flag" [title]="getCountryName(group.country)">{{ getFlag(group.country) }}</span>
                      }
                      {{ group.display_name }}
                      @if (group.activeVersions.length > 0) {
                        <span class="connector-card__badge">Active (v{{ group.activeVersions[0] }})</span>
                      }
                    </mat-card-title>
                    <mat-card-subtitle>
                      {{ group.category }}@if (group.country) { &middot; {{ getCountryName(group.country) }}}
                      @if (group.versions.length > 1) {
                        &middot; {{ group.versions.length }} versions
                      } @else {
                        &middot; v{{ group.latest.version }}
                      }
                    </mat-card-subtitle>
                  </mat-card-header>
                  <mat-card-content>
                    <p class="connector-card__desc">{{ group.latest.description }}</p>
                    @if (group.website_url) {
                      <a class="connector-card__link" [href]="group.website_url" target="_blank" rel="noopener noreferrer" (click)="$event.stopPropagation()">
                        <mat-icon>open_in_new</mat-icon> {{ getDomainFromUrl(group.website_url) }}
                      </a>
                    }
                    <div class="connector-card__meta">
                      <mat-chip>{{ group.latest.capabilities.length }} capabilities</mat-chip>
                      <mat-chip>{{ group.latest.events.length }} events</mat-chip>
                      <mat-chip>{{ group.latest.actions.length }} actions</mat-chip>
                    </div>
                    @if (group.activeVersions.length > 0) {
                      <div class="connector-card__connection-status" [matTooltip]="getConnectionTooltip(group.name)">
                        @if (!credentialMap[group.name]?.length) {
                          <span class="conn-status conn-status--none">
                            <mat-icon>remove_circle_outline</mat-icon> No credentials
                          </span>
                        } @else if (validatingConnectors.has(group.name)) {
                          <span class="conn-status conn-status--pending">
                            <mat-icon class="spin">sync</mat-icon> Checking...
                          </span>
                        } @else if (connectionStatus[group.name]?.status === 'success') {
                          <span class="conn-status conn-status--connected">
                            <mat-icon>check_circle</mat-icon> Connected
                            @if (connectionStatus[group.name]?.response_time_ms) {
                              <span class="conn-status__time">({{ connectionStatus[group.name]?.response_time_ms }}ms)</span>
                            }
                          </span>
                        } @else if (connectionStatus[group.name]?.status === 'failed') {
                          <span class="conn-status conn-status--disconnected">
                            <mat-icon>error</mat-icon> Disconnected
                          </span>
                        } @else if (connectionStatus[group.name]?.status === 'unsupported') {
                          <span class="conn-status conn-status--none">
                            <mat-icon>info</mat-icon> N/A
                          </span>
                        }
                      </div>
                    }
                  </mat-card-content>
                </mat-card>
              }
            </div>
          </div>
        }

        @if (hasMore) {
          <div class="scroll-sentinel" #scrollSentinel>
            <mat-spinner diameter="32"></mat-spinner>
          </div>
        }

        @if (visibleSections.length === 0 && !loading) {
          <div class="connector-list__empty">
            <mat-icon>search_off</mat-icon>
            <p>No connectors match your filters.</p>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    .connector-list__header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }
    .connector-list__filters { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
    .connector-list__search { width: 280px; }
    .connector-list__filter { width: 200px; }

    /* ---- Category sections ---- */
    .category-section { margin-bottom: 8px; }
    .category-section__header {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 8px 0 12px;
    }
    .category-section__icon {
      color: var(--mat-sys-primary, #005cbb);
      font-size: 24px;
    }
    .category-section__title {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
      color: var(--mat-sys-on-surface, #1a1a1a);
    }
    .category-section__count {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 24px;
      height: 24px;
      padding: 0 6px;
      border-radius: 12px;
      background: var(--mat-sys-surface-variant, #e7e0ec);
      color: var(--mat-sys-on-surface-variant, #49454f);
      font-size: 12px;
      font-weight: 600;
    }
    .category-divider {
      height: 1px;
      background: var(--mat-sys-outline-variant, #cac4d0);
      margin: 16px 0 8px;
    }

    /* ---- Grid ---- */
    .connector-list__grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 16px;
    }

    /* ---- Cards ---- */
    .connector-card { cursor: pointer; transition: box-shadow 0.2s, transform 0.15s; }
    .connector-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.15); transform: translateY(-2px); }
    :host ::ng-deep .connector-card .mat-mdc-card-header { align-items: center; }
    :host ::ng-deep .connector-card__logo-container.mat-mdc-card-avatar {
      width: 56px; height: 40px; border-radius: 8px;
    }
    .connector-card--active {
      border-left: 4px solid var(--mat-sys-primary, #005cbb);
      background: color-mix(in srgb, var(--mat-sys-primary-container, #d7e3ff) 30%, transparent);
    }
    .connector-card__badge {
      display: inline-block; font-size: 11px; font-weight: 500;
      padding: 2px 8px; border-radius: 12px;
      background: var(--mat-sys-primary, #005cbb);
      color: var(--mat-sys-on-primary, #fff);
      vertical-align: middle; margin-left: 8px;
    }
    .connector-card__desc {
      font-size: 13px; line-height: 1.5;
      color: var(--mat-sys-on-surface-variant, #444);
      margin-bottom: 8px;
      display: -webkit-box; -webkit-line-clamp: 3;
      -webkit-box-orient: vertical; overflow: hidden;
    }
    .connector-card__link {
      display: inline-flex; align-items: center; gap: 3px;
      font-size: 12px; color: var(--mat-sys-primary, #005cbb);
      text-decoration: none; margin-bottom: 10px; transition: opacity 0.15s;
    }
    .connector-card__link:hover { opacity: 0.75; text-decoration: underline; }
    .connector-card__link mat-icon { font-size: 14px; width: 14px; height: 14px; }
    .connector-card__meta { display: flex; flex-wrap: wrap; gap: 4px; }
    .connector-card__flag { font-size: 20px; vertical-align: middle; margin-right: 4px; }
    .connector-card__logo-container {
      flex-shrink: 0; width: 56px; height: 40px;
      display: flex; align-items: center; justify-content: center;
      margin-right: 12px; border-radius: 8px;
      background: #f8f8f8; border: 1px solid #eee; padding: 4px; overflow: hidden;
    }
    .connector-card__logo { max-width: 100%; max-height: 100%; object-fit: contain; }
    .connector-card__logo-fallback {
      width: 100%; height: 100%;
      display: flex; align-items: center; justify-content: center;
      border-radius: 4px; background: var(--mat-sys-primary, #005cbb);
      color: #fff; font-weight: 700; font-size: 18px;
    }
    .connector-card__connection-status { margin-top: 10px; }
    .conn-status {
      display: inline-flex; align-items: center; gap: 4px;
      font-size: 12px; font-weight: 500; padding: 2px 8px; border-radius: 12px;
    }
    .conn-status mat-icon { font-size: 16px; height: 16px; width: 16px; }
    .conn-status--connected { color: #2e7d32; background: #e8f5e9; }
    .conn-status--disconnected { color: #c62828; background: #fbe9e7; }
    .conn-status--pending { color: #555; background: #f5f5f5; }
    .conn-status--none { color: #999; background: #fafafa; }
    .conn-status__time { opacity: 0.7; }
    @keyframes spin { 100% { transform: rotate(360deg); } }
    .spin { animation: spin 1s linear infinite; }

    /* ---- Scroll sentinel / empty ---- */
    .scroll-sentinel {
      display: flex; justify-content: center; padding: 24px 0;
    }
    .connector-list__empty {
      display: flex; flex-direction: column; align-items: center;
      padding: 48px 0; color: var(--mat-sys-on-surface-variant, #666);
    }
    .connector-list__empty mat-icon { font-size: 48px; height: 48px; width: 48px; margin-bottom: 12px; opacity: 0.4; }
  `],
})
export class ConnectorListComponent implements OnInit, AfterViewInit, OnDestroy {
  @Input() category: string = '';
  @Output() onSelect = new EventEmitter<ConnectorGroup>();
  @Output() onActivate = new EventEmitter<Connector>();
  @Output() onDeactivate = new EventEmitter<ConnectorInstance>();

  @ViewChild('scrollSentinel') scrollSentinelRef!: ElementRef<HTMLElement>;

  connectors: Connector[] = [];
  connectorGroups: ConnectorGroup[] = [];
  filteredGroups: ConnectorGroup[] = [];
  activeInstances: ConnectorInstance[] = [];
  selectedCategory = '';
  selectedCountry = '';
  selectedStatus: 'all' | 'active' | 'inactive' = 'all';
  searchQuery = '';
  availableCountries: { code: string; flag: string; name: string }[] = [];
  loading = true;

  credentialMap: Record<string, CredentialInfo[]> = {};
  connectionStatus: Record<string, CredentialValidationResult> = {};
  validatingConnectors = new Set<string>();

  allSections: CategorySection[] = [];
  visibleSections: (CategorySection & { totalCount: number })[] = [];
  visibleCount = BATCH_SIZE;
  hasMore = false;

  private observer: IntersectionObserver | null = null;
  private observedElement: HTMLElement | null = null;

  constructor(private readonly api: PinquarkApiService) {}

  ngOnInit(): void {
    this.selectedCategory = this.category;
    this.loadAll();
  }

  ngAfterViewInit(): void {
    this.setupObserver();
  }

  ngOnDestroy(): void {
    this.observer?.disconnect();
  }

  loadAll(): void {
    this.loading = true;
    const params = this.selectedCategory ? { category: this.selectedCategory } : undefined;
    forkJoin({
      connectors: this.api.listConnectors(params),
      instances: this.api.listConnectorInstances(),
      credentials: this.api.listCredentials(),
    }).subscribe(({ connectors, instances, credentials }: {
      connectors: Connector[];
      instances: ConnectorInstance[];
      credentials: CredentialInfo[];
    }) => {
      this.connectors = connectors;
      this.activeInstances = instances.filter((i: ConnectorInstance) => i.is_enabled);
      this.credentialMap = {};
      for (const cred of credentials) {
        if (!this.credentialMap[cred.connector_name]) {
          this.credentialMap[cred.connector_name] = [];
        }
        this.credentialMap[cred.connector_name].push(cred);
      }
      this.connectorGroups = this.buildGroups();
      this.buildAvailableCountries();
      this.visibleCount = BATCH_SIZE;
      this.applyFilters();
      this.validateAllCredentials();
      this.loading = false;
    });
  }

  applyFilters(): void {
    let result = this.connectorGroups;

    if (this.selectedStatus === 'active') {
      result = result.filter(g => g.activeVersions.length > 0);
    } else if (this.selectedStatus === 'inactive') {
      result = result.filter(g => g.activeVersions.length === 0);
    }

    if (this.selectedCountry) {
      result = result.filter(g => g.country === this.selectedCountry);
    }

    if (this.searchQuery.trim()) {
      const q = this.searchQuery.trim().toLowerCase();
      result = result.filter(g =>
        g.display_name.toLowerCase().includes(q) ||
        g.name.toLowerCase().includes(q) ||
        g.description.toLowerCase().includes(q) ||
        g.category.toLowerCase().includes(q) ||
        this.getCountryName(g.country).toLowerCase().includes(q)
      );
    }

    result.sort((a, b) => {
      const aActive = a.activeVersions.length > 0 ? 0 : 1;
      const bActive = b.activeVersions.length > 0 ? 0 : 1;
      return aActive - bActive;
    });

    this.filteredGroups = result;
    this.allSections = this.buildCategorySections(result);
    this.computeVisibleSections();
  }

  loadMore(): void {
    this.visibleCount += BATCH_SIZE;
    this.computeVisibleSections();
  }

  // ------------------------------------------------------------------
  // Helpers
  // ------------------------------------------------------------------

  getConnectionTooltip(connectorName: string): string {
    if (!this.credentialMap[connectorName]?.length) return 'No credentials configured';
    if (this.validatingConnectors.has(connectorName)) return 'Validating connection...';
    const r = this.connectionStatus[connectorName];
    if (!r) return 'Checking...';
    return r.message + (r.response_time_ms ? ` (${r.response_time_ms}ms)` : '');
  }

  getFlag(code: string): string { return COUNTRY_FLAG_MAP[code] ?? code; }
  getCountryName(code: string): string { return COUNTRY_NAME_MAP[code] ?? code; }

  getDomainFromUrl(url: string): string {
    try { return new URL(url).hostname.replace(/^www\./, ''); }
    catch { return url; }
  }

  // ------------------------------------------------------------------
  // Category grouping
  // ------------------------------------------------------------------

  private buildCategorySections(groups: ConnectorGroup[]): CategorySection[] {
    const byCat = new Map<string, ConnectorGroup[]>();
    for (const g of groups) {
      const cat = CATEGORY_ORDER.includes(g.category) ? g.category : 'other';
      if (!byCat.has(cat)) byCat.set(cat, []);
      byCat.get(cat)!.push(g);
    }

    return CATEGORY_ORDER
      .filter(c => byCat.has(c))
      .map(cat => ({
        category: cat,
        displayName: CATEGORY_DISPLAY[cat]?.name ?? cat,
        icon: CATEGORY_DISPLAY[cat]?.icon ?? 'category',
        groups: byCat.get(cat)!,
      }));
  }

  private computeVisibleSections(): void {
    let remaining = this.visibleCount;
    const result: (CategorySection & { totalCount: number })[] = [];

    for (const section of this.allSections) {
      if (remaining <= 0) break;
      const slice = section.groups.slice(0, remaining);
      result.push({ ...section, groups: slice, totalCount: section.groups.length });
      remaining -= slice.length;
    }

    this.visibleSections = result;
    const total = this.allSections.reduce((s, sec) => s + sec.groups.length, 0);
    this.hasMore = this.visibleCount < total;

    requestAnimationFrame(() => this.reobserveSentinel());
  }

  // ------------------------------------------------------------------
  // Infinite scroll via IntersectionObserver
  // ------------------------------------------------------------------

  private setupObserver(): void {
    this.observer = new IntersectionObserver(
      entries => {
        if (entries.some(e => e.isIntersecting) && this.hasMore) {
          this.loadMore();
        }
      },
      { rootMargin: '200px' },
    );
    this.reobserveSentinel();
  }

  private reobserveSentinel(): void {
    if (!this.observer) return;
    if (this.observedElement) {
      this.observer.unobserve(this.observedElement);
      this.observedElement = null;
    }
    const el = this.scrollSentinelRef?.nativeElement;
    if (el) {
      this.observer.observe(el);
      this.observedElement = el;
    }
  }

  // ------------------------------------------------------------------
  // Internal
  // ------------------------------------------------------------------

  private validateAllCredentials(): void {
    for (const [connectorName, creds] of Object.entries(this.credentialMap)) {
      const firstCred = creds[0];
      this.validatingConnectors.add(connectorName);
      this.api.validateCredentials(connectorName, firstCred.credential_name).subscribe({
        next: (result: CredentialValidationResult) => {
          this.validatingConnectors.delete(connectorName);
          this.connectionStatus[connectorName] = result;
        },
        error: () => {
          this.validatingConnectors.delete(connectorName);
          this.connectionStatus[connectorName] = { status: 'failed', message: 'Validation failed' };
        },
      });
    }
  }

  private buildGroups(): ConnectorGroup[] {
    const groupMap = new Map<string, Connector[]>();
    for (const c of this.connectors) {
      const key = `${c.category}/${c.name}`;
      if (!groupMap.has(key)) groupMap.set(key, []);
      groupMap.get(key)!.push(c);
    }

    return Array.from(groupMap.values()).map(versions => {
      const sorted = [...versions].sort((a, b) =>
        b.version.localeCompare(a.version, undefined, { numeric: true }),
      );
      const latest = sorted[0];
      const activeVersions = sorted
        .filter(v => this.activeInstances.some(
          i => i.connector_name === v.name && i.connector_version === v.version,
        ))
        .map(v => v.version);

      return {
        name: latest.name,
        category: latest.category,
        display_name: latest.display_name,
        description: latest.description,
        country: latest.country,
        logo_url: latest.logo_url,
        website_url: latest.website_url,
        interface: latest.interface,
        latest,
        versions: sorted,
        activeVersions,
      };
    });
  }

  private buildAvailableCountries(): void {
    const codes = new Set(this.connectorGroups.map(g => g.country).filter(Boolean));
    this.availableCountries = Array.from(codes)
      .map(code => ({
        code,
        flag: COUNTRY_FLAG_MAP[code] ?? code,
        name: COUNTRY_NAME_MAP[code] ?? code,
      }))
      .sort((a, b) => a.name.localeCompare(b.name));
  }
}
