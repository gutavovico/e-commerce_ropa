/**
 * Componente de Gestion Administrativa para CU24: Gestionar temporadas y colecciones.
 * Nomenclatura oficial: "Gestionar temporadas y colecciones"
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
import {
  AbstractControl,
  NonNullableFormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  ValidatorFn,
  Validators,
} from '@angular/forms';
import { RouterLink } from '@angular/router';
import { TemporadasColeccionesAdminService } from '../servicios/temporadas-colecciones-admin.service';
import { LoginService } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import {
  ColeccionActualizarDto,
  ColeccionCrearDto,
  ColeccionItem,
  PestanaGestion,
  TemporadaActualizarDto,
  TemporadaCrearDto,
  TemporadaItem,
} from '../modelos/temporadas-colecciones.dto';

export const validadorRangoFechas: ValidatorFn = (
  control: AbstractControl
): ValidationErrors | null => {
  const fechaInicio = control.get('fecha_inicio')?.value;
  const fechaFin = control.get('fecha_fin')?.value;

  if (fechaInicio && fechaFin) {
    const dInicio = new Date(fechaInicio);
    const dFin = new Date(fechaFin);
    if (dFin <= dInicio) {
      return {
        fechasInvalidas:
          'La fecha de finalizacion debe ser estrictamente posterior a la fecha de inicio.',
      };
    }
  }
  return null;
};

@Component({
  selector: 'app-temporadas-colecciones-admin',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './temporadas-colecciones-admin.component.html',
  styleUrls: ['./temporadas-colecciones-admin.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TemporadasColeccionesAdminComponent implements OnInit {
  protected readonly servicio = inject(TemporadasColeccionesAdminService);
  private readonly loginService = inject(LoginService);
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly cdr = inject(ChangeDetectorRef);

  // --- Seguridad y RBAC ---
  readonly usuario = computed(() => this.loginService.usuarioActual());
  readonly rolUsuario = computed(() =>
    String(this.usuario()?.rol || '').toLowerCase().trim()
  );
  readonly esAdmin = computed(() => this.rolUsuario() === 'administrador');
  readonly esEncargado = computed(
    () => this.rolUsuario() === 'encargado_sucursal'
  );

  // --- Estado de Pestanas y Filtros ---
  readonly pestanaActiva = computed(() => this.servicio.pestanaActiva());

  readonly busquedaTemporada = signal<string>('');
  readonly filtroAnioTemporada = signal<number | null>(null);
  readonly filtroEstadoTemporada = signal<'todos' | 'activas' | 'inactivas'>('todos');
  readonly filtroOrdenTemporada = signal<string>('anio_desc');
  readonly paginaTemporada = signal<number>(1);
  readonly limiteTemporada = signal<number>(10);

  readonly busquedaColeccion = signal<string>('');
  readonly filtroTemporadaColeccion = signal<number | null>(null);
  readonly filtroEstadoColeccion = signal<'todos' | 'activas' | 'inactivas'>('todos');
  readonly paginaColeccion = signal<number>(1);
  readonly limiteColeccion = signal<number>(10);

  // --- Estado de Modales ---
  readonly modalTemporadaAbierto = signal<boolean>(false);
  readonly modoEdicionTemporada = signal<boolean>(false);
  readonly temporadaEnEdicion = signal<TemporadaItem | null>(null);

  readonly modalColeccionAbierto = signal<boolean>(false);
  readonly modoEdicionColeccion = signal<boolean>(false);
  readonly coleccionEnEdicion = signal<ColeccionItem | null>(null);

  readonly modalConfirmarEstadoAbierto = signal<boolean>(false);
  readonly elementoParaConmutar = signal<{
    tipo: 'temporada' | 'coleccion';
    id: number;
    nombre: string;
    estado_activo: boolean;
  } | null>(null);

  // --- Banners Contextuales ---
  readonly errorBanner = signal<string | null>(null);
  readonly mensajeExitoBanner = signal<string | null>(null);

  private debounceTemporadaTimer: any = null;
  private debounceColeccionTimer: any = null;

  // Lista de anios disponibles para el selector
  readonly aniosDisponibles = [2027, 2026, 2025, 2024, 2023, 2022, 2021, 2020];

  // Tipos de temporada comercial
  readonly tiposTemporada = [
    { valor: 'primavera_verano', etiqueta: 'Primavera - Verano' },
    { valor: 'otono_invierno', etiqueta: 'Otono - Invierno' },
    { valor: 'resort', etiqueta: 'Resort / Crucero' },
    { valor: 'capsula_especial', etiqueta: 'Capsula Especial' },
    { valor: 'atemporal', etiqueta: 'Atemporal / Permanente' },
  ];

  // --- Formulario Reactivo: Temporada ---
  readonly formTemporada = this.fb.group(
    {
      nombre: ['', [Validators.required, Validators.minLength(3)]],
      tipo: [''],
      anio: [2026, [Validators.required, Validators.min(2020), Validators.max(2100)]],
      fecha_inicio: ['', [Validators.required]],
      fecha_fin: ['', [Validators.required]],
      estado_activo: [true],
    },
    { validators: [validadorRangoFechas] }
  );

  // --- Formulario Reactivo: Coleccion ---
  readonly formColeccion = this.fb.group({
    id_temporada: [null as number | null, [Validators.required]],
    nombre: ['', [Validators.required, Validators.minLength(3)]],
    descripcion: [''],
    id_proveedor: [null as number | null],
    estado_activo: [true],
  });

  ngOnInit(): void {
    this.cargarDatosPestanaActual();
    this.servicio.cargarTemporadasActivasParaSelector().subscribe();
  }

  cambiarPestana(pestana: PestanaGestion): void {
    this.servicio.cambiarPestana(pestana);
    this.limpiarBanners();
    this.cargarDatosPestanaActual();
  }

  cargarDatosPestanaActual(): void {
    if (this.pestanaActiva() === 'temporadas') {
      this.cargarTemporadas();
    } else {
      this.cargarColecciones();
    }
  }

  limpiarBanners(): void {
    this.errorBanner.set(null);
    this.mensajeExitoBanner.set(null);
    this.servicio.limpiarMensajes();
  }

  // ==========================================================================
  // GESTION DE TEMPORADAS
  // ==========================================================================

  cargarTemporadas(resetPagina: boolean = false): void {
    if (resetPagina) {
      this.paginaTemporada.set(1);
    }
    this.servicio
      .cargarTemporadas({
        q: this.busquedaTemporada().trim() || undefined,
        anio: this.filtroAnioTemporada() || undefined,
        estado_activo: this.filtroEstadoTemporada(),
        ordenar_por: this.filtroOrdenTemporada() as any,
        pagina: this.paginaTemporada(),
        limite: this.limiteTemporada(),
      })
      .subscribe({
        error: (err) => {
          this.errorBanner.set(this.servicio.error());
          this.cdr.markForCheck();
        },
      });
  }

  onBusquedaTemporada(evento: Event): void {
    const valor = (evento.target as HTMLInputElement).value;
    this.busquedaTemporada.set(valor);

    if (this.debounceTemporadaTimer) {
      clearTimeout(this.debounceTemporadaTimer);
    }
    this.debounceTemporadaTimer = setTimeout(() => {
      this.cargarTemporadas(true);
    }, 300);
  }

  onFiltroAnioTemporada(evento: Event): void {
    const val = (evento.target as HTMLSelectElement).value;
    this.filtroAnioTemporada.set(val ? Number(val) : null);
    this.cargarTemporadas(true);
  }

  onFiltroEstadoTemporada(evento: Event): void {
    const val = (evento.target as HTMLSelectElement).value as
      | 'todos'
      | 'activas'
      | 'inactivas';
    this.filtroEstadoTemporada.set(val);
    this.cargarTemporadas(true);
  }

  onFiltroOrdenTemporada(evento: Event): void {
    const val = (evento.target as HTMLSelectElement).value;
    this.filtroOrdenTemporada.set(val);
    this.cargarTemporadas(true);
  }

  cambiarPaginaTemporada(nuevaPagina: number): void {
    if (
      nuevaPagina >= 1 &&
      nuevaPagina <= this.servicio.totalPaginasTemporadas()
    ) {
      this.paginaTemporada.set(nuevaPagina);
      this.cargarTemporadas();
    }
  }

  abrirModalCrearTemporada(): void {
    if (!this.esAdmin()) return;
    this.limpiarBanners();
    this.modoEdicionTemporada.set(false);
    this.temporadaEnEdicion.set(null);
    this.formTemporada.reset({
      nombre: '',
      tipo: '',
      anio: new Date().getFullYear(),
      fecha_inicio: '',
      fecha_fin: '',
      estado_activo: true,
    });
    this.modalTemporadaAbierto.set(true);
  }

  abrirModalEditarTemporada(item: TemporadaItem): void {
    if (!this.esAdmin()) return;
    this.limpiarBanners();
    this.modoEdicionTemporada.set(true);
    this.temporadaEnEdicion.set(item);
    this.formTemporada.reset({
      nombre: item.nombre,
      tipo: item.tipo || '',
      anio: item.anio,
      fecha_inicio: item.fecha_inicio,
      fecha_fin: item.fecha_fin,
      estado_activo: item.estado_activo,
    });
    this.modalTemporadaAbierto.set(true);
  }

  guardarTemporada(): void {
    if (this.formTemporada.invalid || !this.esAdmin()) {
      this.formTemporada.markAllAsTouched();
      return;
    }

    const val = this.formTemporada.getRawValue();

    if (this.modoEdicionTemporada() && this.temporadaEnEdicion()) {
      const id = this.temporadaEnEdicion()!.id_temporada;
      const payload: TemporadaActualizarDto = {
        nombre: val.nombre.trim(),
        tipo: val.tipo ? val.tipo : null,
        anio: Number(val.anio),
        fecha_inicio: val.fecha_inicio,
        fecha_fin: val.fecha_fin,
      };

      this.servicio.actualizarTemporada(id, payload).subscribe({
        next: () => {
          this.mensajeExitoBanner.set(this.servicio.mensajeExito());
          this.modalTemporadaAbierto.set(false);
          this.servicio.cargarTemporadasActivasParaSelector().subscribe();
          this.cargarTemporadas();
          this.cdr.markForCheck();
        },
        error: () => {
          this.errorBanner.set(this.servicio.error());
          this.cdr.markForCheck();
        },
      });
    } else {
      const payload: TemporadaCrearDto = {
        nombre: val.nombre.trim(),
        tipo: val.tipo ? val.tipo : null,
        anio: Number(val.anio),
        fecha_inicio: val.fecha_inicio,
        fecha_fin: val.fecha_fin,
        estado_activo: val.estado_activo,
      };

      this.servicio.crearTemporada(payload).subscribe({
        next: () => {
          this.mensajeExitoBanner.set(this.servicio.mensajeExito());
          this.modalTemporadaAbierto.set(false);
          this.servicio.cargarTemporadasActivasParaSelector().subscribe();
          this.cargarTemporadas(true);
          this.cdr.markForCheck();
        },
        error: () => {
          this.errorBanner.set(this.servicio.error());
          this.cdr.markForCheck();
        },
      });
    }
  }

  // ==========================================================================
  // GESTION DE COLECCIONES
  // ==========================================================================

  cargarColecciones(resetPagina: boolean = false): void {
    if (resetPagina) {
      this.paginaColeccion.set(1);
    }
    this.servicio
      .cargarColecciones({
        q: this.busquedaColeccion().trim() || undefined,
        id_temporada: this.filtroTemporadaColeccion() || undefined,
        estado_activo: this.filtroEstadoColeccion(),
        pagina: this.paginaColeccion(),
        limite: this.limiteColeccion(),
      })
      .subscribe({
        error: (err) => {
          this.errorBanner.set(this.servicio.error());
          this.cdr.markForCheck();
        },
      });
  }

  onBusquedaColeccion(evento: Event): void {
    const valor = (evento.target as HTMLInputElement).value;
    this.busquedaColeccion.set(valor);

    if (this.debounceColeccionTimer) {
      clearTimeout(this.debounceColeccionTimer);
    }
    this.debounceColeccionTimer = setTimeout(() => {
      this.cargarColecciones(true);
    }, 300);
  }

  onFiltroTemporadaColeccion(evento: Event): void {
    const val = (evento.target as HTMLSelectElement).value;
    this.filtroTemporadaColeccion.set(val ? Number(val) : null);
    this.cargarColecciones(true);
  }

  onFiltroEstadoColeccion(evento: Event): void {
    const val = (evento.target as HTMLSelectElement).value as
      | 'todos'
      | 'activas'
      | 'inactivas';
    this.filtroEstadoColeccion.set(val);
    this.cargarColecciones(true);
  }

  cambiarPaginaColeccion(nuevaPagina: number): void {
    if (
      nuevaPagina >= 1 &&
      nuevaPagina <= this.servicio.totalPaginasColecciones()
    ) {
      this.paginaColeccion.set(nuevaPagina);
      this.cargarColecciones();
    }
  }

  abrirModalCrearColeccion(): void {
    if (!this.esAdmin()) return;
    this.limpiarBanners();
    this.modoEdicionColeccion.set(false);
    this.coleccionEnEdicion.set(null);

    // Asegurar lista actualizada de temporadas activas
    this.servicio.cargarTemporadasActivasParaSelector().subscribe();

    this.formColeccion.reset({
      id_temporada: null,
      nombre: '',
      descripcion: '',
      id_proveedor: null,
      estado_activo: true,
    });
    this.modalColeccionAbierto.set(true);
  }

  abrirModalEditarColeccion(item: ColeccionItem): void {
    if (!this.esAdmin()) return;
    this.limpiarBanners();
    this.modoEdicionColeccion.set(true);
    this.coleccionEnEdicion.set(item);

    this.servicio.cargarTemporadasActivasParaSelector().subscribe();

    this.formColeccion.reset({
      id_temporada: item.id_temporada,
      nombre: item.nombre,
      descripcion: item.descripcion || '',
      id_proveedor: null,
      estado_activo: item.estado_activo,
    });
    this.modalColeccionAbierto.set(true);
  }

  guardarColeccion(): void {
    if (this.formColeccion.invalid || !this.esAdmin()) {
      this.formColeccion.markAllAsTouched();
      return;
    }

    const val = this.formColeccion.getRawValue();

    if (this.modoEdicionColeccion() && this.coleccionEnEdicion()) {
      const id = this.coleccionEnEdicion()!.id_coleccion;
      const payload: ColeccionActualizarDto = {
        id_temporada: Number(val.id_temporada),
        nombre: val.nombre.trim(),
        descripcion: val.descripcion?.trim() || null,
        id_proveedor: val.id_proveedor ? Number(val.id_proveedor) : null,
      };

      this.servicio.actualizarColeccion(id, payload).subscribe({
        next: () => {
          this.mensajeExitoBanner.set(this.servicio.mensajeExito());
          this.modalColeccionAbierto.set(false);
          this.cargarColecciones();
          this.cdr.markForCheck();
        },
        error: () => {
          this.errorBanner.set(this.servicio.error());
          this.cdr.markForCheck();
        },
      });
    } else {
      const payload: ColeccionCrearDto = {
        id_temporada: Number(val.id_temporada),
        nombre: val.nombre.trim(),
        descripcion: val.descripcion?.trim() || null,
        id_proveedor: val.id_proveedor ? Number(val.id_proveedor) : null,
        estado_activo: val.estado_activo,
      };

      this.servicio.crearColeccion(payload).subscribe({
        next: () => {
          this.mensajeExitoBanner.set(this.servicio.mensajeExito());
          this.modalColeccionAbierto.set(false);
          this.cargarColecciones(true);
          this.cdr.markForCheck();
        },
        error: () => {
          this.errorBanner.set(this.servicio.error());
          this.cdr.markForCheck();
        },
      });
    }
  }

  // ==========================================================================
  // CONMUTACION DE ESTADO / BAJA LOGICA
  // ==========================================================================

  solicitarConmutarEstado(
    tipo: 'temporada' | 'coleccion',
    id: number,
    nombre: string,
    estado_activo: boolean
  ): void {
    if (!this.esAdmin()) return;
    this.limpiarBanners();
    this.elementoParaConmutar.set({ tipo, id, nombre, estado_activo });
    this.modalConfirmarEstadoAbierto.set(true);
  }

  confirmarConmutarEstado(): void {
    const item = this.elementoParaConmutar();
    if (!item || !this.esAdmin()) return;

    const nuevoEstado = !item.estado_activo;

    if (item.tipo === 'temporada') {
      this.servicio.conmutarEstadoTemporada(item.id, nuevoEstado).subscribe({
        next: () => {
          this.mensajeExitoBanner.set(this.servicio.mensajeExito());
          this.modalConfirmarEstadoAbierto.set(false);
          this.elementoParaConmutar.set(null);
          this.cargarTemporadas();
          this.servicio.cargarTemporadasActivasParaSelector().subscribe();
          this.cdr.markForCheck();
        },
        error: () => {
          this.errorBanner.set(this.servicio.error());
          this.modalConfirmarEstadoAbierto.set(false);
          this.cdr.markForCheck();
        },
      });
    } else {
      this.servicio.conmutarEstadoColeccion(item.id, nuevoEstado).subscribe({
        next: () => {
          this.mensajeExitoBanner.set(this.servicio.mensajeExito());
          this.modalConfirmarEstadoAbierto.set(false);
          this.elementoParaConmutar.set(null);
          this.cargarColecciones();
          this.cdr.markForCheck();
        },
        error: () => {
          this.errorBanner.set(this.servicio.error());
          this.modalConfirmarEstadoAbierto.set(false);
          this.cdr.markForCheck();
        },
      });
    }
  }

  cerrarModales(): void {
    this.modalTemporadaAbierto.set(false);
    this.modalColeccionAbierto.set(false);
    this.modalConfirmarEstadoAbierto.set(false);
    this.elementoParaConmutar.set(null);
    this.limpiarBanners();
  }
}
