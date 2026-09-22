/**
 * Pruebas unitarias para BitacoraAdminService (CU30: Consultar bitacora).
 * Nomenclatura oficial: "Consultar bitacora"
 */

import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { BitacoraAdminService } from './bitacora-admin.service';
import { LoginService } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import { BitacoraFiltros, BitacoraListadoRespuesta } from '../modelos/bitacora.dto';

describe('BitacoraAdminService', () => {
  let service: BitacoraAdminService;
  let httpMock: HttpTestingController;

  const mockLoginService = {
    obtenerToken: () => 'fake-jwt-token-admin',
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        BitacoraAdminService,
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: LoginService, useValue: mockLoginService },
      ],
    });

    service = TestBed.inject(BitacoraAdminService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('debe crearse e inicializarse correctamente el servicio', () => {
    expect(service).toBeTruthy();
    expect(service.eventos()).toEqual([]);
    expect(service.totalEventos()).toBe(0);
    expect(service.cargando()).toBe(false);
  });

  it('debe listar eventos y actualizar senales reactivas', () => {
    const mockRespuesta: BitacoraListadoRespuesta = {
      items: [
        {
          id_bitacora: 1,
          id_usuario: 1,
          usuario_nombre: 'admin@fashionstore.com',
          accion: 'CREAR_PROVEEDOR',
          tabla_modulo: 'PROVEEDORES',
          direccion_ip: '127.0.0.1',
          severidad: 'INFO',
          tiene_payload: true,
          creado_en: '2026-09-22T03:00:00Z',
        },
      ],
      total: 1,
      pagina: 1,
      limite: 20,
      total_paginas: 1,
      metricas: {
        total_eventos: 1,
        eventos_criticos: 0,
        advertencias_errores: 0,
        usuarios_activos: 1,
      },
    };

    const filtros: BitacoraFiltros = {
      ordenar_por: 'creado_en_desc',
      pagina: 1,
      limite: 20,
    };

    service.listar(filtros).subscribe((resp) => {
      expect(resp.total).toBe(1);
      expect(resp.items.length).toBe(1);
    });

    const req = httpMock.expectOne((r) => r.url === '/api/v1/admin/bitacora');
    expect(req.request.method).toBe('GET');
    expect(req.request.headers.get('Authorization')).toBe('Bearer fake-jwt-token-admin');
    expect(req.request.params.get('ordenar_por')).toBe('creado_en_desc');

    req.flush(mockRespuesta);

    expect(service.eventos().length).toBe(1);
    expect(service.totalEventos()).toBe(1);
    expect(service.metricas().total_eventos).toBe(1);
    expect(service.cargando()).toBe(false);
  });

  it('debe recuperar el detalle unitario de un evento con payloads', () => {
    const mockDetalle = {
      id_bitacora: 42,
      id_usuario: 1,
      usuario_nombre: 'admin@fashionstore.com',
      accion: 'MODIFICAR_PRENDA',
      tabla_modulo: 'PRODUCTOS',
      direccion_ip: '192.168.1.1',
      severidad: 'WARN' as const,
      tiene_payload: true,
      payload_anterior: { precio: 100 },
      payload_nuevo: { precio: 120 },
      creado_en: '2026-09-22T03:10:00Z',
    };

    service.obtenerDetalle(42).subscribe((det) => {
      expect(det.id_bitacora).toBe(42);
      expect(det.payload_nuevo).toEqual({ precio: 120 });
    });

    const req = httpMock.expectOne('/api/v1/admin/bitacora/42');
    expect(req.request.method).toBe('GET');
    req.flush(mockDetalle);

    expect(service.eventoSeleccionado()?.id_bitacora).toBe(42);
    expect(service.cargandoDetalle()).toBe(false);

    service.cerrarModalDetalle();
    expect(service.eventoSeleccionado()).toBeNull();
  });

  it('debe manejar error HTTP 403 y actualizar senal de error', () => {
    const filtros: BitacoraFiltros = {
      ordenar_por: 'creado_en_desc',
      pagina: 1,
      limite: 20,
    };

    service.listar(filtros).subscribe({
      next: () => {},
      error: (err) => {
        expect(err.message).toContain('Acceso denegado');
      },
    });

    const req = httpMock.expectOne((r) => r.url === '/api/v1/admin/bitacora');
    req.flush({ detail: 'No autorizado' }, { status: 403, statusText: 'Forbidden' });

    expect(service.error()).toContain('Acceso denegado');
    expect(service.cargando()).toBe(false);
  });
});
