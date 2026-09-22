import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { of } from 'rxjs';
import { signal } from '@angular/core';

import { InicioComponent } from './inicio.component';
import { InicioService } from '../servicios/inicio.service';
import { PerfilService } from '../../autenticacion_seguridad/cu04_gestionar_perfil/servicios/perfil.service';
import { ProductoRecomendadoItem } from '../modelos/inicio.modelos';

describe('InicioComponent', () => {
  let component: InicioComponent;
  let fixture: ComponentFixture<InicioComponent>;

  const mockProductos: ProductoRecomendadoItem[] = [
    {
      id_producto: 1,
      nombre: 'Vestido plisado en seda natural',
      descripcion: 'Caída etérea con plisado manual al calor artesanal.',
      categoria: 'Alta Costura',
      id_categoria: 10,
      precio_base: 890,
      imagen_url: 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=800',
      activo: true,
      badge_editorial: 'EDICIÓN LIMITADA • N.º 12/50',
      subtitulo_atelier: 'ALTA COSTURA',
      tono_principal: 'Marfil Puro',
      score_relevancia: 0.96,
      motivo_individual: 'Afinidad con tus piezas de Vestidos',
      stock_total_disponible: 5,
      variantes: [
        {
          id_variante: 101,
          sku: 'SKU-001',
          talla: '38',
          id_talla: 1,
          color: 'Marfil Puro',
          id_color: 1,
          precio_extra: 0,
          disponible: true,
          cantidad_disponible: 5,
        },
      ],
    },
    {
      id_producto: 2,
      nombre: 'Blazer estructurado en lana virgen',
      descripcion: 'Lana virgen italiana certificada.',
      categoria: 'Sastrería',
      id_categoria: 12,
      precio_base: 740,
      imagen_url: 'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=800',
      activo: true,
      badge_editorial: 'SASTRERÍA ATELIER',
      subtitulo_atelier: 'BIELLA 1850',
      tono_principal: 'Camel Puro',
      score_relevancia: 0.92,
      motivo_individual: 'Afinidad con tus piezas de Sastrería',
      stock_total_disponible: 8,
      variantes: [],
    },
  ];

  let mockInicioService: any;
  let mockPerfilService: any;

  beforeEach(async () => {
    mockInicioService = {
      cargando: signal<boolean>(false),
      tieneHistorial: signal<boolean>(true),
      recomendaciones: signal<ProductoRecomendadoItem[]>(mockProductos),
      motivoGeneral: signal<string | null>(
        'Basado en tu última adquisición de sastrería y seda en Flagship Serrano (Madrid).'
      ),
      boutiqueReferencia: signal<string>('Boutique Serrano (Madrid)'),
      mensajeEmptyState: signal<string | null>(null),
      totalRecomendados: signal<number>(2),
      error: signal<string | null>(null),
      favoritos: signal<Set<number>>(new Set()),
      cestaCount: signal<number>(0),
      prendaAgregadaMensaje: signal<string | null>(null),
      obtenerToken: vi.fn().mockReturnValue('mock-token-jwt'),
      cargarRecomendaciones: vi.fn().mockReturnValue(of({
        tiene_historial: true,
        items: mockProductos,
        total_recomendados: 2,
      })),
      toggleFavorito: vi.fn((id: number) => {
        const set = new Set(mockInicioService.favoritos());
        if (set.has(id)) set.delete(id);
        else set.add(id);
        mockInicioService.favoritos.set(set);
      }),
      agregarACesta: vi.fn((p: ProductoRecomendadoItem) => {
        mockInicioService.cestaCount.update((c: number) => c + 1);
        mockInicioService.prendaAgregadaMensaje.set(`"${p.nombre}" ha sido añadida`);
      }),
    };

    mockPerfilService = {
      perfil: signal({
        nombres: 'Ana',
        apellidos: 'Valenzuela',
      }),
      cargarPerfil: vi.fn().mockReturnValue(of({})),
    };

    await TestBed.configureTestingModule({
      imports: [InicioComponent],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        { provide: InicioService, useValue: mockInicioService },
        { provide: PerfilService, useValue: mockPerfilService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(InicioComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe crearse correctamente', () => {
    expect(component).toBeTruthy();
  });

  it('debe inicializarse como vista hija bajo MainLayoutComponent', () => {
    expect(component).toBeTruthy();
  });

  it('debe renderizar el saludo de bienvenida con el nombre del cliente y la boutique habitual', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Bienvenida, Ana Valenzuela');
    expect(compiled.textContent).toContain('Boutique Serrano (Madrid)');
  });

  it('debe renderizar el Banner Hero editorial de colecciones con CTA a /colecciones (CU36)', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const heroTitle = compiled.querySelector('h1');
    expect(heroTitle?.textContent).toContain('Visita nuestra colección más reciente');

    const ctaColeccion = compiled.querySelector('a[href="/colecciones"]');
    expect(ctaColeccion).toBeTruthy();
    expect(ctaColeccion?.textContent).toContain('EXPLORAR COLECCIÓN');
  });

  it('debe renderizar las prendas recomendadas en la grilla cuando tieneHistorial() es true (CU18)', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Recomendado para ti');
    expect(compiled.textContent).toContain(
      'Basado en tu última adquisición de sastrería y seda en Flagship Serrano (Madrid).'
    );

    const productCards = compiled.querySelectorAll('article');
    expect(productCards.length).toBe(2);
    expect(compiled.textContent).toContain('Vestido plisado en seda natural');
    expect(compiled.textContent).toContain('890 €');
    expect(compiled.textContent).toContain('Blazer estructurado en lana virgen');
    expect(compiled.textContent).toContain('740 €');
  });

  it('debe renderizar el contenedor Empty State con el copy normativo si no tiene compras previas (CU18)', () => {
    mockInicioService.cargando.set(false);
    mockInicioService.tieneHistorial.set(false);
    mockInicioService.recomendaciones.set([]);
    mockInicioService.mensajeEmptyState.set(
      'Aún no contamos con suficientes interacciones o compras previas para personalizar tu selección. Explora nuestras colecciones activas para descubrir piezas afines a tu estilo'
    );
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Personalización Atelier');
    expect(compiled.textContent).toContain(
      'Aún no contamos con suficientes interacciones o compras previas para personalizar tu selección. Explora nuestras colecciones activas para descubrir piezas afines a tu estilo'
    );

    const catalogoBtn = compiled.querySelector('a[href="/catalogo"]');
    expect(catalogoBtn).toBeTruthy();
  });

  it('debe permitir añadir productos a la bolsa y alternar favoritos reactivamente', () => {
    expect(component['esFavorito'](1)).toBe(false);

    const favoriteBtn = fixture.nativeElement.querySelector('article button') as HTMLButtonElement;
    favoriteBtn?.click();
    fixture.detectChanges();

    expect(mockInicioService.toggleFavorito).toHaveBeenCalledWith(1);
  });

  it('debe renderizar las 3 garantías exclusivas en la sección Experiencia Atelier', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Experiencia Atelier');
    expect(compiled.textContent).toContain('Patronaje a Medida en Serrano');
    expect(compiled.textContent).toContain('Entrega con Guante Blanco');
    expect(compiled.textContent).toContain('Trazabilidad Integral de Tejidos');
  });
});
