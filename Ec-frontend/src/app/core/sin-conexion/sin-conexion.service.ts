import { DestroyRef, Injectable, computed, effect, inject, signal, untracked } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

import { AlmacenLocal } from './almacen-local';
import { ConectividadService } from './conectividad.service';
import {
  BandejaAvisosDto,
  CatalogoLocalDto,
  DispositivoDto,
  DispositivoLocal,
  LoteDto,
  OperacionLocal,
  OperacionServidorDto,
} from './sin-conexion.models';

const API = '/api/v1/sin-conexion';
const LOTE_MAXIMO = 50;
/** Se vuelve a descargar el catálogo al entrar si el guardado tiene más de esto (RN42). */
const VIGENCIA_CATALOGO_MS = 60 * 60_000;
const ESPERA_INICIAL_MS = 5_000;
const ESPERA_MAXIMA_MS = 5 * 60_000;

export interface NuevaReservaLocal {
  idSucursal: number;
  fechaHoraAtencion: string;
  items: { id_variante: number; cantidad: number }[];
  observacion?: string;
  resumen: OperacionLocal['resumen'];
}

/**
 * P2-CU14 / CU15 A1 / CU19 · Catálogo descargado, reservas sin conexión y sincronización en la PWA.
 *
 * - Al entrar en una tienda con sesión de cliente se cargan los datos locales (también sin red) y,
 *   si hay red, se registra el dispositivo, se descarga el catálogo y se envía lo pendiente.
 * - Al volver la red se sincroniza solo; si falla, se reintenta con espera creciente (CU19 A1).
 * - Ninguna operación se borra al enviarse (RN37); el resultado del servidor se guarda en ella.
 *
 * La cabecera `X-Tenant` la pone `authInterceptor` (la tienda del portal): no se añade aquí.
 */
@Injectable({ providedIn: 'root' })
export class SinConexionService {
  private readonly http = inject(HttpClient);
  private readonly almacen = inject(AlmacenLocal);
  private readonly conectividad = inject(ConectividadService);

  readonly enLinea = this.conectividad.enLinea;

  /** Tienda y cliente activos: `${codigo}:${idCliente}`. */
  readonly clave = signal<string | null>(null);
  readonly codigoTienda = signal<string | null>(null);
  readonly dispositivo = signal<DispositivoLocal | null>(null);
  readonly catalogo = signal<CatalogoLocalDto | null>(null);
  readonly guardadoEn = signal<string | null>(null);
  readonly operaciones = signal<OperacionLocal[]>([]);
  readonly avisosNoLeidos = signal(0);
  readonly sincronizando = signal(false);
  readonly descargando = signal(false);
  readonly aviso = signal<string | null>(null);
  /** CU19 A5: la sesión expiró; las operaciones se conservan hasta volver a entrar. */
  readonly sesionExpirada = signal(false);

  readonly pendientes = computed(() =>
    this.operaciones().filter((o) => o.estado === 'registrada_localmente' || o.estado === 'enviada')
  );
  /** RN33 / CU14 A5: la empresa permite reservar sin conexión. */
  readonly puedeReservarSinConexion = computed(
    () => !!this.dispositivo()?.parametros?.operacion_offline_habilitada && !!this.catalogo()
  );
  readonly horasVencimiento = computed(() => this.dispositivo()?.parametros?.horas_vencimiento_reserva ?? 24);
  /** El cliente está registrado en la tienda (`null`: aún no se sabe, p. ej. sin red). */
  readonly registradoEnTienda = signal<boolean | null>(null);
  /** El dispositivo ya se registró en el servidor alguna vez: se puede sincronizar. */
  readonly preparado = computed(() => !!this.dispositivo()?.codigoCorto);

  private reintentos = 0;
  private temporizador: ReturnType<typeof setTimeout> | null = null;

  constructor() {
    // Al volver la red, se envía lo pendiente (CU19 paso 1).
    effect(() => {
      if (this.enLinea() && untracked(() => this.clave())) {
        untracked(() => void this.sincronizar());
      }
    });
    inject(DestroyRef).onDestroy(() => this.cancelarReintento());
  }

