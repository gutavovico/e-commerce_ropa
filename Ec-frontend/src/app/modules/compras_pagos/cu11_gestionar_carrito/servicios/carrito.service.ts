import { Injectable, computed, inject, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, catchError, finalize, tap, throwError } from 'rxjs';

import {
  BoutiqueRecogida,
  Carrito,
  CarritoItem,
  CheckoutPayload,
  ItemAgregarPayload,
  ItemCantidadPayload,
  TipoEntrega,
  VentaCreada,
} from '../modelos/carrito.model';

const CARRITO_VACIO: Carrito = {
  id_carrito: 0,
  items: [],
  resumen: {
    total_prendas: 0,
    total_lineas: 0,
    subtotal: '0.00',
    descuento: '0.00',
    total: '0.00',
    iva_incluido: '0.00',
    moneda: 'EUR',
  },
  expira_en: null,
  sucursales_expedicion: [],
};

/**
 * Estado reactivo de la Bolsa de Compra.
 *
 * Es la única fuente de verdad del carrito en la aplicación: tanto la pantalla `/bolsa` como el
 * contador de la barra superior leen de aquí, de modo que añadir una prenda desde el detalle
 * actualiza el contador sin ninguna coordinación adicional.
 *
 * El servidor recalcula los importes en cada operación y devuelve la bolsa completa; el cliente
 * nunca los deriva por su cuenta. Por eso todos los métodos de escritura reemplazan el estado
 * con la respuesta en lugar de aplicar cambios locales.
 */
