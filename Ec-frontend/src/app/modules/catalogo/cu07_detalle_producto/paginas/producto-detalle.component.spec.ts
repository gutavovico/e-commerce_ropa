import { TestBed } from '@angular/core/testing';
import { provideRouter, ActivatedRoute } from '@angular/router';
import { Location } from '@angular/common';
import { of } from 'rxjs';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { ProductoDetalleComponent } from './producto-detalle.component';
import { ProductoDetalleService } from '../servicios/producto-detalle.service';
import { CatalogoService } from '../../servicios/catalogo.service';
import {
  DisponibilidadSucursales,
  ProductoDetalle,
} from '../modelos/producto-detalle.model';

describe('ProductoDetalleComponent (CU07, CU08, CU09, CU10, CU12)', () => {
  const mockProducto: ProductoDetalle = {
    id_producto: 10,
    nombre: 'Vestido Plisado en Seda Marfil Natural',
    descripcion: 'Vestido de fiesta confeccionado en pura seda.',
    precio_base: '890.00',
    precio_final: '890.00',
    tiene_descuento: false,
    descuento_monto: '0.00',
    porcentaje_descuento: null,
    cuotas_info: 'o 3 pagos de 296,66 € sin intereses',
    subtitulo_atelier: 'ALTA COSTURA · MILÁN / LYON',
    linea_confeccion: 'ALTA COSTURA LYON',
    etiqueta_badge: 'EDICIÓN LIMITADA',
    sku_base: 'ATEL-2025-VD9',
    rating_promedio: 4.9,
    total_resenas: 38,
    beneficio_membresia: 'Beneficio Privé',
    categoria_id: 3,
    categoria_nombre: 'Vestidos',
    coleccion_id: 4,
    coleccion_nombre: 'Seda & Plisados de Lyon',
    imagen_principal: 'https://images.unsplash.com/photo-1566174053879-31528523f8ae',
    galeria: [
      { url: 'https://images.unsplash.com/photo-1566174053879-31528523f8ae', etiqueta: 'FRONTAL', orden: 1 },
      { url: 'https://images.unsplash.com/photo-1566174053879-31528523f8ae?auto=format&fit=crop&w=1000&h=1200&crop=top&q=85', etiqueta: 'DETALLE TEJIDO', orden: 2 },
      { url: 'https://images.unsplash.com/photo-1566174053879-31528523f8ae?auto=format&fit=crop&w=1000&h=1200&crop=center&q=85', etiqueta: 'SILUETA & CAÍDA', orden: 3 },
      { url: 'https://images.unsplash.com/photo-1566174053879-31528523f8ae?auto=format&fit=crop&w=1000&h=1200&crop=bottom&q=85', etiqueta: 'ACABADO & VUELO', orden: 4 },
    ],
    modelo_ar_url: null,
    modelo_info: 'MODELO: 1,77M · TALLA 38 ES',
    composicion: {
      cuerpo_principal: '100% Seda Natural 22 Momme',
      forro_interior: 'Crepé de seda puro',
      tecnica_textil: 'Plisado artesanal',
      descripcion_confeccion: '48 horas de moldeado',
      instrucciones_cuidado: [
        'Limpieza profesional en seco con percloroetileno moderado.',
        'Planchado únicamente vertical mediante vapor suave a distancia mínima de 15 cm.',
        'Conservar en su funda transpirable de algodón incluida.',
      ],
    },
    colores_disponibles: [
      { id_color: 7, nombre: 'Ébano', codigo_hex: '#1A1A1A', disponible: true },
      { id_color: 5, nombre: 'Marfil', codigo_hex: '#FCFBF8', disponible: true },
    ],
    tallas_disponibles: [
      { id_talla: 8, codigo: '38', orden: 11, disponible: true, stock_total: 10 },
      { id_talla: 7, codigo: '36', orden: 10, disponible: true, stock_total: 5 },
      { id_talla: 9, codigo: '40', orden: 12, disponible: false, stock_total: 0 },
    ],
    variantes: [
      {
        id_variante: 100,
        id_producto: 10,
        id_talla: 8,
        talla_codigo: '38',
        talla_orden: 11,
        id_color: 7,
        color_nombre: 'Ébano',
        color_hex: '#1A1A1A',
        sku: 'SKU-FEM-10-38-EBA',
        precio_extra: '0.00',
        precio_final_variante: '890.00',
        stock_total_disponible: 10,
        tiene_stock: true,
      },
      {
        id_variante: 101,
        id_producto: 10,
        id_talla: 7,
        talla_codigo: '36',
        talla_orden: 10,
        id_color: 7,
        color_nombre: 'Ébano',
        color_hex: '#1A1A1A',
        sku: 'SKU-FEM-10-36-EBA',
        precio_extra: '0.00',
        precio_final_variante: '890.00',
        stock_total_disponible: 5,
        tiene_stock: true,
      },
    ],
    piezas_look_complementario: [
      {
        id_producto: 20,
        nombre: 'Bermuda sastre en algodón egipcio',
        subtitulo_atelier: 'ALTA COSTURA ATELIER',
        categoria: 'Pantalones',
        precio_base: '310.00',
        precio_final: '310.00',
        imagen_url: 'https://images.unsplash.com/photo-1509631179647-0177331693ae',
      },
    ],
    total_guardados: 142,
  };

  const mockDisponibilidad: DisponibilidadSucursales = {
    id_producto: 10,
    id_variante: 100,
    sku: 'SKU-FEM-10-38-EBA',
    sucursales: [
      {
        id_sucursal: 1,
        nombre: 'Flagship Madrid Serrano',
        ciudad: 'Madrid',
        direccion: 'Calle Serrano 48',
        telefono: '91 555 1234',
        horario_apertura: '09:00',
        horario_cierre: '20:00',
        cantidad_disponible: 2,
        cantidad_reservada: 0,
        estado_stock: 'disponible',
        badge_stock: '2 UDS EN STOCK',
        citas_disponibles_texto: 'Citas disponibles hoy y mañana',
        permite_reserva_directa: true,
      },
    ],
    total_disponible_global: 2,
  };

  let mockDetalleService: {
    obtenerDetalle: ReturnType<typeof vi.fn>;
    obtenerDisponibilidad: ReturnType<typeof vi.fn>;
  };

  let mockLocation: {
    back: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    mockDetalleService = {
      obtenerDetalle: vi.fn().mockReturnValue(of(mockProducto)),
      obtenerDisponibilidad: vi.fn().mockReturnValue(of(mockDisponibilidad)),
    };

    mockLocation = {
      back: vi.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [ProductoDetalleComponent],
      providers: [
        provideRouter([]),
        { provide: ProductoDetalleService, useValue: mockDetalleService },
        { provide: Location, useValue: mockLocation },
        {
          provide: ActivatedRoute,
          useValue: {
            paramMap: of({ get: () => '10' }),
          },
        },
      ],
    }).compileComponents();
  });

  it('debe crearse y cargar los datos de la prenda y galería de 4 tomas', () => {
    const fixture = TestBed.createComponent(ProductoDetalleComponent);
    fixture.detectChanges();

    const comp = fixture.componentInstance;
    expect(comp).toBeTruthy();
    expect(mockDetalleService.obtenerDetalle).toHaveBeenCalledWith(10);
    expect(comp['producto']()?.nombre).toBe('Vestido Plisado en Seda Marfil Natural');

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('h1')?.textContent).toContain(
      'Vestido Plisado en Seda Marfil Natural'
    );
    expect(compiled.textContent).toContain('FRONTAL');
    expect(compiled.textContent).toContain('DETALLE TEJIDO');
    expect(compiled.textContent).toContain('SILUETA & CAÍDA');
  });

  it('debe filtrar reactivamente las tallas para mostrar únicamente las del color seleccionado', () => {
    const fixture = TestBed.createComponent(ProductoDetalleComponent);
    fixture.detectChanges();

    const comp = fixture.componentInstance;
    // Por defecto se activa Ébano (id 7), con tallas 36 y 38
    const tallas = comp['tallasDisponiblesParaColor']();
    expect(tallas.map((t) => t.codigo)).toEqual(['36', '38']);
    expect(tallas.some((t) => t.codigo === '40')).toBe(false);
  });

  it('debe alternar la fotografía principal al seleccionar una miniatura', () => {
    const fixture = TestBed.createComponent(ProductoDetalleComponent);
    fixture.detectChanges();

    const comp = fixture.componentInstance;
    comp.seleccionarToma('https://images.unsplash.com/photo-1566174053879-31528523f8ae', 1);

    expect(comp['imagenPrincipal']()).toBe(
      'https://images.unsplash.com/photo-1566174053879-31528523f8ae'
    );
    expect(comp['tomaActivaIndice']()).toBe(1);
  });

  it('debe actualizar reactivamente la variante y SKU al seleccionar otra talla', () => {
    const fixture = TestBed.createComponent(ProductoDetalleComponent);
    fixture.detectChanges();

    const comp = fixture.componentInstance;
    comp.seleccionarTalla(7); // Talla 36

    expect(comp['varianteActiva']()?.id_talla).toBe(7);
    expect(comp['varianteActiva']()?.sku).toBe('SKU-FEM-10-36-EBA');
    expect(mockDetalleService.obtenerDisponibilidad).toHaveBeenCalledWith(10, 101);
  });

  it('debe invocar Location.back() al hacer clic en ← VOLVER', () => {
    const fixture = TestBed.createComponent(ProductoDetalleComponent);
    fixture.detectChanges();

    const comp = fixture.componentInstance;
    comp.volver();

    expect(mockLocation.back).toHaveBeenCalled();
  });

  it('debe abrir y cerrar el modal de reserva de cita presencial (CU12)', () => {
    const fixture = TestBed.createComponent(ProductoDetalleComponent);
    fixture.detectChanges();

    const comp = fixture.componentInstance;
    expect(comp['modalReservaAbierto']()).toBe(false);

    comp.abrirModalReserva();
    expect(comp['modalReservaAbierto']()).toBe(true);

    comp.cerrarModalReserva();
    expect(comp['modalReservaAbierto']()).toBe(false);
  });

  it('debe abrir y cerrar el modal informativo del probador AR (CU10)', () => {
    const fixture = TestBed.createComponent(ProductoDetalleComponent);
    fixture.detectChanges();

    const comp = fixture.componentInstance;
    expect(comp['modalARAbierto']()).toBe(false);

    comp.abrirModalAR();
    expect(comp['modalARAbierto']()).toBe(true);

    comp.cerrarModalAR();
    expect(comp['modalARAbierto']()).toBe(false);
  });
});