  // ---------------------------------------------------------------- tienda

  /**
   * Carga lo guardado de esta tienda y, con red, la prepara para trabajar sin conexión.
   *
   * Solo llama a la API cuando se sabe que el cliente está registrado en la tienda (`registrado ===
   * true`): con `null` (sus tiendas aún no llegaron, o no hay red) se queda con lo local; el portal
   * vuelve a llamar cuando se conoce. Así no se pide nada que el servidor rechazaría con 403
   * `CLIENTE_NO_REGISTRADO`.
   */
  async prepararTienda(codigo: string, idCliente: number, registrado: boolean | null): Promise<void> {
    const clave = `${codigo}:${idCliente}`;
    if (this.clave() !== clave) {
      this.cancelarReintento();
      this.reintentos = 0;
      this.clave.set(clave);
      this.codigoTienda.set(codigo);
      this.dispositivo.set(null);
      this.catalogo.set(null);
      this.guardadoEn.set(null);
      this.operaciones.set([]);
      this.avisosNoLeidos.set(0);
    }
    this.registradoEnTienda.set(registrado);
    await this.cargarLocal();

    if (!this.enLinea() || registrado !== true) return;
    try {
      await this.registrarDispositivo();
      const guardado = this.guardadoEn();
      if (!guardado || Date.now() - new Date(guardado).getTime() > VIGENCIA_CATALOGO_MS) {
        await this.descargarCatalogo();
      }
      await this.sincronizar();
      await this.cargarAvisos();
    } catch {
      // Sin red o servidor caído: se trabaja con lo guardado (CU14 A4).
    }
  }

  /** Al cerrar sesión: fuera el catálogo, pero nunca las operaciones pendientes (RNF03). */
  async cerrarSesion(): Promise<void> {
    this.cancelarReintento();
    this.clave.set(null);
    this.codigoTienda.set(null);
    this.dispositivo.set(null);
    this.catalogo.set(null);
    this.guardadoEn.set(null);
    this.operaciones.set([]);
    this.avisosNoLeidos.set(0);
    await this.almacen.borrarCatalogos();
  }

  private async cargarLocal(): Promise<void> {
    const clave = this.clave();
    const codigo = this.codigoTienda();
    if (!clave || !codigo) return;
    const [dispositivo, catalogo, operaciones] = await Promise.all([
      this.almacen.dispositivo(clave),
      this.almacen.catalogo(codigo),
      this.almacen.operaciones(clave),
    ]);
    this.dispositivo.set(dispositivo ?? null);
    this.catalogo.set(catalogo?.paquete ?? null);
    this.guardadoEn.set(catalogo?.guardadoEn ?? null);
    this.ordenar(operaciones);
  }

  // ---------------------------------------------------------------- CU14

  async registrarDispositivo(): Promise<DispositivoLocal> {
    const clave = this.exigirClave();
    const [codigo, idCliente] = clave.split(':');
    const local: DispositivoLocal = (await this.almacen.dispositivo(clave)) ?? {
      clave,
      codigo,
      idCliente: Number(idCliente),
      identificador: crypto.randomUUID(),
      codigoCorto: null,
      correlativo: 0,
      parametros: null,
    };
    if (!local.codigoCorto) await this.almacen.guardarDispositivo(local); // el UUID se conserva aunque falle la red

    const dto = await firstValueFrom(
      this.http.post<DispositivoDto>(`${API}/dispositivos`, { identificador: local.identificador, plataforma: 'pwa' })
    );
    const actual = (await this.almacen.dispositivo(clave)) ?? local;
    const registrado: DispositivoLocal = {
      ...actual,
      codigoCorto: dto.codigo_corto,
      parametros: {
        operacion_offline_habilitada: dto.operacion_offline_habilitada,
        dias_antiguedad_offline: dto.dias_antiguedad_offline,
        horas_vencimiento_reserva: dto.horas_vencimiento_reserva,
        moneda: dto.moneda,
      },
    };
    await this.almacen.guardarDispositivo(registrado);
    if (this.clave() === clave) this.dispositivo.set(registrado);
    return registrado;
  }