@Injectable({
  providedIn: 'root',
})
export class CarritoService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1';

  // --- Estado ---
  private readonly _carrito = signal<Carrito>(CARRITO_VACIO);
  readonly carrito = this._carrito.asReadonly();

  readonly cargando = signal<boolean>(false);
  readonly procesando = signal<boolean>(false);
  readonly error = signal<string | null>(null);

  readonly tipoEntrega = signal<TipoEntrega>('domicilio');
  readonly direccionEnvio = signal<string>('');
  readonly sucursalRetiro = signal<number | null>(null);
  readonly cuponAplicado = signal<string | null>(null);

  // --- Derivados ---
  readonly items = computed<CarritoItem[]>(() => this._carrito().items);
  readonly resumen = computed(() => this._carrito().resumen);
  readonly subtotal = computed(() => this.resumen().subtotal);
  readonly descuento = computed(() => this.resumen().descuento);
  readonly total = computed(() => this.resumen().total);
  readonly ivaIncluido = computed(() => this.resumen().iva_incluido);
  readonly totalPrendas = computed(() => this.resumen().total_prendas);
  readonly estaVacia = computed(() => this.items().length === 0);
  readonly haySucursalesMultiples = computed(
    () => this._carrito().sucursales_expedicion.length > 1
  );
  readonly expiraEn = computed(() => this._carrito().expira_en);
  readonly hayDescuento = computed(() => this.descuento() !== '0.00');

  // ---------------------------------------------------------------------
  // Lectura
  // ---------------------------------------------------------------------

  /** Carga la bolsa del cliente autenticado. Una bolsa vacía es un 200, no un 404. */
  cargarCarrito(): Observable<Carrito> {
    this.cargando.set(true);
    this.error.set(null);

    return this.http.get<Carrito>(`${this.baseUrl}/carrito`).pipe(
      tap((carrito) => this._carrito.set(carrito)),
      catchError((err: HttpErrorResponse) => this.manejarError(err)),
      finalize(() => this.cargando.set(false))
    );
  }

  /** Directorio de boutiques para el selector de recogida. */
  obtenerBoutiques(): Observable<BoutiqueRecogida[]> {
    return this.http.get<BoutiqueRecogida[]>(`${this.baseUrl}/sucursales/activas`);
  }

  // ---------------------------------------------------------------------
  // Escritura
  // ---------------------------------------------------------------------

  /** Añade una prenda. Si ya estaba para la misma boutique, el backend consolida cantidades. */
  agregarItem(payload: ItemAgregarPayload): Observable<Carrito> {
    this.procesando.set(true);
    this.error.set(null);

    return this.http.post<Carrito>(`${this.baseUrl}/carrito/items`, payload).pipe(
      tap((carrito) => this._carrito.set(carrito)),
      catchError((err: HttpErrorResponse) => this.manejarError(err)),
      finalize(() => this.procesando.set(false))
    );
  }

  /** Fija la cantidad de una línea (valor absoluto). */
  actualizarCantidad(idLinea: number, cantidad: number): Observable<Carrito> {
    this.procesando.set(true);
    this.error.set(null);

    const payload: ItemCantidadPayload = { cantidad };
    return this.http
      .patch<Carrito>(`${this.baseUrl}/carrito/items/${idLinea}`, payload)
      .pipe(
        tap((carrito) => this._carrito.set(carrito)),
        catchError((err: HttpErrorResponse) => this.manejarError(err)),
        finalize(() => this.procesando.set(false))
      );
  }

  /** Elimina una línea de la bolsa. */
  eliminarItem(idLinea: number): Observable<Carrito> {
    this.procesando.set(true);
    this.error.set(null);

    return this.http.delete<Carrito>(`${this.baseUrl}/carrito/items/${idLinea}`).pipe(
      tap((carrito) => this._carrito.set(carrito)),
      catchError((err: HttpErrorResponse) => this.manejarError(err)),
      finalize(() => this.procesando.set(false))
    );
  }

  /** Transforma la bolsa en una orden `pendiente` lista para la pasarela de pago. */
  tramitarPedido(): Observable<VentaCreada> {
    this.procesando.set(true);
    this.error.set(null);

    const payload: CheckoutPayload = {
      tipo_venta: 'digital_web',
      tipo_entrega: this.tipoEntrega(),
      direccion_envio:
        this.tipoEntrega() === 'domicilio' ? this.direccionEnvio().trim() : null,
      id_sucursal_retiro:
        this.tipoEntrega() === 'recogida_boutique' ? this.sucursalRetiro() : null,
      codigo_cupon: this.cuponAplicado(),
    };

    return this.http.post<VentaCreada>(`${this.baseUrl}/ventas/checkout`, payload).pipe(
      tap(() => this._carrito.set(CARRITO_VACIO)),
      catchError((err: HttpErrorResponse) => this.manejarError(err)),
      finalize(() => this.procesando.set(false))
    );
  }

  /** Vacía el estado local. Se usa al cerrar sesión: la bolsa es de cada cliente. */
  limpiarEstado(): void {
    this._carrito.set(CARRITO_VACIO);
    this.cuponAplicado.set(null);
    this.error.set(null);
  }

  // ---------------------------------------------------------------------
  // Traducción de errores
  // ---------------------------------------------------------------------

  /**
   * Convierte el error HTTP en un mensaje legible para el cliente.
   *
   * El backend responde con el contrato `{detail, code}`, así que el texto de negocio —que ya
   * nombra la prenda y las existencias concretas— se muestra tal cual. Solo se sustituye cuando
   * no hay detalle aprovechable.
   */
  private manejarError(err: HttpErrorResponse): Observable<never> {
    const detalle: string | undefined = err.error?.detail;
    let mensaje: string;

    switch (err.status) {
      case 0:
        mensaje = 'No se pudo conectar con el atelier. Revisa tu conexión de red.';
        break;
      case 401:
        mensaje = 'Tu sesión ha expirado. Inicia sesión de nuevo para continuar.';
        break;
      case 403:
        mensaje = 'Esta prenda pertenece a la bolsa de otro cliente.';
        break;
      case 404:
        mensaje = detalle ?? 'La prenda solicitada ya no está disponible en el catálogo.';
        break;
      case 409:
        // Incluye STOCK_INSUFICIENTE y CARRITO_VACIO: el detalle del backend es el más preciso.
        mensaje = detalle ?? 'Las existencias han cambiado mientras preparabas tu bolsa.';
        break;
      case 400:
      case 422:
        mensaje = detalle ?? 'Revisa los datos introducidos antes de continuar.';
        break;
      default:
        mensaje = detalle ?? 'No fue posible completar la operación. Inténtalo de nuevo.';
    }

    this.error.set(mensaje);
    return throwError(() => err);
  }
}
