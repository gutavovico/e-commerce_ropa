import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { DatePipe, Location } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { ImportePipe } from '../../../../core/tenant/moneda';
import { RutaPortalPipe } from '../../../../core/tenant/ruta-portal.pipe';
import { MarcaTiendaComponent } from '../../../../core/tenant/marca-tienda.component';
import { SinConexionService } from '../../../../core/sin-conexion/sin-conexion.service';
import { franjasDeCita } from '../../../../core/sin-conexion/franjas-cita';
import { ProductoLocalDto, VarianteLocalDto } from '../../../../core/sin-conexion/sin-conexion.models';

/**
 * P2-CU14 (A4) y P2-CU15 (A1) · Catálogo guardado en el dispositivo: búsqueda, detalle con existencias
 * por sucursal y reserva sin conexión. Es una hoja del portal (`/{codigo}/sin-conexion`).
 *
 * Las existencias son las de la última descarga: el servidor las vuelve a validar al sincronizar.
 */
@Component({
  selector: 'app-catalogo-local',
  standalone: true,
  imports: [DatePipe, FormsModule, RouterLink, ImportePipe, RutaPortalPipe, MarcaTiendaComponent],
  templateUrl: './catalogo-local.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CatalogoLocalComponent {
  private readonly location = inject(Location);
  protected readonly servicio = inject(SinConexionService);

  protected readonly texto = signal('');
  protected readonly categoria = signal<number | null>(null);
  protected readonly seleccionado = signal<ProductoLocalDto | null>(null);
  protected readonly variante = signal<VarianteLocalDto | null>(null);
  protected readonly sucursal = signal<number | null>(null);
  protected readonly franja = signal<string | null>(null);
  protected readonly cantidad = signal(1);
  protected readonly guardando = signal(false);
  protected readonly error = signal<string | null>(null);
  protected readonly reservada = signal<string | null>(null);

  protected readonly catalogo = this.servicio.catalogo;

  protected readonly productos = computed(() => {
    const catalogo = this.catalogo();
    if (!catalogo) return [];
    const texto = this.texto().trim().toLowerCase();
    const categoria = this.categoria();
    return catalogo.productos.filter(
      (p) =>
        (categoria === null || p.id_categoria === categoria) &&
        (!texto || p.nombre.toLowerCase().includes(texto) || (p.descripcion ?? '').toLowerCase().includes(texto))
    );
  });

  /** Existencias de la variante elegida en cada sucursal activa de la tienda. */
  protected readonly existencias = computed(() => {
    const catalogo = this.catalogo();
    const variante = this.variante();
    if (!catalogo || !variante) return [];
    return catalogo.sucursales.map((s) => ({
      ...s,
      disponible:
        catalogo.existencias.find((e) => e.id_variante === variante.id_variante && e.id_sucursal === s.id_sucursal)
          ?.cantidad_disponible ?? 0,
    }));
  });

  protected readonly disponibleEnSucursal = computed(
    () => this.existencias().find((e) => e.id_sucursal === this.sucursal())?.disponible ?? 0
  );
  protected readonly cantidades = computed(() =>
    Array.from({ length: Math.min(5, this.disponibleEnSucursal()) }, (_, i) => i + 1)
  );
  protected readonly franjas = computed(() => franjasDeCita(new Date(), this.servicio.horasVencimiento()));

  protected nombreTalla(id: number): string {
    return this.catalogo()?.tallas.find((t) => t.id_talla === id)?.codigo ?? '—';
  }

  protected nombreColor(id: number): string {
    return this.catalogo()?.colores.find((c) => c.id_color === id)?.nombre ?? '—';
  }

  protected elegir(producto: ProductoLocalDto): void {
    this.seleccionado.set(producto);
    this.variante.set(producto.variantes[0] ?? null);
    this.sucursal.set(null);
    this.franja.set(null);
    this.cantidad.set(1);
    this.error.set(null);
    this.reservada.set(null);
  }

  protected cerrarDetalle(): void {
    this.seleccionado.set(null);
  }

  protected elegirVariante(id: number): void {
    this.variante.set(this.seleccionado()?.variantes.find((v) => v.id_variante === Number(id)) ?? null);
    this.sucursal.set(null);
  }

  protected async reservar(): Promise<void> {
    const producto = this.seleccionado();
    const variante = this.variante();
    const idSucursal = this.sucursal();
    const franja = this.franja();
    if (!producto || !variante || idSucursal === null || !franja) {
      this.error.set('Elige la talla y color, la sucursal y la hora de tu visita.');
      return;
    }
    const sucursal = this.existencias().find((s) => s.id_sucursal === idSucursal);
    this.guardando.set(true);
    this.error.set(null);
    try {
      const operacion = await this.servicio.reservarSinConexion({
        idSucursal,
        fechaHoraAtencion: franja,
        items: [{ id_variante: variante.id_variante, cantidad: this.cantidad() }],
        resumen: {
          producto: producto.nombre,
          variante: `${this.nombreTalla(variante.id_talla)} · ${this.nombreColor(variante.id_color)}`,
          sucursal: sucursal?.nombre ?? '',
        },
      });
      this.reservada.set(operacion.codigoProvisional);
    } catch (error) {
      this.error.set(error instanceof Error ? error.message : 'No se pudo guardar la reserva.');
    } finally {
      this.guardando.set(false);
    }
  }

  protected volver(): void {
    this.location.back();
  }
}
