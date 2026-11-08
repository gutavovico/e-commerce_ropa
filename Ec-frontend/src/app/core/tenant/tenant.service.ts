import { Injectable, computed, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ResolveEnd, Router } from '@angular/router';
import { Observable, filter, tap } from 'rxjs';
import { EmpresaPublica, RegistroEnTiendaRespuesta } from './tenant.models';

/**
 * P2-CU02 · Tienda (empresa) del portal web `/{codigo}`.
 *
 * - `tenantActual` lo fija `tenantGuard` al entrar en un portal y se limpia al salir de él (cualquier
 *   navegación cuyo primer segmento no sea el código de la tienda). `authInterceptor` lo envía en la
 *   cabecera `X-Tenant`: fuera del portal (directorio, login general, panel `/admin`) no se envía.
 * - `misEmpresas` son las tiendas en las que está registrado el cliente con sesión (`null` = sin cargar).
 * - `ruta()` antepone `/{codigo}` a las rutas del cliente mientras se navega dentro de un portal.
 */
@Injectable({ providedIn: 'root' })
export class TenantService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  readonly tenantActual = signal<EmpresaPublica | null>(null);
  readonly misEmpresas = signal<EmpresaPublica[] | null>(null);
  /** Un 403 CLIENTE_NO_REGISTRADO pide abrir «Registrarme en esta tienda». */
  readonly registroSolicitado = signal(false);

  readonly estaRegistradoEnTienda = computed(() => {
    const tienda = this.tenantActual();
    const empresas = this.misEmpresas();
    if (!tienda || empresas === null) return null;
    return empresas.some((e) => e.codigo === tienda.codigo);
  });

  constructor() {
    this.router.events
      .pipe(filter((e): e is ResolveEnd => e instanceof ResolveEnd))
      .subscribe((evento) => {
        const actual = this.tenantActual();
        if (actual && primerSegmento(evento.urlAfterRedirects) !== actual.codigo) {
          this.tenantActual.set(null);
          this.registroSolicitado.set(false);
        }
      });
  }

  /** Datos públicos del portal; 404 si no existe, 403 si no está disponible. */
  cargar(codigo: string): Observable<EmpresaPublica> {
    return this.http
      .get<EmpresaPublica>(`/api/v1/tenants/${encodeURIComponent(codigo)}`)
      .pipe(tap((empresa) => this.tenantActual.set(empresa)));
  }

  directorio(): Observable<EmpresaPublica[]> {
    return this.http.get<EmpresaPublica[]>('/api/v1/tenants');
  }

  cargarMisEmpresas(): Observable<EmpresaPublica[]> {
    return this.http
      .get<EmpresaPublica[]>('/api/v1/mis-empresas')
      .pipe(tap((empresas) => this.misEmpresas.set(empresas)));
  }

  /** «Registrarme en esta tienda» (A8). La tienda viaja en `X-Tenant`. */
  registrarmeEnTienda(): Observable<RegistroEnTiendaRespuesta> {
    return this.http.post<RegistroEnTiendaRespuesta>('/api/v1/mis-empresas', {}).pipe(
      tap((respuesta) => {
        const actuales = this.misEmpresas() ?? [];
        if (!actuales.some((e) => e.codigo === respuesta.empresa.codigo)) {
          this.misEmpresas.set([...actuales, respuesta.empresa]);
        }
        this.registroSolicitado.set(false);
      })
    );
  }

  limpiarSesion(): void {
    this.misEmpresas.set(null);
    this.registroSolicitado.set(false);
  }

  /**
   * Ruta del cliente dentro del portal actual: `ruta('/productos', 5)` → `['/', 'menshopping',
   * 'productos', 5]`. Fuera de un portal devuelve la ruta sin prefijo.
   */
  ruta(destino: string | readonly (string | number)[], ...resto: (string | number)[]): (string | number)[] {
    const partes: (string | number)[] = Array.isArray(destino)
      ? [...(destino as (string | number)[]), ...resto]
      : [destino as string, ...resto];
    const tienda = this.tenantActual();
    if (!tienda) return partes;
    const [primero, ...demas] = partes;
    const segmentos = String(primero).split('/').filter((s) => s.length > 0);
    return ['/', tienda.codigo, ...segmentos, ...demas];
  }
}

/** Primer segmento de una URL (`/menshopping/bolsa?x=1` → `menshopping`). */
export function primerSegmento(url: string): string {
  return (url.split(/[?#]/)[0].split('/')[1] ?? '').toLowerCase();
}
