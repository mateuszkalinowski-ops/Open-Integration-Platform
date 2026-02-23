import { Component, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
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
      <pinquark-connector-list
        (onSelect)="onGroupSelect($event)"
      ></pinquark-connector-list>
    }
  `,
})
export class ConnectorsPage {
  @ViewChild(ConnectorListComponent) connectorList!: ConnectorListComponent;

  selectedGroup: ConnectorGroup | null = null;

  constructor(
    private readonly snackBar: MatSnackBar,
    private readonly api: PinquarkApiService,
  ) {}

  onGroupSelect(group: ConnectorGroup): void {
    this.selectedGroup = group;
  }

  onBackToList(): void {
    this.selectedGroup = null;
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
}
