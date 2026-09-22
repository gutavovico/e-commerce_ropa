/**
 * Componente Principal para CU29: Visualizar indicadores empresariales.
 * Nomenclatura oficial: "Visualizar indicadores empresariales"
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
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { IndicadoresAdminService } from '../servicios/indicadores-admin.service';
import { LoginService } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import {
  PeriodoFiltro,
  PuntoSerieTemporal,
  SucursalDesempeno,
} from '../modelos/indicadores.dto';

interface PuntoGrafico {
  fecha_inicio: string;
  etiqueta_tiempo: string;
  monto_ingresos: number;
  cantidad_ordenes: number;
  x: number;
  y: number;
}

interface LineaGuiaY {
  valor: number;
  y: number;
  etiqueta: string;
}

@Component({
  selector: 'app-indicadores-admin',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './indicadores-admin.component.html',
  styleUrls: ['./indicadores-admin.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class IndicadoresAdminComponent implements OnInit {
  protected readonly servicio = inject(IndicadoresAdminService);
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
  readonly idSucursalEncargado = computed(() => this.usuario()?.id_sucursal ?? null);
  readonly nombreSucursalEncargado = computed(() => {
    const id = this.idSucursalEncargado();
    if (!id) return 'Sede asignada';
    const suc = this.sucursalesDisponibles().find((s) => s.id_sucursal === id);
    return suc ? `${suc.nombre} (${suc.ciudad})` : `Sucursal #${id}`;
  });

  // --- Estado de Filtros ---
  readonly periodoSeleccionado = signal<PeriodoFiltro>('30d');
  readonly fechaDesde = signal<string>('');
  readonly fechaHasta = signal<string>('');
  readonly idSucursalFiltro = signal<number | null>(null);
  readonly errorFechas = signal<string | null>(null);

  // --- Estado de UI y Datos ---
  readonly cargando = computed(() => this.servicio.cargando());
  readonly errorServicio = computed(() => this.servicio.error());
  readonly resumen = computed(() => this.servicio.resumen());
  readonly serieTemporal = computed(() => this.servicio.serieTemporal());
  readonly topProductos = computed(() => this.servicio.topProductos());
  readonly distribucion = computed(() => this.servicio.distribucion());
  readonly comparativa = computed(() => this.servicio.comparativa());
  readonly sucursalesDisponibles = computed(() => this.servicio.sucursales());

  // Punto activo en la grafica de serie temporal
  readonly puntoActivo = signal<PuntoGrafico | null>(null);

  // Ordenamiento de tabla comparativa de sucursales
  readonly columnaOrdenSucursal = signal<keyof SucursalDesempeno>('monto_facturado');
  readonly ordenAscendente = signal<boolean>(false);

  // Opciones predefinidas de periodo
  readonly opcionesPeriodo: Array<{ clave: PeriodoFiltro; etiqueta: string }> = [
    { clave: '7d', etiqueta: 'Ultimos 7 dias' },
    { clave: '30d', etiqueta: 'Ultimos 30 dias' },
    { clave: 'mes_actual', etiqueta: 'Mes actual' },
    { clave: 'anio_actual', etiqueta: 'Ano actual' },
    { clave: 'personalizado', etiqueta: 'Personalizado' },
  ];

  // Geometria SVG para serie temporal
  readonly svgAncho = 860;
  readonly svgAlto = 280;
  readonly svgMargen = { superior: 24, derecho: 30, inferior: 45, izquierdo: 65 };

  readonly puntosGraficoCalculados = computed<PuntoGrafico[]>(() => {
    const puntos = this.serieTemporal()?.puntos || [];
    if (puntos.length === 0) return [];

    const anchoUtil = this.svgAncho - this.svgMargen.izquierdo - this.svgMargen.derecho;
    const altoUtil = this.svgAlto - this.svgMargen.superior - this.svgMargen.inferior;

    const maxMonto = Math.max(...puntos.map((p) => p.monto_ingresos), 1);

    return puntos.map((p, index) => {
      const x =
        puntos.length === 1
          ? this.svgMargen.izquierdo + anchoUtil / 2
          : this.svgMargen.izquierdo + (index / (puntos.length - 1)) * anchoUtil;

      const factorAltura = p.monto_ingresos / maxMonto;
      const y = this.svgMargen.superior + altoUtil - factorAltura * altoUtil;

      return {
        fecha_inicio: p.fecha_inicio,
        etiqueta_tiempo: p.etiqueta_tiempo,
        monto_ingresos: p.monto_ingresos,
        cantidad_ordenes: p.cantidad_ordenes,
        x: Math.round(x * 10) / 10,
        y: Math.round(y * 10) / 10,
      };
    });
  });

  readonly lineaCurvaSvg = computed<string>(() => {
    const pts = this.puntosGraficoCalculados();
    if (pts.length === 0) return '';
    if (pts.length === 1) return `M ${pts[0].x} ${pts[0].y}`;

    return pts.reduce((acc, p, i) => `${acc} ${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`, '');
  });

  readonly areaSombreadaSvg = computed<string>(() => {
    const pts = this.puntosGraficoCalculados();
    if (pts.length === 0) return '';

    const yBase = this.svgAlto - this.svgMargen.inferior;
    const primerPunto = pts[0];
    const ultimoPunto = pts[pts.length - 1];

    let path = `M ${primerPunto.x} ${yBase} L ${primerPunto.x} ${primerPunto.y}`;
    for (let i = 1; i < pts.length; i++) {
      path += ` L ${pts[i].x} ${pts[i].y}`;
    }
    path += ` L ${ultimoPunto.x} ${yBase} Z`;
    return path;
  });

  readonly lineasGuiaY = computed<LineaGuiaY[]>(() => {
    const puntos = this.serieTemporal()?.puntos || [];
    const maxMonto = Math.max(...puntos.map((p) => p.monto_ingresos), 100);
    const altoUtil = this.svgAlto - this.svgMargen.superior - this.svgMargen.inferior;

    const divisiones = 4;
    const lineas: LineaGuiaY[] = [];

    for (let i = 0; i <= divisiones; i++) {
      const valor = (maxMonto / divisiones) * i;
      const y = this.svgMargen.superior + altoUtil - (i / divisiones) * altoUtil;
      lineas.push({
        valor,
        y: Math.round(y * 10) / 10,
        etiqueta: valor >= 1000 ? `${(valor / 1000).toFixed(1)}k` : `${Math.round(valor)}`,
      });
    }

    return lineas;
  });

  readonly maximoMontoProductos = computed<number>(() => {
    const prods = this.topProductos();
    if (prods.length === 0) return 1;
    return Math.max(...prods.map((p) => p.monto_total_generado), 1);
  });

  readonly sucursalesOrdenadas = computed<SucursalDesempeno[]>(() => {
    const items = [...this.comparativa()];
    const col = this.columnaOrdenSucursal();
    const asc = this.ordenAscendente();

    return items.sort((a, b) => {
      const valA = a[col];
      const valB = b[col];
      if (typeof valA === 'string' && typeof valB === 'string') {
        return asc ? valA.localeCompare(valB) : valB.localeCompare(valA);
      }
      return asc ? Number(valA) - Number(valB) : Number(valB) - Number(valA);
    });
  });

  readonly tieneDatosTransaccionales = computed<boolean>(() => {
    const r = this.resumen();
    return !!r && (r.total_transacciones > 0 || r.ingresos_totales > 0);
  });

  ngOnInit(): void {
    if (this.esAdmin()) {
      this.servicio.cargarSucursalesAuxiliares();
    }
    this.cargarDatos();
  }

  cargarDatos(): void {
    this.errorFechas.set(null);
    this.servicio
      .consultarDashboardConsolidado({
        periodo: this.periodoSeleccionado(),
        fecha_desde:
          this.periodoSeleccionado() === 'personalizado' ? this.fechaDesde() : null,
        fecha_hasta:
          this.periodoSeleccionado() === 'personalizado' ? this.fechaHasta() : null,
        id_sucursal: this.esAdmin() ? this.idSucursalFiltro() : null,
      })
      .subscribe({
        next: () => {
          this.cdr.markForCheck();
        },
        error: () => {
          this.cdr.markForCheck();
        },
      });
  }

  seleccionarPeriodo(periodo: PeriodoFiltro): void {
    this.periodoSeleccionado.set(periodo);
    this.errorFechas.set(null);

    if (periodo !== 'personalizado') {
      this.cargarDatos();
    }
  }

  aplicarPeriodoPersonalizado(): void {
    const desde = this.fechaDesde();
    const hasta = this.fechaHasta();

    if (!desde || !hasta) {
      this.errorFechas.set('Debe ingresar ambas fechas (inicial y final).');
      return;
    }

    if (new Date(desde) > new Date(hasta)) {
      this.errorFechas.set(
        'Rango inconsistente: la fecha inicial no puede ser posterior a la fecha final.'
      );
      return;
    }

    this.errorFechas.set(null);
    this.cargarDatos();
  }

  cambiarSucursalFiltro(event: Event): void {
    if (!this.esAdmin()) return;

    const select = event.target as HTMLSelectElement;
    const val = select.value;
    this.idSucursalFiltro.set(val === '' ? null : Number(val));
    this.cargarDatos();
  }

  activarPunto(p: PuntoGrafico | null): void {
    this.puntoActivo.set(p);
  }

  cambiarOrdenSucursales(columna: keyof SucursalDesempeno): void {
    if (this.columnaOrdenSucursal() === columna) {
      this.ordenAscendente.update((v) => !v);
    } else {
      this.columnaOrdenSucursal.set(columna);
      this.ordenAscendente.set(false);
    }
  }

  limpiarError(): void {
    this.servicio.limpiarError();
    this.errorFechas.set(null);
  }

  formatearMoneda(monto: number | null | undefined): string {
    const val = Number(monto || 0);
    return `Bs. ${val.toLocaleString('es-BO', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  }

  formatearPorcentaje(porcentaje: number | null | undefined): string {
    const val = Number(porcentaje || 0);
    const signo = val > 0 ? '+' : '';
    return `${signo}${val.toFixed(1)}%`;
  }
}
