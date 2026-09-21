import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { of } from 'rxjs';
import { signal } from '@angular/core';

import { ColeccionesComponent } from './colecciones.component';
import { ColeccionesService } from '../../servicios/colecciones.service';
import {
  ColeccionResumen,
  ProductoColeccionItem,
} from '../../modelos/colecciones.modelos';

describe('ColeccionesComponent', () => {
  let component: ColeccionesComponent;
  let fixture: ComponentFixture<ColeccionesComponent>;
  let router: Router;

  const mockPiezasClave: ProductoColeccionItem[] = [
    {
      id_producto: 1,
      nombre: 'Vestido plisado en seda natural',
      descripcion: 'Textura micro-plisada artesanal con caída orgánica al movimiento.',
      categoria: 'Alta Costura',
      id_categoria: 10,
      precio_base: 890,
      imagen_url: 'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=800',
      badge_editorial: 'COLECCIÓN 07',
      subtitulo_atelier: 'SEDA LYON · ALTA COSTURA',
      tono_principal: 'Marfil Puro',
      stock_total_disponible: 5,
      variantes: [],
      colores: [
        { nombre: 'Marfil', hex: '#F5F2EB' },
        { nombre: 'Ébano', hex: '#1F1F1F' },
      ],
    },
    {
      id_producto: 2,
      nombre: 'Blazer estructurado en lana virgen',
      descripcion: 'Solapa de muesca pronunciada y botonadura interior de asta natural.',
      categoria: 'Sastrería',
      id_categoria: 12,
      precio_base: 740,
      imagen_url: 'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=800',
      badge_editorial: 'EN SERRANO',
      subtitulo_atelier: 'BIELLA 380G · SASTRERÍA ATELIER',
      tono_principal: 'Camel Puro',
      stock_total_disponible: 8,
      variantes: [],
      colores: [
        { nombre: 'Camel', hex: '#C19A6B' },
        { nombre: 'Ébano', hex: '#1F1F1F' },
      ],
    },
  ];

  const mockColeccionDestacada: ColeccionResumen = {
    id_coleccion: 1,
    nombre: 'Sastrería en Lana Virgen & Seda Natural',
    descripcion:
      'Cortes fluidos y armaduras arquitectónicas concebidas con tejidos de molinos históricos de Biella y Lyon. Confección de precisión diseñada para una cadencia eterna.',
    temporada_id: 1,
    temporada_nombre: 'Primavera / Verano 2026',
    temporada_tipo: 'primavera_verano',
    proveedor_nombre: 'Loro Piana & Tessitura Taiana',
    taller_origen: 'Atelier Central Serrano',
    es_destacada: true,
    precio_desde: 740,
    total_prendas: 2,
    piezas_clave: mockPiezasClave,
    imagen_portada: 'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=800',
    badge_edicion: 'EDICIÓN VIGENTE',
    estado_disponibilidad: 'DISPONIBLE',
  };

  const mockOtrasColecciones: ColeccionResumen[] = [
    {
      id_coleccion: 2,
      nombre: 'Edición Milano: Punto & Lino',
      descripcion:
        'Hilados ligeros de cachemira y cortes fluidos diseñados para el verano mediterráneo.',
      temporada_id: 2,
      temporada_nombre: 'Primavera · Verano 2024',
      temporada_tipo: 'primavera_verano',
      proveedor_nombre: 'Lanificio Cerruti',
      taller_origen: 'Molinos de Biella & Como',
      es_destacada: false,
      precio_desde: 340,
      total_prendas: 6,
      piezas_clave: [],
      imagen_portada: 'https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=800',
      badge_edicion: 'EDICIÓN SS24 MILANO',
      estado_disponibilidad: 'DISPONIBLE',
    },
    {
      id_coleccion: 3,
      nombre: 'Abrigos en Alpaca & Lana',
      descripcion:
        'Prendas de abrigo envolventes confeccionadas con hilatura artesanal de baby alpaca.',
      temporada_id: 3,
      temporada_nombre: 'Otoño · Invierno 2023',
      temporada_tipo: 'otono_invierno',
      proveedor_nombre: 'Inca Tops Arequipa',
      taller_origen: 'Atelier de Alta Montaña',
      es_destacada: false,
      precio_desde: 680,
      total_prendas: 2,
      piezas_clave: [],
      imagen_portada: 'https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=800',
      badge_edicion: 'EDICIÓN N° 03 INVIERNO',
      estado_disponibilidad: 'ÚLTIMAS UNIDADES',
    },
  ];

  let mockColeccionesService: any;

  beforeEach(async () => {
    mockColeccionesService = {
      cargando: signal<boolean>(false),
      cargandoDetalle: signal<boolean>(false),
      coleccionDestacada: signal<ColeccionResumen | null>(mockColeccionDestacada),
      otrasColecciones: signal<ColeccionResumen[]>(mockOtrasColecciones),
      temporadaActivaNombre: signal<string>('Primavera / Verano 2026'),
      totalColecciones: signal<number>(3),
      coleccionDetalle: signal<any>(null),
      error: signal<string | null>(null),
      cargarColeccionesActivas: vi.fn().mockReturnValue(
        of({
          temporada_activa_id: 1,
          temporada_activa_nombre: 'Primavera / Verano 2026',
          temporada_activa_tipo: 'primavera_verano',
          coleccion_destacada: mockColeccionDestacada,
          otras_colecciones: mockOtrasColecciones,
          total_colecciones: 3,
        })
      ),
      cargarDetalleColeccion: vi.fn().mockReturnValue(of(null)),
    };

    await TestBed.configureTestingModule({
      imports: [ColeccionesComponent],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        { provide: ColeccionesService, useValue: mockColeccionesService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ColeccionesComponent);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    fixture.detectChanges();
  });

  it('debe crear el componente exitosamente', () => {
    expect(component).toBeTruthy();
  });

  it('debe renderizar el encabezado con el botón VOLVER y el logotipo FASHION STORE', () => {
    const el = fixture.nativeElement as HTMLElement;
    const header = el.querySelector('header');
    expect(header).toBeTruthy();
    expect(header?.textContent).toContain('VOLVER');
    expect(header?.textContent).toContain('FASHION STORE');
  });

  it('debe renderizar el título principal "Colecciones" y su descripción editorial', () => {
    const el = fixture.nativeElement as HTMLElement;
    const h1 = el.querySelector('h1');
    expect(h1?.textContent?.trim()).toBe('Colecciones');
    expect(el.textContent).toContain('Explora y visualiza todas las colecciones disponibles de la firma');
  });

  it('debe renderizar la Colección Destacada con sus piezas clave y badges editoriales', () => {
    const el = fixture.nativeElement as HTMLElement;
    const h2 = el.querySelector('h2');
    expect(h2?.textContent).toContain('Sastrería en Lana Virgen & Seda Natural');

    // Verificar presencia de las piezas clave
    expect(el.textContent).toContain('Vestido plisado en seda natural');
    expect(el.textContent).toContain('890 €');
    expect(el.textContent).toContain('COLECCIÓN 07');
    expect(el.textContent).toContain('DISPONIBLE');
    expect(el.textContent).toContain('Blazer estructurado en lana virgen');
    expect(el.textContent).toContain('740 €');
  });

  it('debe renderizar la sección "Otras colecciones" con sus tarjetas y precios de entrada', () => {
    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('Otras colecciones');
    expect(el.textContent).toContain('Edición Milano: Punto & Lino');
    expect(el.textContent).toContain('Desde 340 €');
    expect(el.textContent).toContain('Abrigos en Alpaca & Lana');
    expect(el.textContent).toContain('Desde 680 €');
    expect(el.textContent).toContain('VER COLECCIÓN');
  });

  it('debe navegar al catálogo al hacer click en una pieza clave', () => {
    const navigateSpy = vi.spyOn(router, 'navigate');
    const articulo = fixture.nativeElement.querySelector('article');
    articulo.click();

    expect(navigateSpy).toHaveBeenCalledWith(['/buscar'], {
      queryParams: { q: 'Vestido plisado en seda natural' },
    });
  });

  it('debe navegar al detalle de la colección al hacer click en una card de Otras colecciones', () => {
    const navigateSpy = vi.spyOn(router, 'navigate');
    const articles = fixture.nativeElement.querySelectorAll('article');
    const coleccionCard = articles[2] as HTMLElement;
    coleccionCard.click();

    expect(navigateSpy).toHaveBeenCalledWith(['/colecciones', 2]);
  });

  it('debe mostrar el estado de error y botón de reintento si falla la carga', () => {
    mockColeccionesService.cargando.set(false);
    mockColeccionesService.error.set('Error al sincronizar las colecciones del Atelier.');
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('Error al sincronizar las colecciones del Atelier.');
    expect(el.textContent).toContain('REINTENTAR');
  });
});
