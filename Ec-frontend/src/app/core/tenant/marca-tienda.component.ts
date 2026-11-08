import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { TenantService } from './tenant.service';
import { LoginService } from '../../modules/autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import { NOMBRE_PLATAFORMA } from './tenant.models';

/**
 * Nombre visible de la marca (P2-CU02 §B.3): la tienda del portal; en el panel, la empresa del
 * empleado; fuera de ambos, la plataforma. Sustituye a «FASHION STORE» escrito a mano.
 */
@Component({
  selector: 'app-marca-tienda',
  standalone: true,
  template: `{{ nombre() }}`,
  styles: [':host { display: contents; }'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MarcaTiendaComponent {
  private readonly tenant = inject(TenantService);
  private readonly login = inject(LoginService);

  readonly nombre = computed(
    () => this.tenant.tenantActual()?.nombre ?? this.empresaDeLaSesion() ?? NOMBRE_PLATAFORMA
  );

  /** Empresa del empleado con sesión (los dobles de prueba de LoginService pueden no traer la signal). */
  private empresaDeLaSesion(): string | undefined {
    const usuarioActual = this.login.usuarioActual;
    return typeof usuarioActual === 'function' ? usuarioActual()?.tenant?.nombre : undefined;
  }
}