  /** Descarga el paquete y solo entonces reemplaza el guardado (A2). Sin espacio → indispensable (A3). */
  async descargarCatalogo(modo: 'completo' | 'indispensable' = 'completo'): Promise<void> {
    const clave = this.exigirClave();
    const codigo = this.codigoTienda()!;
    const dispositivo = this.dispositivo() ?? (await this.registrarDispositivo());
    this.descargando.set(true);
    try {
      const paquete = await firstValueFrom(
        this.http.get<CatalogoLocalDto>(`${API}/catalogo`, {
          params: { dispositivo: dispositivo.identificador, modo },
        })
      );
      const guardadoEn = new Date().toISOString();
      try {
        await this.almacen.guardarCatalogo({ codigo, paquete, guardadoEn });
      } catch (error) {
        if (modo === 'completo' && esFaltaDeEspacio(error)) {
          this.aviso.set('No hay espacio suficiente en el dispositivo: se descargó solo lo indispensable.');
          return this.descargarCatalogo('indispensable');
        }
        throw error;
      }
      if (this.clave() === clave) {
        this.catalogo.set(paquete);
        this.guardadoEn.set(guardadoEn);
      }
    } finally {
      this.descargando.set(false);
    }
  }

  // ---------------------------------------------------------------- CU15 A1

  /** Guarda la reserva en el dispositivo con su código provisional (RN34). */
  async reservarSinConexion(nueva: NuevaReservaLocal): Promise<OperacionLocal> {
    const clave = this.exigirClave();
    const dispositivo = this.dispositivo();
    if (!dispositivo?.codigoCorto || !dispositivo.parametros) {
      throw new Error('Para reservar sin conexión, entra antes en la tienda con conexión.');
    }
    if (!dispositivo.parametros.operacion_offline_habilitada) {
      throw new Error('Esta tienda no permite reservar sin conexión.');
    }
    const correlativo = await this.almacen.siguienteCorrelativo(clave);
    const operacion: OperacionLocal = {
      uuid: crypto.randomUUID(),
      clave,
      tipo: 'reserva',
      idSucursal: nueva.idSucursal,
      registradaEn: new Date().toISOString(),
      codigoProvisional: `PROV-${dispositivo.codigoCorto}-${String(correlativo).padStart(6, '0')}`,
      datos: { fecha_hora_atencion: nueva.fechaHoraAtencion, observacion: nueva.observacion, items: nueva.items },
      estado: 'registrada_localmente',
      motivo: null,
      mensaje: null,
      codigoReserva: null,
      estadoConflicto: null,
      resumen: nueva.resumen,
    };
    await this.almacen.guardarOperacion(operacion);
    this.dispositivo.set({ ...dispositivo, correlativo });
    this.ordenar([...this.operaciones(), operacion]);
    if (this.enLinea()) void this.sincronizar();
    return operacion;
  }

  // ---------------------------------------------------------------- CU19

