import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { signal } from '@angular/core';
import { of, throwError } from 'rxjs';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { CategoriasTallasColoresAdminComponent } from './categorias-tallas-colores-admin.component';
import { AtributosAdminService } from '../servicios/atributos-admin.service';
import {
  CategoriaAdmin,
  ColorAdmin,
  TallaAdmin,
} from '../modelos/atributos.dto';

describe('CategoriasTallasColoresAdminComponent (CU23)', () => {
  let fixture: ComponentFixture<CategoriasTallasColoresAdminComponent>;
  let component: CategoriasTallasColoresAdminComponent;

  const mockCategorias: CategoriaAdmin[] = [
    {
      id_categoria: 1,
      nombre: 'Prendas Superiores',
      id_categoria_padre: null,
      padre_nombre: null,
      total_productos: 14,
      total_subcategorias: 2,
    },
    {
      id_categoria: 2,
      nombre: 'Blusas Atelier',
      id_categoria_padre: 1,
      padre_nombre: 'Prendas Superiores',
      total_productos: 9,
      total_subcategorias: 0,
    },
    {
      id_categoria: 3,
      nombre: 'Vestidos de Noche',
      id_categoria_padre: null,
      padre_nombre: null,
      total_productos: 5,
      total_subcategorias: 0,
    },
  ];

  const mockTallas: TallaAdmin[] = [
    { id_talla: 1, codigo: 'XS', orden: 1, total_variantes: 8 },
    { id_talla: 2, codigo: 'S', orden: 2, total_variantes: 12 },
    { id_talla: 3, codigo: 'M', orden: 3, total_variantes: 15 },
  ];

  const mockColores: ColorAdmin[] = [
    { id_color: 1, nombre: 'Negro Absoluto', codigo_hex: '#0A0A0A', total_variantes: 20 },
    { id_color: 2, nombre: 'Blanco Marfil', codigo_hex: '#FFFFF0', total_variantes: 16 },
  ];

  let mockService: any;

  beforeEach(async () => {
    mockService = {
      categorias: signal<CategoriaAdmin[]>([...mockCategorias]),
      tallas: signal<TallaAdmin[]>([...mockTallas]),
      colores: signal<ColorAdmin[]>([...mockColores]),
      cargando: signal<boolean>(false),
      guardando: signal<boolean>(false),
      error: signal<string | null>(null),
      mensajeExito: signal<string | null>(null),

      cargarCategorias: vi.fn().mockReturnValue(of(mockCategorias)),
      cargarTallas: vi.fn().mockReturnValue(of(mockTallas)),
      cargarColores: vi.fn().mockReturnValue(of(mockColores)),

      crearCategoria: vi.fn().mockReturnValue(of(mockCategorias[0])),
      actualizarCategoria: vi.fn().mockReturnValue(of(mockCategorias[0])),
      eliminarCategoria: vi.fn().mockReturnValue(of(undefined)),

      crearTalla: vi.fn().mockReturnValue(of(mockTallas[0])),
      actualizarTalla: vi.fn().mockReturnValue(of(mockTallas[0])),
      eliminarTalla: vi.fn().mockReturnValue(of(undefined)),

      crearColor: vi.fn().mockReturnValue(of(mockColores[0])),
      actualizarColor: vi.fn().mockReturnValue(of(mockColores[0])),
      eliminarColor: vi.fn().mockReturnValue(of(undefined)),

      limpiarMensajes: vi.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [CategoriasTallasColoresAdminComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        { provide: AtributosAdminService, useValue: mockService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(CategoriasTallasColoresAdminComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe crearse e inicializarse correctamente el componente (AC-13)', () => {
    expect(component).toBeTruthy();
    expect(component.pestanaActiva()).toBe('categorias');
    expect(mockService.cargarCategorias).toHaveBeenCalled();
    expect(mockService.cargarTallas).toHaveBeenCalled();
    expect(mockService.cargarColores).toHaveBeenCalled();
  });

  it('debe alternar de forma reactiva entre las 3 pestañas editoriales (AC-15)', () => {
    component.cambiarPestana('tallas');
    expect(component.pestanaActiva()).toBe('tallas');
    expect(component.filtroBusqueda()).toBe('');

    component.cambiarPestana('colores');
    expect(component.pestanaActiva()).toBe('colores');

    component.cambiarPestana('categorias');
    expect(component.pestanaActiva()).toBe('categorias');
  });

  it('debe filtrar colecciones reactivamente segun terminoBusqueda (AC-15)', () => {
    // Filtrar categorias
    component.filtroBusqueda.set('Blusas');
    expect(component.categoriasFiltradas().length).toBe(1);
    expect(component.categoriasFiltradas()[0].nombre).toBe('Blusas Atelier');

    // Cambiar a tallas y filtrar
    component.cambiarPestana('tallas');
    component.filtroBusqueda.set('xs');
    expect(component.tallasFiltradas().length).toBe(1);
    expect(component.tallasFiltradas()[0].codigo).toBe('XS');

    // Cambiar a colores y filtrar
    component.cambiarPestana('colores');
    component.filtroBusqueda.set('Marfil');
    expect(component.coloresFiltrados().length).toBe(1);
    expect(component.coloresFiltrados()[0].nombre).toBe('Blanco Marfil');
  });

  it('debe abrir y cerrar modal de categorias con formulario reactivo (AC-16)', () => {
    component.abrirModalCategoria();
    expect(component.modalCategoriaAbierto()).toBe(true);
    expect(component.categoriaEnEdicion()).toBeNull();
    expect(component.categoriaForm.controls.nombre.value).toBe('');

    component.cerrarModalCategoria();
    expect(component.modalCategoriaAbierto()).toBe(false);
  });

  it('debe excluir la propia categoria en modo edicion para evitar ciclos jerarquicos (AC-4, AC-16)', () => {
    const cat = mockCategorias[0]; // Prendas Superiores (id: 1)
    component.abrirModalCategoria(cat);

    expect(component.categoriaEnEdicion()).toBe(cat);
    // Categorias disponibles para padre no deben incluir a id: 1
    const padresDisponibles = component.categoriasPadreDisponibles();
    const contienePropia = padresDisponibles.some((c) => c.id_categoria === cat.id_categoria);
    expect(contienePropia).toBe(false);
  });

  it('debe abrir modal de tallas y normalizar codigo a mayusculas (AC-6, AC-16)', () => {
    component.abrirModalTalla();
    expect(component.modalTallaAbierto()).toBe(true);

    const event = { target: { value: 'xxl' } } as unknown as Event;
    component.onCodigoTallaInput(event);
    expect(component.tallaForm.controls.codigo.value).toBe('XXL');
  });

  it('debe sincronizar bidireccionalmente el selector de color nativo y el campo #HEX (AC-9, AC-16)', () => {
    component.abrirModalColor();
    expect(component.modalColorAbierto()).toBe(true);

    // 1. Entrada desde el picker nativo
    const eventPicker = { target: { value: '#ff5733' } } as unknown as Event;
    component.actualizarHexDesdePicker(eventPicker);
    expect(component.colorForm.controls.codigo_hex.value).toBe('#FF5733');

    // 2. Entrada manual por texto
    const eventText = { target: { value: '00ff00' } } as unknown as Event;
    component.onHexTextInput(eventText);
    expect(component.colorForm.controls.codigo_hex.value).toBe('#00FF00');
  });

  it('debe capturar error 409 y mostrar Luxury Banner preservando el formulario intacto (AC-17)', () => {
    mockService.crearCategoria.mockReturnValue(
      throwError(() => new Error('Ya existe una categoria registrada con el nombre "Blusas".'))
    );

    component.abrirModalCategoria();
    component.categoriaForm.controls.nombre.setValue('Blusas');
    component.guardarCategoria();

    // El modal permanece abierto y los datos no se pierden
    expect(component.modalCategoriaAbierto()).toBe(true);
    expect(component.categoriaForm.controls.nombre.value).toBe('Blusas');
    expect(component.notificacionConflicto()).toContain('Ya existe una categoria');
  });

  it('debe abrir y confirmar modal de eliminacion invocando el servicio (AC-5, AC-8, AC-11)', () => {
    component.abrirConfirmarEliminar('categorias', 2, 'Blusas');
    expect(component.modalEliminarAbierto()).toBe(true);
    expect(component.elementoAEliminar()?.id).toBe(2);

    component.confirmarEliminacion();
    expect(mockService.eliminarCategoria).toHaveBeenCalledWith(2);
    expect(component.modalEliminarAbierto()).toBe(false);
  });

  it('debe cerrar la alerta de conflicto al invocar cerrarAlertaConflicto() (AC-17)', () => {
    component.notificacionConflicto.set('Error de conflicto simulado');
    component.cerrarAlertaConflicto();

    expect(component.notificacionConflicto()).toBeNull();
    expect(mockService.limpiarMensajes).toHaveBeenCalled();
  });

  it('debe incluir el enlace de retorno al Panel Principal (/admin)', () => {
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Volver al Panel Principal');
  });
});
