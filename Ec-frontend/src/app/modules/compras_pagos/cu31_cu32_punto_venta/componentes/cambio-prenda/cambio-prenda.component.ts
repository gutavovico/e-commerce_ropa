import { ChangeDetectionStrategy, Component, DestroyRef, computed, inject, input, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';

import { ImportePipe } from '../../../../../core/tenant/moneda';
import { MarcaTiendaComponent } from '../../../../../core/tenant/marca-tienda.component';
import { Cambio, CambioIn, CambioPrevio, VentaCambiable } from '../../modelos/cambio-prenda.dto';
import { MetodoPagoCaja, VariantePos } from '../../modelos/punto-venta.dto';
import { CambioPrendaService } from '../../servicios/cambio-prenda.service';
import { PuntoVentaService } from '../../servicios/punto-venta.service';

const METODOS: { valor: MetodoPagoCaja; nombre: string }[] = [
  { valor: 'efectivo', nombre: 'Efectivo' },
  { valor: 'tarjeta_debito', nombre: 'Débito' },
  { valor: 'tarjeta_credito', nombre: 'Crédito' },
  { valor: 'qr', nombre: 'QR' },
  { valor: 'transferencia', nombre: 'Transferencia' },
];

/**
 * P2-CU18 · Pestaña «Cambios» de la caja: busca la venta pagada por su comprobante, elige qué se
 * devuelve y qué se lleva el cliente, cobra o devuelve la diferencia y emite el ticket del cambio.
 * Todos los importes salen del servidor (`previsualizar`, `registrar`).
 */
@Component({
  selector: 'app-cambio-prenda',
  standalone: true,
  imports: [DatePipe, ImportePipe, MarcaTiendaComponent],
  templateUrl: './cambio-prenda.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CambioPrendaComponent {
  private readonly servicio = inject(CambioPrendaService);
  private readonly caja = inject(PuntoVentaService);

  /** Sucursal elegida por el administrador (null: la del cajero o encargado). */
  readonly idSucursal = input<number | null>(null);
  /** AC-13: sin conexión no se registra el cambio. */
  readonly enLinea = input<boolean>(true);

  protected readonly metodos = METODOS;
  protected readonly comprobante = signal('');
  protected readonly venta = signal<VentaCambiable | null>(null);
  protected readonly devolver = signal<Record<number, number>>({});
  protected readonly nuevas = signal<{ variante: VariantePos; cantidad: number }[]>([]);
  protected readonly textoPrenda = signal('');
  protected readonly resultados = signal<VariantePos[]>([]);
  protected readonly previo = signal<CambioPrevio | null>(null);
  protected readonly metodo = signal<MetodoPagoCaja>('efectivo');
  protected readonly monto = signal('');
  protected readonly referencia = signal('');
  protected readonly cargando = signal(false);
  protected readonly error = signal<string | null>(null);
  protected readonly cambio = signal<Cambio | null>(null);

  protected readonly diferencia = computed(() => Number(this.previo()?.diferencia ?? '0'));
  protected readonly hayDevueltas = computed(() => Object.values(this.devolver()).some((c) => c > 0));
  protected readonly puedeRegistrar = computed(
    () => this.enLinea() && !this.cargando() && this.previo() !== null && this.hayDevueltas() && this.nuevas().length > 0
  );

  private espera: ReturnType<typeof setTimeout> | null = null;

  constructor() {
    inject(DestroyRef).onDestroy(() => this.espera && clearTimeout(this.espera));
  }

  protected buscarVenta(): void {
    const texto = this.comprobante().trim();
    if (!texto) return;
    this.reiniciar(false);
    this.cargando.set(true);
    this.servicio.ventaCambiable(texto, this.idSucursal()).subscribe({
      next: (venta) => {
        this.venta.set(venta);
        this.cargando.set(false);
      },
      error: (e: HttpErrorResponse) => this.fallo(e),
    });
  }

  protected cambiarDevolucion(idDetalle: number, delta: number, maximo: number): void {
    const actual = this.devolver()[idDetalle] ?? 0;
    const siguiente = Math.max(0, Math.min(maximo, actual + delta));
    this.devolver.set({ ...this.devolver(), [idDetalle]: siguiente });
    this.previsualizar();
  }

  protected buscarPrendas(texto: string): void {
    this.textoPrenda.set(texto);
    if (this.espera) clearTimeout(this.espera);
    if (texto.trim().length < 2) {
      this.resultados.set([]);
      return;
    }
    this.espera = setTimeout(() => {
      this.caja.buscarVariantes(texto, this.idSucursal()).subscribe({
        next: (r) => this.resultados.set(r),
        error: () => this.resultados.set([]),
      });
    }, 300);
  }

  protected agregarNueva(variante: VariantePos): void {
    if (variante.disponible_en_sucursal <= 0) {
      this.error.set(`No hay existencias de ${variante.nombre_producto} (${variante.talla_codigo}) en esta sucursal.`);
      return;
    }
    const lista = [...this.nuevas()];
    const existente = lista.find((n) => n.variante.id_variante === variante.id_variante);
    if (existente) existente.cantidad += 1;
    else lista.push({ variante, cantidad: 1 });
    this.nuevas.set(lista);
    this.resultados.set([]);
    this.textoPrenda.set('');
    this.previsualizar();
  }

  protected quitarNueva(idVariante: number): void {
    this.nuevas.set(this.nuevas().filter((n) => n.variante.id_variante !== idVariante));
    this.previsualizar();
  }

  private cuerpo(conCobro: boolean): CambioIn | null {
    const venta = this.venta();
    if (!venta) return null;
    const devueltas = Object.entries(this.devolver())
      .filter(([, c]) => c > 0)
      .map(([id, cantidad]) => ({ id_venta_detalle: Number(id), cantidad }));
    const cuerpo: CambioIn = {
      id_venta: venta.id_venta,
      id_sucursal: this.idSucursal(),
      devueltas,
      nuevas: this.nuevas().map((n) => ({ id_variante: n.variante.id_variante, cantidad: n.cantidad })),
    };
    if (conCobro && this.diferencia() > 0) {
      const efectivo = this.metodo() === 'efectivo';
      cuerpo.cobro = {
        metodo_pago: this.metodo(),
        monto_recibido: efectivo ? this.monto().trim().replace(',', '.') || null : null,
        referencia: efectivo ? null : this.referencia().trim() || null,
      };
    }
    return cuerpo;
  }

  /** AC-6: valores y diferencia siempre del servidor. */
  private previsualizar(): void {
    const cuerpo = this.cuerpo(false);
    this.error.set(null);
    if (!cuerpo || cuerpo.devueltas.length === 0 || cuerpo.nuevas.length === 0) {
      this.previo.set(null);
      return;
    }
    this.servicio.previsualizar(cuerpo).subscribe({
      next: (p) => this.previo.set(p),
      error: (e: HttpErrorResponse) => {
        this.previo.set(null);
        this.error.set(mensajeDe(e));
      },
    });
  }

  protected registrar(): void {
    const cuerpo = this.cuerpo(true);
    if (!cuerpo || !this.puedeRegistrar()) return;
    this.cargando.set(true);
    this.error.set(null);
    this.servicio.registrar(cuerpo).subscribe({
      next: (cambio) => {
        this.cambio.set(cambio);
        this.cargando.set(false);
      },
      error: (e: HttpErrorResponse) => this.fallo(e),
    });
  }

  protected imprimir(): void {
    window.print();
  }

  protected reiniciar(limpiarComprobante = true): void {
    if (limpiarComprobante) this.comprobante.set('');
    this.venta.set(null);
    this.devolver.set({});
    this.nuevas.set([]);
    this.resultados.set([]);
    this.previo.set(null);
    this.monto.set('');
    this.referencia.set('');
    this.cambio.set(null);
    this.error.set(null);
  }

  private fallo(e: HttpErrorResponse): void {
    this.cargando.set(false);
    this.error.set(mensajeDe(e));
  }
}

function mensajeDe(e: HttpErrorResponse): string {
  if (e.status === 0) return 'Sin conexión con el servidor.';
  const detalle = e.error?.detail;
  return typeof detalle === 'string' ? detalle : 'No se pudo completar el cambio. Inténtalo de nuevo.';
}
