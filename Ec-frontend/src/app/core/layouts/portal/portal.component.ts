import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { RegistroEnTiendaComponent } from '../../tenant/registro-en-tienda.component';

/**
 * P2-CU02 · Contenedor del portal `/{codigo}`. No es una pantalla: no añade navegación; las cuatro
 * raíces siguen bajo `MainLayoutComponent` y las hojas conservan su «← Volver» (Hub-and-Spoke).
 * Solo aporta el aviso «Registrarme en esta tienda».
 */
@Component({
  selector: 'app-portal',
  standalone: true,
  imports: [RouterOutlet, RegistroEnTiendaComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <app-registro-en-tienda />
    <router-outlet />
  `,
})
export class PortalComponent {}
