import { Pipe, PipeTransform, inject } from '@angular/core';
import { TenantService } from './tenant.service';

/**
 * Antepone `/{codigo}` a una ruta del cliente cuando se navega dentro del portal de una tienda
 * (P2-CU02). Uso: `[routerLink]="'/bolsa' | rutaPortal"` o `[routerLink]="['/productos', id] | rutaPortal"`.
 *
 * Impuro a propósito: depende de la tienda actual (signal), no solo de su entrada.
 */
@Pipe({ name: 'rutaPortal', standalone: true, pure: false })
export class RutaPortalPipe implements PipeTransform {
  private readonly tenant = inject(TenantService);

  transform(destino: string | readonly (string | number)[]): (string | number)[] {
    return this.tenant.ruta(destino);
  }
}
