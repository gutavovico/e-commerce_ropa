/**
 * Componente de Consulta Administrativa para CU28: Consultar ventas y reservas.
 * Nomenclatura oficial: "Consultar ventas y reservas"
 */

import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { VentasReservasAdminService } from '../servicios/ventas-reservas-admin.service';
import { LoginService } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import {
  TransaccionResumenItem,
  VentaDetalleCompleto,
  ReservaDetalleCompleto,
  CanalOrigenFiltro,
  CriterioOrdenTransaccion,
  TipoOperacionFiltro,
} from '../modelos/ventas-reservas.dto';

@Component({
  selector: 'app-ventas-reservas-admin',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './ventas-reservas-admin.component.html',
  styleUrls: ['./ventas-reservas-admin.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class VentasReservasAdminComponent implements OnInit {
  protected readonly servicio = inject(VentasReservasAdminService);
  private readonly loginService = inject(LoginService);
  private readonly cdr = inject(ChangeDetectorRef);

  // --- Seguridad y RBAC ---
  readonly usuario = computed(() => this.loginService.usuarioActual());
  readonly rolUsuario = computed(() =>
    String(this.usuario()?.rol || '').toLowerCase().trim()
  );
  readonly esAdmin = computed(
    () => this.rolUsuario() === 'administrador' || this.rolUsuario() === 'admin'
  );
  readonly esEncargado = computed(
    () => this.rolUsuario() === 'encargado_sucursal'
  );

  // --- Estado Reactivo de Consulta ---
  readonly transacciones = computed(() => this.servicio.transacciones());
  readonly metricas = computed(() => this.servicio.metricas());
  readonly totalTransacciones = computed(() => this.servicio.totalTransacciones());
  readonly totalPaginas = computed(() => this.servicio.totalPaginas());
  readonly cargando = computed(() => this.servicio.cargando());
  readonly errorServicio = computed(() => this.servicio.error());
  readonly sucursalesDisponibles = computed(() => this.servicio.sucursalesDisponibles());

  // --- Filtros Reactivos ---
  readonly busquedaTexto = signal<string>('');
  readonly filtroTipoOperacion = signal<TipoOperacionFiltro>('todas');
  readonly filtroEstado = signal<string>('todos');
  readonly filtroCanalOrigen = signal<CanalOrigenFiltro>('todos');
  readonly filtroSucursal = signal<number | null>(null);
  readonly filtroFechaDesde = signal<string | null>(null);
  readonly filtroFechaHasta = signal<string | null>(null);
  readonly filtroOrden = signal<CriterioOrdenTransaccion>('creado_en_desc');
  readonly paginaActual = signal<number>(1);

  // --- Estado de Modales ---
  readonly modalDetalleAbierto = signal<boolean>(false);
  readonly tipoDetalleActual = signal<'venta' | 'reserva' | null>(null);
  readonly detalleVenta = signal<VentaDetalleCompleto | null>(null);
  readonly detalleReserva = signal<ReservaDetalleCompleto | null>(null);

  // --- Banners Contextuales (Luxury Banners) ---
  readonly errorBanner = signal<string | null>(null);

  private debounceTimer: ReturnType<typeof setTimeout> | null = null;

  ngOnInit(): void {
    this.cargarDatos();
    if (this.esAdmin()) {
      this.servicio.cargarSucursalesAuxiliares();
    }
  }

  cargarDatos(): void {
    this.servicio
      .listarTransacciones({
        q: this.busquedaTexto(),
        tipo_operacion: this.filtroTipoOperacion(),
        estado: this.filtroEstado(),
        id_sucursal: this.filtroSucursal(),
        fecha_desde: this.filtroFechaDesde(),
        fecha_hasta: this.filtroFechaHasta(),
        canal_origen: this.filtroCanalOrigen(),
        ordenar_por: this.filtroOrden(),
        pagina: this.paginaActual(),
        limite: 10,
      })
      .subscribe({
        error: (err) => {
          this.mostrarError(err.message || 'Error al cargar transacciones.');
        },
      });
  }

  onBusquedaInput(event: Event): void {
    const valor = (event.target as HTMLInputElement).value;
    this.busquedaTexto.set(valor);

    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }
    this.debounceTimer = setTimeout(() => {
      this.paginaActual.set(1);
      this.cargarDatos();
    }, 300);
  }

  onFiltroTipoOperacionChange(event: Event): void {
    const valor = (event.target as HTMLSelectElement).value as TipoOperacionFiltro;
    this.filtroTipoOperacion.set(valor);
    this.paginaActual.set(1);
    this.cargarDatos();
  }

  onFiltroEstadoChange(event: Event): void {
    const valor = (event.target as HTMLSelectElement).value;
    this.filtroEstado.set(valor);
    this.paginaActual.set(1);
    this.cargarDatos();
  }

  onFiltroCanalChange(event: Event): void {
    const valor = (event.target as HTMLSelectElement).value as CanalOrigenFiltro;
    this.filtroCanalOrigen.set(valor);
    this.paginaActual.set(1);
    this.cargarDatos();
  }

  onFiltroSucursalChange(event: Event): void {
    const valor = (event.target as HTMLSelectElement).value;
    this.filtroSucursal.set(valor ? Number(valor) : null);
    this.paginaActual.set(1);
    this.cargarDatos();
  }

  onFiltroFechaDesdeChange(event: Event): void {
    const valor = (event.target as HTMLInputElement).value;
    this.filtroFechaDesde.set(valor || null);
    this.paginaActual.set(1);
    this.cargarDatos();
  }

  onFiltroFechaHastaChange(event: Event): void {
    const valor = (event.target as HTMLInputElement).value;
    this.filtroFechaHasta.set(valor || null);
    this.paginaActual.set(1);
    this.cargarDatos();
  }

  onFiltroOrdenChange(event: Event): void {
    const valor = (event.target as HTMLSelectElement).value as CriterioOrdenTransaccion;
    this.filtroOrden.set(valor);
    this.paginaActual.set(1);
    this.cargarDatos();
  }

  resetearFiltros(): void {
    this.busquedaTexto.set('');
    this.filtroTipoOperacion.set('todas');
    this.filtroEstado.set('todos');
    this.filtroCanalOrigen.set('todos');
    this.filtroSucursal.set(null);
    this.filtroFechaDesde.set(null);
    this.filtroFechaHasta.set(null);
    this.filtroOrden.set('creado_en_desc');
    this.paginaActual.set(1);
    this.cargarDatos();
  }

  cambiarPagina(nuevaPagina: number): void {
    if (nuevaPagina < 1 || nuevaPagina > this.totalPaginas()) {
      return;
    }
    this.paginaActual.set(nuevaPagina);
    this.cargarDatos();
  }

  // --- Detalle Transaccional (Modal) ---
  verDetalle(item: TransaccionResumenItem): void {
    this.limpiarBanners();
    this.tipoDetalleActual.set(item.tipo_operacion);

    if (item.tipo_operacion === 'venta') {
      this.servicio.obtenerDetalleVenta(item.id_transaccion).subscribe({
        next: (detalle) => {
          this.detalleVenta.set(detalle);
          this.detalleReserva.set(null);
          this.modalDetalleAbierto.set(true);
          this.cdr.markForCheck();
        },
        error: (err) => {
          this.mostrarError(err.message || 'Error al cargar detalle de venta.');
        },
      });
    } else {
      this.servicio.obtenerDetalleReserva(item.id_transaccion).subscribe({
        next: (detalle) => {
          this.detalleReserva.set(detalle);
          this.detalleVenta.set(null);
          this.modalDetalleAbierto.set(true);
          this.cdr.markForCheck();
        },
        error: (err) => {
          this.mostrarError(err.message || 'Error al cargar detalle de reserva.');
        },
      });
    }
  }

  cerrarModal(): void {
    this.modalDetalleAbierto.set(false);
    this.detalleVenta.set(null);
    this.detalleReserva.set(null);
    this.tipoDetalleActual.set(null);
  }

  onOverlayClick(event: Event): void {
    if ((event.target as HTMLElement).classList.contains('modal-overlay')) {
      this.cerrarModal();
    }
  }

  onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Escape') {
      this.cerrarModal();
    }
  }

  // --- Badges Semanticos ---
  badgeClaseEstado(estado: string): string {
    const s = estado.toLowerCase();
    switch (s) {
      case 'pagada':
      case 'atendida':
      case 'confirmada':
        return 'bg-emerald-50 text-emerald-800 border-emerald-200';
      case 'pendiente':
        return 'bg-amber-50 text-amber-800 border-amber-200';
      case 'en_atencion':
        return 'bg-blue-50 text-blue-800 border-blue-200';
      case 'anulada':
      case 'cancelada':
      case 'vencida':
      case 'devuelta':
        return 'bg-rose-50 text-rose-800 border-rose-200';
      default:
        return 'bg-slate-50 text-slate-800 border-slate-200';
    }
  }

  badgeClaseTipo(tipo: string): string {
    return tipo === 'venta'
      ? 'bg-indigo-50 text-indigo-800 border-indigo-200'
      : 'bg-violet-50 text-violet-800 border-violet-200';
  }

  formatearMonto(monto: number): string {
    return new Intl.NumberFormat('es-BO', {
      style: 'currency',
      currency: 'BOB',
      minimumFractionDigits: 2,
    }).format(monto);
  }

  formatearFecha(fecha: string): string {
    if (!fecha) return '-';
    const d = new Date(fecha);
    return d.toLocaleDateString('es-BO', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  formatearEstado(estado: string): string {
    return estado
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase());
  }

  // --- Banners Contextuales ---
  mostrarError(mensaje: string): void {
    this.errorBanner.set(mensaje);
    this.cdr.markForCheck();
  }

  limpiarBanners(): void {
    this.errorBanner.set(null);
  }

  // --- Paginacion rango de paginas ---
  rangosPaginas(): number[] {
    const total = this.totalPaginas();
    const actual = this.paginaActual();
    const rango: number[] = [];

    const inicio = Math.max(1, actual - 2);
    const fin = Math.min(total, actual + 2);

    for (let i = inicio; i <= fin; i++) {
      rango.push(i);
    }
    return rango;
  }
}
