import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpHeaders } from '@angular/common/http';
import { Observable, catchError, of, tap } from 'rxjs';
import {
  ProductoRecomendadoItem,
  RecomendacionesResponse,
} from '../modelos/inicio.modelos';

@Injectable({
  providedIn: 'root',
})
export class InicioService {
  private readonly http = inject(HttpClient);
  private readonly endpoint = '/api/v1/catalogo/recomendaciones/personalizadas';
  private readonly TOKEN_KEY = 'fashionstore_token';

  // --- Estado Reactivo con Signals ---
  readonly cargando = signal<boolean>(true);
  readonly tieneHistorial = signal<boolean>(false);
  readonly recomendaciones = signal<ProductoRecomendadoItem[]>([]);
  readonly motivoGeneral = signal<string | null>(null);
  readonly boutiqueReferencia = signal<string>('Boutique Serrano (Madrid)');
  readonly mensajeEmptyState = signal<string | null>(null);
  readonly totalRecomendados = signal<number>(0);
  readonly error = signal<string | null>(null);

  // Estados interactivos locales
  readonly favoritos = signal<Set<number>>(new Set());
  readonly cestaCount = signal<number>(0);
  readonly prendaAgregadaMensaje = signal<string | null>(null);

  /**
   * Obtiene el token de autenticación si el cliente inició sesión.
   */
  obtenerToken(): string | null {
    if (typeof window === 'undefined') {
      return null;
    }
    return (
      localStorage.getItem(this.TOKEN_KEY) ||
      sessionStorage.getItem(this.TOKEN_KEY)
    );
  }

  /**
   * Carga las recomendaciones personalizadas desde el backend de FastAPI.
   */
  cargarRecomendaciones(limite: number = 6): Observable<RecomendacionesResponse> {
    this.cargando.set(true);
    this.error.set(null);

    let headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });

    const token = this.obtenerToken();
    if (token) {
      headers = headers.set('Authorization', `Bearer ${token}`);
    }

    return this.http
      .get<RecomendacionesResponse>(`${this.endpoint}?limite=${limite}`, { headers })
      .pipe(
        tap((res) => {
          this.tieneHistorial.set(res.tiene_historial);
          this.recomendaciones.set(res.items || []);
          this.motivoGeneral.set(res.motivo_general || null);
          this.boutiqueReferencia.set(res.boutique_referencia || 'Boutique Serrano (Madrid)');
          this.mensajeEmptyState.set(res.mensaje_empty_state || null);
          this.totalRecomendados.set(res.total_recomendados || res.items?.length || 0);
          this.cargando.set(false);
        }),
        catchError((err: HttpErrorResponse) => {
          this.cargando.set(false);
          this.error.set(
            'El servicio de selección personalizada de Atelier no se encuentra disponible temporalmente.'
          );
          // Retornar fallback seguro sin interrumpir la experiencia
          const fallbackResponse: RecomendacionesResponse = {
            tiene_historial: false,
            motivo_general: null,
            boutique_referencia: 'Boutique Serrano (Madrid)',
            mensaje_empty_state:
              'Aún no contamos con suficientes interacciones o compras previas para personalizar tu selección. Explora nuestras colecciones activas para descubrir piezas afines a tu estilo',
            total_recomendados: 0,
            items: [],
          };
          return of(fallbackResponse);
        })
      );
  }

  /**
   * Alterna el estado de favoritos (wishlist) para una prenda.
   */
  toggleFavorito(idProducto: number): void {
    const actuales = new Set(this.favoritos());
    if (actuales.has(idProducto)) {
      actuales.delete(idProducto);
    } else {
      actuales.add(idProducto);
    }
    this.favoritos.set(actuales);
  }

  /**
   * Incrementa la cesta y activa notificación efímera Atelier.
   */
  agregarACesta(producto: ProductoRecomendadoItem): void {
    this.cestaCount.update((count) => count + 1);
    this.prendaAgregadaMensaje.set(`"${producto.nombre}" ha sido añadida a tu bolsa de compra.`);
    setTimeout(() => {
      this.prendaAgregadaMensaje.set(null);
    }, 4000);
  }
}
