import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: 'connectors', pathMatch: 'full' },
  {
    path: 'connectors',
    loadComponent: () =>
      import('./pages/connectors/connectors.page').then(m => m.ConnectorsPage),
  },
  {
    path: 'credentials',
    loadComponent: () =>
      import('./pages/credentials/credentials.page').then(m => m.CredentialsPage),
  },
  {
    path: 'flows',
    loadComponent: () =>
      import('./pages/flows/flows.page').then(m => m.FlowsPage),
  },
  {
    path: 'workflows/:id',
    loadComponent: () =>
      import('./pages/workflow-builder/workflow-builder.page').then(m => m.WorkflowBuilderPage),
  },
  {
    path: 'logs',
    loadComponent: () =>
      import('./pages/logs/logs.page').then(m => m.LogsPage),
  },
  {
    path: 'settings',
    loadComponent: () =>
      import('./pages/settings/settings.page').then(m => m.SettingsPage),
  },
];
