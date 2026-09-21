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
  NonNullableFormBuilder,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ProveedoresAdminService } from '../servicios/proveedores-admin.service';
import { LoginService } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import {
  FiltrosProveedores,
  ProveedorActualizarPayload,
  ProveedorCrearPayload,
  ProveedorItemAdmin,
} from '../modelos/proveedor.dto';

@Component({
  selector: 'app-proveedores-admin',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './proveedores-admin.component.html',
  styleUrls: ['./proveedores-admin.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProveedoresAdminComponent implements OnInit {
  protected readonly proveedoresService = inject(ProveedoresAdminService);
  private readonly loginService = inject(LoginService);
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly cdr = inject(ChangeDetectorRef);

  // Roles y Privilegios RBAC
  readonly usuario = computed(() => this.loginService.usuarioActual());
  readonly rolUsuario = computed(() =>
    String(this.usuario()?.rol || '').toLowerCase().trim()
  );
  readonly esAdmin = computed(() => this.rolUsuario() === 'administrador');
  readonly esEncargado = computed(
    () => this.rolUsuario() === 'encargado_sucursal'
  );

  // Filtros reactivos de consulta
  readonly busquedaTexto = signal<string>('');
  readonly filtroEstado = signal<string>('todos');
  readonly filtroRubro = signal<string>('todos');
  readonly paginaActual = signal<number>(1);
  readonly limitePorPagina = signal<number>(10);

  // Modales y estado de edicion
  readonly modalCrearAbierto = signal<boolean>(false);
  readonly modalEditarAbierto = signal<boolean>(false);
  readonly modalConfirmarEstadoAbierto = signal<boolean>(false);
  readonly proveedorSeleccionado = signal<ProveedorItemAdmin | null>(null);

  // Luxury Banner de errores contextuales
  readonly errorBanner = signal<string | null>(null);

  private debounceTimer: any = null;

  // Catalogos de referencia para rubros y ciudades comerciales
  readonly rubrosDisponibles = [
    'Confeccion y Sastreria',
    'Telas y Tejidos',
    'Avios y Merceria',
    'Calzado y Cuero',
    'Accesorios y Bisuteria',
    'Empaque y Logistica',
    'Otros',
  ];

  readonly ciudadesDisponibles = [
    'La Paz',
    'Santa Cruz',
    'Cochabamba',
    'El Alto',
    'Sucre',
    'Tarija',
    'Oruro',
    'Potosi',
    'Beni',
    'Pando',
  ];

  // Formulario 1: Alta de Nuevo Proveedor
  readonly formCrear = this.fb.group({
    razon_social: ['', [Validators.required, Validators.minLength(3)]],
    nit_rut: ['', [Validators.required, Validators.minLength(5)]],
    rubro: ['Confeccion y Sastreria', [Validators.required]],
    contacto_nombre: ['', [Validators.required, Validators.minLength(3)]],
    telefono: ['', [Validators.required, Validators.minLength(7)]],
    email: ['', [Validators.required, Validators.email]],
    direccion: ['', [Validators.required, Validators.minLength(5)]],
    ciudad: ['La Paz', [Validators.required]],
  });

  // Formulario 2: Edicion de Proveedor Existente
  readonly formEditar = this.fb.group({
    razon_social: ['', [Validators.required, Validators.minLength(3)]],
    nit_rut: ['', [Validators.required, Validators.minLength(5)]],
    rubro: ['Confeccion y Sastreria', [Validators.required]],
    contacto_nombre: ['', [Validators.required, Validators.minLength(3)]],
    telefono: ['', [Validators.required, Validators.minLength(7)]],
    email: ['', [Validators.required, Validators.email]],
    direccion: ['', [Validators.required, Validators.minLength(5)]],
    ciudad: ['La Paz', [Validators.required]],
  });

  ngOnInit(): void {
    this.cargarProveedores();
  }

  cargarProveedores(resetPagina: boolean = false): void {
    if (resetPagina) {
      this.paginaActual.set(1);
    }

    let estadoActivo: boolean | null = null;
    if (this.filtroEstado() === 'activos') {
      estadoActivo = true;
    } else if (this.filtroEstado() === 'inactivos') {
      estadoActivo = false;
    }

    const rubroFiltro =
      this.filtroRubro() !== 'todos' ? this.filtroRubro() : null;

    const filtros: FiltrosProveedores = {
      q: this.busquedaTexto().trim() || null,
      estado_activo: estadoActivo,
      rubro: rubroFiltro,
      pagina: this.paginaActual(),
      limite: this.limitePorPagina(),
    };

    this.proveedoresService.cargarProveedores(filtros).subscribe({
      next: () => {
        this.cdr.markForCheck();
      },
      error: (err: any) => {
        this.errorBanner.set(
          err?.message || 'No fue posible cargar el directorio de proveedores.'
        );
        this.cdr.markForCheck();
      },
    });
  }

  alCambiarBusqueda(texto: string): void {
    this.busquedaTexto.set(texto);
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }
    this.debounceTimer = setTimeout(() => {
      this.cargarProveedores(true);
    }, 300);
  }

  alCambiarFiltroEstado(estado: string): void {
    this.filtroEstado.set(estado);
    this.cargarProveedores(true);
  }

  alCambiarFiltroRubro(rubro: string): void {
    this.filtroRubro.set(rubro);
    this.cargarProveedores(true);
  }

  paginaAnterior(): void {
    if (this.paginaActual() > 1) {
      this.paginaActual.update((p) => p - 1);
      this.cargarProveedores();
    }
  }

  paginaSiguiente(): void {
    if (this.paginaActual() < this.proveedoresService.totalPaginas()) {
      this.paginaActual.update((p) => p + 1);
      this.cargarProveedores();
    }
  }

  irAPagina(p: number): void {
    if (p >= 1 && p <= this.proveedoresService.totalPaginas()) {
      this.paginaActual.set(p);
      this.cargarProveedores();
    }
  }

  // Operaciones de Creacion
  abrirModalCrear(): void {
    this.formCrear.reset({
      razon_social: '',
      nit_rut: '',
      rubro: 'Confeccion y Sastreria',
      contacto_nombre: '',
      telefono: '',
      email: '',
      direccion: '',
      ciudad: 'La Paz',
    });
    this.errorBanner.set(null);
    this.modalCrearAbierto.set(true);
  }

  cerrarModalCrear(): void {
    this.modalCrearAbierto.set(false);
  }

  guardarNuevoProveedor(): void {
    if (this.formCrear.invalid) {
      this.formCrear.markAllAsTouched();
      return;
    }

    const raw = this.formCrear.getRawValue();
    const payload: ProveedorCrearPayload = {
      razon_social: raw.razon_social.trim(),
      nit_rut: raw.nit_rut.trim(),
      contacto_nombre: raw.contacto_nombre.trim(),
      telefono: raw.telefono.trim(),
      email: raw.email.trim(),
      direccion: raw.direccion.trim(),
      ciudad: raw.ciudad.trim(),
      rubro: raw.rubro.trim(),
    };

    this.proveedoresService.crearProveedor(payload).subscribe({
      next: () => {
        this.cerrarModalCrear();
        this.cargarProveedores(true);
      },
      error: (err: any) => {
        const msg =
          err?.error?.detail ||
          err?.message ||
          'Error al dar de alta el proveedor en el catalogo.';
        this.errorBanner.set(typeof msg === 'string' ? msg : JSON.stringify(msg));
        this.cdr.markForCheck();
      },
    });
  }

  // Operaciones de Edicion
  abrirModalEditar(proveedor: ProveedorItemAdmin): void {
    this.proveedorSeleccionado.set(proveedor);
    this.formEditar.reset({
      razon_social: proveedor.razon_social,
      nit_rut: proveedor.nit_rut,
      rubro: proveedor.rubro || 'Confeccion y Sastreria',
      contacto_nombre: proveedor.contacto_nombre || '',
      telefono: proveedor.telefono || '',
      email: proveedor.email || '',
      direccion: proveedor.direccion || '',
      ciudad: proveedor.ciudad || 'La Paz',
    });
    this.errorBanner.set(null);
    this.modalEditarAbierto.set(true);
  }

  cerrarModalEditar(): void {
    this.modalEditarAbierto.set(false);
    this.proveedorSeleccionado.set(null);
  }

  guardarEdicionProveedor(): void {
    const prov = this.proveedorSeleccionado();
    if (!prov) return;

    if (this.formEditar.invalid) {
      this.formEditar.markAllAsTouched();
      return;
    }

    const raw = this.formEditar.getRawValue();
    const payload: ProveedorActualizarPayload = {
      razon_social: raw.razon_social.trim(),
      nit_rut: raw.nit_rut.trim(),
      contacto_nombre: raw.contacto_nombre.trim(),
      telefono: raw.telefono.trim(),
      email: raw.email.trim(),
      direccion: raw.direccion.trim(),
      ciudad: raw.ciudad.trim(),
      rubro: raw.rubro.trim(),
    };

    this.proveedoresService
      .actualizarProveedor(prov.id_proveedor, payload)
      .subscribe({
        next: () => {
          this.cerrarModalEditar();
          this.cargarProveedores();
        },
        error: (err: any) => {
          const msg =
            err?.error?.detail ||
            err?.message ||
            'Error al actualizar las especificaciones del proveedor.';
          this.errorBanner.set(typeof msg === 'string' ? msg : JSON.stringify(msg));
          this.cdr.markForCheck();
        },
      });
  }

  // Conmutacion de Estado (Baja Logica / Reactivacion)
  abrirModalConfirmarEstado(proveedor: ProveedorItemAdmin): void {
    this.proveedorSeleccionado.set(proveedor);
    this.modalConfirmarEstadoAbierto.set(true);
  }

  cerrarModalConfirmarEstado(): void {
    this.modalConfirmarEstadoAbierto.set(false);
    this.proveedorSeleccionado.set(null);
  }

  confirmarCambioEstado(): void {
    const prov = this.proveedorSeleccionado();
    if (!prov) return;

    const nuevoActivo = !prov.estado_activo;

    this.proveedoresService
      .cambiarEstadoProveedor(prov.id_proveedor, nuevoActivo)
      .subscribe({
        next: () => {
          this.cerrarModalConfirmarEstado();
          this.cargarProveedores();
        },
        error: (err: any) => {
          const msg =
            err?.error?.detail ||
            err?.message ||
            'Error al conmutar el estado operativo del proveedor.';
          this.errorBanner.set(typeof msg === 'string' ? msg : JSON.stringify(msg));
          this.cerrarModalConfirmarEstado();
          this.cdr.markForCheck();
        },
      });
  }

  descartarErrorBanner(): void {
    this.errorBanner.set(null);
    this.proveedoresService.limpiarMensajes();
  }

  descartarMensajeExito(): void {
    this.proveedoresService.limpiarMensajes();
  }
}
