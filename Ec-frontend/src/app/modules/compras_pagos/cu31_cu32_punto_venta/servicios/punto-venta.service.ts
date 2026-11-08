import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import {
  ClientePos,
  CobroPosIn,
  CuponPos,
  PedidoWebEfectivo,
  PrevisualizacionPos,
  ReservaPos,
  SucursalOpcion,
  VariantePos,
  VentaPos,
  VentaPosIn,
} from '../modelos/punto-venta.dto';

/**
 * Cliente HTTP del punto de venta (`/api/v1/pos`) y de los cobros en efectivo de CU16.
 *
 * Sin estado ni importes derivados: cada respuesta del servidor sustituye al estado de la página.
 * El JWT lo adjunta `authInterceptor`.
 */
@Injectable({ providedIn: 'root' })
export class PuntoVentaService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/pos';

  private parametrosSucursal(idSucursal: number | null): HttpParams {
    return idSucursal ? new HttpParams().set('id_sucursal', idSucursal) : new HttpParams();
  }

  listarSucursales(): Observable<SucursalOpcion[]> {
    return this.http
      .get<SucursalOpcion[]>('/api/v1/sucursales/activas')
      .pipe(map((lista) => lista.map((s) => ({ id_sucursal: s.id_sucursal, nombre: s.nombre }))));
  }

  /** Todas las tallas/colores cuyo nombre, categoría o SKU coinciden, con el stock de la boutique. */
  buscarVariantes(texto: string, idSucursal: number | null): Observable<VariantePos[]> {
    return this.http.get<VariantePos[]>(`${this.base}/variantes`, {
      params: this.parametrosSucursal(idSucursal).set('q', texto.trim()),
    });
  }

  /** Clientes registrados por nombre, apellidos o correo. */
  buscarClientes(texto: string): Observable<ClientePos[]> {
    return this.http.get<ClientePos[]>(`${this.base}/clientes`, { params: { q: texto.trim() } });
  }

  /** Reservas activas del cliente que esta caja puede cobrar. */
  reservasDeCliente(idCliente: number, idSucursal: number | null): Observable<ReservaPos[]> {
    return this.http.get<ReservaPos[]>(`${this.base}/clientes/${idCliente}/reservas`, {
      params: this.parametrosSucursal(idSucursal),
    });
  }

  /** Cupones vigentes; sin texto, todos. */
  listarCupones(texto: string): Observable<CuponPos[]> {
    const params = texto.trim() ? new HttpParams().set('q', texto.trim()) : new HttpParams();
    return this.http.get<CuponPos[]>(`${this.base}/cupones`, { params });
  }

  consultarReserva(referencia: string, idSucursal: number | null): Observable<ReservaPos> {
    return this.http.get<ReservaPos>(`${this.base}/reservas/${encodeURIComponent(referencia.trim())}`, {
      params: this.parametrosSucursal(idSucursal),
    });
  }

  previsualizar(datos: VentaPosIn): Observable<PrevisualizacionPos> {
    return this.http.post<PrevisualizacionPos>(`${this.base}/ventas/previsualizar`, datos);
  }

  registrarVenta(datos: VentaPosIn): Observable<VentaPos> {
    return this.http.post<VentaPos>(`${this.base}/ventas`, datos);
  }

  listarVentas(
    idSucursal: number | null,
    opciones: { estado?: 'pendiente' | 'pagada' | 'anulada'; soloHoy: boolean },
  ): Observable<VentaPos[]> {
    let params = this.parametrosSucursal(idSucursal).set('solo_hoy', opciones.soloHoy);
    if (opciones.estado) params = params.set('estado', opciones.estado);
    return this.http.get<VentaPos[]>(`${this.base}/ventas`, { params });
  }

  obtenerVenta(idVenta: number): Observable<VentaPos> {
    return this.http.get<VentaPos>(`${this.base}/ventas/${idVenta}`);
  }

  cobrar(idVenta: number, cobro: CobroPosIn): Observable<VentaPos> {
    return this.http.post<VentaPos>(`${this.base}/ventas/${idVenta}/cobrar`, cobro);
  }

  anular(idVenta: number, motivo: string): Observable<VentaPos> {
    return this.http.post<VentaPos>(`${this.base}/ventas/${idVenta}/anular`, { motivo });
  }

  /** PDF del comprobante (`application/pdf`), para descargar como archivo. */
  descargarComprobante(idVenta: number): Observable<Blob> {
    return this.http.get(`${this.base}/ventas/${idVenta}/comprobante.pdf`, { responseType: 'blob' });
  }

  listarPedidosWebEfectivo(idSucursal: number | null): Observable<PedidoWebEfectivo[]> {
    return this.http.get<PedidoWebEfectivo[]>(`${this.base}/pedidos-web-efectivo`, {
      params: this.parametrosSucursal(idSucursal),
    });
  }

  /** CU16: confirmar en mostrador el cobro en efectivo de un pedido web. */
  confirmarPedidoWeb(idPago: number): Observable<unknown> {
    return this.http.post(`/api/v1/admin/pagos/${idPago}/confirmar-efectivo`, {});
  }

  /** CU16: anular el pago en efectivo pendiente de un pedido web. */
  cancelarPedidoWeb(idPago: number): Observable<unknown> {
    return this.http.post(`/api/v1/admin/pagos/${idPago}/cancelar-efectivo`, {});
  }

  /** Mensaje legible de un error `{detail, code}` del backend. */
  static mensajeError(error: unknown, porDefecto = 'No fue posible completar la operación.'): string {
    if (error instanceof HttpErrorResponse) {
      const detalle = error.error?.detail;
      if (typeof detalle === 'string' && detalle) return detalle;
      if (Array.isArray(detalle) && detalle[0]?.msg) return detalle[0].msg;
      if (error.status === 0) return 'No hay conexión con el servidor.';
    }
    return porDefecto;
  }
}
