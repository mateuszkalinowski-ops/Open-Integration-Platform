import { ModuleWithProviders, NgModule } from '@angular/core';

import { PINQUARK_CONFIG, PinquarkConfig } from './services/pinquark-api.service';

@NgModule({})
export class PinquarkIntegrationsModule {
  static forRoot(config: PinquarkConfig): ModuleWithProviders<PinquarkIntegrationsModule> {
    return {
      ngModule: PinquarkIntegrationsModule,
      providers: [
        { provide: PINQUARK_CONFIG, useValue: config },
      ],
    };
  }
}
