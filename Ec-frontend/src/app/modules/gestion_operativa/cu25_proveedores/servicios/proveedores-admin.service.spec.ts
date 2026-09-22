import { TestBed } from '@angular/core/testing';
import {
  provideHttpClientTesting,
  HttpTestingController,
} from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { ProveedoresAdminService } from './proveedores-admin.service';
import {
  ListaPaginadaProveedores,
  ProveedorActualizarPayload,
  ProveedorCrearPayload,
  ProveedorItemAdmin,
} from '../modelos/proveedor.dto';

describe('ProveedoresAdminService', () => {
  let service: ProveedoresAdminService;
  let httpMock: HttpTestingController;

  const mockItem: ProveedorItemAdmin = {
    id_proveedor: 1,
    razon_social: 'Hilaturas Andinas S.A.',
    nit_rut: '1020304050',
    contacto_nombre: 'Gonzalo Morales',
    telefono: '70123456',
    email: 'contacto@hilaturasandinas.com',
    direccion: 'Av. Industrial #450',
    ciudad: 'La Paz',
    rubro: 'Tejidos Naturales (Seda/Lino)',
    estado_activo: true,
    creado_en: '2026-09-21T10:00:00Z',
    actualizado_en: '2026-09-21T10:00:00Z',
  };

  const mockLista: ListaPaginadaProveedores = {
    items: [mockItem],
    total: 1,
    pagina: 1,
    limite: 20,
    total_paginas: 1,
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        ProveedoresAdminService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });

    service = TestBed.inject(ProveedoresAdminService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('debe instanciarse correctamente con estado inicial limpio', () => {
    expect(service).toBeTruthy();
    expect(service.proveedores()).toEqual([]);
    expect(service.cargando()).toBe(false);
    expect(service.guardando()).toBe(false);
    expect(service.error()).toBeNull();
    expect(service.mensajeExito()).toBeNull();
  });

  it('debe cargar proveedores con query params y actualizar Signals reactivos', () => {
    service
      .cargarProveedores({ q: 'Andinas', estado: 'activos', rubro: 'Tejidos' })
      .subscribe((res) => {
        expect(res.items.length).toBe(1);
        expect(res.total).toBe(1);
      });

    const req = httpMock.expectOne(
      (r) =>
        r.url === '/api/v1/admin/proveedores' &&
        r.params.get('q') === 'Andinas' &&
        r.params.get('estado') === 'activos' &&
        r.params.get('rubro') === 'Tejidos'
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockLista);

    expect(service.proveedores().length).toBe(1);
    expect(service.totalRegistros()).toBe(1);
    expect(service.cargando()).toBe(false);
  });

  it('debe omitir parametros vacios o de valor todos al consultar proveedores', () => {
    service
      .cargarProveedores({ q: '', estado: 'todos', rubro: 'todos' })
      .subscribe();

    const req = httpMock.expectOne((r) => r.url === '/api/v1/admin/proveedores');
    expect(req.request.params.has('q')).toBe(false);
    expect(req.request.params.has('estado')).toBe(false);
    expect(req.request.params.has('rubro')).toBe(false);
    req.flush(mockLista);
  });

  it('debe crear un nuevo proveedor y agregarlo al inicio de la lista reactiva', () => {
    const payload: ProveedorCrearPayload = {
      razon_social: 'Sederia Central',
      nit_rut: '5566778899',
      contacto_nombre: 'Mariana Lopez',
      telefono: '78912345',
      email: 'mariana@sederiacentral.com',
      direccion: 'Calle Comercio #120',
      ciudad: 'Cochabamba',
      rubro: 'Sastreria de Lujo',
    };

    const nuevoItem: ProveedorItemAdmin = {
      ...payload,
      id_proveedor: 2,
      estado_activo: true,
      creado_en: '2026-09-21T11:00:00Z',
      actualizado_en: '2026-09-21T11:00:00Z',
    };

    service.crearProveedor(payload).subscribe((item) => {
      expect(item.id_proveedor).toBe(2);
      expect(item.razon_social).toBe('Sederia Central');
    });

    const req = httpMock.expectOne('/api/v1/admin/proveedores');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush(nuevoItem);

    expect(service.proveedores().length).toBe(1);
    expect(service.proveedores()[0].id_proveedor).toBe(2);
    expect(service.mensajeExito()).toContain('exitosamente');
  });

  it('debe actualizar la ficha comercial y reflejar los cambios en el Signal reactivo', () => {
    service.proveedores.set([mockItem]);

    const payload: ProveedorActualizarPayload = {
      telefono: '79998877',
      contacto_nombre: 'Gonzalo Morales Actualizado',
    };

    const itemActualizado: ProveedorItemAdmin = {
      ...mockItem,
      ...payload,
      actualizado_en: '2026-09-21T12:00:00Z',
    };

    service.actualizarProveedor(1, payload).subscribe((item) => {
      expect(item.telefono).toBe('79998877');
    });

    const req = httpMock.expectOne('/api/v1/admin/proveedores/1');
    expect(req.request.method).toBe('PUT');
    req.flush(itemActualizado);

    expect(service.proveedores()[0].contacto_nombre).toBe(
      'Gonzalo Morales Actualizado'
    );
    expect(service.mensajeExito()).toContain('actualizada');
  });

  it('debe cambiar el estado operativo (baja logica) y actualizar el item en la lista', () => {
    service.proveedores.set([mockItem]);

    const itemDesactivado: ProveedorItemAdmin = {
      ...mockItem,
      estado_activo: false,
    };

    service.cambiarEstadoProveedor(1, false).subscribe((item) => {
      expect(item.estado_activo).toBe(false);
    });

    const req = httpMock.expectOne('/api/v1/admin/proveedores/1/estado');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ estado_activo: false });
    req.flush(itemDesactivado);

    expect(service.proveedores()[0].estado_activo).toBe(false);
    expect(service.mensajeExito()).toContain('desactivado');
  });

  it('debe capturar error HTTP 409 y reflejar mensaje descriptivo de conflicto', () => {
    service
      .crearProveedor({
        razon_social: 'Duplicado S.A.',
        nit_rut: '1020304050',
        contacto_nombre: 'Test',
        telefono: '70000000',
        email: 'test@duplicado.com',
        direccion: 'Calle Test 123',
        ciudad: 'La Paz',
        rubro: 'Sastreria',
      })
      .subscribe({
        error: (err) => {
          expect(err.status).toBe(409);
        },
      });

    const req = httpMock.expectOne('/api/v1/admin/proveedores');
    req.flush(
      { detail: 'Ya existe un proveedor registrado con el NIT/RUT 1020304050.' },
      { status: 409, statusText: 'Conflict' }
    );

    expect(service.error()).toContain('NIT/RUT');
    expect(service.guardando()).toBe(false);
  });

  it('debe capturar error HTTP 422 y reflejar mensaje descriptivo de datos invalidos', () => {
    service.cargarProveedores().subscribe({
      error: (err) => {
        expect(err.status).toBe(422);
      },
    });

    const req = httpMock.expectOne((r) => r.url === '/api/v1/admin/proveedores');
    req.flush(
      { detail: 'Datos invalidos en parametros de consulta.' },
      { status: 422, statusText: 'Unprocessable Entity' }
    );

    expect(service.error()).toContain('Datos invalidos');
    expect(service.cargando()).toBe(false);
  });

  it('debe limpiar los mensajes contextuales al invocar limpiarMensajes', () => {
    service.error.set('Un error');
    service.mensajeExito.set('Un exito');

    service.limpiarMensajes();

    expect(service.error()).toBeNull();
    expect(service.mensajeExito()).toBeNull();
  });
});
