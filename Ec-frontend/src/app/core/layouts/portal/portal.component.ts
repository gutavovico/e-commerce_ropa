import { ChangeDetectionStrategy, Component, effect, inject, untracked } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { RegistroEnTiendaComponent } from '../../tenant/registro-en-tienda.component';
import { BandaSinConexionComponent } from '../../sin-conexion/banda-sin-conexion.component';
import { SinConexionService } from '../../sin-conexion/sin-conexion.service';
import { TenantService } from '../../tenant/tenant.service';
import { LoginService } from '../../../modules/autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';

/**
 * P2-CU02 · Contenedor del portal `/{codigo}`. No es una pantalla: no añade navegación; las cuatro
 * raíces siguen bajo `MainLayoutComponent` y las hojas conservan su «← Volver» (Hub-and-Spoke).
 * Aporta el aviso «Registrarme en esta tienda» y, desde P2-CU14, la banda de estado sin conexión y
 * la preparación de la tienda para usarla sin red (dispositivo, catálogo y sincronización).
 */
@Component({
  selector: 'app-portal',
  standalone: true,
  imports: [RouterOutlet, RegistroEnTiendaComponent, BandaSinConexionComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <app-banda-sin-conexion />
    <app-registro-en-tienda />
    <router-outlet />
  `,
})
export class PortalComponent {
  private readonly tenant = inject(TenantService);
  private readonly login = inject(LoginService);
  private readonly sinConexion = inject(SinConexionService);

  constructor() {
    effect(() => {
      const tienda = this.tenant.tenantActual();
      const usuario = this.login.usuarioActual();
      const registrado = this.tenant.estaRegistradoEnTienda();
      untracked(() => {
        if (tienda && usuario?.rol === 'cliente') {
          void this.sinConexion.prepararTienda(tienda.codigo, usuario.id_usuario, registrado);
        } else if (!usuario && this.sinConexion.clave()) {
          // Cerró sesión: se borra el catálogo, nunca las operaciones pendientes (RNF03).
          void this.sinConexion.cerrarSesion();
        }
      });
    });
  }
}
