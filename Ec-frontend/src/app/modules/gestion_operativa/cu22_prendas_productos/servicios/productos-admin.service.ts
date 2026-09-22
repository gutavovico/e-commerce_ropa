import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, tap, catchError, throwError } from 'rxjs';
import {
  MatrizVariantesPayload,
  ParametrosFiltroProducto,
  ProductoActualizarPayload,
  ProductoCrearPayload,
  ProductoDetalleAdmin,
  ProductoResumenAdmin,
  VarianteAdmin,
  VarianteItemPayload,
} from '../modelos/producto.dto';

@Injectable({
  providedIn: 'root',
})
export class ProductosAdminService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/admin';

  // --- Signals de Estado Reactivo ---
  readonly productos = signal<ProductoResumenAdmin[]>([]);
  readonly productoSeleccionado = signal<ProductoDetalleAdmin | null>(null);
  readonly variantes = signal<VarianteAdmin[]>([]);
  readonly cargando = signal<boolean>(false);
  readonly guardando = signal<boolean>(false);
  readonly error = signal<string | null>(null);
  readonly mensajeExito = signal<string | null>(null);

  private obtenerHeaders(): HttpHeaders {
    let headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    if (typeof window !== 'undefined') {
      const token =
        localStorage.getItem('fashionstore_token') ||
        sessionStorage.getItem('fashionstore_token');
      if (token) {
        headers = headers.set('Authorization', `Bearer ${token}`);
      }
    }
    return headers;
  }

  // =========================================================================
  // GESTION DE PRENDAS Y PRODUCTOS
  // =========================================================================

  cargarProductos(filtros?: ParametrosFiltroProducto): Observable<ProductoResumenAdmin[]> {
    this.cargando.set(true);
    this.error.set(null);

    let params = new HttpParams();
    if (filtros) {
      if (filtros.q) {
        params = params.set('q', filtros.q);
      }
      if (filtros.id_categoria !== undefined && filtros.id_categoria !== null) {
        params = params.set('id_categoria', filtros.id_categoria.toString());
      }
      if (filtros.activo !== undefined && filtros.activo !== null) {
        params = params.set('activo', filtros.activo.toString());
      }
      if (filtros.pagina) {
        params = params.set('pagina', filtros.pagina.toString());
      }
      if (filtros.limite) {
        params = params.set('limite', filtros.limite.toString());
      }
    }

    return this.http
      .get<ProductoResumenAdmin[]>(`${this.baseUrl}/productos`, {
        headers: this.obtenerHeaders(),
        params,
      })
      .pipe(
        tap((data) => {
          this.productos.set(data);
          this.cargando.set(false);
        }),
        catchError((err: HttpErrorResponse) => {
          this.cargando.set(false);
          const errorMsg =
            err.error?.detail || err.error?.message || 'Error al cargar el catalogo de prendas.';
          this.error.set(errorMsg);
          return throwError(() => err);
        })
      );
  }

  cargarProductoPorId(id: number): Observable<ProductoDetalleAdmin> {
    this.cargando.set(true);
    this.error.set(null);

    return this.http
      .get<ProductoDetalleAdmin>(`${this.baseUrl}/productos/${id}`, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((data) => {
          this.productoSeleccionado.set(data);
          this.variantes.set(data.variantes || []);
          this.cargando.set(false);
        }),
        catchError((err: HttpErrorResponse) => {
          this.cargando.set(false);
          const errorMsg =
            err.error?.detail || err.error?.message || 'Error al consultar la ficha de la prenda.';
          this.error.set(errorMsg);
          return throwError(() => err);
        })
      );
  }

  crearProducto(payload: ProductoCrearPayload): Observable<ProductoResumenAdmin> {
    this.guardando.set(true);
    this.error.set(null);
    this.mensajeExito.set(null);

    return this.http
      .post<ProductoResumenAdmin>(`${this.baseUrl}/productos`, payload, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((nuevo) => {
          this.productos.update((lista) => [nuevo, ...lista]);
          this.guardando.set(false);
          this.mensajeExito.set(`Prenda "${nuevo.nombre}" registrada correctamente.`);
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const errorMsg =
            err.error?.detail || err.error?.message || 'Error al registrar la nueva prenda.';
          this.error.set(errorMsg);
          return throwError(() => err);
        })
      );
  }

  actualizarProducto(
    id: number,
    payload: ProductoActualizarPayload
  ): Observable<ProductoResumenAdmin> {
    this.guardando.set(true);
    this.error.set(null);
    this.mensajeExito.set(null);

    return this.http
      .put<ProductoResumenAdmin>(`${this.baseUrl}/productos/${id}`, payload, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((actualizado) => {
          this.productos.update((lista) =>
            lista.map((p) => (p.id_producto === id ? actualizado : p))
          );
          if (this.productoSeleccionado()?.id_producto === id) {
            const actual = this.productoSeleccionado()!;
            this.productoSeleccionado.set({ ...actual, ...actualizado });
          }
          this.guardando.set(false);
          this.mensajeExito.set(`Prenda "${actualizado.nombre}" actualizada correctamente.`);
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const errorMsg =
            err.error?.detail || err.error?.message || 'Error al actualizar la prenda.';
          this.error.set(errorMsg);
          return throwError(() => err);
        })
      );
  }

  cambiarEstadoProducto(id: number, activo: boolean): Observable<ProductoResumenAdmin> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .patch<ProductoResumenAdmin>(
        `${this.baseUrl}/productos/${id}/estado`,
        { activo },
        { headers: this.obtenerHeaders() }
      )
      .pipe(
        tap((actualizado) => {
          this.productos.update((lista) =>
            lista.map((p) => (p.id_producto === id ? actualizado : p))
          );
          if (this.productoSeleccionado()?.id_producto === id) {
            const actual = this.productoSeleccionado()!;
            this.productoSeleccionado.set({ ...actual, activo });
          }
          this.guardando.set(false);
          const accion = activo ? 'publicada' : 'desactivada (baja logica)';
          this.mensajeExito.set(`Prenda ${accion} correctamente.`);
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const errorMsg =
            err.error?.detail || err.error?.message || 'Error al cambiar estado de la prenda.';
          this.error.set(errorMsg);
          return throwError(() => err);
        })
      );
  }

  eliminarProducto(id: number): Observable<void> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .delete<void>(`${this.baseUrl}/productos/${id}`, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap(() => {
          this.productos.update((lista) => lista.filter((p) => p.id_producto !== id));
          if (this.productoSeleccionado()?.id_producto === id) {
            this.productoSeleccionado.set(null);
            this.variantes.set([]);
          }
          this.guardando.set(false);
          this.mensajeExito.set('Prenda eliminada correctamente.');
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const errorMsg =
            err.error?.detail || err.error?.message || 'No se pudo eliminar la prenda.';
          this.error.set(errorMsg);
          return throwError(() => err);
        })
      );
  }

  subirImagen(archivo: File): Observable<{ url: string }> {
    const formData = new FormData();
    formData.append('archivo', archivo);

    let headers = new HttpHeaders();
    if (typeof window !== 'undefined') {
      const token =
        localStorage.getItem('fashionstore_token') ||
        sessionStorage.getItem('fashionstore_token');
      if (token) {
        headers = headers.set('Authorization', `Bearer ${token}`);
      }
    }

    return this.http
      .post<{ url: string }>(`${this.baseUrl}/productos/upload-imagen`, formData, {
        headers,
      })
      .pipe(
        catchError((err: HttpErrorResponse) => {
          const errorMsg =
            err.error?.detail || err.error?.message || 'Error al subir la imagen de la prenda.';
          this.error.set(errorMsg);
          return throwError(() => err);
        })
      );
  }

  // =========================================================================
  // GESTION DE VARIANTES Y MATRIZ DE SKUs
  // =========================================================================

  generarMatrizVariantes(
    idProducto: number,
    payload: MatrizVariantesPayload
  ): Observable<VarianteAdmin[]> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .post<VarianteAdmin[]>(
        `${this.baseUrl}/productos/${idProducto}/variantes/matriz`,
        payload,
        { headers: this.obtenerHeaders() }
      )
      .pipe(
        tap((nuevas) => {
          this.variantes.update((actuales) => [...actuales, ...nuevas]);
          this.guardando.set(false);
          this.mensajeExito.set(
            `Se han generado ${nuevas.length} combinaciones de variantes (SKUs).`
          );
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const errorMsg =
            err.error?.detail || err.error?.message || 'Error al generar matriz de variantes.';
          this.error.set(errorMsg);
          return throwError(() => err);
        })
      );
  }

  crearVarianteIndividual(
    idProducto: number,
    payload: VarianteItemPayload
  ): Observable<VarianteAdmin> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .post<VarianteAdmin>(
        `${this.baseUrl}/productos/${idProducto}/variantes`,
        payload,
        { headers: this.obtenerHeaders() }
      )
      .pipe(
        tap((nueva) => {
          this.variantes.update((actuales) => [...actuales, nueva]);
          this.guardando.set(false);
          this.mensajeExito.set(`Variante SKU ${nueva.sku} registrada correctamente.`);
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const errorMsg =
            err.error?.detail || err.error?.message || 'Error al registrar variante individual.';
          this.error.set(errorMsg);
          return throwError(() => err);
        })
      );
  }

  listarVariantes(idProducto: number): Observable<VarianteAdmin[]> {
    this.cargando.set(true);
    this.error.set(null);

    return this.http
      .get<VarianteAdmin[]>(`${this.baseUrl}/productos/${idProducto}/variantes`, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((data) => {
          this.variantes.set(data);
          this.cargando.set(false);
        }),
        catchError((err: HttpErrorResponse) => {
          this.cargando.set(false);
          const errorMsg =
            err.error?.detail || err.error?.message || 'Error al listar las variantes.';
          this.error.set(errorMsg);
          return throwError(() => err);
        })
      );
  }

  actualizarVariante(
    idVariante: number,
    payload: { sku?: string; precio_extra?: number; activo?: boolean }
  ): Observable<VarianteAdmin> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .put<VarianteAdmin>(`${this.baseUrl}/variantes/${idVariante}`, payload, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((actualizada) => {
          this.variantes.update((lista) =>
            lista.map((v) => (v.id_variante === idVariante ? actualizada : v))
          );
          this.guardando.set(false);
          this.mensajeExito.set(`Variante ${actualizada.sku} actualizada correctamente.`);
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const errorMsg =
            err.error?.detail || err.error?.message || 'Error al actualizar variante.';
          this.error.set(errorMsg);
          return throwError(() => err);
        })
      );
  }

  cambiarEstadoVariante(idVariante: number, activo: boolean): Observable<VarianteAdmin> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .patch<VarianteAdmin>(
        `${this.baseUrl}/variantes/${idVariante}/estado`,
        { activo },
        { headers: this.obtenerHeaders() }
      )
      .pipe(
        tap((actualizada) => {
          this.variantes.update((lista) =>
            lista.map((v) => (v.id_variante === idVariante ? actualizada : v))
          );
          this.guardando.set(false);
          this.mensajeExito.set(
            `Variante ${actualizada.sku} ${activo ? 'activada' : 'desactivada'}.`
          );
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const errorMsg =
            err.error?.detail || err.error?.message || 'Error al cambiar estado de la variante.';
          this.error.set(errorMsg);
          return throwError(() => err);
        })
      );
  }

  eliminarVariante(idVariante: number): Observable<void> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .delete<void>(`${this.baseUrl}/variantes/${idVariante}`, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap(() => {
          this.variantes.update((lista) => lista.filter((v) => v.id_variante !== idVariante));
          this.guardando.set(false);
          this.mensajeExito.set('Variante eliminada correctamente.');
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const errorMsg =
            err.error?.detail || err.error?.message || 'No se pudo eliminar la variante.';
          this.error.set(errorMsg);
          return throwError(() => err);
        })
      );
  }

  limpiarMensajes(): void {
    this.error.set(null);
    this.mensajeExito.set(null);
  }
}
