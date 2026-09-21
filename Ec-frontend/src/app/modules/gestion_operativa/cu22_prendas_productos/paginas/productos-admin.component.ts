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
import { ProductosAdminService } from '../servicios/productos-admin.service';
import { AtributosAdminService } from '../../cu23_categorias_tallas_colores/servicios/atributos-admin.service';
import { CategoriaAdmin } from '../../cu23_categorias_tallas_colores/modelos/atributos.dto';
import {
  MatrizVariantesPayload,
  ProductoActualizarPayload,
  ProductoCrearPayload,
  ProductoDetalleAdmin,
  ProductoResumenAdmin,
  VarianteAdmin,
  VarianteEdicionItem,
} from '../modelos/producto.dto';

function slugifyTexto(texto: string, maxLen = 16): string {
  if (!texto) return '';
  return texto
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-zA-Z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .toUpperCase()
    .slice(0, maxLen);
}

@Component({
  selector: 'app-productos-admin',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './productos-admin.component.html',
  styleUrls: ['./productos-admin.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProductosAdminComponent implements OnInit {
  protected readonly productosService = inject(ProductosAdminService);
  protected readonly atributosService = inject(AtributosAdminService);
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly cdr = inject(ChangeDetectorRef);

  // --- Signals de Estado de Filtros ---
  readonly filtroBusqueda = signal<string>('');
  readonly filtroCategoria = signal<number | null>(null);
  readonly filtroActivo = signal<boolean | null>(null);

  // --- Signals de Modales ---
  readonly modalPrendaAbierto = signal<boolean>(false);
  readonly modalMatrizAbierto = signal<boolean>(false);
  readonly modalEliminarAbierto = signal<boolean>(false);

  // --- Elementos Seleccionados / En Edicion ---
  readonly prendaEnEdicion = signal<ProductoResumenAdmin | null>(null);
  readonly prendaSeleccionada = signal<ProductoResumenAdmin | null>(null);
  readonly prendaAEliminar = signal<ProductoResumenAdmin | null>(null);

  // --- Luxury Banners / Notificaciones ---
  readonly notificacionConflicto = signal<string | null>(null);

  // --- Signals Heredadas de Servicios ---
  readonly productos = this.productosService.productos;
  readonly productoDetalle = this.productosService.productoSeleccionado;
  readonly variantes = this.productosService.variantes;
  readonly cargando = this.productosService.cargando;
  readonly guardando = this.productosService.guardando;
  readonly error = this.productosService.error;
  readonly mensajeExito = this.productosService.mensajeExito;

  readonly categorias = this.atributosService.categorias;
  readonly tallas = this.atributosService.tallas;
  readonly colores = this.atributosService.colores;

  // --- Formulario Reactivo de Prenda ---
  readonly formPrenda = this.fb.group({
    nombre: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(200)]],
    id_categoria: [0, [Validators.required, Validators.min(1)]],
    precio_base: [0, [Validators.required, Validators.min(0.01)]],
    descripcion: [''],
    imagen_url: [''],
    activo: [true],
  });

  // --- Signals de Gestion y Carga de Imagen ---
  readonly subiendoImagen = signal<boolean>(false);
  readonly previsualizacionImagen = signal<string | null>(null);
  readonly modoUrlManual = signal<boolean>(false);
  readonly arrastrandoArchivo = signal<boolean>(false);

  // --- Estado Reactivo del Generador de Matriz ---
  readonly tallasSeleccionadas = signal<number[]>([]);
  readonly coloresSeleccionados = signal<number[]>([]);
  readonly precioExtraDefecto = signal<number>(0);
  readonly variantesMatrizGeneradas = signal<VarianteEdicionItem[]>([]);

  // --- Computed de Filtro de Productos ---
  readonly productosFiltrados = computed(() => {
    const q = this.filtroBusqueda().trim().toLowerCase();
    const idCat = this.filtroCategoria();
    const act = this.filtroActivo();

    return this.productos().filter((p) => {
      const coincideTexto =
        !q ||
        p.nombre.toLowerCase().includes(q) ||
        (p.descripcion && p.descripcion.toLowerCase().includes(q)) ||
        (p.categoria_nombre && p.categoria_nombre.toLowerCase().includes(q));

      const coincideCat = idCat === null || p.id_categoria === idCat;
      const coincideAct = act === null || p.activo === act;

      return coincideTexto && coincideCat && coincideAct;
    });
  });

  // Categorias ordenadas para selector jerarquico
  readonly categoriasRaiz = computed(() => {
    return this.categorias().filter((c) => !c.id_categoria_padre);
  });

  readonly subcategoriasPorPadre = computed(() => {
    const mapa = new Map<number, CategoriaAdmin[]>();
    for (const c of this.categorias()) {
      if (c.id_categoria_padre) {
        const sub = mapa.get(c.id_categoria_padre) || [];
        sub.push(c);
        mapa.set(c.id_categoria_padre, sub);
      }
    }
    return mapa;
  });

  ngOnInit(): void {
    this.cargarDatosIniciales();
  }

  cargarDatosIniciales(): void {
    this.productosService.cargarProductos().subscribe();
    this.atributosService.cargarCategorias().subscribe();
    this.atributosService.cargarTallas().subscribe();
    this.atributosService.cargarColores().subscribe();
  }

  // =========================================================================
  // GESTION DE PRENDA (ALTA / EDICION)
  // =========================================================================

  abrirCrearPrenda(): void {
    this.prendaEnEdicion.set(null);
    this.notificacionConflicto.set(null);
    this.formPrenda.reset({
      nombre: '',
      id_categoria: this.categorias().length > 0 ? this.categorias()[0].id_categoria : 0,
      precio_base: 0,
      descripcion: '',
      imagen_url: '',
      activo: true,
    });
    this.previsualizacionImagen.set(null);
    this.modoUrlManual.set(false);
    this.subiendoImagen.set(false);
    this.arrastrandoArchivo.set(false);
    this.modalPrendaAbierto.set(true);
  }

  abrirEditarPrenda(prenda: ProductoResumenAdmin): void {
    this.prendaEnEdicion.set(prenda);
    this.notificacionConflicto.set(null);
    this.formPrenda.reset({
      nombre: prenda.nombre,
      id_categoria: prenda.id_categoria,
      precio_base: prenda.precio_base,
      descripcion: prenda.descripcion || '',
      imagen_url: prenda.imagen_url || '',
      activo: prenda.activo,
    });
    this.previsualizacionImagen.set(prenda.imagen_url || null);
    this.modoUrlManual.set(false);
    this.subiendoImagen.set(false);
    this.arrastrandoArchivo.set(false);
    this.modalPrendaAbierto.set(true);
  }

  cerrarModalPrenda(): void {
    this.modalPrendaAbierto.set(false);
    this.prendaEnEdicion.set(null);
    this.notificacionConflicto.set(null);
    this.previsualizacionImagen.set(null);
    this.modoUrlManual.set(false);
    this.subiendoImagen.set(false);
    this.arrastrandoArchivo.set(false);
  }

  guardarPrenda(): void {
    if (this.formPrenda.invalid) {
      this.formPrenda.markAllAsTouched();
      return;
    }

    const val = this.formPrenda.getRawValue();
    const edicion = this.prendaEnEdicion();
    const urlImagenFinal = val.imagen_url ? val.imagen_url.trim() : null;

    if (edicion) {
      const payload: ProductoActualizarPayload = {
        nombre: val.nombre,
        id_categoria: val.id_categoria,
        precio_base: val.precio_base,
        descripcion: val.descripcion || null,
        imagen_url: urlImagenFinal,
        activo: val.activo,
      };

      this.productosService.actualizarProducto(edicion.id_producto, payload).subscribe({
        next: () => {
          this.cerrarModalPrenda();
        },
        error: (err) => {
          const msg =
            err.error?.detail || err.error?.message || 'Error al actualizar la prenda comercial.';
          this.notificacionConflicto.set(msg);
          this.cdr.markForCheck();
        },
      });
    } else {
      const payload: ProductoCrearPayload = {
        nombre: val.nombre,
        id_categoria: val.id_categoria,
        precio_base: val.precio_base,
        descripcion: val.descripcion || null,
        imagen_url: urlImagenFinal,
        activo: val.activo,
      };

      this.productosService.crearProducto(payload).subscribe({
        next: () => {
          this.cerrarModalPrenda();
        },
        error: (err) => {
          const msg =
            err.error?.detail || err.error?.message || 'Error al registrar la prenda en el catalogo.';
          this.notificacionConflicto.set(msg);
          this.cdr.markForCheck();
        },
      });
    }
  }

  cambiarEstadoPrenda(prenda: ProductoResumenAdmin, activo: boolean): void {
    this.productosService.cambiarEstadoProducto(prenda.id_producto, activo).subscribe();
  }

  abrirModalEliminar(prenda: ProductoResumenAdmin): void {
    this.prendaAEliminar.set(prenda);
    this.notificacionConflicto.set(null);
    this.modalEliminarAbierto.set(true);
  }

  cerrarModalEliminar(): void {
    this.modalEliminarAbierto.set(false);
    this.prendaAEliminar.set(null);
    this.notificacionConflicto.set(null);
  }

  confirmarEliminarPrenda(): void {
    const prenda = this.prendaAEliminar();
    if (!prenda) return;

    this.productosService.eliminarProducto(prenda.id_producto).subscribe({
      next: () => {
        this.cerrarModalEliminar();
      },
      error: (err) => {
        const msg =
          err.error?.detail ||
          err.error?.message ||
          'No se puede eliminar la prenda porque posee dependencias operativas o inventario.';
        this.notificacionConflicto.set(msg);
        this.cdr.markForCheck();
      },
    });
  }

  // =========================================================================
  // GENERADOR INTERACTIVO DE MATRIZ DE VARIANTES (SKUs)
  // =========================================================================

  abrirModalMatriz(prenda: ProductoResumenAdmin): void {
    this.prendaSeleccionada.set(prenda);
    this.notificacionConflicto.set(null);
    this.tallasSeleccionadas.set([]);
    this.coloresSeleccionados.set([]);
    this.precioExtraDefecto.set(0);
    this.variantesMatrizGeneradas.set([]);
    this.modalMatrizAbierto.set(true);

    // Cargar variantes actuales para referencia
    this.productosService.cargarProductoPorId(prenda.id_producto).subscribe();
  }

  cerrarModalMatriz(): void {
    this.modalMatrizAbierto.set(false);
    this.prendaSeleccionada.set(null);
    this.notificacionConflicto.set(null);
    this.variantesMatrizGeneradas.set([]);
  }

  toggleTalla(idTalla: number): void {
    const actuales = this.tallasSeleccionadas();
    if (actuales.includes(idTalla)) {
      this.tallasSeleccionadas.set(actuales.filter((id) => id !== idTalla));
    } else {
      this.tallasSeleccionadas.set([...actuales, idTalla]);
    }
  }

  toggleColor(idColor: number): void {
    const actuales = this.coloresSeleccionados();
    if (actuales.includes(idColor)) {
      this.coloresSeleccionados.set(actuales.filter((id) => id !== idColor));
    } else {
      this.coloresSeleccionados.set([...actuales, idColor]);
    }
  }

  generarCombinaciones(): void {
    const prenda = this.prendaSeleccionada();
    if (!prenda) return;

    const idsTallas = this.tallasSeleccionadas();
    const idsColores = this.coloresSeleccionados();
    if (idsTallas.length === 0 || idsColores.length === 0) {
      this.notificacionConflicto.set(
        'Debe seleccionar al menos una talla y un color para generar combinaciones.'
      );
      return;
    }

    this.notificacionConflicto.set(null);
    const tallasMap = new Map(this.tallas().map((t) => [t.id_talla, t]));
    const coloresMap = new Map(this.colores().map((c) => [c.id_color, c]));

    const filas: VarianteEdicionItem[] = [];
    const basePrice = prenda.precio_base;
    const extraDefault = Number(this.precioExtraDefecto()) || 0;

    for (const idTalla of idsTallas) {
      for (const idColor of idsColores) {
        const talla = tallasMap.get(idTalla);
        const color = coloresMap.get(idColor);
        if (!talla || !color) continue;

        const sku = `FS-${slugifyTexto(prenda.nombre, 18)}-${slugifyTexto(
          talla.codigo,
          8
        )}-${slugifyTexto(color.nombre, 10)}`;

        filas.push({
          id_talla: idTalla,
          talla_codigo: talla.codigo,
          id_color: idColor,
          color_nombre: color.nombre,
          color_hex: color.codigo_hex,
          sku,
          precio_extra: extraDefault,
          precio_final: basePrice + extraDefault,
        });
      }
    }

    this.variantesMatrizGeneradas.set(filas);
  }

  eliminarFilaMatriz(index: number): void {
    this.variantesMatrizGeneradas.update((filas) => filas.filter((_, i) => i !== index));
  }

  actualizarPrecioExtraFila(index: number, nuevoExtraStr: string): void {
    const nuevoExtra = parseFloat(nuevoExtraStr) || 0;
    const prenda = this.prendaSeleccionada();
    const basePrice = prenda ? prenda.precio_base : 0;

    this.variantesMatrizGeneradas.update((filas) =>
      filas.map((f, i) => {
        if (i === index) {
          return {
            ...f,
            precio_extra: nuevoExtra,
            precio_final: basePrice + nuevoExtra,
          };
        }
        return f;
      })
    );
  }

  guardarMatrizLote(): void {
    const prenda = this.prendaSeleccionada();
    const filas = this.variantesMatrizGeneradas();
    if (!prenda || filas.length === 0) return;

    const idsTallas = Array.from(new Set(filas.map((f) => f.id_talla)));
    const idsColores = Array.from(new Set(filas.map((f) => f.id_color)));
    const extraDefecto = Number(this.precioExtraDefecto()) || 0;

    const payload: MatrizVariantesPayload = {
      ids_tallas: idsTallas,
      ids_colores: idsColores,
      precio_extra_defecto: extraDefecto,
    };

    this.productosService.generarMatrizVariantes(prenda.id_producto, payload).subscribe({
      next: () => {
        // Refrescar listado de productos para actualizar contadores
        this.productosService.cargarProductos().subscribe();
        this.cerrarModalMatriz();
      },
      error: (err) => {
        const msg =
          err.error?.detail ||
          err.error?.message ||
          'Error al registrar variantes. Verifique que no existan combinaciones o SKUs duplicados.';
        this.notificacionConflicto.set(msg);
        this.cdr.markForCheck();
      },
    });
  }

  eliminarVarianteExistente(v: VarianteAdmin): void {
    this.productosService.eliminarVariante(v.id_variante).subscribe({
      next: () => {
        this.productosService.cargarProductos().subscribe();
      },
      error: (err) => {
        const msg =
          err.error?.detail ||
          err.error?.message ||
          'No se puede eliminar la variante porque posee inventario o transacciones.';
        this.notificacionConflicto.set(msg);
        this.cdr.markForCheck();
      },
    });
  }

  cambiarEstadoVarianteExistente(v: VarianteAdmin, activo: boolean): void {
    this.productosService.cambiarEstadoVariante(v.id_variante, activo).subscribe();
  }

  // =========================================================================
  // GESTION DE CARGA DE IMAGEN (FILE UPLOAD / DROPZONE)
  // =========================================================================

  onArchivoSeleccionado(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input?.files && input.files.length > 0) {
      this.procesarArchivo(input.files[0]);
    }
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.arrastrandoArchivo.set(true);
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.arrastrandoArchivo.set(false);
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.arrastrandoArchivo.set(false);
    if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
      this.procesarArchivo(event.dataTransfer.files[0]);
    }
  }

  procesarArchivo(archivo: File): void {
    const formatosPermitidos = ['image/jpeg', 'image/png', 'image/webp'];
    if (!formatosPermitidos.includes(archivo.type)) {
      this.notificacionConflicto.set(
        'Formato no permitido. Solo se admiten imagenes en formato JPEG, PNG o WebP.'
      );
      this.cdr.markForCheck();
      return;
    }

    const maxTamano = 5 * 1024 * 1024; // 5 MB
    if (archivo.size > maxTamano) {
      this.notificacionConflicto.set(
        'El archivo supera el limite maximo permitido de 5 MB.'
      );
      this.cdr.markForCheck();
      return;
    }

    this.notificacionConflicto.set(null);
    this.subiendoImagen.set(true);

    if (typeof FileReader !== 'undefined') {
      const reader = new FileReader();
      reader.onload = () => {
        this.previsualizacionImagen.set(reader.result as string);
        this.cdr.markForCheck();
      };
      reader.readAsDataURL(archivo);
    }

    this.productosService.subirImagen(archivo).subscribe({
      next: (resp) => {
        this.subiendoImagen.set(false);
        this.formPrenda.controls.imagen_url.setValue(resp.url);
        this.previsualizacionImagen.set(resp.url);
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.subiendoImagen.set(false);
        const msg =
          err.error?.detail || err.error?.message || 'Error al subir la imagen al servidor.';
        this.notificacionConflicto.set(msg);
        this.cdr.markForCheck();
      },
    });
  }

  quitarImagen(): void {
    this.formPrenda.controls.imagen_url.setValue('');
    this.previsualizacionImagen.set(null);
    this.cdr.markForCheck();
  }

  toggleModoUrlManual(): void {
    this.modoUrlManual.update((v) => !v);
  }

  onUrlManualChange(url: string): void {
    const urlLimpia = url.trim();
    this.formPrenda.controls.imagen_url.setValue(urlLimpia);
    this.previsualizacionImagen.set(urlLimpia ? urlLimpia : null);
    this.cdr.markForCheck();
  }
}
