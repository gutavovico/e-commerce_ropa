import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { AtributosAdminService } from './atributos-admin.service';
import {
  CategoriaAdmin,
  CategoriaCrearPayload,
  ColorAdmin,
  ColorCrearPayload,
  TallaAdmin,
  TallaCrearPayload,
} from '../modelos/atributos.dto';

describe('AtributosAdminService (CU23)', () => {
  let service: AtributosAdminService;
  let httpMock: HttpTestingController;

  const mockCategorias: CategoriaAdmin[] = [
    {
      id_categoria: 1,
      nombre: 'Prendas Superiores',
      id_categoria_padre: null,
      padre_nombre: null,
      total_productos: 12,
      total_subcategorias: 2,
    },
    {
      id_categoria: 2,
      nombre: 'Blusas',
      id_categoria_padre: 1,
      padre_nombre: 'Prendas Superiores',
      total_productos: 8,
      total_subcategorias: 0,
    },
  ];

  const mockTallas: TallaAdmin[] = [
    { id_talla: 1, codigo: 'XS', orden: 1, total_variantes: 10 },
    { id_talla: 2, codigo: 'S', orden: 2, total_variantes: 15 },
    { id_talla: 3, codigo: 'M', orden: 3, total_variantes: 20 },
  ];

  const mockColores: ColorAdmin[] = [
    { id_color: 1, nombre: 'Negro Ebano', codigo_hex: '#0A0A0A', total_variantes: 25 },
    { id_color: 2, nombre: 'Blanco Marfil', codigo_hex: '#FFFFF0', total_variantes: 18 },
  ];

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        AtributosAdminService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });

    service = TestBed.inject(AtributosAdminService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('debe crearse correctamente el servicio', () => {
    expect(service).toBeTruthy();
    expect(service.categorias()).toEqual([]);
    expect(service.tallas()).toEqual([]);
    expect(service.colores()).toEqual([]);
  });

  // --- CATEGORIAS ---

  it('debe cargar las categorias y actualizar la señal reactiva', () => {
    service.cargarCategorias().subscribe((data) => {
      expect(data.length).toBe(2);
      expect(data).toEqual(mockCategorias);
    });

    const req = httpMock.expectOne('/api/v1/admin/categorias');
    expect(req.request.method).toBe('GET');
    req.flush(mockCategorias);

    expect(service.categorias().length).toBe(2);
    expect(service.cargando()).toBe(false);
  });

  it('debe crear una nueva categoria y agregarla al estado', () => {
    const payload: CategoriaCrearPayload = { nombre: 'Vestidos de Gala', id_categoria_padre: null };
    const nuevaCategoria: CategoriaAdmin = {
      id_categoria: 3,
      nombre: 'Vestidos de Gala',
      id_categoria_padre: null,
      padre_nombre: null,
      total_productos: 0,
      total_subcategorias: 0,
    };

    service.crearCategoria(payload).subscribe((cat) => {
      expect(cat.id_categoria).toBe(3);
    });

    const req = httpMock.expectOne('/api/v1/admin/categorias');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush(nuevaCategoria);

    expect(service.categorias()).toContainEqual(nuevaCategoria);
    expect(service.mensajeExito()).toContain('registrada correctamente');
  });

  it('debe eliminar una categoria del estado reactivo', () => {
    service.categorias.set(mockCategorias);

    service.eliminarCategoria(2).subscribe();

    const req = httpMock.expectOne('/api/v1/admin/categorias/2');
    expect(req.request.method).toBe('DELETE');
    req.flush(null, { status: 204, statusText: 'No Content' });

    expect(service.categorias().length).toBe(1);
    expect(service.categorias().find((c) => c.id_categoria === 2)).toBeUndefined();
  });

  // --- TALLAS ---

  it('debe cargar las tallas ordenadas secuencialmente', () => {
    service.cargarTallas().subscribe((data) => {
      expect(data.length).toBe(3);
    });

    const req = httpMock.expectOne('/api/v1/admin/tallas');
    expect(req.request.method).toBe('GET');
    req.flush(mockTallas);

    expect(service.tallas().length).toBe(3);
  });

  it('debe crear una talla y ordenar la lista reactiva por orden', () => {
    service.tallas.set(mockTallas);
    const payload: TallaCrearPayload = { codigo: 'L', orden: 4 };
    const nuevaTalla: TallaAdmin = { id_talla: 4, codigo: 'L', orden: 4, total_variantes: 0 };

    service.crearTalla(payload).subscribe();

    const req = httpMock.expectOne('/api/v1/admin/tallas');
    expect(req.request.method).toBe('POST');
    req.flush(nuevaTalla);

    expect(service.tallas().length).toBe(4);
    expect(service.tallas()[3].codigo).toBe('L');
  });

  // --- COLORES ---

  it('debe cargar los colores y actualizar el estado', () => {
    service.cargarColores().subscribe((data) => {
      expect(data.length).toBe(2);
    });

    const req = httpMock.expectOne('/api/v1/admin/colores');
    expect(req.request.method).toBe('GET');
    req.flush(mockColores);

    expect(service.colores().length).toBe(2);
  });

  it('debe crear un color textil con representacion #HEX', () => {
    const payload: ColorCrearPayload = { nombre: 'Rojo Carmesí', codigo_hex: '#DC2626' };
    const nuevoColor: ColorAdmin = {
      id_color: 3,
      nombre: 'Rojo Carmesí',
      codigo_hex: '#DC2626',
      total_variantes: 0,
    };

    service.crearColor(payload).subscribe();

    const req = httpMock.expectOne('/api/v1/admin/colores');
    expect(req.request.method).toBe('POST');
    req.flush(nuevoColor);

    expect(service.colores().length).toBe(1);
    expect(service.colores()[0].codigo_hex).toBe('#DC2626');
  });

  // --- MANEJO DE ERRORES ---

  it('debe capturar error 409 y configurar el mensaje de error en la señal', () => {
    service.crearCategoria({ nombre: 'Blusas', id_categoria_padre: null }).subscribe({
      error: (err) => {
        expect(err.message).toContain('Ya existe una categoria');
      },
    });

    const req = httpMock.expectOne('/api/v1/admin/categorias');
    req.flush(
      { detail: 'Ya existe una categoria registrada con el nombre "Blusas".', code: 'CATEGORIA_DUPLICADA' },
      { status: 409, statusText: 'Conflict' }
    );

    expect(service.error()).toContain('Ya existe una categoria');
  });
});