  /** Envía lo pendiente. Devuelve false si no pudo (sin red, error o sesión expirada). */
  async sincronizar(): Promise<boolean> {
    const clave = this.clave();
    const dispositivo = this.dispositivo();
    if (!clave || !this.enLinea() || this.sincronizando() || this.registradoEnTienda() === false) return false;
    const pendientes = this.pendientes().slice(0, LOTE_MAXIMO);
    if (!dispositivo?.codigoCorto) return false;
    if (pendientes.length === 0) {
      await this.refrescarEstados().catch(() => undefined);
      return true;
    }

    this.sincronizando.set(true);
    try {
      for (const op of pendientes) await this.actualizar({ ...op, estado: 'enviada' });
      const lote = await firstValueFrom(
        this.http.post<LoteDto>(`${API}/sincronizar`, {
          dispositivo: dispositivo.identificador,
          operaciones: pendientes.map((op) => ({
            uuid: op.uuid,
            tipo: op.tipo,
            id_sucursal: op.idSucursal,
            registrada_en: op.registradaEn,
            codigo_provisional: op.codigoProvisional,
            datos: op.datos,
          })),
        })
      );
      let reintentar = false;
      for (const r of lote.resultados) {
        const op = this.operaciones().find((o) => o.uuid === r.uuid);
        if (!op) continue;
        if (r.estado === 'reintentar') {
          reintentar = true;
          await this.actualizar({ ...op, estado: 'registrada_localmente', mensaje: r.mensaje });
        } else {
          await this.actualizar({
            ...op,
            estado: r.estado,
            motivo: r.motivo,
            mensaje: r.mensaje,
            codigoReserva: r.codigo_reserva,
          });
        }
      }
      this.sesionExpirada.set(false);
      this.reintentos = 0;
      await this.cargarAvisos().catch(() => undefined);
      if (reintentar || this.pendientes().length > 0) this.programarReintento();
      return !reintentar;
    } catch (error) {
      // Se conservan como pendientes (RN37) y se reintenta más tarde (A1).
      for (const op of pendientes) {
        const actual = this.operaciones().find((o) => o.uuid === op.uuid);
        if (actual?.estado === 'enviada') await this.actualizar({ ...actual, estado: 'registrada_localmente' });
      }
      if (error instanceof HttpErrorResponse && error.status === 401) {
        this.sesionExpirada.set(true);
      } else {
        this.programarReintento();
      }
      return false;
    } finally {
      this.sincronizando.set(false);
    }
  }

  /** Trae del servidor cómo van las operaciones (p. ej. un conflicto resuelto en CU20). */
  async refrescarEstados(): Promise<void> {
    const dispositivo = this.dispositivo();
    if (!dispositivo?.codigoCorto || !this.enLinea()) return;
    const remotas = await firstValueFrom(
      this.http.get<OperacionServidorDto[]>(`${API}/operaciones`, { params: { dispositivo: dispositivo.identificador } })
    );
    for (const remota of remotas) {
      const local = this.operaciones().find((o) => o.uuid === remota.uuid);
      if (!local) continue;
      if (local.estado !== remota.estado || local.estadoConflicto !== remota.estado_conflicto) {
        await this.actualizar({
          ...local,
          estado: remota.estado,
          motivo: remota.motivo,
          codigoReserva: remota.codigo_reserva ?? local.codigoReserva,
          estadoConflicto: remota.estado_conflicto,
        });
      }
    }
  }

  async cargarAvisos(): Promise<BandejaAvisosDto> {
    const bandeja = await firstValueFrom(this.http.get<BandejaAvisosDto>('/api/v1/avisos'));
    this.avisosNoLeidos.set(bandeja.no_leidos);
    return bandeja;
  }

  async marcarAvisoLeido(idAviso: number): Promise<void> {
    await firstValueFrom(this.http.post(`/api/v1/avisos/${idAviso}/leido`, {}));
    this.avisosNoLeidos.update((n) => Math.max(0, n - 1));
  }

  // ---------------------------------------------------------------- apoyo

  private async actualizar(operacion: OperacionLocal): Promise<void> {
    await this.almacen.guardarOperacion(operacion);
    this.ordenar(this.operaciones().map((o) => (o.uuid === operacion.uuid ? operacion : o)));
  }

  private ordenar(operaciones: OperacionLocal[]): void {
    this.operaciones.set([...operaciones].sort((a, b) => b.registradaEn.localeCompare(a.registradaEn)));
  }

  private programarReintento(): void {
    this.cancelarReintento();
    const espera = Math.min(ESPERA_MAXIMA_MS, ESPERA_INICIAL_MS * 2 ** this.reintentos);
    this.reintentos += 1;
    this.temporizador = setTimeout(() => void this.sincronizar(), espera);
  }

  private cancelarReintento(): void {
    if (this.temporizador) clearTimeout(this.temporizador);
    this.temporizador = null;
  }

  private exigirClave(): string {
    const clave = this.clave();
    if (!clave) throw new Error('No hay una tienda abierta.');
    return clave;
  }
}

function esFaltaDeEspacio(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'QuotaExceededError';
}
