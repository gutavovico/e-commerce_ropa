import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';

import { CatalogoService } from './catalogo.service';
import { ProductoPaginado, FiltrosDisponibles, ProductoItem } from '../modelos/catalogo.modelos';

describe('CatalogoService (CU06)', () => {
  let service: CatalogoService;
  let httpMock: HttpTestingController;

  const mockProductoItem: ProductoItem = {
    id_producto: 1,
    nombre: 'Vestido plisado seda',
    descripcion: 'Seda natural con corte atelier',
    categoria: 'Vestidos',
    id_categoria: 1,
    coleccion: 'Sastrería Atelier',
    id_coleccion: 1,
    temporada: 'Otoño / Invierno 2024',
    id_temporada: 1,
    precio_base: 890,
    imagen_url: 'https://example.com/foto1.jpg',
    activo: true,
    badge_editorial: 'PIEZA MAESTRA',
    subtitulo_atelier: 'Sastrería Atelier',
    talla_sugerida: '38',
    color_sugerido: 'Ébano',
    variantes: [
      {
        id_variante: 101,
        sku: 'VES-EBA-38',
        talla: '38',
        id_talla: 2,
        color: 'Ébano',
        id_color: 3,
        codigo_hex: '#1A1A1A',
        precio_extra: 0,
        disponible: true,
        cantidad_disponible: 5,
      },
    ],
    en_favoritos: false,
  };

  const mockRespuestaPaginada: ProductoPaginado = {
    items: [mockProductoItem],
    paginacion: {
      total_registros: 1,
      pagina_actual: 1,
      limite: 12,
      total_paginas: 1,
      tiene_siguiente: false,
      tiene_anterior: false,
    },
    filtros_aplicados: {
      q: 'vestido',
      pagina: 1,
      limite: 12,
    },
  };

  const mockFiltrosDisponibles: FiltrosDisponibles = {
    categorias: [{ id: 1, nombre: 'Vestidos', codigo: 'VES', conteo: 5 }],
    colecciones: [{ id: 1, nombre: 'Sastrería Atelier', conteo: 12 }],
    temporadas: [{ id: 1, nombre: 'Otoño / Invierno 2024', codigo: 'FW24', conteo: 20 }],
    tallas: [
      { id: 1, nombre: '36', conteo: 4 },
      { id: 2, nombre: '38', conteo: 8 },
      { id: 3, nombre: '40', conteo: 5 },
    ],
    colores: [
      { id: 1, nombre: 'Marfil', extra: '#FCFBF8', conteo: 3 },
      { id: 2, nombre: 'Camel', extra: '#C2A688', conteo: 6 },
      { id: 3, nombre: 'Ébano', extra: '#1A1A1A', conteo: 10 },
    ],
    precio_min_global: 250,
    precio_max_global: 2400,
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        CatalogoService,
      ],
    });

    service = TestBed.inject(CatalogoService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('debe inicializarse con señales por defecto', () => {
    expect(service.productos()).toEqual([]);
    expect(service.cargando()).toBe(false);
    expect(service.error()).toBeNull();
    expect(service.cestaCount()).toBe(2);
    expect(service.busquedasRecientes().length).toBeGreaterThan(0);
  });

  it('debe buscar productos y actualizar las signals de estado', () => {
    service.buscarProductos({ q: 'vestido', pagina: 1, limite: 12 }).subscribe((res) => {
      expect(res.items.length).toBe(1);
      expect(res.items[0].nombre).toBe('Vestido plisado seda');
    });

    expect(service.cargando()).toBe(true);

    const req = httpMock.expectOne((r) => r.url === '/api/v1/productos' && r.params.has('q'));
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('q')).toBe('vestido');
    expect(req.request.params.get('pagina')).toBe('1');

    req.flush(mockRespuestaPaginada);

    expect(service.cargando()).toBe(false);
    expect(service.productos().length).toBe(1);
    expect(service.paginacion().total_registros).toBe(1);
    expect(service.totalSugerencias()).toBe(1);
  });

  it('debe manejar errores en la búsqueda y actualizar la signal error', () => {
    service.buscarProductos({ q: 'inexistente' }).subscribe({
      next: () => {
        throw new Error('No debería tener éxito');
      },
      error: (err) => {
        expect(err.status).toBe(500);
      },
    });

    const req = httpMock.expectOne((r) => r.url === '/api/v1/productos');
    req.flush({ detail: 'Fallo interno de catálogo' }, { status: 500, statusText: 'Server Error' });

    expect(service.cargando()).toBe(false);
    expect(service.error()).toBe('Fallo interno de catálogo');
  });

  it('debe obtener los filtros disponibles del servidor', () => {
    service.obtenerFiltrosDisponibles().subscribe((filtros) => {
      expect(filtros.tallas.some((t) => t.nombre === '38')).toBe(true);
    });

    const req = httpMock.expectOne('/api/v1/catalogo/filtros-disponibles');
    expect(req.request.method).toBe('GET');
    req.flush(mockFiltrosDisponibles);

    expect(service.filtrosDisponibles()).toEqual(mockFiltrosDisponibles);
  });

  it('debe alternar favoritos correctamente en las signals', () => {
    service.productos.set([mockProductoItem]);

    // Agregar a favoritos
    service.toggleFavorito(1);
    expect(service.favoritos().has(1)).toBe(true);
    expect(service.productos()[0].en_favoritos).toBe(true);

    // Quitar de favoritos
    service.toggleFavorito(1);
    expect(service.favoritos().has(1)).toBe(false);
    expect(service.productos()[0].en_favoritos).toBe(false);
  });

  it('debe incrementar el contador de la cesta al agregar prenda', () => {
    const cuentaInicial = service.cestaCount();
    service.agregarACesta(mockProductoItem);
    expect(service.cestaCount()).toBe(cuentaInicial + 1);
  });

  it('debe limpiar el historial de búsquedas recientes', () => {
    expect(service.busquedasRecientes().length).toBeGreaterThan(0);
    service.limpiarHistorial();
    expect(service.busquedasRecientes().length).toBe(0);
  });
});
