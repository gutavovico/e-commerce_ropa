import { TestBed } from '@angular/core/testing';
import {
  provideHttpClientTesting,
  HttpTestingController,
} from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { ProductosAdminService } from './productos-admin.service';
import {
  MatrizVariantesPayload,
  ProductoCrearPayload,
  ProductoResumenAdmin,
  VarianteAdmin,
} from '../modelos/producto.dto';

describe('ProductosAdminService', () => {
  let service: ProductosAdminService;
  let httpMock: HttpTestingController;

  const mockProducto: ProductoResumenAdmin = {
    id_producto: 1,
    nombre: 'Vestido Seda Plisado',
    descripcion: 'Alta costura atelier',
    precio_base: 450.0,
    id_categoria: 2,
    categoria_nombre: 'Vestidos',
    id_coleccion: null,
    coleccion_nombre: null,
    imagen_url: null,
    modelo_ar_url: null,
    activo: true,
    total_variantes: 2,
    stock_total: 10,
    creado_en: '2026-09-20T00:00:00Z',
  };

  const mockVariante: VarianteAdmin = {
    id_variante: 10,
    id_producto: 1,
    id_talla: 1,
    talla_codigo: '38',
    id_color: 2,
    color_nombre: 'Marfil',
    color_hex: '#FFFFF0',
    sku: 'FS-VESTIDO-SEDA-38-MARFIL',
    precio_extra: 0.0,
    precio_final: 450.0,
    activo: true,
    stock_disponible: 5,
    creado_en: '2026-09-20T00:00:00Z',
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        ProductosAdminService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });

    service = TestBed.inject(ProductosAdminService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('debe instanciarse correctamente', () => {
    expect(service).toBeTruthy();
    expect(service.productos()).toEqual([]);
    expect(service.cargando()).toBe(false);
  });

  it('debe cargar la lista de productos y actualizar la signal (cargarProductos)', () => {
    service.cargarProductos().subscribe((data) => {
      expect(data.length).toBe(1);
      expect(data[0].nombre).toBe('Vestido Seda Plisado');
    });

    expect(service.cargando()).toBe(true);

    const req = httpMock.expectOne('/api/v1/admin/productos');
    expect(req.request.method).toBe('GET');
    req.flush([mockProducto]);

    expect(service.cargando()).toBe(false);
    expect(service.productos().length).toBe(1);
    expect(service.productos()[0].id_producto).toBe(1);
  });

  it('debe crear un producto nuevo y agregarlo a la signal (crearProducto)', () => {
    const payload: ProductoCrearPayload = {
      nombre: 'Blazer Esmoquin Terciopelo',
      id_categoria: 3,
      precio_base: 380.0,
      activo: true,
    };

    const nuevoProducto: ProductoResumenAdmin = {
      ...mockProducto,
      id_producto: 2,
      nombre: 'Blazer Esmoquin Terciopelo',
      precio_base: 380.0,
    };

    service.crearProducto(payload).subscribe((data) => {
      expect(data.id_producto).toBe(2);
    });

    expect(service.guardando()).toBe(true);

    const req = httpMock.expectOne('/api/v1/admin/productos');
    expect(req.request.method).toBe('POST');
    req.flush(nuevoProducto);

    expect(service.guardando()).toBe(false);
    expect(service.productos().length).toBe(1);
    expect(service.mensajeExito()).toContain('registrada correctamente');
  });

  it('debe conmutar el estado logico de un producto (cambiarEstadoProducto)', () => {
    service.productos.set([mockProducto]);

    service.cambiarEstadoProducto(1, false).subscribe();

    const req = httpMock.expectOne('/api/v1/admin/productos/1/estado');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ activo: false });

    req.flush({ ...mockProducto, activo: false });

    expect(service.productos()[0].activo).toBe(false);
    expect(service.mensajeExito()).toContain('desactivada (baja logica)');
  });

  it('debe eliminar un producto y retirarlo de la signal (eliminarProducto)', () => {
    service.productos.set([mockProducto]);

    service.eliminarProducto(1).subscribe();

    const req = httpMock.expectOne('/api/v1/admin/productos/1');
    expect(req.request.method).toBe('DELETE');
    req.flush(null);

    expect(service.productos().length).toBe(0);
    expect(service.mensajeExito()).toContain('eliminada correctamente');
  });

  it('debe generar la matriz de variantes y actualizar la signal (generarMatrizVariantes)', () => {
    const payload: MatrizVariantesPayload = {
      ids_tallas: [1],
      ids_colores: [2],
      precio_extra_defecto: 0.0,
    };

    service.generarMatrizVariantes(1, payload).subscribe((nuevas) => {
      expect(nuevas.length).toBe(1);
      expect(nuevas[0].sku).toBe('FS-VESTIDO-SEDA-38-MARFIL');
    });

    const req = httpMock.expectOne('/api/v1/admin/productos/1/variantes/matriz');
    expect(req.request.method).toBe('POST');
    req.flush([mockVariante]);

    expect(service.variantes().length).toBe(1);
    expect(service.mensajeExito()).toContain('1 combinaciones de variantes');
  });

  it('debe capturar errores HTTP y actualizar la signal de error', () => {
    service.cargarProductos().subscribe({
      error: () => {
        expect(service.error()).toBe('Error de autenticacion');
      },
    });

    const req = httpMock.expectOne('/api/v1/admin/productos');
    req.flush(
      { detail: 'Error de autenticacion' },
      { status: 401, statusText: 'Unauthorized' }
    );

    expect(service.cargando()).toBe(false);
  });

  it('debe subir una imagen local y retornar la url estatica (subirImagen)', () => {
    const archivo = new File(['contenido-simulado'], 'vestido.png', {
      type: 'image/png',
    });

    service.subirImagen(archivo).subscribe((resp) => {
      expect(resp.url).toBe('/static/uploads/productos/prod_vestido.png');
    });

    const req = httpMock.expectOne('/api/v1/admin/productos/upload-imagen');
    expect(req.request.method).toBe('POST');
    expect(req.request.body instanceof FormData).toBe(true);

    req.flush({ url: '/static/uploads/productos/prod_vestido.png' });
  });

  it('debe propagar error si la subida de imagen falla y actualizar la signal de error', () => {
    const archivo = new File(['contenido'], 'archivo.pdf', {
      type: 'application/pdf',
    });

    service.subirImagen(archivo).subscribe({
      error: (err) => {
        expect(err.status).toBe(400);
        expect(service.error()).toBe('Formato de imagen no admitido.');
      },
    });

    const req = httpMock.expectOne('/api/v1/admin/productos/upload-imagen');
    req.flush(
      { detail: 'Formato de imagen no admitido.' },
      { status: 400, statusText: 'Bad Request' }
    );
  });
});
