import { TestBed } from '@angular/core/testing';
import { TenantService } from './tenant.service';
import { EmpresaPublica } from './tenant.models';

/** Tienda de las pruebas: datos públicos tal como los devuelve `GET /api/v1/tenants/fashionstore`. */
export const TIENDA_FASHION: EmpresaPublica = { codigo: 'fashionstore', nombre: 'FASHION STORE' };

/** Simula estar dentro del portal de una tienda (lo que hace `tenantGuard` al entrar en `/{codigo}`). */
export function entrarEnTienda(tienda: EmpresaPublica = TIENDA_FASHION): TenantService {
  const servicio = TestBed.inject(TenantService);
  servicio.tenantActual.set(tienda);
  return servicio;
}
