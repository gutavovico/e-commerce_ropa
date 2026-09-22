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
import { UsuariosAdminService } from '../servicios/usuarios-admin.service';
import { SucursalesAdminService } from '../../../gestion_operativa/cu21_sucursales_ciudades/servicios/sucursales-admin.service';
import {
  RolUsuario,
  UsuarioActualizarPayload,
  UsuarioAdmin,
  UsuarioCrearPayload,
} from '../modelos/usuario.dto';

@Component({
  selector: 'app-usuarios-admin',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './usuarios-admin.component.html',
  styleUrls: ['./usuarios-admin.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class UsuariosAdminComponent implements OnInit {
  protected readonly usuariosService = inject(UsuariosAdminService);
  protected readonly sucursalesService = inject(SucursalesAdminService);
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly cdr = inject(ChangeDetectorRef);

  // --- Filtros reactivos ---
  readonly busquedaTexto = signal<string>('');
  readonly filtroRol = signal<string>('todos');
  readonly filtroSucursal = signal<number | null>(null);
  readonly filtroEstado = signal<string>('todos');
  readonly paginaActual = signal<number>(1);
  readonly limitePorPagina = signal<number>(10);

  // --- Estados de modales ---
  readonly modalUsuarioAbierto = signal<boolean>(false);
  readonly modoEdicion = signal<boolean>(false);
  readonly usuarioEditandoId = signal<number | null>(null);

  readonly modalResetAbierto = signal<boolean>(false);
  readonly usuarioResetId = signal<number | null>(null);
  readonly usuarioResetNombre = signal<string>('');

  readonly modalEliminarAbierto = signal<boolean>(false);
  readonly usuarioEliminarId = signal<number | null>(null);
  readonly usuarioEliminarNombre = signal<string>('');

  // Banner de alerta contextual de error (409/422)
  readonly errorBanner = signal<string | null>(null);

  private debounceTimer: any = null;

  // --- Formulario Principal: Alta y Edicion ---
  readonly formUsuario = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: [''],
    nombres: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(100)]],
    apellidos: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(100)]],
    telefono: [''],
    rol: ['cliente' as RolUsuario, [Validators.required]],
    id_sucursal: [null as number | null],
  });

  // --- Formulario de Restablecimiento de Contrasena ---
  readonly formReset = this.fb.group({
    nuevo_password: ['', [Validators.required, Validators.minLength(8)]],
  });

  // Signal derivado para mostrar u ocultar el selector de sucursal
  readonly rolSeleccionadoForm = signal<RolUsuario>('cliente');
  readonly esRolOperativo = computed(() => {
    const rol = this.rolSeleccionadoForm();
    return rol === 'encargado_sucursal' || rol === 'cajero';
  });

  ngOnInit(): void {
    this.cargarDatos();

    // Escucha reactiva del cambio de rol para condicionar obligatoriedad de sucursal
    this.formUsuario.get('rol')?.valueChanges.subscribe((nuevoRol) => {
      this.rolSeleccionadoForm.set(nuevoRol as RolUsuario);
      const sucursalControl = this.formUsuario.get('id_sucursal');
      if (nuevoRol === 'encargado_sucursal' || nuevoRol === 'cajero') {
        sucursalControl?.setValidators([Validators.required, Validators.min(1)]);
      } else {
        sucursalControl?.clearValidators();
        sucursalControl?.setValue(null);
      }
      sucursalControl?.updateValueAndValidity();
      this.cdr.markForCheck();
    });
  }

  cargarDatos(): void {
    this.usuariosService.cargarUsuarios().subscribe();
    this.sucursalesService.cargarSucursales().subscribe();
  }

  // --- Manejo de Filtros y Busqueda ---

  onBuscarInput(evento: Event): void {
    const valor = (evento.target as HTMLInputElement).value;
    this.busquedaTexto.set(valor);
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }
    this.debounceTimer = setTimeout(() => {
      this.paginaActual.set(1);
      this.aplicarFiltros();
    }, 300);
  }

  onCambiarFiltroRol(evento: Event): void {
    const rol = (evento.target as HTMLSelectElement).value;
    this.filtroRol.set(rol);
    this.paginaActual.set(1);
    this.aplicarFiltros();
  }

  onCambiarFiltroSucursal(evento: Event): void {
    const valor = (evento.target as HTMLSelectElement).value;
    const idSucursal = valor ? Number(valor) : null;
    this.filtroSucursal.set(idSucursal);
    this.paginaActual.set(1);
    this.aplicarFiltros();
  }

  onCambiarFiltroEstado(evento: Event): void {
    const estado = (evento.target as HTMLSelectElement).value;
    this.filtroEstado.set(estado);
    this.paginaActual.set(1);
    this.aplicarFiltros();
  }

  aplicarFiltros(): void {
    let activo: boolean | undefined = undefined;
    if (this.filtroEstado() === 'activos') {
      activo = true;
    } else if (this.filtroEstado() === 'inactivos') {
      activo = false;
    }

    this.usuariosService
      .cargarUsuarios({
        q: this.busquedaTexto(),
        rol: this.filtroRol(),
        id_sucursal: this.filtroSucursal() || undefined,
        activo: activo,
        pagina: this.paginaActual(),
        limite: this.limitePorPagina(),
      })
      .subscribe();
  }

  cambiarPagina(nuevaPagina: number): void {
    if (nuevaPagina < 1) return;
    this.paginaActual.set(nuevaPagina);
    this.aplicarFiltros();
  }

  // --- Modales y Acciones CRUD ---

  abrirModalCrear(): void {
    this.errorBanner.set(null);
    this.modoEdicion.set(false);
    this.usuarioEditandoId.set(null);
    this.formUsuario.reset({
      email: '',
      password: '',
      nombres: '',
      apellidos: '',
      telefono: '',
      rol: 'cliente',
      id_sucursal: null,
    });
    this.rolSeleccionadoForm.set('cliente');

    // En creacion, la contrasena es estrictamente obligatoria
    this.formUsuario.get('password')?.setValidators([
      Validators.required,
      Validators.minLength(8),
    ]);
    this.formUsuario.get('password')?.updateValueAndValidity();

    this.modalUsuarioAbierto.set(true);
    this.cdr.markForCheck();
  }

  abrirModalEditar(usuario: UsuarioAdmin): void {
    this.errorBanner.set(null);
    this.modoEdicion.set(true);
    this.usuarioEditandoId.set(usuario.id_usuario);

    this.formUsuario.patchValue({
      email: usuario.email,
      password: '',
      nombres: usuario.nombres,
      apellidos: usuario.apellidos,
      telefono: usuario.telefono || '',
      rol: usuario.rol,
      id_sucursal: usuario.id_sucursal,
    });
    this.rolSeleccionadoForm.set(usuario.rol);

    // En edicion la contrasena es opcional
    this.formUsuario.get('password')?.clearValidators();
    this.formUsuario.get('password')?.updateValueAndValidity();

    this.modalUsuarioAbierto.set(true);
    this.cdr.markForCheck();
  }

  cerrarModalUsuario(): void {
    this.modalUsuarioAbierto.set(false);
    this.errorBanner.set(null);
  }

  guardarUsuario(): void {
    if (this.formUsuario.invalid) {
      this.formUsuario.markAllAsTouched();
      return;
    }

    this.errorBanner.set(null);
    const formVals = this.formUsuario.getRawValue();

    if (this.modoEdicion()) {
      const id = this.usuarioEditandoId();
      if (!id) return;

      const payload: UsuarioActualizarPayload = {
        email: formVals.email,
        nombres: formVals.nombres,
        apellidos: formVals.apellidos,
        telefono: formVals.telefono || null,
        rol: formVals.rol,
        id_sucursal: formVals.id_sucursal,
      };

      this.usuariosService.actualizarUsuario(id, payload).subscribe({
        next: () => {
          this.cerrarModalUsuario();
        },
        error: (err) => {
          this.errorBanner.set(err.message);
          this.cdr.markForCheck();
        },
      });
    } else {
      const payload: UsuarioCrearPayload = {
        email: formVals.email,
        password: formVals.password,
        nombres: formVals.nombres,
        apellidos: formVals.apellidos,
        telefono: formVals.telefono || null,
        rol: formVals.rol,
        id_sucursal: formVals.id_sucursal,
      };

      this.usuariosService.crearUsuario(payload).subscribe({
        next: () => {
          this.cerrarModalUsuario();
        },
        error: (err) => {
          this.errorBanner.set(err.message);
          this.cdr.markForCheck();
        },
      });
    }
  }

  // --- Conmutacion de Estado (Activo / Suspendido) ---

  conmutarEstado(usuario: UsuarioAdmin): void {
    this.errorBanner.set(null);
    const nuevoEstado = !usuario.activo;

    this.usuariosService.cambiarEstado(usuario.id_usuario, nuevoEstado).subscribe({
      error: (err) => {
        this.errorBanner.set(err.message);
        this.cdr.markForCheck();
      },
    });
  }

  // --- Modal de Restablecimiento de Contrasena ---

  abrirModalReset(usuario: UsuarioAdmin): void {
    this.errorBanner.set(null);
    this.usuarioResetId.set(usuario.id_usuario);
    this.usuarioResetNombre.set(usuario.nombre_completo);
    this.formReset.reset({ nuevo_password: '' });
    this.modalResetAbierto.set(true);
    this.cdr.markForCheck();
  }

  cerrarModalReset(): void {
    this.modalResetAbierto.set(false);
    this.usuarioResetId.set(null);
    this.errorBanner.set(null);
  }

  guardarResetPassword(): void {
    if (this.formReset.invalid) {
      this.formReset.markAllAsTouched();
      return;
    }

    const id = this.usuarioResetId();
    if (!id) return;

    this.errorBanner.set(null);
    const payload = this.formReset.getRawValue();

    this.usuariosService.resetPassword(id, payload).subscribe({
      next: () => {
        this.cerrarModalReset();
      },
      error: (err) => {
        this.errorBanner.set(err.message);
        this.cdr.markForCheck();
      },
    });
  }

  // --- Modal de Eliminacion Fisica / Baja Logica ---

  abrirModalEliminar(usuario: UsuarioAdmin): void {
    this.errorBanner.set(null);
    this.usuarioEliminarId.set(usuario.id_usuario);
    this.usuarioEliminarNombre.set(usuario.nombre_completo);
    this.modalEliminarAbierto.set(true);
    this.cdr.markForCheck();
  }

  cerrarModalEliminar(): void {
    this.modalEliminarAbierto.set(false);
    this.usuarioEliminarId.set(null);
    this.errorBanner.set(null);
  }

  confirmarEliminacion(): void {
    const id = this.usuarioEliminarId();
    if (!id) return;

    this.errorBanner.set(null);
    this.usuariosService.eliminarUsuario(id).subscribe({
      next: () => {
        this.cerrarModalEliminar();
      },
      error: (err) => {
        this.errorBanner.set(err.message);
        this.cdr.markForCheck();
      },
    });
  }

  // --- Helpers de Estilo y Presentacion Editorial ---

  obtenerIniciales(nombres: string, apellidos: string): string {
    const n = nombres ? nombres.trim().charAt(0).toUpperCase() : '';
    const a = apellidos ? apellidos.trim().charAt(0).toUpperCase() : '';
    return `${n}${a}` || 'FS';
  }

  obtenerClaseBadgeRol(rol: string): string {
    switch (rol) {
      case 'administrador':
        return 'bg-[#0F172A] text-white border-slate-900';
      case 'encargado_sucursal':
        return 'bg-indigo-50 text-indigo-800 border-indigo-200';
      case 'cajero':
        return 'bg-amber-50 text-amber-800 border-amber-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  }

  obtenerNombreRol(rol: string): string {
    switch (rol) {
      case 'administrador':
        return 'Administrador';
      case 'encargado_sucursal':
        return 'Encargado';
      case 'cajero':
        return 'Cajero';
      default:
        return 'Cliente';
    }
  }

  descartarErrorBanner(): void {
    this.errorBanner.set(null);
    this.usuariosService.limpiarMensajes();
  }
}
