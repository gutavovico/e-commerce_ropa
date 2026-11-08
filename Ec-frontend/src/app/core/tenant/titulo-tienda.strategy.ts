import { Injectable, Injector, inject } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { RouterStateSnapshot, TitleStrategy } from '@angular/router';
import { TenantService } from './tenant.service';
import { NOMBRE_PLATAFORMA } from './tenant.models';

/**
 * P2-CU02: los títulos de las rutas se escribieron como «FASHION STORE | …». Dentro del portal de una
 * tienda se muestra su nombre; fuera, el de la plataforma.
 *
 * `TenantService` se obtiene al actualizar el título, no al construir la estrategia: el Router necesita
 * esta estrategia para construirse y `TenantService` necesita el Router (NG0200, dependencia circular,
 * que dejaba la aplicación en blanco al arrancar).
 */
@Injectable({ providedIn: 'root' })
export class TituloTiendaStrategy extends TitleStrategy {
  private readonly title = inject(Title);
  private readonly injector = inject(Injector);

  override updateTitle(snapshot: RouterStateSnapshot): void {
    const marca = this.injector.get(TenantService).tenantActual()?.nombre ?? NOMBRE_PLATAFORMA;
    const titulo = this.buildTitle(snapshot);
    this.title.setTitle(titulo ? titulo.replace('FASHION STORE', marca) : marca);
  }
}
