import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, Router, ActivatedRoute } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { of } from 'rxjs';
import { signal } from '@angular/core';

import { ColeccionDetalleComponent } from './coleccion-detalle.component';
import { ColeccionesService } from '../../servicios/colecciones.service';
import {
  ColeccionDetalle,
  ProductoColeccionItem,
} from '../../modelos/colecciones.modelos';

describe('ColeccionDetalleComponent', () => {
  let component: ColeccionDetalleComponent;
  let fixture: ComponentFixture<ColeccionDetalleComponent>;
  let router: Router;

  const mockPrendas: ProductoColeccionItem[] = [
    {
      id_producto: 101,
      nombre: 'Vestido plisado en seda natural',
      categoria: 'Alta Costura',
      id_categoria: 10,
      precio_base: 890,
      subtitulo_atelier: 'SEDA LYON',
      imagen_url: 'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=800',
      stock_total_disponible: 5,
      variantes: [],
      colores: [{ nombre: 'Marfil', hex: '#F5F2EB' }],
    },
    {
      id_producto: 102,
      nombre: 'Blazer estructurado en lana virgen',
      categoria: 'Sastrería',
      id_categoria: 12,
      precio_base: 740,
      subtitulo_atelier: 'BIELLA 380G',
      imagen_url: 'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=800',
      stock_total_disponible: 8,
      variantes: [],
      colores: [{ nombre: 'Camel', hex: '#C19A6B' }],
    },
  ];

  const mockDetalleConPrendas: ColeccionDetalle = {
    id_coleccion: 1,
    nombre: 'Sastrería en Lana Virgen & Seda Natural',
    descripcion:
      'Piezas confeccionadas con hilaturas nobles de Biella y seda pura de Lyon. Siluetas de precisión diseñadas para una cadencia eterna.',
    temporada_id: 1,
    temporada_nombre: 'Primavera / Verano 2026',
    taller_origen: 'Atelier Central Serrano',
    total_prendas: 2,
    productos: mockPrendas,
  };

  const mockDetalleVacio: ColeccionDetalle = {
    id_coleccion: 99,
    nombre: 'Cápsula Haute Couture Futura',
    descripcion: 'Colección en fase de hilatura fina.',
    temporada_id: 1,
    temporada_nombre: 'Otoño / Invierno 2026',
    total_prendas: 0,
    productos: [],
    mensaje_empty_state: 'Próximo lanzamiento',
  };

  let mockColeccionesService: any;

  beforeEach(async () => {
    mockColeccionesService = {
      cargandoDetalle: signal<boolean>(false),
      coleccionDetalle: signal<ColeccionDetalle | null>(mockDetalleConPrendas),
      error: signal<string | null>(null),
      cargarDetalleColeccion: vi.fn().mockReturnValue(of(mockDetalleConPrendas)),
    };

    await TestBed.configureTestingModule({
      imports: [ColeccionDetalleComponent],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        { provide: ColeccionesService, useValue: mockColeccionesService },
        {
          provide: ActivatedRoute,
          useValue: {
            paramMap: of(new Map([['id', '1']])),
            snapshot: {
              paramMap: {
                get: (key: string) => (key === 'id' ? '1' : null),
              },
            },
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ColeccionDetalleComponent);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    fixture.detectChanges();
  });

  it('debe crear el componente exitosamente', () => {
    expect(component).toBeTruthy();
  });

  it('debe mostrar la cabecera con el botón VOLVER A COLECCIONES y el nombre de la colección', () => {
    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('VOLVER A COLECCIONES');
    expect(el.textContent).toContain('Sastrería en Lana Virgen & Seda Natural');
    expect(el.textContent).toContain('Atelier Central Serrano');
  });

  it('debe renderizar el listado de prendas con sus precios y botones VER', () => {
    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('Vestido plisado en seda natural');
    expect(el.textContent).toContain('890 €');
    expect(el.textContent).toContain('Blazer estructurado en lana virgen');
    expect(el.textContent).toContain('740 €');
    expect(el.textContent).toContain('VER');
  });

  it('debe mostrar el Empty State normativo "Próximo lanzamiento" cuando la colección no tiene prendas', () => {
    mockColeccionesService.coleccionDetalle.set(mockDetalleVacio);
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('Próximo lanzamiento');
    expect(el.textContent).toContain('se encuentran en confección en nuestro taller');
    expect(el.textContent).toContain('VOLVER AL ARCHIVO DE COLECCIONES');
  });

  it('debe mostrar el mensaje de error cuando la colección no existe', () => {
    mockColeccionesService.coleccionDetalle.set(null);
    mockColeccionesService.error.set('La colección solicitada no existe o no se encuentra disponible.');
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('Colección no disponible');
    expect(el.textContent).toContain('La colección solicitada no existe o no se encuentra disponible.');
  });
});
