/**
 * Componente Principal para CU30: Consultar bitacora.
 * Nomenclatura oficial: "Consultar bitacora"
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
import { BitacoraAdminService } from '../servicios/bitacora-admin.service';
import { LoginService } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import {
  BitacoraFiltros,
  CriterioOrdenBitacora,
  SeveridadBitacora,
} from '../modelos/bitacora.dto';

@Component({
  selector: 'app-bitacora-admin',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './bitacora-admin.component.html',
  styleUrls: ['./bitacora-admin.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BitacoraAdminComponent implements OnInit {
  protected readonly servicio = inject(BitacoraAdminService);
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

  // --- Estado Reactivo de Consulta y Filtros ---
  readonly eventos = computed(() => this.servicio.eventos());
  readonly metricas = computed(() => this.servicio.metricas());
  readonly totalEventos = computed(() => this.servicio.totalEventos());
  readonly totalPaginas = computed(() => this.servicio.totalPaginas());
  readonly paginaActual = computed(() => this.servicio.paginaActual());
  readonly cargando = computed(() => this.servicio.cargando());
  readonly errorServicio = computed(() => this.servicio.error());

  readonly eventoSeleccionado = computed(() => this.servicio.eventoSeleccionado());
  readonly cargandoDetalle = computed(() => this.servicio.cargandoDetalle());
  readonly errorDetalle = computed(() => this.servicio.errorDetalle());

  // Modelos de filtros
  readonly fechaInicio = signal<string>('');
  readonly fechaFin = signal<string>('');
  readonly severidadSeleccionada = signal<string>('');
  readonly tablaModuloSeleccionada = signal<string>('');
  readonly accionSeleccionada = signal<string>('');
  readonly terminoBusqueda = signal<string>('');
  readonly ordenSeleccionado = signal<CriterioOrdenBitacora>('creado_en_desc');
  readonly limiteSeleccionado = signal<number>(20);

  private debounceTimer: ReturnType<typeof setTimeout> | null = null;

  ngOnInit(): void {
    this.cargarDatos();
  }

  cargarDatos(): void {
    const filtros: BitacoraFiltros = {
      fecha_inicio: this.fechaInicio() || null,
      fecha_fin: this.fechaFin() || null,
      severidad: (this.severidadSeleccionada() as SeveridadBitacora) || null,
      tabla_modulo: this.tablaModuloSeleccionada() || null,
      accion: this.accionSeleccionada() || null,
      q: this.terminoBusqueda() || null,
      ordenar_por: this.ordenSeleccionado(),
      pagina: this.paginaActual(),
      limite: this.limiteSeleccionado(),
    };

    this.servicio.listar(filtros).subscribe({
      next: () => {
        this.cdr.markForCheck();
      },
      error: () => {
        this.cdr.markForCheck();
      },
    });
  }

  onFiltroTextoChange(valor: string): void {
    this.terminoBusqueda.set(valor);
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }
    this.debounceTimer = setTimeout(() => {
      this.servicio.paginaActual.set(1);
      this.cargarDatos();
    }, 300);
  }

  onFiltroSelectChange(): void {
    this.servicio.paginaActual.set(1);
    this.cargarDatos();
  }

  limpiarFiltros(): void {
    this.fechaInicio.set('');
    this.fechaFin.set('');
    this.severidadSeleccionada.set('');
    this.tablaModuloSeleccionada.set('');
    this.accionSeleccionada.set('');
    this.terminoBusqueda.set('');
    this.ordenSeleccionado.set('creado_en_desc');
    this.servicio.paginaActual.set(1);
    this.cargarDatos();
  }

  cambiarPagina(nuevaPagina: number): void {
    if (nuevaPagina >= 1 && nuevaPagina <= this.totalPaginas()) {
      this.servicio.paginaActual.set(nuevaPagina);
      this.cargarDatos();
    }
  }

  abrirModalPayload(id_bitacora: number): void {
    this.servicio.obtenerDetalle(id_bitacora).subscribe({
      next: () => {
        this.cdr.markForCheck();
      },
      error: () => {
        this.cdr.markForCheck();
      },
    });
  }

  cerrarModalPayload(): void {
    this.servicio.cerrarModalDetalle();
    this.cdr.markForCheck();
  }

  formatearJson(obj: unknown): string {
    if (!obj) {
      return 'Sin datos registrados.';
    }
    try {
      return JSON.stringify(obj, null, 2);
    } catch {
      return String(obj);
    }
  }

  getBadgeSeveridad(severidad: string): string {
    switch (severidad.toUpperCase()) {
      case 'CRITICAL':
        return 'bg-red-100 text-red-800 border-red-300 font-bold';
      case 'ERROR':
        return 'bg-rose-50 text-rose-700 border-rose-200 font-semibold';
      case 'WARN':
        return 'bg-amber-50 text-amber-800 border-amber-200 font-semibold';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200 font-medium';
    }
  }
}
