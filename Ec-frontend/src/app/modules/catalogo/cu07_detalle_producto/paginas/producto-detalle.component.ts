import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { CommonModule, Location } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ProductoDetalleService } from '../servicios/producto-detalle.service';
import {
  DisponibilidadSucursales,
  GaleriaToma,
  ProductoDetalle,
  ReservaConfirmacion,
  TallaResumen,
  VarianteDetalle,
} from '../modelos/producto-detalle.model';
import { ModalReservaBoutiqueComponent } from '../componentes/modal-reserva-boutique/modal-reserva-boutique.component';
import { CatalogoService } from '../../servicios/catalogo.service';
import { CarritoService } from '../../../compras_pagos/cu11_gestionar_carrito/servicios/carrito.service';

@Component({
  selector: 'app-producto-detalle',
  standalone: true,
  imports: [CommonModule, RouterLink, ModalReservaBoutiqueComponent],
  templateUrl: './producto-detalle.component.html',
  styleUrls: ['./producto-detalle.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProductoDetalleComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly location = inject(Location);
  private readonly detalleService = inject(ProductoDetalleService);
  private readonly catalogoService = inject(CatalogoService);
  private readonly carritoService = inject(CarritoService);

  // --- Signals de Estado de Ficha ---
  protected readonly cargando = signal<boolean>(true);
  protected readonly error = signal<string | null>(null);
  /** Evita dobles altas si el cliente pulsa «añadir» repetidamente. */
  protected readonly anadiendoABolsa = signal<boolean>(false);

  protected readonly producto = signal<ProductoDetalle | null>(null);
  protected readonly varianteActiva = signal<VarianteDetalle | null>(null);
  protected readonly colorSeleccionadoId = signal<number | null>(null);
  protected readonly imagenPrincipal = signal<string>('');
  protected readonly tomaActivaIndice = signal<number>(0);

  protected readonly disponibilidad = signal<DisponibilidadSucursales | null>(null);
  protected readonly modalReservaAbierto = signal<boolean>(false);
  protected readonly modalARAbierto = signal<boolean>(false);

  protected readonly esFavorito = signal<boolean>(false);
  protected readonly totalGuardados = signal<number>(142);
  protected readonly mensajeToast = signal<string | null>(null);

  // --- Computeds ---
  protected readonly textoDisponibilidad = computed(() => {
    const disp = this.disponibilidad();
    const v = this.varianteActiva();
    if (!disp || !v) {
      return 'Consultando existencias en boutiques...';
    }

    const sucsConStock = disp.sucursales.filter((s) => s.cantidad_disponible > 0);
    if (sucsConStock.length === 0) {
      return 'Agotada para salida inmediata en boutiques. Admite confección a medida bajo pedido.';
    }

    const detalleSedes = sucsConStock
      .slice(0, 2)
      .map((s) => `${s.cantidad_disponible} unidad${s.cantidad_disponible > 1 ? 'es' : ''} en ${s.nombre}`)
      .join(' y ');

    return `${detalleSedes}. Salida inmediata disponible.`;
  });

  protected readonly sucursalesActivas = computed(() => {
    return this.disponibilidad()?.sucursales || [];
  });

  /**
   * Tallas disponibles EXCLUSIVAMENTE para el color seleccionado.
   * Filtra las variantes por colorSeleccionadoId y expone únicamente las tallas correspondientes.
   */
  protected readonly tallasDisponiblesParaColor = computed<TallaResumen[]>(() => {
    const prod = this.producto();
    const colorId = this.colorSeleccionadoId() ?? this.varianteActiva()?.id_color;
    if (!prod) return [];
    if (!colorId) return prod.tallas_disponibles;

    const variantesColor = prod.variantes.filter((v) => v.id_color === colorId);
    const tallasMap = new Map<number, TallaResumen>();

    for (const v of variantesColor) {
      if (!tallasMap.has(v.id_talla)) {
        tallasMap.set(v.id_talla, {
          id_talla: v.id_talla,
          codigo: v.talla_codigo,
          orden: v.talla_orden,
          disponible: v.tiene_stock,
          stock_total: v.stock_total_disponible,
        });
      }
    }

    return Array.from(tallasMap.values()).sort((a, b) => a.orden - b.orden);
  });

  /**
   * Precio acumulado del look complementario Atelier.
   */
  protected readonly totalLookPrecio = computed<string>(() => {
    const prod = this.producto();
    if (!prod) return '0.00';
    let total = Number(prod.precio_final || 0);
    for (const comp of prod.piezas_look_complementario || []) {
      total += Number(comp.precio_final || 0);
    }
    return total.toFixed(2);
  });

  /**
   * Galería de tomas de la MISMA prenda seleccionada en diferentes ángulos:
   * Toma 1: Frontal de la prenda.
   * Toma 2: Detalle macro del tejido / cuello / escote de la misma prenda.
   * Toma 3: Silueta y caída del drapeado de la misma prenda.
   * Toma 4: Acabado inferior de costura y bajo de la misma prenda.
   */
  protected readonly galeriaPrenda = computed<GaleriaToma[]>(() => {
    const prod = this.producto();
    if (!prod || !prod.imagen_principal) return [];

    const imgBase = prod.imagen_principal;
    const cleanUrl = imgBase.split('?')[0];

    const tomas: GaleriaToma[] = [
      {
        url: imgBase,
        etiqueta: 'FRONTAL',
        orden: 1,
      },
      {
        url: `${cleanUrl}?auto=format&fit=crop&w=1000&h=1200&crop=top&q=85`,
        etiqueta: 'DETALLE TEJIDO',
        orden: 2,
      },
      {
        url: `${cleanUrl}?auto=format&fit=crop&w=1000&h=1200&crop=center&q=85`,
        etiqueta: 'SILUETA & CAÍDA',
        orden: 3,
      },
      {
        url: `${cleanUrl}?auto=format&fit=crop&w=1000&h=1200&crop=bottom&q=85`,
        etiqueta: 'ACABADO & COSTURA',
        orden: 4,
      },
    ];

    return tomas;
  });

  ngOnInit(): void {
    this.route.paramMap.subscribe((params) => {
      const idParam = params.get('id');
      const id = idParam ? parseInt(idParam, 10) : 10;
      this.cargarProducto(id);
    });
  }

  /**
   * Carga la ficha de alta costura desde el backend FastAPI.
   */
  cargarProducto(id: number): void {
    this.cargando.set(true);
    this.error.set(null);

    this.detalleService.obtenerDetalle(id).subscribe({
      next: (data) => {
        this.producto.set(data);
        this.imagenPrincipal.set(data.imagen_principal);
        this.totalGuardados.set(data.total_guardados || 142);
        this.tomaActivaIndice.set(0);

        // Seleccionar por defecto la primera variante con existencias o la primera
        const varianteInicial =
          data.variantes.find((v) => v.tiene_stock) || data.variantes[0] || null;
        this.varianteActiva.set(varianteInicial);

        if (varianteInicial) {
          this.colorSeleccionadoId.set(varianteInicial.id_color);
          this.consultarDisponibilidadVariante(data.id_producto, varianteInicial.id_variante);
        } else if (data.colores_disponibles.length > 0) {
          this.colorSeleccionadoId.set(data.colores_disponibles[0].id_color);
        }

        this.cargando.set(false);
      },
      error: (err) => {
        this.cargando.set(false);
        this.error.set(
          err.status === 404
            ? 'La prenda de alta costura solicitada no se encuentra disponible o ha sido retirada del catálogo.'
            : 'No fue posible conectar con el atelier. Por favor, reintenta más tarde.'
        );
      },
    });
  }

  /**
   * Consulta disponibilidad multisede para la variante seleccionada.
   */
  private consultarDisponibilidadVariante(idProducto: number, idVariante: number): void {
    this.detalleService.obtenerDisponibilidad(idProducto, idVariante).subscribe({
      next: (disp) => {
        this.disponibilidad.set(disp);
      },
      error: (err) => {
        console.warn('No se pudo cargar disponibilidad multisede:', err);
      },
    });
  }

  /**
   * Cambia la fotografía principal activa al hacer clic en una miniatura de la galería.
   */
  seleccionarToma(url: string, index: number): void {
    this.imagenPrincipal.set(url);
    this.tomaActivaIndice.set(index);
  }

  /**
   * Selecciona un color, actualiza la imagen a ese color y ajusta la variante y tallas.
   */
  seleccionarColor(idColor: number): void {
    const prod = this.producto();
    if (!prod) return;

    this.colorSeleccionadoId.set(idColor);

    // Variantes asociadas a este color
    const variantesColor = prod.variantes.filter((v) => v.id_color === idColor);
    if (variantesColor.length === 0) return;

    // Intentar conservar la talla seleccionada si existe en este nuevo color
    const tallaActualId = this.varianteActiva()?.id_talla;
    let nuevaVariante = variantesColor.find((v) => v.id_talla === tallaActualId);

    // Si la talla no existe en este color, seleccionar la primera con existencias o la primera
    if (!nuevaVariante) {
      nuevaVariante = variantesColor.find((v) => v.tiene_stock) || variantesColor[0];
    }

    this.varianteActiva.set(nuevaVariante);

    // Actualizar imagen principal al color seleccionado
    const colorObj = prod.colores_disponibles.find((c) => c.id_color === idColor);
    const nuevaFoto = nuevaVariante.imagen_url || colorObj?.imagen_url;
    if (nuevaFoto) {
      this.imagenPrincipal.set(nuevaFoto);
      this.tomaActivaIndice.set(0);
    }

    if (nuevaVariante) {
      this.consultarDisponibilidadVariante(prod.id_producto, nuevaVariante.id_variante);
    }
  }

  /**
   * Selecciona una talla de entre las disponibles para el color activo.
   */
  seleccionarTalla(idTalla: number): void {
    const prod = this.producto();
    if (!prod) return;

    const colorActualId = this.colorSeleccionadoId() ?? this.varianteActiva()?.id_color;

    // Buscar variante para el color actual y la talla seleccionada
    const coincidencia =
      prod.variantes.find((v) => v.id_color === colorActualId && v.id_talla === idTalla) ||
      prod.variantes.find((v) => v.id_talla === idTalla) ||
      null;

    if (coincidencia) {
      this.varianteActiva.set(coincidencia);
      this.consultarDisponibilidadVariante(prod.id_producto, coincidencia.id_variante);
    }
  }

  /**
   * Añade la prenda seleccionada a la bolsa de compras (CU11).
   *
   * Hasta el 2026-09-22 esto solo mostraba un aviso: la prenda nunca llegaba a persistirse, de
   * modo que la pantalla de Bolsa de Compra jamás habría tenido contenido que mostrar. Ahora
   * escribe en `carrito_detalle` mediante `POST /api/v1/carrito/items`.
   */
  anadirABolsa(): void {
    const prod = this.producto();
    const variante = this.varianteActiva();
    if (!prod || !variante || this.anadiendoABolsa()) return;

    // No se envía `id_sucursal`: el backend resuelve la boutique con mayor disponibilidad para
    // esa variante en la temporada vigente. El cliente puede revisarla después en la bolsa.
    this.anadiendoABolsa.set(true);
    this.carritoService
      .agregarItem({ id_variante: variante.id_variante, cantidad: 1 })
      .subscribe({
        next: () => {
          this.anadiendoABolsa.set(false);
          this.mostrarNotificacion(
            `✓ Añadido a la bolsa: ${prod.nombre} (Talla ${variante.talla_codigo})`
          );
        },
        error: (err) => {
          this.anadiendoABolsa.set(false);
          if (err?.status === 401) {
            this.mostrarNotificacion(
              'Inicia sesión para guardar prendas en tu bolsa de compra.'
            );
            return;
          }
          this.mostrarNotificacion(
            this.carritoService.error() ??
              'No fue posible añadir la prenda a tu bolsa. Inténtalo de nuevo.'
          );
        },
      });
  }

  /** Navega a la Bolsa de Compra desde la ficha de producto. */
  irABolsa(): void {
    this.router.navigate(['/bolsa']);
  }

  /**
   * Alterna estado de favorito/guardado.
   */
  toggleFavorito(): void {
    const nuevo = !this.esFavorito();
    this.esFavorito.set(nuevo);
    this.totalGuardados.update((c) => (nuevo ? c + 1 : c - 1));
    this.mostrarNotificacion(
      nuevo
        ? '✓ Prenda guardada en tus piezas predilectas de atelier'
        : 'Pieza retirada de tu lista de guardados'
    );
  }

  /**
   * Retorno nativo con Location.back() respetando el patrón Hub-and-Spoke.
   */
  volver(): void {
    this.location.back();
  }

  /**
   * Abre modal de reserva en boutique (CU12).
   */
  abrirModalReserva(): void {
    this.modalReservaAbierto.set(true);
  }

  /**
   * Cierra modal de reserva.
   */
  cerrarModalReserva(): void {
    this.modalReservaAbierto.set(false);
  }

  /**
   * Abre modal informativo del probador AR (CU10).
   */
  abrirModalAR(): void {
    this.modalARAbierto.set(true);
  }

  /**
   * Cierra modal AR.
   */
  cerrarModalAR(): void {
    this.modalARAbierto.set(false);
  }

  /**
   * Maneja la confirmación exitosa de la reserva.
   */
  onReservaConfirmada(confirmacion: ReservaConfirmacion): void {
    this.mostrarNotificacion(
      `✓ Cita confirmada (${confirmacion.codigo_reserva}) en ${confirmacion.nombre_sucursal}`
    );
  }

  private mostrarNotificacion(mensaje: string): void {
    this.mensajeToast.set(mensaje);
    setTimeout(() => {
      this.mensajeToast.set(null);
    }, 4000);
  }
}
