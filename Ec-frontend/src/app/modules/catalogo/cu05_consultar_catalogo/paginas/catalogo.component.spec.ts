import { TestBed } from '@angular/core/testing';
import { provideRouter, Router, ActivatedRoute } from '@angular/router';
import { signal } from '@angular/core';
import { of } from 'rxjs';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { CatalogoComponent } from './catalogo.component';
import { CatalogoService } from '../../servicios/catalogo.service';
import {
  CatalogoRespuesta,
  ProductoCatalogoItem,
} from '../modelos/catalogo.model';

describe('CatalogoComponent (CU05)', () => {
  const mockProducto: ProductoCatalogoItem = {
    id_producto: 1,
    nombre: 'Traje sastre arquitectónico en lana fría',
    descripcion: 'Prenda confeccionada en lana de Biella.',
    precio_base: '890.00',
    precio_final: '890.00',
    tiene_descuento: false,
    porcentaje_descuento: null,
    imagen_url: 'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f',
    categoria_id: 1,
    categoria_nombre: 'Sastrería & Trajes',
    subtitulo_atelier: 'SASTRERÍA ATELIER',
    etiqueta_badge: 'EDICIÓN LIMITADA',
    rating_promedio: 4.9,
    tallas_disponibles: ['36', '38'],
    colores_disponibles: [
      { id_color: 1, nombre: 'Negro Ébano', codigo_hex: '#1A1A1A' },
    ],
    stock_total_disponible: 10,
    tiene_stock: true,
    es_favorito: false,
  };

  const mockRespuesta: CatalogoRespuesta = {
    resumen_categorias: [
      { id_categoria: 1, nombre: 'Sastrería & Trajes', total_prendas: 8 },
      { id_categoria: 2, nombre: 'Vestidos de Gala', total_prendas: 6 },
    ],
    total_articulos: 1,
    pagina_actual: 1,
    limite: 8,
    total_paginas: 1,
    tiene_siguiente: false,
    tiene_anterior: false,
    categoria_seleccionada_id: null,
    items: [mockProducto],
  };

  let mockCatalogoService: {
    consultarCatalogo: ReturnType<typeof vi.fn>;
    cestaCount: ReturnType<typeof signal<number>>;
  };

  let router: Router;

  beforeEach(async () => {
    mockCatalogoService = {
      consultarCatalogo: vi.fn().mockReturnValue(of(mockRespuesta)),
      cestaCount: signal(2),
    };

    await TestBed.configureTestingModule({
      imports: [CatalogoComponent],
      providers: [
        provideRouter([]),
        { provide: CatalogoService, useValue: mockCatalogoService },
        {
          provide: ActivatedRoute,
          useValue: {
            queryParams: of({}),
          },
        },
      ],
    }).compileComponents();

    router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockResolvedValue(true);
  });

  it('debe crearse correctamente e invocar la carga inicial del catálogo', () => {
    const fixture = TestBed.createComponent(CatalogoComponent);
    fixture.detectChanges();

    const comp = fixture.componentInstance;
    expect(comp).toBeTruthy();
    expect(mockCatalogoService.consultarCatalogo).toHaveBeenCalled();
  });

  it('debe renderizar el título editorial "CATÁLOGO DE PRENDAS" y chips de categorías', () => {
    const fixture = TestBed.createComponent(CatalogoComponent);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const h1 = compiled.querySelector('h1');
    expect(h1?.textContent).toContain('CATÁLOGO DE PRENDAS');

    // Verificar chips de categorías
    const textoBotones = Array.from(compiled.querySelectorAll('button')).map(
      (b) => b.textContent?.trim()
    );
    expect(textoBotones.some((t) => t?.includes('TODOS LOS PRODUCTOS'))).toBe(true);
    expect(textoBotones.some((t) => t?.includes('Sastrería & Trajes'))).toBe(true);
  });

  it('debe filtrar las prendas al hacer clic en un chip de categoría', () => {
    const fixture = TestBed.createComponent(CatalogoComponent);
    fixture.detectChanges();

    const comp = fixture.componentInstance;
    comp.seleccionarCategoria(2);
    fixture.detectChanges();

    expect(comp['categoriaSeleccionada']()).toBe(2);
    expect(mockCatalogoService.consultarCatalogo).toHaveBeenCalledWith(
      expect.objectContaining({
        categoria_id: 2,
        pagina: 1,
      })
    );
  });

  it('debe alternar producto en favoritos al hacer click en el botón de wishlist', () => {
    const fixture = TestBed.createComponent(CatalogoComponent);
    fixture.detectChanges();

    const comp = fixture.componentInstance;
    comp.toggleFavorito(mockProducto);
    fixture.detectChanges();

    expect(comp['favoritos']().has(mockProducto.id_producto)).toBe(true);

    // Segundo click elimina de favoritos
    comp.toggleFavorito(mockProducto);
    fixture.detectChanges();
    expect(comp['favoritos']().has(mockProducto.id_producto)).toBe(false);
  });

  it('debe incrementar la cesta al pulsar "AÑADIR A LA CESTA"', () => {
    const fixture = TestBed.createComponent(CatalogoComponent);
    fixture.detectChanges();

    const comp = fixture.componentInstance;
    const countInicial = mockCatalogoService.cestaCount();
    comp.anadirACesta(mockProducto);

    expect(mockCatalogoService.cestaCount()).toBe(countInicial + 1);
  });

  it('debe navegar a "/buscar" al invocar irABusquedaAvanzada()', () => {
    const fixture = TestBed.createComponent(CatalogoComponent);
    fixture.detectChanges();

    const comp = fixture.componentInstance;
    comp.irABusquedaAvanzada();

    expect(router.navigate).toHaveBeenCalledWith(['/buscar']);
  });

  it('debe alternar la densidad de vista de cuadrícula (grid4 vs grid2)', () => {
    const fixture = TestBed.createComponent(CatalogoComponent);
    fixture.detectChanges();

    const comp = fixture.componentInstance;
    expect(comp['vistaColumnas']()).toBe('grid4');

    comp.cambiarVista('grid2');
    expect(comp['vistaColumnas']()).toBe('grid2');
  });

  it('debe renderizar el estado vacío cuando la categoría no tiene artículos', () => {
    mockCatalogoService.consultarCatalogo.mockReturnValue(
      of({
        ...mockRespuesta,
        total_articulos: 0,
        items: [],
      })
    );

    const fixture = TestBed.createComponent(CatalogoComponent);
    const comp = fixture.componentInstance;
    comp.cargarCatalogo();
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('COLECCIÓN NO DISPONIBLE ACTUALMENTE');
  });
});
