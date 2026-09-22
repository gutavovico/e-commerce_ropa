import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { signal } from '@angular/core';
import { of, throwError } from 'rxjs';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ProductosAdminComponent } from './productos-admin.component';
import { ProductosAdminService } from '../servicios/productos-admin.service';
import { AtributosAdminService } from '../../cu23_categorias_tallas_colores/servicios/atributos-admin.service';
import {
  ProductoDetalleAdmin,
  ProductoResumenAdmin,
  VarianteAdmin,
} from '../modelos/producto.dto';
import {
  CategoriaAdmin,
  ColorAdmin,
  TallaAdmin,
} from '../../cu23_categorias_tallas_colores/modelos/atributos.dto';

describe('ProductosAdminComponent (CU22)', () => {
  let fixture: ComponentFixture<ProductosAdminComponent>;
  let component: ProductosAdminComponent;

  const mockProductos: ProductoResumenAdmin[] = [
    {
      id_producto: 1,
      nombre: 'Vestido Seda Noir',
      descripcion: 'Vestido de fiesta en seda pura italiana',
      precio_base: 280.0,
      id_categoria: 1,
      categoria_nombre: 'Vestidos de Gala',
      id_coleccion: null,
      coleccion_nombre: null,
      imagen_url: null,
      modelo_ar_url: null,
      activo: true,
      total_variantes: 4,
      stock_total: 35,
      creado_en: '2026-09-20T10:00:00Z',
    },
    {
      id_producto: 2,
      nombre: 'Blazer Lana Camel',
      descripcion: 'Sastreria fina estructurada',
      precio_base: 350.0,
      id_categoria: 2,
      categoria_nombre: 'Sastreria Fina',
      id_coleccion: null,
      coleccion_nombre: null,
      imagen_url: null,
      modelo_ar_url: null,
      activo: false,
      total_variantes: 2,
      stock_total: 0,
      creado_en: '2026-09-20T11:00:00Z',
    },
  ];

  const mockCategorias: CategoriaAdmin[] = [
    {
      id_categoria: 1,
      nombre: 'Vestidos de Gala',
      id_categoria_padre: null,
      padre_nombre: null,
      total_productos: 10,
      total_subcategorias: 0,
    },
    {
      id_categoria: 2,
      nombre: 'Sastreria Fina',
      id_categoria_padre: null,
      padre_nombre: null,
      total_productos: 5,
      total_subcategorias: 0,
    },
  ];

  const mockTallas: TallaAdmin[] = [
    { id_talla: 1, codigo: 'S', orden: 1, total_variantes: 10 },
    { id_talla: 2, codigo: 'M', orden: 2, total_variantes: 12 },
    { id_talla: 3, codigo: 'L', orden: 3, total_variantes: 8 },
  ];

  const mockColores: ColorAdmin[] = [
    { id_color: 1, nombre: 'Negro Obsidian', codigo_hex: '#0F172A', total_variantes: 25 },
    { id_color: 2, nombre: 'Camel Atelier', codigo_hex: '#AD8C63', total_variantes: 18 },
  ];

  const mockProductoDetalle: ProductoDetalleAdmin = {
    id_producto: 1,
    nombre: 'Vestido Seda Noir',
    descripcion: 'Vestido de fiesta en seda pura italiana',
    precio_base: 280.0,
    id_categoria: 1,
    categoria_nombre: 'Vestidos de Gala',
    id_coleccion: null,
    coleccion_nombre: null,
    imagen_url: null,
    modelo_ar_url: null,
    activo: true,
    total_variantes: 1,
    stock_total: 15,
    creado_en: '2026-09-20T10:00:00Z',
    variantes: [
      {
        id_variante: 101,
        id_producto: 1,
        id_talla: 1,
        talla_codigo: 'S',
        id_color: 1,
        color_nombre: 'Negro Obsidian',
        color_hex: '#0F172A',
        sku: 'FS-VESTIDO-SEDA-NOIR-S-NEGRO',
        precio_extra: 0.0,
        precio_final: 280.0,
        activo: true,
        stock_disponible: 15,
        creado_en: '2026-09-20T10:30:00Z',
      },
    ],
  };

  let mockProductosService: any;
  let mockAtributosService: any;

  beforeEach(async () => {
    mockProductosService = {
      productos: signal<ProductoResumenAdmin[]>([...mockProductos]),
      productoSeleccionado: signal<ProductoDetalleAdmin | null>(mockProductoDetalle),
      variantes: signal<VarianteAdmin[]>([...mockProductoDetalle.variantes]),
      cargando: signal<boolean>(false),
      guardando: signal<boolean>(false),
      error: signal<string | null>(null),
      mensajeExito: signal<string | null>(null),

      cargarProductos: vi.fn().mockReturnValue(of(mockProductos)),
      cargarProductoPorId: vi.fn().mockReturnValue(of(mockProductoDetalle)),
      crearProducto: vi.fn().mockReturnValue(of(mockProductos[0])),
      actualizarProducto: vi.fn().mockReturnValue(of(mockProductos[0])),
      cambiarEstadoProducto: vi.fn().mockReturnValue(of(mockProductos[0])),
      eliminarProducto: vi.fn().mockReturnValue(of(undefined)),
      generarMatrizVariantes: vi.fn().mockReturnValue(of(mockProductoDetalle.variantes)),
      crearVarianteManual: vi.fn().mockReturnValue(of(mockProductoDetalle.variantes[0])),
      actualizarVariante: vi.fn().mockReturnValue(of(mockProductoDetalle.variantes[0])),
      cambiarEstadoVariante: vi.fn().mockReturnValue(of(mockProductoDetalle.variantes[0])),
      eliminarVariante: vi.fn().mockReturnValue(of(undefined)),
      subirImagen: vi.fn().mockReturnValue(of({ url: '/static/uploads/productos/prod_test.png' })),
      limpiarMensajes: vi.fn(),
    };

    mockAtributosService = {
      categorias: signal<CategoriaAdmin[]>([...mockCategorias]),
      tallas: signal<TallaAdmin[]>([...mockTallas]),
      colores: signal<ColorAdmin[]>([...mockColores]),
      cargarCategorias: vi.fn().mockReturnValue(of(mockCategorias)),
      cargarTallas: vi.fn().mockReturnValue(of(mockTallas)),
      cargarColores: vi.fn().mockReturnValue(of(mockColores)),
    };

    await TestBed.configureTestingModule({
      imports: [ProductosAdminComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        { provide: ProductosAdminService, useValue: mockProductosService },
        { provide: AtributosAdminService, useValue: mockAtributosService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ProductosAdminComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe inicializar el componente y cargar catalogos base (AC-12)', () => {
    expect(component).toBeTruthy();
    expect(mockProductosService.cargarProductos).toHaveBeenCalled();
    expect(mockAtributosService.cargarCategorias).toHaveBeenCalled();
    expect(mockAtributosService.cargarTallas).toHaveBeenCalled();
    expect(mockAtributosService.cargarColores).toHaveBeenCalled();
  });

  it('debe renderizar el boton de retorno hacia /admin y el titulo institucional (AC-12)', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const enlaces = Array.from(compiled.querySelectorAll('a'));
    const botonVolver = enlaces.find((a) =>
      a.textContent?.includes('Volver al Panel Principal')
    );
    expect(botonVolver).toBeTruthy();
    expect(botonVolver?.getAttribute('routerLink')).toBe('/admin');

    const titulo = compiled.querySelector('h1');
    expect(titulo?.textContent).toContain('Gestionar productos');
  });

  it('debe filtrar productos en vivo por texto de busqueda', () => {
    component.filtroBusqueda.set('Seda');
    const filtrados = component.productosFiltrados();
    expect(filtrados.length).toBe(1);
    expect(filtrados[0].nombre).toBe('Vestido Seda Noir');

    component.filtroBusqueda.set('Inexistente');
    expect(component.productosFiltrados().length).toBe(0);
  });

  it('debe abrir y cerrar el modal de creacion de prenda (AC-13)', () => {
    expect(component.modalPrendaAbierto()).toBe(false);

    component.abrirCrearPrenda();
    expect(component.modalPrendaAbierto()).toBe(true);
    expect(component.prendaEnEdicion()).toBeNull();
    expect(component.formPrenda.get('nombre')?.value).toBe('');

    component.cerrarModalPrenda();
    expect(component.modalPrendaAbierto()).toBe(false);
  });

  it('debe abrir modal de edicion con datos prellenados de la prenda (AC-13)', () => {
    const prenda = mockProductos[0];
    component.abrirEditarPrenda(prenda);

    expect(component.modalPrendaAbierto()).toBe(true);
    expect(component.prendaEnEdicion()?.id_producto).toBe(1);
    expect(component.formPrenda.get('nombre')?.value).toBe(prenda.nombre);
    expect(component.formPrenda.get('precio_base')?.value).toBe(prenda.precio_base);
  });

  it('debe registrar una nueva prenda exitosamente y cerrar el modal (AC-13)', () => {
    component.abrirCrearPrenda();
    component.formPrenda.setValue({
      nombre: 'Pantalon Lino Blanco',
      id_categoria: 1,
      precio_base: 180.0,
      descripcion: 'Lino 100% natural',
      imagen_url: '',
      activo: true,
    });

    component.guardarPrenda();
    expect(mockProductosService.crearProducto).toHaveBeenCalledWith({
      nombre: 'Pantalon Lino Blanco',
      id_categoria: 1,
      precio_base: 180.0,
      descripcion: 'Lino 100% natural',
      imagen_url: null,
      activo: true,
    });
    expect(component.modalPrendaAbierto()).toBe(false);
  });

  it('debe mostrar Luxury Banner en caso de conflicto HTTP 409 al registrar prenda (AC-17)', () => {
    mockProductosService.crearProducto.mockReturnValueOnce(
      throwError(() => ({
        status: 409,
        error: { detail: 'Ya existe una prenda comercial con el nombre ingresado.' },
      }))
    );

    component.abrirCrearPrenda();
    component.formPrenda.setValue({
      nombre: 'Vestido Seda Noir',
      id_categoria: 1,
      precio_base: 280.0,
      descripcion: 'Duplicado',
      imagen_url: '',
      activo: true,
    });

    component.guardarPrenda();
    expect(component.notificacionConflicto()).toBe(
      'Ya existe una prenda comercial con el nombre ingresado.'
    );
    expect(component.modalPrendaAbierto()).toBe(true);
    expect(component.formPrenda.get('nombre')?.value).toBe('Vestido Seda Noir');
  });

  it('debe conmutar el estado activo/inactivo de una prenda comercial (AC-14)', () => {
    const prenda = mockProductos[0];
    component.cambiarEstadoPrenda(prenda, false);
    expect(mockProductosService.cambiarEstadoProducto).toHaveBeenCalledWith(prenda.id_producto, false);
  });

  it('debe abrir el generador de matriz de variantes (AC-15)', () => {
    const prenda = mockProductos[0];
    component.abrirModalMatriz(prenda);

    expect(component.modalMatrizAbierto()).toBe(true);
    expect(component.prendaSeleccionada()?.id_producto).toBe(1);
    expect(component.tallasSeleccionadas().length).toBe(0);
    expect(component.coloresSeleccionados().length).toBe(0);
    expect(mockProductosService.cargarProductoPorId).toHaveBeenCalledWith(prenda.id_producto);
  });

  it('debe gestionar seleccion de chips de tallas y colores reactivamente (AC-15)', () => {
    component.toggleTalla(1);
    component.toggleTalla(2);
    expect(component.tallasSeleccionadas()).toEqual([1, 2]);

    component.toggleTalla(1);
    expect(component.tallasSeleccionadas()).toEqual([2]);

    component.toggleColor(1);
    expect(component.coloresSeleccionados()).toEqual([1]);
  });

  it('debe calcular combinaciones cartesianas con SKU generado y precio final reactivo (AC-15)', () => {
    const prenda = mockProductos[0];
    component.abrirModalMatriz(prenda);

    component.tallasSeleccionadas.set([1, 2]); // S, M
    component.coloresSeleccionados.set([1]); // Negro Obsidian
    component.precioExtraDefecto.set(25.0);

    component.generarCombinaciones();

    const combinaciones = component.variantesMatrizGeneradas();
    expect(combinaciones.length).toBe(2);

    expect(combinaciones[0].talla_codigo).toBe('S');
    expect(combinaciones[0].color_nombre).toBe('Negro Obsidian');
    expect(combinaciones[0].precio_extra).toBe(25.0);
    expect(combinaciones[0].precio_final).toBe(305.0); // 280 + 25
    expect(combinaciones[0].sku).toBe('FS-VESTIDO-SEDA-NOIR-S-NEGRO-OBSI');

    expect(combinaciones[1].talla_codigo).toBe('M');
    expect(combinaciones[1].precio_final).toBe(305.0);
  });

  it('debe permitir sobreescribir el precio extra de una fila individual de la matriz (AC-15)', () => {
    const prenda = mockProductos[0];
    component.abrirModalMatriz(prenda);

    component.tallasSeleccionadas.set([1]);
    component.coloresSeleccionados.set([1]);
    component.generarCombinaciones();

    expect(component.variantesMatrizGeneradas()[0].precio_extra).toBe(0);
    expect(component.variantesMatrizGeneradas()[0].precio_final).toBe(280.0);

    component.actualizarPrecioExtraFila(0, '45.50');
    expect(component.variantesMatrizGeneradas()[0].precio_extra).toBe(45.5);
    expect(component.variantesMatrizGeneradas()[0].precio_final).toBe(325.5);
  });

  it('debe persistir en lote la matriz de variantes y refrescar el listado (AC-16)', () => {
    const prenda = mockProductos[0];
    component.abrirModalMatriz(prenda);

    component.tallasSeleccionadas.set([1, 2]);
    component.coloresSeleccionados.set([1]);
    component.generarCombinaciones();

    component.guardarMatrizLote();

    expect(mockProductosService.generarMatrizVariantes).toHaveBeenCalledWith(prenda.id_producto, {
      ids_tallas: [1, 2],
      ids_colores: [1],
      precio_extra_defecto: 0,
    });
    expect(component.modalMatrizAbierto()).toBe(false);
  });

  it('debe mostrar Luxury Banner en modal matriz si el backend responde 409 por colision de tupla o SKU (AC-17)', () => {
    mockProductosService.generarMatrizVariantes.mockReturnValueOnce(
      throwError(() => ({
        status: 409,
        error: { detail: 'Ya existen variantes con la combinacion de talla y color especificada.' },
      }))
    );

    const prenda = mockProductos[0];
    component.abrirModalMatriz(prenda);

    component.tallasSeleccionadas.set([1]);
    component.coloresSeleccionados.set([1]);
    component.generarCombinaciones();

    component.guardarMatrizLote();

    expect(component.notificacionConflicto()).toBe(
      'Ya existen variantes con la combinacion de talla y color especificada.'
    );
    expect(component.modalMatrizAbierto()).toBe(true);
  });

  it('debe gestionar la eliminacion de prenda con modal de confirmacion y advertencia de dependencias (AC-18)', () => {
    const prenda = mockProductos[0];
    component.abrirModalEliminar(prenda);
    expect(component.modalEliminarAbierto()).toBe(true);
    expect(component.prendaAEliminar()?.id_producto).toBe(prenda.id_producto);

    component.confirmarEliminarPrenda();
    expect(mockProductosService.eliminarProducto).toHaveBeenCalledWith(prenda.id_producto);
    expect(component.modalEliminarAbierto()).toBe(false);
  });

  it('debe atrapar error al eliminar prenda con inventario o dependencias y desplegar banner (AC-18)', () => {
    mockProductosService.eliminarProducto.mockReturnValueOnce(
      throwError(() => ({
        status: 409,
        error: { detail: 'No se puede eliminar la prenda porque posee dependencias operativas o inventario.' },
      }))
    );

    const prenda = mockProductos[0];
    component.abrirModalEliminar(prenda);
    component.confirmarEliminarPrenda();

    expect(component.notificacionConflicto()).toBe(
      'No se puede eliminar la prenda porque posee dependencias operativas o inventario.'
    );
    expect(component.modalEliminarAbierto()).toBe(true);
  });

  it('debe renderizar la tabla con miniatura de imagen, texto de variantes bajo categoria y boton de accion Variantes sin columna Matriz de SKUs', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const encabezados = Array.from(compiled.querySelectorAll('th')).map((th) => th.textContent?.trim());

    // La columna Matriz de SKUs no debe existir en el encabezado
    expect(encabezados).not.toContain('Matriz de SKUs');
    expect(encabezados).toEqual([
      'Prenda / Modelo',
      'Categoria',
      'Precio Base',
      'Stock Global',
      'Estado',
      'Acciones',
    ]);

    // La primera fila debe contener el thumbnail y el texto de variantes
    const primeraFila = compiled.querySelector('tbody tr');
    expect(primeraFila).toBeTruthy();

    // Debe existir un contenedor de miniatura cuadrada (con imagen o SVG)
    const miniatura = primeraFila?.querySelector('td div.rounded-xl');
    expect(miniatura).toBeTruthy();

    // Debe mostrar la cantidad de variantes bajo la categoria
    expect(primeraFila?.textContent).toContain('4 variantes');

    // Debe contener el boton "Variantes" en las acciones
    const botonVariantes = Array.from(primeraFila?.querySelectorAll('button') || []).find((b) =>
      b.textContent?.trim().includes('Variantes')
    );
    expect(botonVariantes).toBeTruthy();
  });

  // =========================================================================
  // PRUEBAS DE CARGA DE IMAGENES LOCALES Y DROPZONE
  // =========================================================================

  it('debe procesar y subir una imagen valida actualizando el formulario y la previsualizacion', () => {
    component.abrirCrearPrenda();

    const archivo = new File(['dummy-content'], 'foto_prenda.png', { type: 'image/png' });
    const event = {
      target: {
        files: [archivo],
      },
    } as unknown as Event;

    component.onArchivoSeleccionado(event);

    expect(mockProductosService.subirImagen).toHaveBeenCalledWith(archivo);
    expect(component.formPrenda.controls.imagen_url.value).toBe('/static/uploads/productos/prod_test.png');
    expect(component.previsualizacionImagen()).toBe('/static/uploads/productos/prod_test.png');
    expect(component.subiendoImagen()).toBe(false);
  });

  it('debe rechazar archivos con formato no permitido y mostrar notificacion', () => {
    component.abrirCrearPrenda();

    const archivoInvalido = new File(['documento'], 'doc.pdf', { type: 'application/pdf' });
    component.procesarArchivo(archivoInvalido);

    expect(mockProductosService.subirImagen).not.toHaveBeenCalled();
    expect(component.notificacionConflicto()).toContain('Formato no permitido');
    expect(component.formPrenda.controls.imagen_url.value).toBe('');
  });

  it('debe rechazar archivos cuyo tamano supere 5 MB', () => {
    component.abrirCrearPrenda();

    const archivoPesado = new File(['x'], 'pesado.jpg', { type: 'image/jpeg' });
    Object.defineProperty(archivoPesado, 'size', { value: 6 * 1024 * 1024 });

    component.procesarArchivo(archivoPesado);

    expect(mockProductosService.subirImagen).not.toHaveBeenCalled();
    expect(component.notificacionConflicto()).toContain('5 MB');
    expect(component.formPrenda.controls.imagen_url.value).toBe('');
  });

  it('debe permitir quitar la imagen seleccionada restableciendo el formulario y la miniatura', () => {
    component.abrirCrearPrenda();
    component.formPrenda.controls.imagen_url.setValue('/static/uploads/productos/prod_test.png');
    component.previsualizacionImagen.set('/static/uploads/productos/prod_test.png');

    component.quitarImagen();

    expect(component.formPrenda.controls.imagen_url.value).toBe('');
    expect(component.previsualizacionImagen()).toBeNull();
  });

  it('debe permitir el ingreso manual de URL mediante la opcion dual sobria', () => {
    component.abrirCrearPrenda();
    expect(component.modoUrlManual()).toBe(false);

    component.toggleModoUrlManual();
    expect(component.modoUrlManual()).toBe(true);

    component.onUrlManualChange('https://cdn.fashionstore.com/vestido-lujo.webp');

    expect(component.formPrenda.controls.imagen_url.value).toBe('https://cdn.fashionstore.com/vestido-lujo.webp');
    expect(component.previsualizacionImagen()).toBe('https://cdn.fashionstore.com/vestido-lujo.webp');
  });

  it('debe enviar la imagen_url al guardar una nueva prenda o actualizarla', () => {
    component.abrirCrearPrenda();
    component.formPrenda.controls.nombre.setValue('Vestido Seda Atelier');
    component.formPrenda.controls.id_categoria.setValue(1);
    component.formPrenda.controls.precio_base.setValue(450.0);
    component.formPrenda.controls.imagen_url.setValue('/static/uploads/productos/prod_test.png');

    component.guardarPrenda();

    expect(mockProductosService.crearProducto).toHaveBeenCalledWith(
      expect.objectContaining({
        nombre: 'Vestido Seda Atelier',
        imagen_url: '/static/uploads/productos/prod_test.png',
      })
    );
  });
});

