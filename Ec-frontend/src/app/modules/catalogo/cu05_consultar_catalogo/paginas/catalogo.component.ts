import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { CatalogoService } from '../../servicios/catalogo.service';
import {
  CategoriaResumenItem,
  ProductoCatalogoItem,
} from '../modelos/catalogo.model';

@Component({
  selector: 'app-catalogo',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './catalogo.component.html',
  styleUrls: ['./catalogo.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CatalogoComponent implements OnInit {
  private readonly catalogoService = inject(CatalogoService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  // --- Signals de Estado Reactivo ---
  protected readonly cargando = signal<boolean>(false);
  protected readonly error = signal<string | null>(null);

  protected readonly resumenCategorias = signal<CategoriaResumenItem[]>([]);
  protected readonly categoriaSeleccionada = signal<number | null>(null);
  protected readonly productos = signal<ProductoCatalogoItem[]>([]);

  protected readonly paginaActual = signal<number>(1);
  protected readonly limite = signal<number>(8);
  protected readonly totalArticulos = signal<number>(0);
  protected readonly totalPaginas = signal<number>(1);
  protected readonly tieneSiguiente = signal<boolean>(false);
  protected readonly tieneAnterior = signal<boolean>(false);

  protected readonly ordenarPor = signal<string>('recientes');
  protected readonly vistaColumnas = signal<'grid4' | 'grid2'>('grid4');

  protected readonly favoritos = signal<Set<number>>(new Set());
  protected readonly mensajeFeedback = signal<string | null>(null);

  // --- Computeds ---
  protected readonly totalGlobalPrendas = computed(() => {
    return this.resumenCategorias().reduce((acc, cat) => acc + cat.total_prendas, 0);
  });

  protected readonly categoriaSeleccionadaNombre = computed(() => {
    const catId = this.categoriaSeleccionada();
    if (!catId) return 'Todas las Prendas';
    const cat = this.resumenCategorias().find((c) => c.id_categoria === catId);
    return cat ? cat.nombre : 'Categoría Seleccionada';
  });

  protected readonly rangoPaginacionTexto = computed(() => {
    const total = this.totalArticulos();
    if (total === 0) return '0 de 0 prendas';
    const pag = this.paginaActual();
    const lim = this.limite();
    const inicio = (pag - 1) * lim + 1;
    const fin = Math.min(pag * lim, total);
    return `${inicio} – ${fin} DE ${total} PRENDAS`;
  });

  protected readonly paginasDisponibles = computed(() => {
    const total = this.totalPaginas();
    const paginas: number[] = [];
    for (let i = 1; i <= total; i++) {
      paginas.push(i);
    }
    return paginas;
  });

  ngOnInit(): void {
    // Sincronizar con parámetros de query si existen en la URL
    this.route.queryParams.subscribe((params) => {
      const catParam = params['categoria_id'];
      if (catParam) {
        this.categoriaSeleccionada.set(Number(catParam));
      }
      this.cargarCatalogo();
    });
  }

  /**
   * Carga el catálogo paginado desde el backend invocando GET /api/v1/catalogo.
   */
  cargarCatalogo(): void {
    this.cargando.set(true);
    this.error.set(null);

    this.catalogoService
      .consultarCatalogo({
        categoria_id: this.categoriaSeleccionada(),
        ordenar_por: this.ordenarPor(),
        pagina: this.paginaActual(),
        limite: this.limite(),
      })
      .subscribe({
        next: (respuesta) => {
          this.resumenCategorias.set(respuesta.resumen_categorias || []);
          this.productos.set(respuesta.items || []);
          this.totalArticulos.set(respuesta.total_articulos);
          this.totalPaginas.set(respuesta.total_paginas);
          this.paginaActual.set(respuesta.pagina_actual);
          this.tieneSiguiente.set(respuesta.tiene_siguiente);
          this.tieneAnterior.set(respuesta.tiene_anterior);
          this.cargando.set(false);
        },
        error: (err) => {
          this.cargando.set(false);
          const msg =
            err?.error?.detail ||
            'No fue posible cargar el catálogo de alta costura. Por favor, reintente en unos momentos.';
          this.error.set(msg);
        },
      });
  }

  /**
   * Filtra las prendas al pulsar un chip de categoría superior.
   */
  seleccionarCategoria(idCategoria: number | null): void {
    if (this.categoriaSeleccionada() === idCategoria) return;
    this.categoriaSeleccionada.set(idCategoria);
    this.paginaActual.set(1);
    this.cargarCatalogo();
  }

  /**
   * Cambia el criterio de ordenación y recarga la primera página.
   */
  cambiarOrden(event: Event): void {
    const target = event.target as HTMLSelectElement;
    if (target && target.value) {
      this.ordenarPor.set(target.value);
      this.paginaActual.set(1);
      this.cargarCatalogo();
    }
  }

  /**
   * Conmuta la densidad de columnas de la cuadrícula (4 vs 2 columnas).
   */
  cambiarVista(modo: 'grid4' | 'grid2'): void {
    this.vistaColumnas.set(modo);
  }

  /**
   * Navega a una página específica.
   */
  irAPagina(numPagina: number): void {
    if (numPagina < 1 || numPagina > this.totalPaginas()) return;
    this.paginaActual.set(numPagina);
    this.cargarCatalogo();
    window.scrollTo({ top: 120, behavior: 'smooth' });
  }

  paginaSiguiente(): void {
    if (this.tieneSiguiente()) {
      this.irAPagina(this.paginaActual() + 1);
    }
  }

  paginaAnterior(): void {
    if (this.tieneAnterior()) {
      this.irAPagina(this.paginaActual() - 1);
    }
  }

  /**
   * Alterna un producto en la lista de favoritos/deseos.
   */
  toggleFavorito(prod: ProductoCatalogoItem, event?: Event): void {
    if (event) event.stopPropagation();

    this.favoritos.update((favs) => {
      const nuevo = new Set(favs);
      if (nuevo.has(prod.id_producto)) {
        nuevo.delete(prod.id_producto);
        this.mostrarToast(`Se retiró "${prod.nombre}" de su Wishlist`);
      } else {
        nuevo.add(prod.id_producto);
        this.mostrarToast(`"${prod.nombre}" añadido a su Wishlist`);
      }
      return nuevo;
    });

    // Actualizar bandera en el item
    this.productos.update((items) =>
      items.map((item) =>
        item.id_producto === prod.id_producto
          ? { ...item, es_favorito: this.favoritos().has(prod.id_producto) }
          : item
      )
    );
  }

  /**
   * Añade la prenda a la cesta de compra del cliente.
   */
  anadirACesta(prod: ProductoCatalogoItem, event?: Event): void {
    if (event) event.stopPropagation();
    this.catalogoService.cestaCount.update((c) => c + 1);
    this.mostrarToast(`"${prod.nombre}" añadido a su selección de atelier`);
  }

  /**
   * Redirige al módulo de búsqueda avanzada con filtros combinados (CU06).
   */
  irABusquedaAvanzada(): void {
    this.router.navigate(['/buscar']);
  }

  /**
   * Abre o simula solicitud de asesoría con el atelier.
   */
  solicitarAsesoria(): void {
    this.mostrarToast('Un director de patronaje de Atelier Serrano contactará con usted para su fitting privado.');
  }

  private mostrarToast(mensaje: string): void {
    this.mensajeFeedback.set(mensaje);
    setTimeout(() => {
      this.mensajeFeedback.set(null);
    }, 3500);
  }
}
