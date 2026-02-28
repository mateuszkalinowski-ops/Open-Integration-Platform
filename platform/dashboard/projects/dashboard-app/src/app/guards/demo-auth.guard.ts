import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { PINQUARK_CONFIG } from '@pinquark/integrations';

export const demoAuthGuard: CanActivateFn = () => {
  const config = inject(PINQUARK_CONFIG);
  const router = inject(Router);

  if (config.apiKey) {
    return true;
  }

  return router.createUrlTree(['/gate']);
};
