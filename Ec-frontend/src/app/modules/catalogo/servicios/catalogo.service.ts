import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap, catchError, throwError } from 'rxjs';
import {
  FiltrosBusquedaState,
  FiltrosDisponibles,
  ProductoItem,
  ProductoPaginado,
  PaginacionMeta,
} from '../modelos/catalogo.modelos';

@Injectable({
  providedIn: 'root',
})
export class CatalogoService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1';

  // Signals de estado reactivo del catálogo
  readonly productos = signal<ProductoItem[]>([]);
  readonly paginacion = signal<PaginacionMeta>({
    total_registros: 0,
    pagina_actual: 1,
    limite: 12,
    total_paginas: 0,
    tiene_siguiente: false,
    tiene_anterior: false,
  });
  readonly filtrosDisponibles = signal<FiltrosDisponibles | null>(null);
  readonly cargando = signal<boolean>(false);
  readonly error = signal<string | null>(null);
  readonly totalSugerencias = signal<number>(24);

  // Estado de sesión y cesta
  readonly cestaCount = signal<number>(2);
  readonly favoritos = signal<Set<number>>(new Set<number>());
  readonly busquedasRecientes = signal<string[]>([
    'Vestidos de seda',
    'Blazers camel',
    'Cashmere 100%',
    'Colección Cápsula FW24',
    'Trajes sastre fluídos',
  ]);

  /**
   * Consulta el catálogo de productos con parámetros dinámicos.
   */
  buscarProductos(filtros: Partial<FiltrosBusquedaState>): Observable<ProductoPaginado> {
    this.cargando.set(true);
    this.error.set(null);

    let params = new HttpParams();

    if (filtros.q && filtros.q.trim()) {
      params = params.set('q', filtros.q.trim());
    }
    if (filtros.categoria_id) {
      params = params.set('categoria_id', filtros.categoria_id.toString());
    }
    if (filtros.coleccion_id) {
      params = params.set('coleccion_id', filtros.coleccion_id.toString());
    }
    if (filtros.temporada_id) {
      params = params.set('temporada_id', filtros.temporada_id.toString());
    }
    if (filtros.talla && filtros.talla.trim()) {
      params = params.set('talla', filtros.talla.trim());
    }
    if (filtros.color && filtros.color.trim()) {
      params = params.set('color', filtros.color.trim());
    }
    if (filtros.precio_min !== undefined && filtros.precio_min !== null) {
      params = params.set('precio_min', filtros.precio_min.toString());
    }
    if (filtros.precio_max !== undefined && filtros.precio_max !== null) {
      params = params.set('precio_max', filtros.precio_max.toString());
    }
    if (filtros.solo_en_stock !== undefined) {
      params = params.set('solo_en_stock', filtros.solo_en_stock.toString());
    }
    if (filtros.ordenar_por) {
      params = params.set('ordenar_por', filtros.ordenar_por);
    }
    params = params.set('pagina', (filtros.pagina || 1).toString());
    params = params.set('limite', (filtros.limite || 12).toString());

    return this.http.get<ProductoPaginado>(`${this.baseUrl}/productos`, { params }).pipe(
      tap((res) => {
        // Enriquecer items con estado local de favoritos
        const favs = this.favoritos();
        const itemsEnriquecidos = res.items.map((item) => ({
          ...item,
          en_favoritos: favs.has(item.id_producto),
        }));

        this.productos.set(itemsEnriquecidos);
        this.paginacion.set(res.paginacion);
        this.totalSugerencias.set(res.paginacion.total_registros);
        this.cargando.set(false);
      }),
      catchError((err) => {
        this.cargando.set(false);
        const mensaje =
          err?.error?.detail ||
          'No fue posible cargar las piezas de la colección. Por favor, reintenta.';
        this.error.set(mensaje);
        return throwError(() => err);
      })
    );
  }

  /**
   * Obtiene las dimensiones de filtros disponibles en la base de datos.
   */
  obtenerFiltrosDisponibles(): Observable<FiltrosDisponibles> {
    return this.http
      .get<FiltrosDisponibles>(`${this.baseUrl}/catalogo/filtros-disponibles`)
      .pipe(
        tap((meta) => {
          this.filtrosDisponibles.set(meta);
        }),
        catchError((err) => {
          console.error('Error cargando filtros disponibles:', err);
          return throwError(() => err);
        })
      );
  }

  /**
   * Alterna un producto en la lista de deseos / favoritos.
   */
  toggleFavorito(idProducto: number): void {
    this.favoritos.update((favs) => {
      const nuevo = new Set(favs);
      if (nuevo.has(idProducto)) {
        nuevo.delete(idProducto);
      } else {
        nuevo.add(idProducto);
      }
      return nuevo;
    });

    // Reflejar en la lista actual
    const favs = this.favoritos();
    this.productos.update((items) =>
      items.map((p) => (p.id_producto === idProducto ? { ...p, en_favoritos: favs.has(idProducto) } : p))
    );
  }

  /**
   * Incrementa el contador de la cesta al añadir una prenda.
   */
  agregarACesta(_producto: ProductoItem): void {
    this.cestaCount.update((c) => c + 1);
  }

  /**
   * Limpia las sugerencias e historial de búsquedas recientes.
   */
  limpiarHistorial(): void {
    this.busquedasRecientes.set([]);
  }
}
