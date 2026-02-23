# Embedding Pinquark in an Angular Application

This guide shows how to embed the Pinquark integration UI into your existing Angular application (e.g., Pinquark WMS).

## 1. Install the library

```bash
npm install @pinquark/integrations
```

## 2. Configure the module

In your app module or standalone bootstrap:

```typescript
import { PinquarkIntegrationsModule } from '@pinquark/integrations';

// In NgModule-based app:
@NgModule({
  imports: [
    PinquarkIntegrationsModule.forRoot({
      apiUrl: 'https://api.pinquark.com',  // or http://localhost:8080
      apiKey: environment.pinquarkApiKey,
    })
  ]
})
export class AppModule {}

// In standalone app (main.ts):
bootstrapApplication(AppComponent, {
  providers: [
    importProvidersFrom(
      PinquarkIntegrationsModule.forRoot({
        apiUrl: environment.pinquarkApiUrl,
        apiKey: environment.pinquarkApiKey,
      })
    ),
  ],
});
```

## 3. Use components in your templates

All components are standalone and can be imported directly:

```typescript
import {
  ConnectorListComponent,
  CredentialFormComponent,
  FlowDesignerComponent,
  OperationLogComponent,
} from '@pinquark/integrations';

@Component({
  standalone: true,
  imports: [ConnectorListComponent, FlowDesignerComponent],
  template: `
    <h2>Available Integrations</h2>
    <pinquark-connector-list
      [category]="'courier'"
      (onSelect)="onConnectorSelected($event)"
      (onActivate)="onConnectorActivated($event)"
    ></pinquark-connector-list>

    <h2>Create Integration Flow</h2>
    <pinquark-flow-designer
      (flowCreated)="onFlowCreated($event)"
    ></pinquark-flow-designer>
  `,
})
export class IntegrationsPage {
  onConnectorSelected(connector: any) { /* ... */ }
  onConnectorActivated(connector: any) { /* ... */ }
  onFlowCreated(flow: any) { /* ... */ }
}
```

## 4. Available components

| Component | Selector | Description |
|-----------|----------|-------------|
| `ConnectorListComponent` | `<pinquark-connector-list>` | Grid of available connectors with category filter |
| `CredentialFormComponent` | `<pinquark-credential-form>` | Form to store connector credentials |
| `FlowDesignerComponent` | `<pinquark-flow-designer>` | 3-step wizard to create integration flows |
| `OperationLogComponent` | `<pinquark-operation-log>` | Table of flow execution logs |

## 5. Using the API service directly

For custom UI, inject `PinquarkApiService`:

```typescript
import { PinquarkApiService } from '@pinquark/integrations';

@Component({ /* ... */ })
export class CustomPage {
  constructor(private api: PinquarkApiService) {}

  ngOnInit() {
    this.api.listConnectors({ category: 'courier' }).subscribe(connectors => {
      console.log('Couriers:', connectors);
    });

    this.api.listFlows().subscribe(flows => {
      console.log('Active flows:', flows);
    });
  }
}
```
