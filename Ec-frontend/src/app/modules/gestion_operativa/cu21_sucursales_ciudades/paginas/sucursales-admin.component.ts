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
  Validators,
} from '@angular/forms';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { SucursalesAdminService } from '../servicios/sucursales-admin.service';
import {
  Ciudad,
  CiudadCrearPayload,
  SucursalAdmin,
  SucursalCrearPayload,
} from '../modelos/sucursal.model';

/**
 * Validador de coherencia horaria a nivel de formulario.
 * Garantiza que horario_cierre sea estrictamente mayor que horario_apertura.
 */
export function validarCoherenciaHorarios(
  control: AbstractControl
): ValidationErrors | null {
  const apertura = control.get('horario_apertura')?.value;
  const cierre = control.get('horario_cierre')?.value;

  if (!apertura || !cierre) {
    return null;
  }

  if (cierre <= apertura) {
    return { horarioInvalido: true };
  }

  return null;
}

@Component({
  selector: 'app-sucursales-admin',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, RouterLinkActive],
  templateUrl: './sucursales-admin.component.html',
  styleUrls: ['./sucursales-admin.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SucursalesAdminComponent implements OnInit {
  protected readonly sucursalesService = inject(SucursalesAdminService);
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly cdr = inject(ChangeDetectorRef);

  // --- Signals de Estado Reactivo de la Vista ---
  readonly pestanaActiva = signal<'boutiques' | 'ciudades'>('boutiques');
  readonly filtroCiudad = signal<number | null>(null);
  readonly filtroBusqueda = signal<string>('');
  readonly filtroEstado = signal<'todos' | 'activa' | 'inactiva'>('todos');

  // Modales
  readonly modalBoutiqueAbierto = signal<boolean>(false);
  readonly modalCiudadAbierto = signal<boolean>(false);
  readonly modalEliminarAbierto = signal<boolean>(false);

  // Elementos en edicion o baja
  readonly boutiqueEnEdicion = signal<SucursalAdmin | null>(null);
  readonly ciudadEnEdicion = signal<Ciudad | null>(null);
  readonly elementoAEliminar = signal<{
    tipo: 'boutique' | 'ciudad';
    id: number;
    nombre: string;
  } | null>(null);

  // Alerta de conflicto de dominio 409
  readonly notificacionConflicto = signal<string | null>(null);

  // Signals derivadas del servicio
  readonly ciudades = this.sucursalesService.ciudades;
  readonly sucursales = this.sucursalesService.sucursales;
  readonly cargando = this.sucursalesService.cargando;
  readonly guardando = this.sucursalesService.guardando;
  readonly error = this.sucursalesService.error;
  readonly mensajeExito = this.sucursalesService.mensajeExito;

  // --- Computed Signals de Negocio ---
  readonly totalBoutiques = computed(() => this.sucursales().length);
  readonly totalActivas = computed(
    () => this.sucursales().filter((s) => s.activa).length
  );
  readonly totalInactivas = computed(
    () => this.sucursales().filter((s) => !s.activa).length
  );

  readonly sucursalesFiltradas = computed(() => {
    const lista = this.sucursales();
    const ciudadId = this.filtroCiudad();
    const q = this.filtroBusqueda().trim().toLowerCase();
    const estado = this.filtroEstado();

    return lista.filter((item) => {
      // Filtro por ciudad
      if (ciudadId !== null && item.id_ciudad !== ciudadId) {
        return false;
      }
      // Filtro por estado
      if (estado === 'activa' && !item.activa) {
        return false;
      }
      if (estado === 'inactiva' && item.activa) {
        return false;
      }
      // Filtro por busqueda textual
      if (q.length > 0) {
        const enNombre = item.nombre.toLowerCase().includes(q);
        const enDireccion = item.direccion.toLowerCase().includes(q);
        const enCiudad = item.ciudad_nombre.toLowerCase().includes(q);
        if (!enNombre && !enDireccion && !enCiudad) {
          return false;
        }
      }
      return true;
    });
  });

  // --- Formularios Reactivos Fuertemente Tipados ---
  readonly formularioBoutique = this.fb.group(
    {
      id_ciudad: [0, [Validators.required, Validators.min(1)]],
      nombre: [
        '',
        [
          Validators.required,
          Validators.minLength(3),
          Validators.maxLength(100),
        ],
      ],
      direccion: [
        '',
        [
          Validators.required,
          Validators.minLength(5),
          Validators.maxLength(255),
        ],
      ],
      telefono: ['', [Validators.maxLength(30)]],
      horario_apertura: [
        '10:00',
        [
          Validators.required,
          Validators.pattern(/^([01]\d|2[0-3]):[0-5]\d$/),
        ],
      ],
      horario_cierre: [
        '20:30',
        [
          Validators.required,
          Validators.pattern(/^([01]\d|2[0-3]):[0-5]\d$/),
        ],
      ],
    },
    {
      validators: [validarCoherenciaHorarios],
    }
  );

  readonly formularioCiudad = this.fb.group({
    nombre: [
      '',
      [
        Validators.required,
        Validators.minLength(2),
        Validators.maxLength(100),
      ],
    ],
    pais: [
      'Espana',
      [
        Validators.required,
        Validators.minLength(2),
        Validators.maxLength(100),
      ],
    ],
  });

  ngOnInit(): void {
    this.cargarDatosIniciales();
  }

  cargarDatosIniciales(): void {
    this.sucursalesService.cargarCiudades().subscribe({
      next: () => this.cdr.markForCheck(),
      error: () => this.cdr.markForCheck(),
    });
    this.sucursalesService.cargarSucursales().subscribe({
      next: () => this.cdr.markForCheck(),
      error: () => this.cdr.markForCheck(),
    });
  }

  // --- Manejo de Pestañas ---
  cambiarPestana(pestana: 'boutiques' | 'ciudades'): void {
    this.pestanaActiva.set(pestana);
    this.limpiarAlertas();
    this.cdr.markForCheck();
  }

  // --- Filtros Reactivos ---
  actualizarFiltroCiudad(id: number | null): void {
    this.filtroCiudad.set(id);
  }

  actualizarFiltroBusqueda(valor: string): void {
    this.filtroBusqueda.set(valor);
  }

  actualizarFiltroEstado(estado: 'todos' | 'activa' | 'inactiva'): void {
    this.filtroEstado.set(estado);
  }

  // --- Modales de Boutique ---
  abrirModalNuevaBoutique(): void {
    this.limpiarAlertas();
    this.boutiqueEnEdicion.set(null);
    const primerCiudad = this.ciudades()[0]?.id_ciudad || 0;
    this.formularioBoutique.reset({
      id_ciudad: primerCiudad,
      nombre: '',
      direccion: '',
      telefono: '',
      horario_apertura: '10:00',
      horario_cierre: '20:30',
    });
    this.modalBoutiqueAbierto.set(true);
    this.cdr.markForCheck();
  }

  abrirModalEditarBoutique(sucursal: SucursalAdmin): void {
    this.limpiarAlertas();
    this.boutiqueEnEdicion.set(sucursal);
    this.formularioBoutique.patchValue({
      id_ciudad: sucursal.id_ciudad,
      nombre: sucursal.nombre,
      direccion: sucursal.direccion,
      telefono: sucursal.telefono || '',
      horario_apertura: sucursal.horario_apertura,
      horario_cierre: sucursal.horario_cierre,
    });
    this.modalBoutiqueAbierto.set(true);
    this.cdr.markForCheck();
  }

  cerrarModalBoutique(): void {
    this.modalBoutiqueAbierto.set(false);
    this.boutiqueEnEdicion.set(null);
    this.formularioBoutique.reset();
    this.cdr.markForCheck();
  }

  guardarBoutique(): void {
    if (this.formularioBoutique.invalid) {
      this.formularioBoutique.markAllAsTouched();
      this.cdr.markForCheck();
      return;
    }

    const val = this.formularioBoutique.getRawValue();
    const boutiqueActual = this.boutiqueEnEdicion();

    if (boutiqueActual) {
      // Actualizacion
      this.sucursalesService
        .actualizarSucursal(boutiqueActual.id_sucursal, {
          id_ciudad: val.id_ciudad,
          nombre: val.nombre.trim(),
          direccion: val.direccion.trim(),
          telefono: val.telefono.trim() ? val.telefono.trim() : null,
          horario_apertura: val.horario_apertura,
          horario_cierre: val.horario_cierre,
        })
        .subscribe({
          next: () => {
            this.cerrarModalBoutique();
            this.cdr.markForCheck();
          },
          error: (err: Error) => {
            this.notificacionConflicto.set(err.message);
            this.cdr.markForCheck();
          },
        });
    } else {
      // Creacion
      const payload: SucursalCrearPayload = {
        id_ciudad: val.id_ciudad,
        nombre: val.nombre.trim(),
        direccion: val.direccion.trim(),
        telefono: val.telefono.trim() ? val.telefono.trim() : null,
        horario_apertura: val.horario_apertura,
        horario_cierre: val.horario_cierre,
      };

      this.sucursalesService.crearSucursal(payload).subscribe({
        next: () => {
          this.cerrarModalBoutique();
          this.cdr.markForCheck();
        },
        error: (err: Error) => {
          this.notificacionConflicto.set(err.message);
          this.cdr.markForCheck();
        },
      });
    }
  }

  // --- Alternar Estado Operativo de Boutique ---
  alternarEstadoSucursal(sucursal: SucursalAdmin): void {
    this.limpiarAlertas();
    const nuevoEstado = !sucursal.activa;

    this.sucursalesService
      .cambiarEstado(sucursal.id_sucursal, nuevoEstado)
      .subscribe({
        next: () => {
          this.cdr.markForCheck();
        },
        error: (err: Error) => {
          this.notificacionConflicto.set(err.message);
          this.cdr.markForCheck();
        },
      });
  }

  // --- Modales de Ciudad ---
  abrirModalNuevaCiudad(): void {
    this.limpiarAlertas();
    this.ciudadEnEdicion.set(null);
    this.formularioCiudad.reset({
      nombre: '',
      pais: 'Espana',
    });
    this.modalCiudadAbierto.set(true);
    this.cdr.markForCheck();
  }

  abrirModalEditarCiudad(ciudad: Ciudad): void {
    this.limpiarAlertas();
    this.ciudadEnEdicion.set(ciudad);
    this.formularioCiudad.patchValue({
      nombre: ciudad.nombre,
      pais: ciudad.pais,
    });
    this.modalCiudadAbierto.set(true);
    this.cdr.markForCheck();
  }

  cerrarModalCiudad(): void {
    this.modalCiudadAbierto.set(false);
    this.ciudadEnEdicion.set(null);
    this.formularioCiudad.reset();
    this.cdr.markForCheck();
  }

  guardarCiudad(): void {
    if (this.formularioCiudad.invalid) {
      this.formularioCiudad.markAllAsTouched();
      this.cdr.markForCheck();
      return;
    }

    const val = this.formularioCiudad.getRawValue();
    const ciudadActual = this.ciudadEnEdicion();

    if (ciudadActual) {
      this.sucursalesService
        .actualizarCiudad(ciudadActual.id_ciudad, {
          nombre: val.nombre.trim(),
          pais: val.pais.trim(),
        })
        .subscribe({
          next: () => {
            this.cerrarModalCiudad();
            this.cdr.markForCheck();
          },
          error: (err: Error) => {
            this.notificacionConflicto.set(err.message);
            this.cdr.markForCheck();
          },
        });
    } else {
      const payload: CiudadCrearPayload = {
        nombre: val.nombre.trim(),
        pais: val.pais.trim(),
      };

      this.sucursalesService.crearCiudad(payload).subscribe({
        next: () => {
          this.cerrarModalCiudad();
          this.cdr.markForCheck();
        },
        error: (err: Error) => {
          this.notificacionConflicto.set(err.message);
          this.cdr.markForCheck();
        },
      });
    }
  }

  // --- Eliminacion de Elementos ---
  solicitarEliminacion(
    tipo: 'boutique' | 'ciudad',
    id: number,
    nombre: string
  ): void {
    this.limpiarAlertas();
    this.elementoAEliminar.set({ tipo, id, nombre });
    this.modalEliminarAbierto.set(true);
    this.cdr.markForCheck();
  }

  cerrarModalEliminar(): void {
    this.modalEliminarAbierto.set(false);
    this.elementoAEliminar.set(null);
    this.cdr.markForCheck();
  }

  confirmarEliminacion(): void {
    const el = this.elementoAEliminar();
    if (!el) return;

    if (el.tipo === 'boutique') {
      this.sucursalesService.eliminarSucursal(el.id).subscribe({
        next: () => {
          this.cerrarModalEliminar();
          this.cdr.markForCheck();
        },
        error: (err: Error) => {
          this.cerrarModalEliminar();
          this.notificacionConflicto.set(err.message);
          this.cdr.markForCheck();
        },
      });
    } else {
      this.sucursalesService.eliminarCiudad(el.id).subscribe({
        next: () => {
          this.cerrarModalEliminar();
          this.cdr.markForCheck();
        },
        error: (err: Error) => {
          this.cerrarModalEliminar();
          this.notificacionConflicto.set(err.message);
          this.cdr.markForCheck();
        },
      });
    }
  }

  limpiarAlertas(): void {
    this.notificacionConflicto.set(null);
    this.sucursalesService.limpiarMensajes();
  }
}
