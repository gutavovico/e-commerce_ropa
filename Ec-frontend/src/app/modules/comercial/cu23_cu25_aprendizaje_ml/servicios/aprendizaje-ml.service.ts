import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  ConsultaPrediccionesMl,
  ConsultaSegmentosMl,
  CrearDatasetMlPeticion,
  DatasetMlItem,
  EntrenarModeloMlPeticion,
  ModeloMlItem,
  ResumenAprendizajeMl,
} from '../modelos/aprendizaje-ml.model';

@Injectable({ providedIn: 'root' })
export class AprendizajeMlService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/aprendizaje-ml';

  obtenerResumen(): Observable<ResumenAprendizajeMl> {
    return this.http.get<ResumenAprendizajeMl>(`${this.baseUrl}/resumen`);
  }

  crearDataset(datos: CrearDatasetMlPeticion): Observable<DatasetMlItem> {
    return this.http.post<DatasetMlItem>(`${this.baseUrl}/datasets`, datos);
  }

  entrenarModelo(datos: EntrenarModeloMlPeticion): Observable<ModeloMlItem> {
    return this.http.post<ModeloMlItem>(
      `${this.baseUrl}/modelos/entrenar`,
      datos
    );
  }

  activarModelo(idModelo: number): Observable<ModeloMlItem> {
    return this.http.patch<ModeloMlItem>(
      `${this.baseUrl}/modelos/${idModelo}/activar`,
      {}
    );
  }

  archivarModelo(idModelo: number): Observable<ModeloMlItem> {
    return this.http.patch<ModeloMlItem>(
      `${this.baseUrl}/modelos/${idModelo}/archivar`,
      {}
    );
  }

  consultarPredicciones(filtros?: {
    id_producto?: number | null;
    id_sucursal?: number | null;
    periodo?: string | null;
    tipo_cambio_bob?: number;
  }): Observable<ConsultaPrediccionesMl> {
    let params = new HttpParams();
    if (filtros?.id_producto) {
      params = params.set('id_producto', String(filtros.id_producto));
    }
    if (filtros?.id_sucursal) {
      params = params.set('id_sucursal', String(filtros.id_sucursal));
    }
    if (filtros?.periodo) {
      params = params.set('periodo', filtros.periodo);
    }
    if (filtros?.tipo_cambio_bob) {
      params = params.set('tipo_cambio_bob', String(filtros.tipo_cambio_bob));
    }
    return this.http.get<ConsultaPrediccionesMl>(
      `${this.baseUrl}/predicciones`,
      { params }
    );
  }

  consultarSegmentos(tipoCambioBob = 6.96): Observable<ConsultaSegmentosMl> {
    const params = new HttpParams().set(
      'tipo_cambio_bob',
      String(tipoCambioBob)
    );
    return this.http.get<ConsultaSegmentosMl>(`${this.baseUrl}/segmentos`, {
      params,
    });
  }
}

