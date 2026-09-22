import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { By } from '@angular/platform-browser';
import { signal } from '@angular/core';
import { of } from 'rxjs';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { InventarioGlobalAdminComponent } from './inventario-global-admin.component';
import { InventarioGlobalAdminService } from '../servicios/inventario-global-admin.service';
import { SucursalesAdminService } from '../../cu21_sucursales_ciudades/servicios/sucursales-admin.service';
import { AtributosAdminService } from '../../cu23_categorias_tallas_colores/servicios/atributos-admin.service';
import {
  FiltrosInventarioGlobal,
  InventarioGlobalItem,
  MetricasInventarioGlobal,
  RespuestaInventarioGlobal,
} from '../modelos/inventario-global.dto';
import { SucursalAdmin } from '../../cu21_sucursales_ciudades/modelos/sucursal.model';
import { CategoriaAdmin } from '../../cu23_categorias_tallas_colores/modelos/atributos.dto';

describe('InventarioGlobalAdminComponent (CU26)', () => {
  let fixture: ComponentFixture<InventarioGlobalAdminComponent>;
  let component: InventarioGlobalAdminComponent;

  // --- Datos Mock ---
  const mockItem1: InventarioGlobalItem = {
    id_variante: 101,
    id_producto: 1,
    nombre_producto: 'Vestido Gala Seda Obsidian',
    sku: 'VES-GALA-OBS-M',
    categoria: 'Vestidos',
    talla: 'M',
    color: 'Obsidian Black',
    swatches_hex: '#0F172A',
    total_disponible: 12,
    total_reservado: 2,
    total_fisico: 14,
    estado_stock: 'optimo',
    desglose_sucursales: [
      {
        id_sucursal: 1,
        nombre_sucursal: 'Boutique Calacoto Central',
        ciudad: 'La Paz',
        direccion: 'Av. Ballivian 1234',
        telefono: '+591 2 2791122',
        cantidad_disponible: 8,
        cantidad_reservada: 1,
      },
      {
        id_sucursal: 2,
        nombre_sucursal: 'Boutique Equipetrol',
        ciudad: 'Santa Cruz',
        direccion: 'Av. San Martin 567',
        telefono: '+591 3 3456789',
        cantidad_disponible: 4,
        cantidad_reservada: 1,
      },
    ],
  };

  const mockItem2: InventarioGlobalItem = {
    id_variante: 102,
    id_producto: 2,
    nombre_producto: 'Blazer Velvet Camel',
    sku: 'BLA-VEL-CAM-S',
    categoria: 'Blazers',
    talla: 'S',
    color: 'Camel Luxe',
    swatches_hex: '#AD8C63',
    total_disponible: 3,
    total_reservado: 0,
    total_fisico: 3,
    estado_stock: 'alerta_baja',
    desglose_sucursales: [
      {
        id_sucursal: 1,
        nombre_sucursal: 'Boutique Calacoto Central',
        ciudad: 'La Paz',
        direccion: 'Av. Ballivian 1234',
        telefono: '+591 2 2791122',
        cantidad_disponible: 3,
        cantidad_reservada: 0,
      },
    ],
  };

  const mockItemAgotado: InventarioGlobalItem = {
    id_variante: 103,
    id_producto: 3,
    nombre_producto: 'Pantalon Slim Fit',
    sku: 'PAN-SLIM-32',
    categoria: 'Pantalones',
    talla: '32',
    color: 'Negro',
    swatches_hex: '#000000',
    total_disponible: 0,
    total_reservado: 0,
    total_fisico: 0,
    estado_stock: 'agotado',
    desglose_sucursales: [],
  };

  const mockMetricas: MetricasInventarioGlobal = {
    total_unidades_red: 15,
    variantes_monitoreadas: 3,
    alertas_stock_bajo: 1,
    sedes_activas: 2,
  };

  const mockSucursales: Partial<SucursalAdmin>[] = [
    {
      id_sucursal: 1,
      id_ciudad: 1,
      ciudad_nombre: 'La Paz',
      nombre: 'Boutique Calacoto Central',
      direccion: 'Av. Ballivian 1234',
      telefono: '+591 2 2791122',
      activa: true,
    },
    {
      id_sucursal: 2,
      id_ciudad: 2,
      ciudad_nombre: 'Santa Cruz',
      nombre: 'Boutique Equipetrol',
      direccion: 'Av. San Martin 567',
      telefono: '+591 3 3456789',
      activa: true,
    },
  ];

  const mockCategorias: Partial<CategoriaAdmin>[] = [
    { id_categoria: 10, nombre: 'Vestidos' },
    { id_categoria: 20, nombre: 'Blazers' },
  ];

  // Signals reactivos para el servicio
  const itemsSignal = signal<InventarioGlobalItem[]>([mockItem1, mockItem2, mockItemAgotado]);
  const metricasSignal = signal<MetricasInventarioGlobal>(mockMetricas);
  const totalRegistrosSignal = signal<number>(3);
  const totalPaginasSignal = signal<number>(1);
  const cargandoSignal = signal<boolean>(false);
  const errorSignal = signal<string | null>(null);
  const filtrosSignal = signal<FiltrosInventarioGlobal>({
    q: '',
    id_categoria: null,
    id_sucursal: null,
    pagina: 1,
    limite: 10,
    ordenar_por: 'nombre_asc',
    estado_stock: 'todos',
  });
  const itemSeleccionadoSignal = signal<InventarioGlobalItem | null>(null);
  const modalDetalleAbiertoSignal = signal<boolean>(false);

  const mockInventarioService = {
    items: itemsSignal,
    metricas: metricasSignal,
    totalRegistros: totalRegistrosSignal,
    totalPaginas: totalPaginasSignal,
    cargando: cargandoSignal,
    error: errorSignal,
    filtros: filtrosSignal,
    itemSeleccionadoDetalle: itemSeleccionadoSignal,
    modalDetalleAbierto: modalDetalleAbiertoSignal,
    cargarInventario: vi.fn().mockReturnValue(
      of({
        items: [mockItem1, mockItem2, mockItemAgotado],
        metricas: mockMetricas,
        total: 3,
        pagina: 1,
        limite: 10,
        total_paginas: 1,
      } as RespuestaInventarioGlobal)
    ),
    actualizarFiltros: vi.fn(),
    limpiarFiltros: vi.fn(),
    cambiarPagina: vi.fn(),
    abrirDetalle: vi.fn((item: InventarioGlobalItem) => {
      itemSeleccionadoSignal.set(item);
      modalDetalleAbiertoSignal.set(true);
    }),
    cerrarDetalle: vi.fn(() => {
      itemSeleccionadoSignal.set(null);
      modalDetalleAbiertoSignal.set(false);
    }),
  };

  const mockSucursalesService = {
    sucursales: signal(mockSucursales),
    cargarSucursales: vi.fn().mockReturnValue(of(mockSucursales)),
  };

  const mockAtributosService = {
    categorias: signal(mockCategorias),
    cargarCategorias: vi.fn().mockReturnValue(of(mockCategorias)),
  };

  beforeEach(async () => {
    // Reset signals
    itemsSignal.set([mockItem1, mockItem2, mockItemAgotado]);
    metricasSignal.set(mockMetricas);
    totalRegistrosSignal.set(3);
    totalPaginasSignal.set(1);
    cargandoSignal.set(false);
    errorSignal.set(null);
    filtrosSignal.set({
      q: '',
      id_categoria: null,
      id_sucursal: null,
      pagina: 1,
      limite: 10,
      ordenar_por: 'nombre_asc',
      estado_stock: 'todos',
    });
    itemSeleccionadoSignal.set(null);
    modalDetalleAbiertoSignal.set(false);

    vi.clearAllMocks();

    await TestBed.configureTestingModule({
      imports: [InventarioGlobalAdminComponent],
      providers: [
        provideRouter([]),
        { provide: InventarioGlobalAdminService, useValue: mockInventarioService },
        { provide: SucursalesAdminService, useValue: mockSucursalesService },
        { provide: AtributosAdminService, useValue: mockAtributosService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(InventarioGlobalAdminComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  // ==========================================
  // Criterio # AC-9: Arquitectura y Layout
  // ==========================================
  describe('Criterio # AC-9: Layout Institucional y Encabezado', () => {
    it('debe inicializar el componente y cargar datos iniciales', () => {
      expect(component).toBeTruthy();
      expect(mockInventarioService.cargarInventario).toHaveBeenCalledTimes(1);
      expect(mockSucursalesService.cargarSucursales).toHaveBeenCalledTimes(1);
      expect(mockAtributosService.cargarCategorias).toHaveBeenCalledTimes(1);
    });

    it('debe desplegar el titulo oficial exacto "Consultar inventario global" en h1', () => {
      const h1Element = fixture.debugElement.query(By.css('h1'));
      expect(h1Element).toBeTruthy();
      expect(h1Element.nativeElement.textContent.trim()).toBe('Consultar inventario global');
    });

    it('debe desplegar la miga de pan oficial "CONSULTAR INVENTARIO GLOBAL"', () => {
      const breadcrumb = fixture.debugElement.query(
        By.css('header span.font-bold')
      );
      expect(breadcrumb).toBeTruthy();
      expect(breadcrumb.nativeElement.textContent.trim()).toBe('CONSULTAR INVENTARIO GLOBAL');
    });

    it('debe contener el boton de retorno al panel principal con enlace a /admin', () => {
      const btnVolver = fixture.debugElement.query(By.css('#btn-volver-dashboard'));
      expect(btnVolver).toBeTruthy();
      expect(btnVolver.nativeElement.textContent).toContain('Volver al Panel Principal');
      expect(btnVolver.attributes['routerLink']).toBe('/admin');
    });
  });

  // ==========================================
  // Criterio # AC-10: Tarjetas de Metricas
  // ==========================================
  describe('Criterio # AC-10: Tarjetas de Metricas Superiores (KPIs de Red)', () => {
    it('debe renderizar las 4 tarjetas de metricas cuantitativas de red', () => {
      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.textContent).toContain('Unidades en Red');
      expect(compiled.textContent).toContain('Variantes Monitoreadas');
      expect(compiled.textContent).toContain('Alertas de Stock Bajo');
      expect(compiled.textContent).toContain('Sedes Activas');

      // Validar valores numericos proyectados
      expect(compiled.textContent).toContain('15'); // total_unidades_red
      expect(compiled.textContent).toContain('3');  // variantes_monitoreadas
      expect(compiled.textContent).toContain('1');  // alertas_stock_bajo
      expect(compiled.textContent).toContain('2');  // sedes_activas
    });
  });

  // ==========================================
  // Criterio # AC-11: Barra Reactiva de Filtros
  // ==========================================
  describe('Criterio # AC-11: Barra de Filtros Reactiva', () => {
    it('debe emitir busqueda textual con debounce de 300 ms', async () => {
      mockInventarioService.actualizarFiltros.mockClear();
      component.busquedaControl.setValue('Vestido');
      expect(mockInventarioService.actualizarFiltros).not.toHaveBeenCalled();

      await new Promise((resolve) => setTimeout(resolve, 350));
      expect(mockInventarioService.actualizarFiltros).toHaveBeenCalledWith({ q: 'Vestido' });
    });

    it('debe invocar actualizarFiltros al cambiar categoria', () => {
      component.categoriaControl.setValue(10);
      expect(mockInventarioService.actualizarFiltros).toHaveBeenCalledWith({ id_categoria: 10 });
    });

    it('debe invocar actualizarFiltros al cambiar sucursal', () => {
      component.sucursalControl.setValue(1);
      expect(mockInventarioService.actualizarFiltros).toHaveBeenCalledWith({ id_sucursal: 1 });
    });

    it('debe invocar actualizarFiltros al cambiar estado de stock', () => {
      component.estadoControl.setValue('alerta_baja');
      expect(mockInventarioService.actualizarFiltros).toHaveBeenCalledWith({ estado_stock: 'alerta_baja' });
    });

    it('debe invocar actualizarFiltros al cambiar criterio de ordenacion', () => {
      component.ordenControl.setValue('stock_desc');
      expect(mockInventarioService.actualizarFiltros).toHaveBeenCalledWith({ ordenar_por: 'stock_desc' });
    });

    it('debe reiniciar los controles reactivos y llamar a limpiarFiltros al pulsar Limpiar', () => {
      component.busquedaControl.setValue('Gala', { emitEvent: false });
      component.categoriaControl.setValue(10, { emitEvent: false });
      component.sucursalControl.setValue(1, { emitEvent: false });

      const btnLimpiar = fixture.debugElement.query(By.css('#btn-limpiar-filtros'));
      btnLimpiar.nativeElement.click();

      expect(component.busquedaControl.value).toBe('');
      expect(component.categoriaControl.value).toBeNull();
      expect(component.sucursalControl.value).toBeNull();
      expect(component.estadoControl.value).toBe('todos');
      expect(component.ordenControl.value).toBe('nombre_asc');
      expect(mockInventarioService.limpiarFiltros).toHaveBeenCalledTimes(1);
    });
  });

  // ==========================================
  // Criterio # AC-12: Tabla Maestra Consolidada
  // ==========================================
  describe('Criterio # AC-12: Tabla Maestra Consolidada Multi-Sede', () => {
    it('debe renderizar filas con datos de prendas, SKUs, categorias, tallas y swatches', () => {
      const filas = fixture.debugElement.queryAll(By.css('tbody tr'));
      expect(filas.length).toBe(3);

      const fila1Texto = filas[0].nativeElement.textContent;
      expect(fila1Texto).toContain('Vestido Gala Seda Obsidian');
      expect(fila1Texto).toContain('VES-GALA-OBS-M');
      expect(fila1Texto).toContain('Vestidos');
      expect(fila1Texto).toContain('M');
      expect(fila1Texto).toContain('Obsidian Black');

      const fila2Texto = filas[1].nativeElement.textContent;
      expect(fila2Texto).toContain('Blazer Velvet Camel');
      expect(fila2Texto).toContain('BLA-VEL-CAM-S');
      expect(fila2Texto).toContain('Blazers');
      expect(fila2Texto).toContain('S');

      const fila3Texto = filas[2].nativeElement.textContent;
      expect(fila3Texto).toContain('Pantalon Slim Fit');
      expect(fila3Texto).toContain('PAN-SLIM-32');
    });

    it('debe exhibir chips de existencias por sucursal interactivos', () => {
      const chipsFila1 = fixture.debugElement.queryAll(
        By.css('tbody tr:first-child td:nth-child(4) span.rounded-full')
      );
      expect(chipsFila1.length).toBe(2);
      expect(chipsFila1[0].nativeElement.textContent).toContain('Boutique Calacoto Central');
      expect(chipsFila1[0].nativeElement.textContent).toContain(': 8');
      expect(chipsFila1[1].nativeElement.textContent).toContain('Boutique Equipetrol');
      expect(chipsFila1[1].nativeElement.textContent).toContain(': 4');
    });

    it('debe desplegar badges de estado diferenciados (Optimo, Alerta baja, Agotado)', () => {
      const filas = fixture.debugElement.queryAll(By.css('tbody tr'));
      expect(filas[0].nativeElement.textContent).toContain('Optimo');
      expect(filas[1].nativeElement.textContent).toContain('Alerta baja');
      expect(filas[2].nativeElement.textContent).toContain('Agotado');
    });

    it('debe exhibir el stock total y reservado en red en la columna central', () => {
      const filas = fixture.debugElement.queryAll(By.css('tbody tr'));
      expect(filas[0].nativeElement.textContent).toContain('12');
      expect(filas[0].nativeElement.textContent).toContain('(2 res.)');
    });
  });

  // ==========================================
  // Criterio # AC-13: Modal de Detalle Logistico
  // ==========================================
  describe('Criterio # AC-13: Modal de Detalle Logistico Multi-Sucursal', () => {
    it('debe invocar abrirDetalle al hacer clic en el boton Ver Desglose', () => {
      const btnDesglose = fixture.debugElement.query(
        By.css('#btn-ver-desglose-101')
      );
      expect(btnDesglose).toBeTruthy();
      btnDesglose.nativeElement.click();

      expect(mockInventarioService.abrirDetalle).toHaveBeenCalledWith(mockItem1);
    });

    it('debe mostrar la ventana modal cuando modalDetalleAbierto() es true y hay itemSeleccionado', () => {
      itemSeleccionadoSignal.set(mockItem1);
      modalDetalleAbiertoSignal.set(true);
      fixture.detectChanges();

      const modal = fixture.debugElement.query(By.css('.fixed.inset-0'));
      expect(modal).toBeTruthy();
      expect(modal.nativeElement.textContent).toContain('Detalle Logistico & Derivacion');
      expect(modal.nativeElement.textContent).toContain('Vestido Gala Seda Obsidian');
      expect(modal.nativeElement.textContent).toContain('VES-GALA-OBS-M');
      expect(modal.nativeElement.textContent).toContain('Av. Ballivian 1234');
      expect(modal.nativeElement.textContent).toContain('+591 2 2791122');
      expect(modal.nativeElement.textContent).toContain('12 Unidades');
    });

    it('debe invocar cerrarDetalle al presionar el boton de aspa del modal', () => {
      itemSeleccionadoSignal.set(mockItem1);
      modalDetalleAbiertoSignal.set(true);
      fixture.detectChanges();

      const btnCerrar = fixture.debugElement.query(By.css('#btn-cerrar-modal-detalle'));
      expect(btnCerrar).toBeTruthy();
      btnCerrar.nativeElement.click();

      expect(mockInventarioService.cerrarDetalle).toHaveBeenCalledTimes(1);
    });
  });

  // ==========================================
  // Criterio # AC-14: Luxury Banners
  // ==========================================
  describe('Criterio # AC-14: Luxury Banners y Manejo de Errores', () => {
    it('debe desplegar el banner contextual de error si errorSignal contiene un mensaje', () => {
      errorSignal.set('Error 500: Fallo de comunicacion con el servidor.');
      fixture.detectChanges();

      const bannerError = fixture.debugElement.query(By.css('.bg-red-50'));
      expect(bannerError).toBeTruthy();
      expect(bannerError.nativeElement.textContent).toContain('Aviso del Sistema');
      expect(bannerError.nativeElement.textContent).toContain(
        'Error 500: Fallo de comunicacion con el servidor.'
      );
    });

    it('debe invocar reintentar al pulsar el boton del banner de error', () => {
      errorSignal.set('Error temporal de conexion');
      fixture.detectChanges();

      const btnReintentar = fixture.debugElement.query(By.css('.bg-red-50 button'));
      expect(btnReintentar).toBeTruthy();
      btnReintentar.nativeElement.click();

      // reintentar invoca cargarInventario
      expect(mockInventarioService.cargarInventario).toHaveBeenCalled();
    });
  });

  // ==========================================
  // Criterio # AC-15: Estados de Carga, Paginacion y Vacio
  // ==========================================
  describe('Criterio # AC-15: Estados de Carga, Paginacion y Empty State', () => {
    it('debe mostrar skeleton loader en la tabla mientras cargando() es true', () => {
      cargandoSignal.set(true);
      fixture.detectChanges();

      const skeletons = fixture.debugElement.queryAll(By.css('tr.animate-pulse'));
      expect(skeletons.length).toBe(5);
    });

    it('debe desplegar el empty state editorial si items() esta vacio y no esta cargando', () => {
      itemsSignal.set([]);
      cargandoSignal.set(false);
      fixture.detectChanges();

      const emptyState = fixture.debugElement.query(By.css('tbody tr td.text-center'));
      expect(emptyState).toBeTruthy();
      expect(emptyState.nativeElement.textContent).toContain(
        'No se encontraron prendas con los criterios aplicados'
      );
    });

    it('debe delegar el cambio de pagina al servicio al interactuar con el paginador', () => {
      filtrosSignal.set({
        q: '',
        id_categoria: null,
        id_sucursal: null,
        pagina: 1,
        limite: 10,
        ordenar_por: 'nombre_asc',
        estado_stock: 'todos',
      });
      totalPaginasSignal.set(2);
      fixture.detectChanges();

      const btnSiguiente = fixture.debugElement.queryAll(
        By.css('main div.border-t button')
      )[1];
      expect(btnSiguiente).toBeTruthy();
      btnSiguiente.nativeElement.click();

      expect(mockInventarioService.cambiarPagina).toHaveBeenCalledWith(2);
    });
  });
});
