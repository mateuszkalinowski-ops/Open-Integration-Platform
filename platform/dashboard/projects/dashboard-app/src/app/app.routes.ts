import { Routes } from '@angular/router';
import { demoAuthGuard } from './guards/demo-auth.guard';

export const routes: Routes = [
  {
    path: 'gate',
    loadComponent: () =>
      import('./pages/gate/gate.page').then(m => m.GatePage),
  },
  { path: '', redirectTo: 'connectors', pathMatch: 'full' },
  {
    path: 'catalog',
    canActivate: [demoAuthGuard],
    loadComponent: () =>
      import('./pages/connectors/connectors.page').then(m => m.ConnectorsPage),
  },
  {
    path: 'connectors',
    canActivate: [demoAuthGuard],
    loadComponent: () =>
      import('./pages/connectors/connectors.page').then(m => m.ConnectorsPage),
  },
  {
    path: 'connectors/:category/:name',
    canActivate: [demoAuthGuard],
    loadComponent: () =>
      import('./pages/connectors/connectors.page').then(m => m.ConnectorsPage),
  },
  {
    path: 'credentials',
    canActivate: [demoAuthGuard],
    loadComponent: () =>
      import('./pages/credentials/credentials.page').then(m => m.CredentialsPage),
  },
  {
    path: 'flows',
    canActivate: [demoAuthGuard],
    loadComponent: () =>
      import('./pages/flows/flows.page').then(m => m.FlowsPage),
  },
  {
    path: 'workflows/:id',
    canActivate: [demoAuthGuard],
    loadComponent: () =>
      import('./pages/workflow-builder/workflow-builder.page').then(m => m.WorkflowBuilderPage),
  },
  {
    path: 'logs',
    canActivate: [demoAuthGuard],
    loadComponent: () =>
      import('./pages/logs/logs.page').then(m => m.LogsPage),
  },
  {
    path: 'verification',
    canActivate: [demoAuthGuard],
    loadComponent: () =>
      import('./pages/verification/verification.page').then(m => m.VerificationPage),
  },
  {
    path: 'settings',
    canActivate: [demoAuthGuard],
    loadComponent: () =>
      import('./pages/settings/settings.page').then(m => m.SettingsPage),
  },
];
