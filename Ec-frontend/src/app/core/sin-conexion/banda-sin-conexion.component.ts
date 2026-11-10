import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';

import { RutaPortalPipe } from '../tenant/ruta-portal.pipe';
import { SinConexionService } from './sin-conexion.service';

/**
 * P2-CU14 (A4, RN42, RNF15) · Banda fija del portal: sin conexión, con la fecha de los datos guardados
 * y lo pendiente de sincronizar. Con red solo aparece si queda algo por enviar.
 */
@Component({
  selector: 'app-banda-sin-conexion',
  standalone: true,
  imports: [DatePipe, RouterLink, RutaPortalPipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (visible()) {
      <div
        role="status"
        class="sticky top-0 z-50 w-full px-4 py-2 text-xs flex flex-wrap items-center justify-center gap-x-4 gap-y-1"
        [class]="servicio.enLinea() ? 'bg-amber-50 text-amber-900 border-b border-amber-200' : 'bg-slate-900 text-white'"
      >
        @if (!servicio.enLinea()) {
          <span class="font-semibold uppercase tracking-wider">Sin conexión</span>
          @if (servicio.guardadoEn(); as fecha) {
            <span>Puede estar desactualizado · Datos del {{ fecha | date: 'dd/MM/yyyy HH:mm' }}</span>
          } @else {
            <span>No hay un catálogo guardado en este dispositivo.</span>
          }
        }
        @if (pendientes() > 0) {
          <span>{{ pendientes() }} {{ pendientes() === 1 ? 'reserva por sincronizar' : 'reservas por sincronizar' }}</span>
        }
        @if (!servicio.enLinea() && servicio.catalogo()) {
          <a [routerLink]="'/sin-conexion' | rutaPortal" class="underline font-semibold">Ver catálogo guardado</a>
        }
        <a [routerLink]="'/sincronizacion' | rutaPortal" class="underline font-semibold">Sincronización</a>
      </div>
    }
  `,
})
export class BandaSinConexionComponent {
  protected readonly servicio = inject(SinConexionService);
  protected readonly pendientes = computed(() => this.servicio.pendientes().length);
  protected readonly visible = computed(
    () => this.servicio.clave() !== null && (!this.servicio.enLinea() || this.pendientes() > 0)
  );
}
