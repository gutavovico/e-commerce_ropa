import { ApplicationConfig, isDevMode, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideServiceWorker } from '@angular/service-worker';
import { TitleStrategy, provideRouter } from '@angular/router';
import { provideHttpClient, withFetch, withInterceptors } from '@angular/common/http';

import { routes } from './app.routes';
import { authInterceptor } from './core/interceptors/auth.interceptor';
import { TituloTiendaStrategy } from './core/tenant/titulo-tienda.strategy';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(withFetch(), withInterceptors([authInterceptor])),
    { provide: TitleStrategy, useClass: TituloTiendaStrategy },
    // P2-CU14 (RF16): la aplicación y sus recursos quedan en caché para abrirse sin conexión. La API
    // no se cachea (S18): los datos sin conexión salen de IndexedDB (`core/sin-conexion`).
    provideServiceWorker('ngsw-worker.js', {
      enabled: !isDevMode(),
      registrationStrategy: 'registerWhenStable:30000',
    }),
  ]
};
