/**
 * Pruebas unitarias para TemporadasColeccionesAdminService (CU24).
 * Nomenclatura oficial: "Gestionar temporadas y colecciones"
 */

import { TestBed } from '@angular/core/testing';
import {
  provideHttpClientTesting,
  HttpTestingController,
} from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { TemporadasColeccionesAdminService } from './temporadas-colecciones-admin.service';
import {
  ColeccionItem,
  RespuestaPaginadaColecciones,
  RespuestaPaginadaTemporadas,
  TemporadaItem,
} from '../modelos/temporadas-colecciones.dto';

describe('TemporadasColeccionesAdminService', () => {
  let service: TemporadasColeccionesAdminService;
  let httpMock: HttpTestingController;

  const mockTemporada: TemporadaItem = {
    id_temporada: 1,
    nombre: 'Otono - Invierno 2026',
    tipo: 'otono_invierno',
    anio: 2026,
    fecha_inicio: '2026-03-21',
    fecha_fin: '2026-06-20',
    estado_activo: true,
    total_colecciones: 2,
    creado_en: '2026-09-21T10:00:00Z',
    actualizado_en: '2026-09-21T10:00:00Z',
  };

  const mockRespuestaTemporadas: RespuestaPaginadaTemporadas = {
    items: [mockTemporada],
    total: 1,
    pagina: 1,
    limite: 10,
    total_paginas: 1,
  };

  const mockColeccion: ColeccionItem = {
    id_coleccion: 1,
    id_temporada: 1,
    temporada_nombre: 'Otono - Invierno 2026',
    temporada_anio: 2026,
    nombre: 'Capsula Alpaca Real',
    descripcion: 'Prendas de alta gama en fibra de alpaca',
    estado_activo: true,
    total_productos: 5,
    creado_en: '2026-09-21T10:00:00Z',
    actualizado_en: '2026-09-21T10:00:00Z',
  };

  const mockRespuestaColecciones: RespuestaPaginadaColecciones = {
    items: [mockColeccion],
    total: 1,
    pagina: 1,
    limite: 10,
    total_paginas: 1,
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        TemporadasColeccionesAdminService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });

    service = TestBed.inject(TemporadasColeccionesAdminService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('debe instanciarse correctamente con estado reactivo inicial limpio', () => {
    expect(service).toBeTruthy();
    expect(service.pestanaActiva()).toBe('temporadas');
    expect(service.temporadas()).toEqual([]);
    expect(service.colecciones()).toEqual([]);
    expect(service.cargando()).toBe(false);
    expect(service.guardando()).toBe(false);
    expect(service.error()).toBeNull();
    expect(service.mensajeExito()).toBeNull();
  });

  it('debe cambiar de pestana activa y restablecer mensajes contextuales', () => {
    service.error.set('Error previo');
    service.mensajeExito.set('Exito previo');

    service.cambiarPestana('colecciones');

    expect(service.pestanaActiva()).toBe('colecciones');
    expect(service.error()).toBeNull();
    expect(service.mensajeExito()).toBeNull();
  });

  it('debe cargar temporadas con parametros de consulta y actualizar Signals', () => {
    service
      .cargarTemporadas({ q: 'Otono', anio: 2026, estado_activo: 'activas' })
      .subscribe((res) => {
        expect(res.items.length).toBe(1);
        expect(res.total).toBe(1);
      });

    const req = httpMock.expectOne(
      (r) =>
        r.url === '/api/v1/admin/temporadas' &&
        r.params.get('q') === 'Otono' &&
        r.params.get('anio') === '2026' &&
        r.params.get('estado_activo') === 'activas'
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockRespuestaTemporadas);

    expect(service.temporadas().length).toBe(1);
    expect(service.totalTemporadas()).toBe(1);
    expect(service.cargando()).toBe(false);
  });

  it('debe crear una temporada y recargar el listado', () => {
    const payload = {
      nombre: 'Primavera 2027',
      anio: 2027,
      fecha_inicio: '2027-09-21',
      fecha_fin: '2027-12-21',
      estado_activo: true,
    };

    service.crearTemporada(payload).subscribe((res) => {
      expect(res.nombre).toBe('Primavera 2027');
    });

    const reqPost = httpMock.expectOne('/api/v1/admin/temporadas');
    expect(reqPost.request.method).toBe('POST');
    reqPost.flush({ ...mockTemporada, id_temporada: 2, nombre: 'Primavera 2027' });

    // Recarga automatica
    const reqReload = httpMock.expectOne((r) => r.url === '/api/v1/admin/temporadas');
    expect(reqReload.request.method).toBe('GET');
    reqReload.flush(mockRespuestaTemporadas);

    expect(service.mensajeExito()).toContain('registrada exitosamente');
  });

  it('debe conmutar el estado de una temporada (baja logica o reactivacion)', () => {
    service.conmutarEstadoTemporada(1, false).subscribe((res) => {
      expect(res.estado_activo).toBe(false);
    });

    const reqPatch = httpMock.expectOne('/api/v1/admin/temporadas/1/estado');
    expect(reqPatch.request.method).toBe('PATCH');
    reqPatch.flush({ ...mockTemporada, estado_activo: false });

    // Recarga automatica
    const reqReload = httpMock.expectOne((r) => r.url === '/api/v1/admin/temporadas');
    reqReload.flush(mockRespuestaTemporadas);

    expect(service.mensajeExito()).toContain('dada de baja exitosamente');
  });

  it('debe cargar colecciones con filtros y actualizar Signals', () => {
    service
      .cargarColecciones({ q: 'Alpaca', id_temporada: 1, estado_activo: 'activas' })
      .subscribe((res) => {
        expect(res.items.length).toBe(1);
        expect(res.total).toBe(1);
      });

    const req = httpMock.expectOne(
      (r) =>
        r.url === '/api/v1/admin/colecciones' &&
        r.params.get('q') === 'Alpaca' &&
        r.params.get('id_temporada') === '1' &&
        r.params.get('estado_activo') === 'activas'
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockRespuestaColecciones);

    expect(service.colecciones().length).toBe(1);
    expect(service.totalColecciones()).toBe(1);
    expect(service.cargando()).toBe(false);
  });

  it('debe crear una coleccion vinculada y recargar el catalogo', () => {
    const payload = {
      id_temporada: 1,
      nombre: 'Capsula Seda Salvaje',
      descripcion: 'Seda pura',
      estado_activo: true,
    };

    service.crearColeccion(payload).subscribe((res) => {
      expect(res.nombre).toBe('Capsula Seda Salvaje');
    });

    const reqPost = httpMock.expectOne('/api/v1/admin/colecciones');
    expect(reqPost.request.method).toBe('POST');
    reqPost.flush({ ...mockColeccion, id_coleccion: 2, nombre: 'Capsula Seda Salvaje' });

    // Recarga automatica
    const reqReload = httpMock.expectOne((r) => r.url === '/api/v1/admin/colecciones');
    reqReload.flush(mockRespuestaColecciones);

    expect(service.mensajeExito()).toContain('registrada exitosamente');
  });

  it('debe conmutar el estado de una coleccion', () => {
    service.conmutarEstadoColeccion(1, false).subscribe((res) => {
      expect(res.estado_activo).toBe(false);
    });

    const reqPatch = httpMock.expectOne('/api/v1/admin/colecciones/1/estado');
    expect(reqPatch.request.method).toBe('PATCH');
    reqPatch.flush({ ...mockColeccion, estado_activo: false });

    // Recarga automatica
    const reqReload = httpMock.expectOne((r) => r.url === '/api/v1/admin/colecciones');
    reqReload.flush(mockRespuestaColecciones);

    expect(service.mensajeExito()).toContain('dada de baja exitosamente');
  });

  it('debe manejar error 409 de duplicidad y almacenar mensaje explicito', () => {
    service
      .crearTemporada({
        nombre: 'Otono - Invierno 2026',
        anio: 2026,
        fecha_inicio: '2026-03-21',
        fecha_fin: '2026-06-20',
      })
      .subscribe({
        next: () => {},
        error: (err) => {
          expect(err.status).toBe(409);
        },
      });

    const req = httpMock.expectOne('/api/v1/admin/temporadas');
    req.flush(
      { detail: { codigo: 'TEMPORADA_NOMBRE_DUPLICADO', mensaje: 'Ya existe una temporada con ese nombre.' } },
      { status: 409, statusText: 'Conflict' }
    );

    expect(service.error()).toBe('Ya existe una temporada con ese nombre.');
    expect(service.guardando()).toBe(false);
  });

  it('debe manejar error 422 de validacion semantica y almacenar mensaje en Signal', () => {
    service
      .crearColeccion({
        id_temporada: 999,
        nombre: 'Coleccion Invalida',
      })
      .subscribe({
        next: () => {},
        error: (err) => {
          expect(err.status).toBe(422);
        },
      });

    const req = httpMock.expectOne('/api/v1/admin/colecciones');
    req.flush(
      { detail: { codigo: 'TEMPORADA_INACTIVA_PARA_COLECCION', mensaje: 'La temporada se encuentra inactiva.' } },
      { status: 422, statusText: 'Unprocessable Entity' }
    );

    expect(service.error()).toBe('La temporada se encuentra inactiva.');
  });
});
