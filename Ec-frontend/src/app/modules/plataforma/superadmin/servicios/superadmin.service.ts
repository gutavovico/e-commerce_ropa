import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  BitacoraPlataformaListado,
  CambiarEstadoEmpresaPeticion,
  CatalogoReporteGuardarPeticion,
  CatalogoReporteItem,
  CiudadGlobal,
  CiudadGlobalPeticion,
  ColorGlobal,
  ColorGlobalPeticion,
  EliminacionCatalogoRespuesta,
  EmpresaActualizarPeticion,
  EmpresaCrearPeticion,
  EmpresaDetalle,
  EmpresaResumen,
  EstadoEmpresa,
  EstadoSuscripcion,
  FuncionalidadPlataforma,
  HistorialSuscripcionItem,
  MetadatosCatalogoReportes,
  MetricasPlataforma,
  OperacionSuscripcionPeticion,
  PlanDetalle,
  PlanGuardarPeticion,
  SuscripcionEmpresa,
  TallaGlobal,
  TallaGlobalPeticion,
} from '../modelos/superadmin.model';

@Injectable({ providedIn: 'root' })
export class SuperadminService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/plataforma';

  // --- P2-CU05: Empresas, Métricas y Bitácora ---

  listarEmpresas(filtros?: {
    q?: string;
    estado?: EstadoEmpresa | '';
    id_plan?: number | null;
  }): Observable<EmpresaResumen[]> {
    let params = new HttpParams();
    if (filtros?.q?.trim()) {
      params = params.set('q', filtros.q.trim());
    }
    if (filtros?.estado) {
      params = params.set('estado', filtros.estado);
    }
    if (filtros?.id_plan) {
      params = params.set('id_plan', String(filtros.id_plan));
    }
    return this.http.get<EmpresaResumen[]>(`${this.baseUrl}/empresas`, { params });
  }

  obtenerEmpresa(idTenant: number): Observable<EmpresaDetalle> {
    return this.http.get<EmpresaDetalle>(`${this.baseUrl}/empresas/${idTenant}`);
  }

  registrarEmpresa(datos: EmpresaCrearPeticion): Observable<EmpresaDetalle> {
    return this.http.post<EmpresaDetalle>(`${this.baseUrl}/empresas`, datos);
  }

  actualizarEmpresa(idTenant: number, datos: EmpresaActualizarPeticion): Observable<EmpresaDetalle> {
    return this.http.put<EmpresaDetalle>(`${this.baseUrl}/empresas/${idTenant}`, datos);
  }

  cambiarEstadoEmpresa(
    idTenant: number,
    datos: CambiarEstadoEmpresaPeticion
  ): Observable<EmpresaDetalle> {
    return this.http.patch<EmpresaDetalle>(`${this.baseUrl}/empresas/${idTenant}/estado`, datos);
  }

  obtenerMetricas(): Observable<MetricasPlataforma> {
    return this.http.get<MetricasPlataforma>(`${this.baseUrl}/metricas`);
  }

  listarBitacora(filtros?: {
    id_tenant?: number | null;
    solo_plataforma?: boolean;
    severidad?: string;
    q?: string;
    pagina?: number;
    limite?: number;
  }): Observable<BitacoraPlataformaListado> {
    let params = new HttpParams();
    if (filtros?.id_tenant) {
      params = params.set('id_tenant', String(filtros.id_tenant));
    }
    if (filtros?.solo_plataforma) {
      params = params.set('solo_plataforma', 'true');
    }
    if (filtros?.severidad?.trim()) {
      params = params.set('severidad', filtros.severidad.trim());
    }
    if (filtros?.q?.trim()) {
      params = params.set('q', filtros.q.trim());
    }
    params = params.set('pagina', String(filtros?.pagina ?? 1));
    params = params.set('limite', String(filtros?.limite ?? 20));
    return this.http.get<BitacoraPlataformaListado>(`${this.baseUrl}/bitacora`, { params });
  }

  // --- P2-CU06: Planes y Funcionalidades ---

  listarFuncionalidades(): Observable<FuncionalidadPlataforma[]> {
    return this.http.get<FuncionalidadPlataforma[]>(`${this.baseUrl}/funcionalidades`);
  }

  listarPlanes(soloActivos = false): Observable<PlanDetalle[]> {
    const params = new HttpParams().set('solo_activos', String(soloActivos));
    return this.http.get<PlanDetalle[]>(`${this.baseUrl}/planes`, { params });
  }

  crearPlan(datos: PlanGuardarPeticion): Observable<PlanDetalle> {
    return this.http.post<PlanDetalle>(`${this.baseUrl}/planes`, datos);
  }

  actualizarPlan(idPlan: number, datos: PlanGuardarPeticion): Observable<PlanDetalle> {
    return this.http.put<PlanDetalle>(`${this.baseUrl}/planes/${idPlan}`, datos);
  }

  cambiarEstadoPlan(idPlan: number, activo: boolean): Observable<PlanDetalle> {
    return this.http.patch<PlanDetalle>(`${this.baseUrl}/planes/${idPlan}/estado`, { activo });
  }

  // --- P2-CU07: Suscripciones de Empresas ---

  listarSuscripciones(filtros?: {
    estado?: EstadoSuscripcion | '';
    id_plan?: number | null;
    id_tenant?: number | null;
  }): Observable<SuscripcionEmpresa[]> {
    let params = new HttpParams();
    if (filtros?.estado) {
      params = params.set('estado', filtros.estado);
    }
    if (filtros?.id_plan) {
      params = params.set('id_plan', String(filtros.id_plan));
    }
    if (filtros?.id_tenant) {
      params = params.set('id_tenant', String(filtros.id_tenant));
    }
    return this.http.get<SuscripcionEmpresa[]>(`${this.baseUrl}/suscripciones`, { params });
  }

  listarHistorialSuscripcion(idTenant: number): Observable<HistorialSuscripcionItem[]> {
    return this.http.get<HistorialSuscripcionItem[]>(
      `${this.baseUrl}/empresas/${idTenant}/suscripciones/historial`
    );
  }

  operarSuscripcion(
    idTenant: number,
    datos: OperacionSuscripcionPeticion
  ): Observable<SuscripcionEmpresa> {
    return this.http.post<SuscripcionEmpresa>(
      `${this.baseUrl}/empresas/${idTenant}/suscripcion`,
      datos
    );
  }

  // --- P2-CU08: Catálogos Globales ---

  listarCiudades(soloActivas = false): Observable<CiudadGlobal[]> {
    const params = new HttpParams().set('solo_activas', String(soloActivas));
    return this.http.get<CiudadGlobal[]>(`${this.baseUrl}/catalogos/ciudades`, { params });
  }

  crearCiudad(datos: CiudadGlobalPeticion): Observable<CiudadGlobal> {
    return this.http.post<CiudadGlobal>(`${this.baseUrl}/catalogos/ciudades`, datos);
  }

  actualizarCiudad(idCiudad: number, datos: CiudadGlobalPeticion): Observable<CiudadGlobal> {
    return this.http.put<CiudadGlobal>(`${this.baseUrl}/catalogos/ciudades/${idCiudad}`, datos);
  }

  cambiarEstadoCiudad(idCiudad: number, activo: boolean): Observable<CiudadGlobal> {
    return this.http.patch<CiudadGlobal>(
      `${this.baseUrl}/catalogos/ciudades/${idCiudad}/estado`,
      { activo }
    );
  }

  eliminarCiudad(idCiudad: number): Observable<EliminacionCatalogoRespuesta> {
    return this.http.delete<EliminacionCatalogoRespuesta>(
      `${this.baseUrl}/catalogos/ciudades/${idCiudad}`
    );
  }

  listarTallas(soloActivas = false): Observable<TallaGlobal[]> {
    const params = new HttpParams().set('solo_activas', String(soloActivas));
    return this.http.get<TallaGlobal[]>(`${this.baseUrl}/catalogos/tallas`, { params });
  }

  crearTalla(datos: TallaGlobalPeticion): Observable<TallaGlobal> {
    return this.http.post<TallaGlobal>(`${this.baseUrl}/catalogos/tallas`, datos);
  }

  actualizarTalla(idTalla: number, datos: TallaGlobalPeticion): Observable<TallaGlobal> {
    return this.http.put<TallaGlobal>(`${this.baseUrl}/catalogos/tallas/${idTalla}`, datos);
  }

  cambiarEstadoTalla(idTalla: number, activo: boolean): Observable<TallaGlobal> {
    return this.http.patch<TallaGlobal>(
      `${this.baseUrl}/catalogos/tallas/${idTalla}/estado`,
      { activo }
    );
  }

  eliminarTalla(idTalla: number): Observable<EliminacionCatalogoRespuesta> {
    return this.http.delete<EliminacionCatalogoRespuesta>(
      `${this.baseUrl}/catalogos/tallas/${idTalla}`
    );
  }

  listarColores(soloActivos = false): Observable<ColorGlobal[]> {
    const params = new HttpParams().set('solo_activos', String(soloActivos));
    return this.http.get<ColorGlobal[]>(`${this.baseUrl}/catalogos/colores`, { params });
  }

  crearColor(datos: ColorGlobalPeticion): Observable<ColorGlobal> {
    return this.http.post<ColorGlobal>(`${this.baseUrl}/catalogos/colores`, datos);
  }

  actualizarColor(idColor: number, datos: ColorGlobalPeticion): Observable<ColorGlobal> {
    return this.http.put<ColorGlobal>(`${this.baseUrl}/catalogos/colores/${idColor}`, datos);
  }

  cambiarEstadoColor(idColor: number, activo: boolean): Observable<ColorGlobal> {
    return this.http.patch<ColorGlobal>(
      `${this.baseUrl}/catalogos/colores/${idColor}/estado`,
      { activo }
    );
  }

  eliminarColor(idColor: number): Observable<EliminacionCatalogoRespuesta> {
    return this.http.delete<EliminacionCatalogoRespuesta>(
      `${this.baseUrl}/catalogos/colores/${idColor}`
    );
  }

  // --- P2-CU22: Catálogo de Reportes Permitidos con IA ---

  listarCatalogoReportes(soloActivos = false): Observable<MetadatosCatalogoReportes> {
    const params = new HttpParams().set('solo_activos', String(soloActivos));
    return this.http.get<MetadatosCatalogoReportes>(
      `${this.baseUrl}/catalogo-reportes`,
      { params }
    );
  }

  crearReporteCatalogo(
    datos: CatalogoReporteGuardarPeticion
  ): Observable<CatalogoReporteItem> {
    return this.http.post<CatalogoReporteItem>(
      `${this.baseUrl}/catalogo-reportes`,
      datos
    );
  }

  actualizarReporteCatalogo(
    idReporte: number,
    datos: CatalogoReporteGuardarPeticion
  ): Observable<CatalogoReporteItem> {
    return this.http.put<CatalogoReporteItem>(
      `${this.baseUrl}/catalogo-reportes/${idReporte}`,
      datos
    );
  }

  cambiarEstadoReporteCatalogo(
    idReporte: number,
    activo: boolean
  ): Observable<CatalogoReporteItem> {
    return this.http.patch<CatalogoReporteItem>(
      `${this.baseUrl}/catalogo-reportes/${idReporte}/estado`,
      { activo }
    );
  }
}

