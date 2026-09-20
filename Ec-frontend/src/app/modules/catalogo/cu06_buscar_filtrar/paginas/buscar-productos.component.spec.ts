import { TestBed } from '@angular/core/testing';
import { provideRouter, Router, ActivatedRoute } from '@angular/router';
import { signal } from '@angular/core';
import { of } from 'rxjs';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { BuscarProductosComponent } from './buscar-productos.component';
import { CatalogoService } from '../../servicios/catalogo.service';
import {
  ProductoItem,
  ProductoPaginado,
  FiltrosDisponibles,
} from '../../modelos/catalogo.modelos';

describe('BuscarProductosComponent (CU06)', () => {
  const mockProducto: ProductoItem = {
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
    imagen_url: 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=800&auto=format&fit=crop&q=80',
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

  const mockRespuesta: ProductoPaginado = {
    items: [mockProducto],
    paginacion: {
      total_registros: 1,
      pagina_actual: 1,
      limite: 12,
      total_paginas: 1,
      tiene_siguiente: false,
      tiene_anterior: false,
    },
    filtros_aplicados: {},
  };

  const mockFiltros: FiltrosDisponibles = {
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
      { id: 4, nombre: 'Terracota', extra: '#B85D3B', conteo: 4 },
      { id: 5, nombre: 'Borgoña', extra: '#5E1924', conteo: 2 },
    ],
    precio_min_global: 250,
    precio_max_global: 2400,
  };

  let mockCatalogoService: any;
  let router: Router;

  beforeEach(async () => {
    mockCatalogoService = {
      productos: signal<ProductoItem[]>([mockProducto]),
      paginacion: signal(mockRespuesta.paginacion),
      filtrosDisponibles: signal<FiltrosDisponibles | null>(mockFiltros),
      cargando: signal<boolean>(false),
      error: signal<string | null>(null),
      totalSugerencias: signal<number>(1),
      cestaCount: signal<number>(2),
      busquedasRecientes: signal<string[]>(['Vestidos de seda']),
      buscarProductos: vi.fn().mockReturnValue(of(mockRespuesta)),
      obtenerFiltrosDisponibles: vi.fn().mockReturnValue(of(mockFiltros)),
      toggleFavorito: vi.fn(),
      agregarACesta: vi.fn(),
      limpiarHistorial: vi.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [BuscarProductosComponent],
      providers: [
        provideRouter([]),
        { provide: CatalogoService, useValue: mockCatalogoService },
        {
          provide: ActivatedRoute,
          useValue: {
            queryParams: of({ q: 'vestido' }),
            snapshot: {
              queryParams: { q: 'vestido' },
            },
          },
        },
      ],
    }).compileComponents();

    router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockImplementation(() => Promise.resolve(true));
  });

  it('debe instanciar el componente correctamente', () => {
    const fixture = TestBed.createComponent(BuscarProductosComponent);
    const comp = fixture.componentInstance;
    expect(comp).toBeTruthy();
  });

  it('debe inicializar metadatos y ejecutar consulta con filtros opcionales (solo q recibido)', () => {
    const fixture = TestBed.createComponent(BuscarProductosComponent);
    fixture.detectChanges();

    expect(mockCatalogoService.obtenerFiltrosDisponibles).toHaveBeenCalled();
    expect(mockCatalogoService.buscarProductos).toHaveBeenCalledWith(
      expect.objectContaining({
        q: 'vestido',
        pagina: 1,
      })
    );
    const args = mockCatalogoService.buscarProductos.mock.calls[0][0];
    expect(args.precio_min).toBeUndefined();
    expect(args.precio_max).toBeUndefined();
    expect(args.talla).toBeUndefined();
    expect(args.color).toBeUndefined();
  });

  it('debe proveer una paleta extendida de colores textiles', () => {
    const fixture = TestBed.createComponent(BuscarProductosComponent);
    const comp = fixture.componentInstance;
    fixture.detectChanges();

    const colores = comp['listaColores']();
    expect(colores.length).toBeGreaterThanOrEqual(5);
    expect(colores.some((c) => c.nombre === 'Terracota')).toBe(true);
    expect(colores.some((c) => c.nombre === 'Borgoña')).toBe(true);
  });

  it('debe seleccionar temporada y aplicarla al confirmar la búsqueda', () => {
    const fixture = TestBed.createComponent(BuscarProductosComponent);
    const comp = fixture.componentInstance;

    comp['seleccionarTemporada']('Primavera / Verano 2025');
    expect(comp['temporadaSeleccionada']()).toBe('Primavera / Verano 2025');

    comp['confirmarBusqueda']();
    expect(router.navigate).toHaveBeenCalledWith(
      [],
      expect.objectContaining({
        queryParams: expect.objectContaining({ temporada: 'Primavera / Verano 2025' }),
      })
    );
  });

  it('debe limpiar el input de búsqueda y aplicar los filtros al confirmar búsqueda', () => {
    const fixture = TestBed.createComponent(BuscarProductosComponent);
    const comp = fixture.componentInstance;

    comp['searchControl'].setValue('vestido seda');
    comp['seleccionarTalla']('38');
    comp['seleccionarColor']('Rojo Carmín');

    comp['confirmarBusqueda']();

    // El input debe quedar limpio
    expect(comp['searchControl'].value).toBe('');
    // El término activo debe ser el ingresado
    expect(comp['terminoBusquedaActivo']()).toBe('vestido seda');

    expect(router.navigate).toHaveBeenCalledWith(
      [],
      expect.objectContaining({
        queryParams: expect.objectContaining({
          q: 'vestido seda',
          talla: '38',
          color: 'Rojo Carmín',
        }),
      })
    );
  });

  it('debe permitir quitar el término de búsqueda activo', () => {
    const fixture = TestBed.createComponent(BuscarProductosComponent);
    const comp = fixture.componentInstance;

    comp['terminoBusquedaActivo'].set('vestido');
    comp['quitarTerminoBusqueda']();

    expect(comp['terminoBusquedaActivo']()).toBe('');
    expect(router.navigate).toHaveBeenCalledWith(
      [],
      expect.objectContaining({
        queryParams: expect.not.objectContaining({ q: 'vestido' }),
      })
    );
  });

  it('debe alternar selección de colección opcional', () => {
    const fixture = TestBed.createComponent(BuscarProductosComponent);
    const comp = fixture.componentInstance;

    // Seleccionar nueva
    comp['alternarColeccion']('Alta Costura');
    expect(comp['coleccionSeleccionada']()).toBe('Alta Costura');

    // Deseleccionar
    comp['alternarColeccion']('Alta Costura');
    expect(comp['coleccionSeleccionada']()).toBe('');
  });

  it('debe alternar selección de talla y color', () => {
    const fixture = TestBed.createComponent(BuscarProductosComponent);
    const comp = fixture.componentInstance;

    comp['seleccionarTalla']('40');
    expect(comp['tallaSeleccionada']()).toBe('40');

    comp['seleccionarColor']('Camel');
    expect(comp['colorSeleccionado']()).toBe('Camel');
  });

  it('debe manejar cambios en rango de precios y activar filtro de precio', () => {
    const fixture = TestBed.createComponent(BuscarProductosComponent);
    const comp = fixture.componentInstance;

    const eventMin = { target: { value: '450' } } as unknown as Event;
    comp['onCambioPrecioMin'](eventMin);
    expect(comp['precioMin']()).toBe(450);
    expect(comp['filtroPrecioActivo']()).toBe(true);

    const eventMax = { target: { value: '1500' } } as unknown as Event;
    comp['onCambioPrecioMax'](eventMax);
    expect(comp['precioMax']()).toBe(1500);
  });

  it('debe cambiar el orden de los resultados', () => {
    const fixture = TestBed.createComponent(BuscarProductosComponent);
    const comp = fixture.componentInstance;

    const event = { target: { value: 'precio_asc' } } as unknown as Event;
    comp['cambiarOrden'](event);
    expect(comp['ordenSeleccionado']()).toBe('precio_asc');
  });

  it('debe restablecer los filtros a valores abiertos por defecto', () => {
    const fixture = TestBed.createComponent(BuscarProductosComponent);
    const comp = fixture.componentInstance;

    comp['restablecerFiltros']();

    expect(comp['searchControl'].value).toBe('');
    expect(comp['temporadaSeleccionada']()).toBe('Todas las temporadas');
    expect(comp['coleccionSeleccionada']()).toBe('');
    expect(comp['tallaSeleccionada']()).toBe('');
    expect(comp['colorSeleccionado']()).toBe('');
    expect(comp['precioMin']()).toBe(0);
    expect(comp['precioMax']()).toBe(2500);
    expect(comp['filtroPrecioActivo']()).toBe(false);
    expect(router.navigate).toHaveBeenCalledWith([], { relativeTo: expect.anything(), queryParams: {} });
  });

  it('debe cambiar de página dentro de los rangos válidos', () => {
    const fixture = TestBed.createComponent(BuscarProductosComponent);
    const comp = fixture.componentInstance;

    mockCatalogoService.paginacion.set({
      total_registros: 24,
      pagina_actual: 1,
      limite: 12,
      total_paginas: 2,
      tiene_siguiente: true,
      tiene_anterior: false,
    });

    comp['cambiarPagina'](2);
    expect(router.navigate).toHaveBeenCalledWith(
      [],
      expect.objectContaining({
        queryParams: expect.objectContaining({ pagina: 2 }),
      })
    );
  });

  it('debe alternar la cuadrícula de productos (toggleVista)', () => {
    const fixture = TestBed.createComponent(BuscarProductosComponent);
    const comp = fixture.componentInstance;

    expect(comp['vistaCuadruple']()).toBe(true);
    comp['toggleVista'](false);
    expect(comp['vistaCuadruple']()).toBe(false);
  });

  it('debe interactuar con el servicio al agregar a la cesta y mostrar notificación', () => {
    const fixture = TestBed.createComponent(BuscarProductosComponent);
    const comp = fixture.componentInstance;

    comp['agregarACesta'](mockProducto);

    expect(mockCatalogoService.agregarACesta).toHaveBeenCalledWith(mockProducto);
    expect(comp['mensajeAgregado']()).toContain('Vestido plisado seda');
  });

  it('debe delegar el guardado de favoritos en el servicio', () => {
    const fixture = TestBed.createComponent(BuscarProductosComponent);
    const comp = fixture.componentInstance;

    comp['toggleFavorito'](mockProducto);
    expect(mockCatalogoService.toggleFavorito).toHaveBeenCalledWith(1);
  });

  it('debe aplicar una búsqueda frecuente confirmando y limpiando el searchControl', () => {
    const fixture = TestBed.createComponent(BuscarProductosComponent);
    const comp = fixture.componentInstance;

    comp['aplicarBusquedaFrecuente']('Blazers camel');
    expect(comp['terminoBusquedaActivo']()).toBe('Blazers camel');
    expect(comp['searchControl'].value).toBe('');
    expect(router.navigate).toHaveBeenCalledWith(
      [],
      expect.objectContaining({
        queryParams: expect.objectContaining({ q: 'Blazers camel' }),
      })
    );
  });

  it('debe alternar la visibilidad de la guía de sastrería atelier', () => {
    const fixture = TestBed.createComponent(BuscarProductosComponent);
    const comp = fixture.componentInstance;

    expect(comp['guiaAtelierAbierta']()).toBe(false);
    comp['toggleGuiaAtelier']();
    expect(comp['guiaAtelierAbierta']()).toBe(true);
  });
});
