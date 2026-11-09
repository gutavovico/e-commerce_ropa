import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { SucursalesAdminService } from './sucursales-admin.service';
import {
  Ciudad,
  SucursalAdmin,
  SucursalCrearPayload,
} from '../modelos/sucursal.model';

describe('SucursalesAdminService (CU21)', () => {
  let service: SucursalesAdminService;
  let httpMock: HttpTestingController;

  const mockCiudades: Ciudad[] = [
    {
      id_ciudad: 1,
      nombre: 'Madrid',
      pais: 'Espana',
      creado_en: '2026-01-10T10:00:00Z',
      total_sucursales: 2,
    },
    {
      id_ciudad: 2,
      nombre: 'Barcelona',
      pais: 'Espana',
      creado_en: '2026-01-12T11:00:00Z',
      total_sucursales: 1,
    },
  ];

  const mockSucursales: SucursalAdmin[] = [
    {
      id_sucursal: 10,
      id_ciudad: 1,
      ciudad_nombre: 'Madrid',
      nombre: 'Boutique Serrano Haute Couture',
      direccion: 'Calle de Serrano 45',
      telefono: '+34 910 123 456',
      horario_apertura: '10:00',
      horario_cierre: '20:30',
      activa: true,
      creado_en: '2026-01-15T09:00:00Z',
      total_empleados: 8,
      total_prendas_stock: 120,
      reservas_activas_conteo: 3,
    },
    {
      id_sucursal: 20,
      id_ciudad: 2,
      ciudad_nombre: 'Barcelona',
      nombre: 'Atelier Paseo de Gracia',
      direccion: 'Passeig de Gracia 88',
      telefono: '+34 934 987 654',
      horario_apertura: '10:30',
      horario_cierre: '21:00',
      activa: false,
      creado_en: '2026-01-20T10:00:00Z',
      total_empleados: 0,
      total_prendas_stock: 0,
      reservas_activas_conteo: 0,
    },
  ];

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        SucursalesAdminService,
      ],
    });

    service = TestBed.inject(SucursalesAdminService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('debe inicializarse con señales reactivas vacias', () => {
    expect(service.ciudades()).toEqual([]);
    expect(service.sucursales()).toEqual([]);
    expect(service.cargando()).toBe(false);
    expect(service.guardando()).toBe(false);
    expect(service.error()).toBeNull();
    expect(service.mensajeExito()).toBeNull();
  });

  it('debe cargar la lista de ciudades y actualizar el signal correspondiente', () => {
    service.cargarCiudades().subscribe((data) => {
      expect(data.length).toBe(2);
      expect(data[0].nombre).toBe('Madrid');
    });

    expect(service.cargando()).toBe(true);

    const req = httpMock.expectOne('/api/v1/admin/ciudades');
    expect(req.request.method).toBe('GET');
    req.flush(mockCiudades);

    expect(service.cargando()).toBe(false);
    expect(service.ciudades()).toEqual(mockCiudades);
    expect(service.error()).toBeNull();
  });

  it('carga el uso del plan de sucursales tal como lo devuelve el servidor (P2-CU04 B7)', () => {
    service.cargarUsoPlan().subscribe();
    const req = httpMock.expectOne('/api/v1/admin/sucursales/uso-plan');
    expect(req.request.method).toBe('GET');
    req.flush({ uso: 2, limite: 2, plan: 'Básico' });
    expect(service.usoPlan()).toEqual({ uso: 2, limite: 2, plan: 'Básico' });
  });

  it('muestra el mensaje del servidor ante el límite del plan (409 LIMITE_PLAN_ALCANZADO)', () => {
    let mensaje = '';
    service.cambiarEstado(10, true).subscribe({ error: (err: Error) => (mensaje = err.message) });
    httpMock.expectOne('/api/v1/admin/sucursales/10/estado').flush(
      {
        detail: 'El plan Básico permite 2 sucursales activas y la empresa ya usa 2. Cambie de plan o libere alguna.',
        code: 'LIMITE_PLAN_ALCANZADO',
      },
      { status: 409, statusText: 'Conflict' },
    );
    expect(mensaje).toContain('El plan Básico permite 2 sucursales activas');
  });
  it('debe cargar sucursales administrativas con parametros de filtrado', () => {
    service.cargarSucursales({ id_ciudad: 1, activa: true, q: 'Serrano' }).subscribe((data) => {
      expect(data.length).toBe(1);
      expect(data[0].id_sucursal).toBe(10);
    });

    expect(service.cargando()).toBe(true);

    const req = httpMock.expectOne((r) =>
      r.url === '/api/v1/admin/sucursales' &&
      r.params.get('id_ciudad') === '1' &&
      r.params.get('activa') === 'true' &&
      r.params.get('q') === 'Serrano'
    );
    expect(req.request.method).toBe('GET');
    req.flush([mockSucursales[0]]);

    expect(service.cargando()).toBe(false);
    expect(service.sucursales().length).toBe(1);
    expect(service.sucursales()[0].nombre).toBe('Boutique Serrano Haute Couture');
  });

  it('debe registrar una nueva boutique y anteponerla en la signal', () => {
    service.sucursales.set([...mockSucursales]);

    const nuevaPayload: SucursalCrearPayload = {
      id_ciudad: 1,
      nombre: 'Atelier Gran Via',
      direccion: 'Gran Via 12',
      telefono: '+34 911 222 333',
      horario_apertura: '10:00',
      horario_cierre: '21:00',
    };

    const nuevaCreada: SucursalAdmin = {
      id_sucursal: 30,
      id_ciudad: 1,
      ciudad_nombre: 'Madrid',
      nombre: 'Atelier Gran Via',
      direccion: 'Gran Via 12',
      telefono: '+34 911 222 333',
      horario_apertura: '10:00',
      horario_cierre: '21:00',
      activa: true,
      creado_en: '2026-02-15T10:00:00Z',
      total_empleados: 0,
      total_prendas_stock: 0,
      reservas_activas_conteo: 0,
    };

    service.crearSucursal(nuevaPayload).subscribe((res) => {
      expect(res.id_sucursal).toBe(30);
    });

    const req = httpMock.expectOne('/api/v1/admin/sucursales');
    expect(req.request.method).toBe('POST');
    req.flush(nuevaCreada);

    expect(service.sucursales().length).toBe(3);
    expect(service.sucursales()[0].id_sucursal).toBe(30);
    expect(service.mensajeExito()).toContain('creada con exito');
  });

  it('debe cambiar el estado operativo de una boutique via PATCH', () => {
    service.sucursales.set([...mockSucursales]);

    service.cambiarEstado(20, true).subscribe((res) => {
      expect(res.activa).toBe(true);
    });

    const req = httpMock.expectOne('/api/v1/admin/sucursales/20/estado');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ activa: true });

    const actualizada: SucursalAdmin = {
      ...mockSucursales[1],
      activa: true,
    };
    req.flush(actualizada);

    expect(service.sucursales().find((s) => s.id_sucursal === 20)?.activa).toBe(true);
    expect(service.mensajeExito()).toContain('activada');
  });

  it('debe capturar conflicto 409 al intentar desactivar sucursal con operaciones pendientes', () => {
    service.sucursales.set([...mockSucursales]);

    service.cambiarEstado(10, false).subscribe({
      next: () => {
        throw new Error('No debio cambiar de estado');
      },
      error: (err) => {
        expect(err.message).toContain('reservas');
      },
    });

    const req = httpMock.expectOne('/api/v1/admin/sucursales/10/estado');
    req.flush(
      { detail: 'No se puede desactivar la sucursal: mantiene reservas activas o inventario en custodia.' },
      { status: 409, statusText: 'Conflict' }
    );

    expect(service.error()).toContain('reservas');
  });

  it('debe limpiar los mensajes reactivos de error y exito', () => {
    service.error.set('Error previo');
    service.mensajeExito.set('Exito previo');

    service.limpiarMensajes();

    expect(service.error()).toBeNull();
    expect(service.mensajeExito()).toBeNull();
  });
});
