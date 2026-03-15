import { Component, OnDestroy, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import {
  ConnectorListComponent,
  ConnectorDetailComponent,
  PinquarkApiService,
  Connector,
  ConnectorGroup,
  ConnectorInstance,
} from '@pinquark/integrations';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

@Component({
  selector: 'app-connectors-page',
  standalone: true,
  imports: [CommonModule, ConnectorListComponent, ConnectorDetailComponent, MatSnackBarModule],
  template: `
    @if (selectedGroup) {
      <pinquark-connector-detail
        [group]="selectedGroup"
        (goBack)="onBackToList()"
        (activate)="onConnectorActivate($event)"
        (deactivated)="onDetailDeactivated()"
      ></pinquark-connector-detail>
    } @else {
      @if (contextTitle || contextDescription) {
        <div class="connectors-page__context">
          <div>
            <h2>{{ contextTitle || 'Connector catalog' }}</h2>
            <p>{{ contextDescription || 'Browse connectors filtered for your current context.' }}</p>
          </div>
        </div>
      }
      <pinquark-connector-list
        [category]="catalogCategory"
        [initialSearchQuery]="catalogSearch"
        [eventFilter]="catalogEvent"
        [actionFilter]="catalogAction"
        (onSelect)="onGroupSelect($event)"
      ></pinquark-connector-list>
    }
  `,
  styles: [`
    .connectors-page__context {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 16px;
      padding: 16px 18px;
      border-radius: 12px;
      background: linear-gradient(135deg, #e3f2fd, #f3e5f5);
    }
    .connectors-page__context h2 {
      margin: 0 0 4px;
      font-size: 22px;
    }
    .connectors-page__context p {
      margin: 0;
      color: #555;
    }
  `],
})
export class ConnectorsPage implements OnDestroy {
  @ViewChild(ConnectorListComponent) connectorList!: ConnectorListComponent;

  selectedGroup: ConnectorGroup | null = null;
  catalogCategory = '';
  catalogSearch = '';
  catalogEvent = '';
  catalogAction = '';
  contextTitle = '';
  contextDescription = '';

  private readonly destroy$ = new Subject<void>();

  constructor(
    private readonly snackBar: MatSnackBar,
    private readonly api: PinquarkApiService,
    private readonly route: ActivatedRoute,
    private readonly router: Router,
  ) {
    this.route.queryParamMap.pipe(takeUntil(this.destroy$)).subscribe(params => {
      this.catalogCategory = params.get('category') || '';
      this.catalogSearch = params.get('q') || '';
      this.catalogEvent = params.get('event') || '';
      this.catalogAction = params.get('action') || '';
      this.contextTitle = params.get('title') || '';
      this.contextDescription = params.get('description') || '';
    });
    this.route.paramMap.pipe(takeUntil(this.destroy$)).subscribe(params => {
      const category = params.get('category');
      const name = params.get('name');
      if (category && name) {
        this.loadConnectorDetail(category, name);
      } else {
        this.selectedGroup = null;
      }
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onGroupSelect(group: ConnectorGroup): void {
    void this.router.navigate(['/connectors', group.category, group.name], {
      queryParamsHandling: 'preserve',
    });
  }

  onBackToList(): void {
    this.selectedGroup = null;
    void this.router.navigate(['/connectors'], {
      queryParamsHandling: 'preserve',
    });
  }

  onConnectorActivate(connector: Connector): void {
    this.api.activateConnector({
      connector_name: connector.name,
      connector_version: connector.version,
      connector_category: connector.category,
      display_name: connector.display_name,
    }).subscribe({
      next: () => {
        this.snackBar.open(`Activated: ${connector.display_name} v${connector.version}`, 'OK', { duration: 3000 });
        if (this.connectorList) {
          this.connectorList.loadAll();
        }
        if (this.selectedGroup?.name === connector.name) {
          this.selectedGroup = { ...this.selectedGroup };
        }
      },
      error: () => {
        this.snackBar.open(`Failed to activate ${connector.display_name}`, 'OK', { duration: 3000 });
      },
    });
  }

  onDetailDeactivated(): void {
    this.snackBar.open('Connector deactivated', 'OK', { duration: 3000 });
    if (this.selectedGroup) {
      this.selectedGroup = { ...this.selectedGroup };
    }
  }

  private loadConnectorDetail(category: string, name: string): void {
    this.api.listConnectors({ category }).subscribe({
      next: connectors => {
        const matching = connectors
          .filter(connector => connector.category === category && connector.name === name)
          .sort((a, b) => b.version.localeCompare(a.version, undefined, { numeric: true }));
        if (matching.length === 0) {
          this.selectedGroup = null;
          return;
        }
        const latest = matching[0];
        this.selectedGroup = {
          name: latest.name,
          category: latest.category,
          display_name: latest.display_name,
          description: latest.description,
          country: latest.country,
          logo_url: latest.logo_url,
          website_url: latest.website_url,
          interface: latest.interface,
          auth_type: latest.auth_type,
          status: latest.status,
          supports_oauth2: latest.supports_oauth2,
          sandbox_available: latest.sandbox_available,
          has_webhooks: latest.has_webhooks,
          health: latest.health,
          latest,
          versions: matching,
          activeVersions: [],
        };
      },
      error: () => {
        this.selectedGroup = null;
        this.snackBar.open('Failed to load connector details', 'OK', { duration: 3000 });
      },
    });
  }
}
