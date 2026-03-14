import { bootstrapApplication } from '@angular/platform-browser';
import { provideRouter } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideHttpClient } from '@angular/common/http';
import { provideZoneChangeDetection } from '@angular/core';

import { AppComponent } from './app/app.component';
import { routes } from './app/app.routes';
import { PINQUARK_CONFIG } from '@pinquark/integrations';

declare global {
  interface Window {
    __PINQUARK_CONFIG__?: { apiUrl: string; apiKey: string };
  }
}

const runtimeConfig = window.__PINQUARK_CONFIG__ ?? { apiUrl: '', apiKey: '' };
const savedKey = localStorage.getItem('pinquark_demo_api_key');
const effectiveApiKey = savedKey || runtimeConfig.apiKey;

bootstrapApplication(AppComponent, {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideAnimationsAsync(),
    provideHttpClient(),
    { provide: PINQUARK_CONFIG, useValue: {
      apiUrl: runtimeConfig.apiUrl,
      apiKey: effectiveApiKey,
    } },
  ],
}).catch(err => console.error(err));
