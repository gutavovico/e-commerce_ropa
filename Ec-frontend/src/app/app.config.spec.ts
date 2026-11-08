import { TestBed } from '@angular/core/testing';
import { Router, TitleStrategy } from '@angular/router';
import { describe, it, expect } from 'vitest';

import { appConfig } from './app.config';
import { TenantService } from './core/tenant/tenant.service';

/**
 * Arranque con la configuración real de la aplicación.
 *
 * P2-CU02: la estrategia de títulos (`TituloTiendaStrategy`) depende de `TenantService`, que depende
 * del `Router`, que a su vez necesita la estrategia de títulos. Esa dependencia circular dejaba la
 * aplicación en blanco al arrancar y ninguna prueba la veía, porque ninguna usaba `appConfig`.
 */
describe('appConfig', () => {
  it('resuelve el Router, la estrategia de títulos y TenantService sin dependencias circulares', () => {
    TestBed.configureTestingModule({ providers: [...appConfig.providers] });

    expect(() => TestBed.inject(Router)).not.toThrow();
    expect(() => TestBed.inject(TitleStrategy)).not.toThrow();
    expect(() => TestBed.inject(TenantService)).not.toThrow();
  });
});
