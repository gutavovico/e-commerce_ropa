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
import { RouterLink, RouterLinkActive } from '@angular/router';
import { AtributosAdminService } from '../servicios/atributos-admin.service';
import {
  CategoriaAdmin,
  CategoriaActualizarPayload,
  CategoriaCrearPayload,
  ColorAdmin,
  ColorActualizarPayload,
  ColorCrearPayload,
  TallaAdmin,
  TallaActualizarPayload,
  TallaCrearPayload,
  TipoAtributo,
} from '../modelos/atributos.dto';

@Component({
  selector: 'app-categorias-tallas-colores-admin',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, RouterLinkActive],
  templateUrl: './categorias-tallas-colores-admin.component.html',
  styleUrls: ['./categorias-tallas-colores-admin.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CategoriasTallasColoresAdminComponent implements OnInit {
  protected readonly atributosService = inject(AtributosAdminService);
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly cdr = inject(ChangeDetectorRef);

  // --- Signals de Estado Reactivo de la Vista ---
  readonly pestanaActiva = signal<TipoAtributo>('categorias');
  readonly filtroBusqueda = signal<string>('');

  // Modales de edicion/creacion
  readonly modalCategoriaAbierto = signal<boolean>(false);
  readonly modalTallaAbierto = signal<boolean>(false);
  readonly modalColorAbierto = signal<boolean>(false);
  readonly modalEliminarAbierto = signal<boolean>(false);

  // Elemento en edicion
  readonly categoriaEnEdicion = signal<CategoriaAdmin | null>(null);
  readonly tallaEnEdicion = signal<TallaAdmin | null>(null);
  readonly colorEnEdicion = signal<ColorAdmin | null>(null);

  // Elemento seleccionado para eliminar
  readonly elementoAEliminar = signal<{
    tipo: TipoAtributo;
    id: number;
    nombre: string;
  } | null>(null);

  // Alerta de conflicto de dominio 409 / 422
  readonly notificacionConflicto = signal<string | null>(null);

  // Signals heredadas del servicio
  readonly categorias = this.atributosService.categorias;
  readonly tallas = this.atributosService.tallas;
  readonly colores = this.atributosService.colores;
  readonly cargando = this.atributosService.cargando;
  readonly guardando = this.atributosService.guardando;
  readonly error = this.atributosService.error;
  readonly mensajeExito = this.atributosService.mensajeExito;

  // --- Computed Signals de Filtrado Reactivo ---
  readonly categoriasFiltradas = computed(() => {
    const q = this.filtroBusqueda().trim().toLowerCase();
    const lista = this.categorias();
    if (!q) return lista;
    return lista.filter(
      (c) =>
        c.nombre.toLowerCase().includes(q) ||
        (c.padre_nombre && c.padre_nombre.toLowerCase().includes(q))
    );
  });

  readonly tallasFiltradas = computed(() => {
    const q = this.filtroBusqueda().trim().toLowerCase();
    const lista = this.tallas();
    if (!q) return lista;
    return lista.filter(
      (t) =>
        t.codigo.toLowerCase().includes(q) ||
        t.orden.toString().includes(q)
    );
  });

  readonly coloresFiltrados = computed(() => {
    const q = this.filtroBusqueda().trim().toLowerCase();
    const lista = this.colores();
    if (!q) return lista;
    return lista.filter(
      (c) =>
        c.nombre.toLowerCase().includes(q) ||
        c.codigo_hex.toLowerCase().includes(q)
    );
  });

  // Lista de posibles padres para categorias (excluyendo la categoria en edicion)
  readonly categoriasPadreDisponibles = computed(() => {
    const editando = this.categoriaEnEdicion();
    if (!editando) {
      return this.categorias().filter((c) => c.id_categoria_padre === null);
    }
    return this.categorias().filter(
      (c) => c.id_categoria !== editando.id_categoria && c.id_categoria_padre === null
    );
  });

  // --- Formularios Reactivos ---
  readonly categoriaForm = this.fb.group({
    nombre: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(100)]],
    id_categoria_padre: [null as number | null],
  });

  readonly tallaForm = this.fb.group({
    codigo: ['', [Validators.required, Validators.minLength(1), Validators.maxLength(10)]],
    orden: [0, [Validators.required, Validators.min(0), Validators.max(32767)]],
  });

  readonly colorForm = this.fb.group({
    nombre: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(50)]],
    codigo_hex: ['#000000', [Validators.required, Validators.pattern(/^#[0-9A-Fa-f]{6}$/)]],
  });

  ngOnInit(): void {
    this.cargarDatos();
  }

  cargarDatos(): void {
    this.atributosService.cargarCategorias().subscribe({ error: () => {} });
    this.atributosService.cargarTallas().subscribe({ error: () => {} });
    this.atributosService.cargarColores().subscribe({ error: () => {} });
  }

  cambiarPestana(pestana: TipoAtributo): void {
    this.pestanaActiva.set(pestana);
    this.filtroBusqueda.set('');
    this.notificacionConflicto.set(null);
  }

  actualizarFiltro(valor: string): void {
    this.filtroBusqueda.set(valor);
  }

  // =========================================================================
  // GESTION MODALES: CATEGORIAS
  // =========================================================================

  abrirModalCategoria(categoria?: CategoriaAdmin): void {
    this.notificacionConflicto.set(null);
    if (categoria) {
      this.categoriaEnEdicion.set(categoria);
      this.categoriaForm.setValue({
        nombre: categoria.nombre,
        id_categoria_padre: categoria.id_categoria_padre,
      });
    } else {
      this.categoriaEnEdicion.set(null);
      this.categoriaForm.reset({
        nombre: '',
        id_categoria_padre: null,
      });
    }
    this.modalCategoriaAbierto.set(true);
  }

  cerrarModalCategoria(): void {
    this.modalCategoriaAbierto.set(false);
    this.categoriaEnEdicion.set(null);
    this.categoriaForm.reset();
  }

  guardarCategoria(): void {
    if (this.categoriaForm.invalid) {
      this.categoriaForm.markAllAsTouched();
      return;
    }

    const { nombre, id_categoria_padre } = this.categoriaForm.getRawValue();
    const editando = this.categoriaEnEdicion();

    if (editando) {
      const payload: CategoriaActualizarPayload = {
        nombre: nombre.trim(),
        id_categoria_padre: id_categoria_padre || 0,
      };
      this.atributosService.actualizarCategoria(editando.id_categoria, payload).subscribe({
        next: () => {
          this.cerrarModalCategoria();
          this.cdr.markForCheck();
        },
        error: (err: Error) => {
          this.notificacionConflicto.set(err.message);
          this.cdr.markForCheck();
        },
      });
    } else {
      const payload: CategoriaCrearPayload = {
        nombre: nombre.trim(),
        id_categoria_padre: id_categoria_padre,
      };
      this.atributosService.crearCategoria(payload).subscribe({
        next: () => {
          this.cerrarModalCategoria();
          this.cdr.markForCheck();
        },
        error: (err: Error) => {
          this.notificacionConflicto.set(err.message);
          this.cdr.markForCheck();
        },
      });
    }
  }

  // =========================================================================
  // GESTION MODALES: TALLAS
  // =========================================================================

  abrirModalTalla(talla?: TallaAdmin): void {
    this.notificacionConflicto.set(null);
    if (talla) {
      this.tallaEnEdicion.set(talla);
      this.tallaForm.setValue({
        codigo: talla.codigo,
        orden: talla.orden,
      });
    } else {
      this.tallaEnEdicion.set(null);
      const siguienteOrden = this.tallas().length > 0
        ? Math.max(...this.tallas().map((t) => t.orden)) + 1
        : 1;
      this.tallaForm.reset({
        codigo: '',
        orden: siguienteOrden,
      });
    }
    this.modalTallaAbierto.set(true);
  }

  cerrarModalTalla(): void {
    this.modalTallaAbierto.set(false);
    this.tallaEnEdicion.set(null);
    this.tallaForm.reset();
  }

  onCodigoTallaInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input) {
      const valor = input.value.toUpperCase();
      this.tallaForm.controls.codigo.setValue(valor, { emitEvent: false });
    }
  }

  guardarTalla(): void {
    if (this.tallaForm.invalid) {
      this.tallaForm.markAllAsTouched();
      return;
    }

    const { codigo, orden } = this.tallaForm.getRawValue();
    const editando = this.tallaEnEdicion();

    if (editando) {
      const payload: TallaActualizarPayload = {
        codigo: codigo.trim().toUpperCase(),
        orden,
      };
      this.atributosService.actualizarTalla(editando.id_talla, payload).subscribe({
        next: () => {
          this.cerrarModalTalla();
          this.cdr.markForCheck();
        },
        error: (err: Error) => {
          this.notificacionConflicto.set(err.message);
          this.cdr.markForCheck();
        },
      });
    } else {
      const payload: TallaCrearPayload = {
        codigo: codigo.trim().toUpperCase(),
        orden,
      };
      this.atributosService.crearTalla(payload).subscribe({
        next: () => {
          this.cerrarModalTalla();
          this.cdr.markForCheck();
        },
        error: (err: Error) => {
          this.notificacionConflicto.set(err.message);
          this.cdr.markForCheck();
        },
      });
    }
  }

  // =========================================================================
  // GESTION MODALES: COLORES Y SINCRONIZACION SWATCH
  // =========================================================================

  abrirModalColor(color?: ColorAdmin): void {
    this.notificacionConflicto.set(null);
    if (color) {
      this.colorEnEdicion.set(color);
      this.colorForm.setValue({
        nombre: color.nombre,
        codigo_hex: color.codigo_hex,
      });
    } else {
      this.colorEnEdicion.set(null);
      this.colorForm.reset({
        nombre: '',
        codigo_hex: '#1E293B',
      });
    }
    this.modalColorAbierto.set(true);
  }

  cerrarModalColor(): void {
    this.modalColorAbierto.set(false);
    this.colorEnEdicion.set(null);
    this.colorForm.reset();
  }

  actualizarHexDesdePicker(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input && input.value) {
      this.colorForm.controls.codigo_hex.setValue(input.value.toUpperCase());
    }
  }

  onHexTextInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input) {
      let valor = input.value.trim().toUpperCase();
      if (!valor.startsWith('#') && valor.length > 0) {
        valor = '#' + valor;
      }
      this.colorForm.controls.codigo_hex.setValue(valor, { emitEvent: false });
    }
  }

  guardarColor(): void {
    if (this.colorForm.invalid) {
      this.colorForm.markAllAsTouched();
      return;
    }

    const { nombre, codigo_hex } = this.colorForm.getRawValue();
    const editando = this.colorEnEdicion();

    if (editando) {
      const payload: ColorActualizarPayload = {
        nombre: nombre.trim(),
        codigo_hex: codigo_hex.trim().toUpperCase(),
      };
      this.atributosService.actualizarColor(editando.id_color, payload).subscribe({
        next: () => {
          this.cerrarModalColor();
          this.cdr.markForCheck();
        },
        error: (err: Error) => {
          this.notificacionConflicto.set(err.message);
          this.cdr.markForCheck();
        },
      });
    } else {
      const payload: ColorCrearPayload = {
        nombre: nombre.trim(),
        codigo_hex: codigo_hex.trim().toUpperCase(),
      };
      this.atributosService.crearColor(payload).subscribe({
        next: () => {
          this.cerrarModalColor();
          this.cdr.markForCheck();
        },
        error: (err: Error) => {
          this.notificacionConflicto.set(err.message);
          this.cdr.markForCheck();
        },
      });
    }
  }

  // =========================================================================
  // GESTION ELIMINACION
  // =========================================================================

  abrirConfirmarEliminar(tipo: TipoAtributo, id: number, nombre: string): void {
    this.notificacionConflicto.set(null);
    this.elementoAEliminar.set({ tipo, id, nombre });
    this.modalEliminarAbierto.set(true);
  }

  cerrarModalEliminar(): void {
    this.modalEliminarAbierto.set(false);
    this.elementoAEliminar.set(null);
  }

  confirmarEliminacion(): void {
    const item = this.elementoAEliminar();
    if (!item) return;

    if (item.tipo === 'categorias') {
      this.atributosService.eliminarCategoria(item.id).subscribe({
        next: () => {
          this.cerrarModalEliminar();
          this.cdr.markForCheck();
        },
        error: (err: Error) => {
          this.notificacionConflicto.set(err.message);
          this.cerrarModalEliminar();
          this.cdr.markForCheck();
        },
      });
    } else if (item.tipo === 'tallas') {
      this.atributosService.eliminarTalla(item.id).subscribe({
        next: () => {
          this.cerrarModalEliminar();
          this.cdr.markForCheck();
        },
        error: (err: Error) => {
          this.notificacionConflicto.set(err.message);
          this.cerrarModalEliminar();
          this.cdr.markForCheck();
        },
      });
    } else if (item.tipo === 'colores') {
      this.atributosService.eliminarColor(item.id).subscribe({
        next: () => {
          this.cerrarModalEliminar();
          this.cdr.markForCheck();
        },
        error: (err: Error) => {
          this.notificacionConflicto.set(err.message);
          this.cerrarModalEliminar();
          this.cdr.markForCheck();
        },
      });
    }
  }

  cerrarAlertaConflicto(): void {
    this.notificacionConflicto.set(null);
    this.atributosService.limpiarMensajes();
  }
}
