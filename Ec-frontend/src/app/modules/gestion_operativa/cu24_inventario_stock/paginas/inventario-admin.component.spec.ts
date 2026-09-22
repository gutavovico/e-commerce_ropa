import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, RouterLink } from '@angular/router';
import { By } from '@angular/platform-browser';
import { signal } from '@angular/core';
import { of, throwError } from 'rxjs';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { InventarioAdminComponent } from './inventario-admin.component';
import { InventarioAdminService } from '../servicios/inventario-admin.service';
import { SucursalesAdminService } from '../../cu21_sucursales_ciudades/servicios/sucursales-admin.service';
import { AtributosAdminService } from '../../cu23_categorias_tallas_colores/servicios/atributos-admin.service';
import { ProductosAdminService } from '../../cu22_prendas_productos/servicios/productos-admin.service';
import { LoginService } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import { UsuarioSesion } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/modelos/login.dto';
import {
  HistorialKardexOut,
  InventarioItemAdmin,
  ListaPaginadaInventario,
} from '../modelos/inventario.dto';
import { SucursalAdmin } from '../../cu21_sucursales_ciudades/modelos/sucursal.model';
import { CategoriaAdmin } from '../../cu23_categorias_tallas_colores/modelos/atributos.dto';
import {
  ProductoDetalleAdmin,
  ProductoResumenAdmin,
  VarianteAdmin,
} from '../../cu22_prendas_productos/modelos/producto.dto';

describe('InventarioAdminComponent (CU24)', () => {
  let fixture: ComponentFixture<InventarioAdminComponent>;
  let component: InventarioAdminComponent;

  const mockAdminUser: UsuarioSesion = {
    id_usuario: 1,
    email: 'admin.corporativo@fashionstore.com',
    nombres: 'Gustavo',
    apellidos: 'Vico',
    rol: 'administrador',
    token: 'jwt-token-admin',
  };

  const mockEncargadoUser: UsuarioSesion = {
    id_usuario: 5,
    email: 'encargado.calacoto@fashionstore.com',
    nombres: 'Roberto',
    apellidos: 'Gomez',
    rol: 'encargado_sucursal',
    id_sucursal: 10,
    token: 'jwt-token-encargado',
  };

  const usuarioActualSignal = signal<UsuarioSesion | null>(mockAdminUser);

  const mockItem1: InventarioItemAdmin = {
    id_inventario: 101,
    id_sucursal: 10,
    id_variante: 201,
    cantidad_disponible: 18,
    cantidad_reservada: 2,
    stock_total: 20,
    stock_minimo: 5,
    stock_alerta: 8,
    estado: 'disponible',
    estado_calculado: 'optimo',
    actualizado_en: '2026-09-21T12:00:00Z',
    sucursal: {
      id_sucursal: 10,
      nombre: 'Boutique Calacoto Central',
      ciudad: 'La Paz',
    },
    variante: {
      id_variante: 201,
      id_producto: 50,
      nombre_prenda: 'Vestido Gala Seda Obsidian',
      sku: 'VES-OBS-M',
      talla: 'M',
      color_nombre: 'Obsidian Black',
      color_hex: '#0F172A',
      precio_base: 450,
      precio_final: 450,
      imagen_url: 'https://cdn.fashionstore.com/vestido-gala.jpg',
      categoria_nombre: 'Vestidos de Alta Noche',
    },
  };

  const mockItemAgotado: InventarioItemAdmin = {
    id_inventario: 102,
    id_sucursal: 20,
    id_variante: 202,
    cantidad_disponible: 0,
    cantidad_reservada: 0,
    stock_total: 0,
    stock_minimo: 3,
    stock_alerta: 5,
    estado: 'agotada',
    estado_calculado: 'agotado',
    actualizado_en: '2026-09-21T13:00:00Z',
    sucursal: {
      id_sucursal: 20,
      nombre: 'Boutique Equipetrol',
      ciudad: 'Santa Cruz',
    },
    variante: {
      id_variante: 202,
      id_producto: 51,
      nombre_prenda: 'Blazer Velvet Camel',
      sku: 'BLA-CAM-S',
      talla: 'S',
      color_nombre: 'Camel Luxe',
      color_hex: '#AD8C63',
      precio_base: 380,
      precio_final: 380,
      imagen_url: null,
      categoria_nombre: 'Blazers y Abrigos',
    },
  };

  const inventarioSignal = signal<InventarioItemAdmin[]>([mockItem1, mockItemAgotado]);
  const totalRegistrosSignal = signal<number>(2);
  const paginaActualSignal = signal<number>(1);
  const totalPaginasSignal = signal<number>(1);
  const cargandoSignal = signal<boolean>(false);
  const guardandoSignal = signal<boolean>(false);
  const kardexActualSignal = signal<HistorialKardexOut | null>(null);
  const errorSignal = signal<string | null>(null);
  const mensajeExitoSignal = signal<string | null>(null);

  const mockInventarioService = {
    inventario: inventarioSignal,
    totalRegistros: totalRegistrosSignal,
    paginaActual: paginaActualSignal,
    totalPaginas: totalPaginasSignal,
    cargando: cargandoSignal,
    guardando: guardandoSignal,
    kardexActual: kardexActualSignal,
    error: errorSignal,
    mensajeExito: mensajeExitoSignal,
    cargarInventario: vi.fn().mockReturnValue(
      of({
        items: [mockItem1, mockItemAgotado],
        total: 2,
        pagina: 1,
        limite: 10,
        total_paginas: 1,
      } as ListaPaginadaInventario)
    ),
    crearStockInicial: vi.fn().mockReturnValue(of(mockItem1)),
    ajustarStock: vi.fn().mockReturnValue(of(mockItem1)),
    transferirMercaderia: vi.fn().mockReturnValue(of({
      mensaje: 'Traspaso completado',
      id_sucursal_origen: 10,
      id_sucursal_destino: 20,
      id_variante: 201,
      sku: 'VES-OBS-M',
      cantidad_transferida: 3,
      saldo_origen_nuevo: 15,
      saldo_destino_nuevo: 3,
      fecha: '2026-09-21T14:00:00Z',
    })),
    cargarKardex: vi.fn().mockReturnValue(of({
      id_inventario: 101,
      prenda_sku: 'VES-OBS-M',
      sucursal_nombre: 'Boutique Calacoto Central',
      saldo_actual: 18,
      movimientos: [
        {
          id_movimiento: 1,
          id_inventario: 101,
          tipo_movimiento: 'ingreso_proveedor',
          cantidad: 20,
          saldo_anterior: 0,
          saldo_nuevo: 20,
          motivo: 'Recepcion inicial lote #LOT-2026',
          referencia_documento: 'GR-1001',
          id_usuario: 1,
          usuario_nombre: 'Gustavo Vico',
          creado_en: '2026-09-21T10:00:00Z',
        },
      ],
    } as HistorialKardexOut)),
    limpiarMensajes: vi.fn(),
  };

  const mockSucursales: SucursalAdmin[] = [
    {
      id_sucursal: 10,
      nombre: 'Boutique Calacoto Central',
      id_ciudad: 1,
      ciudad_nombre: 'La Paz',
      direccion: 'Av. Ballivian #1234',
      telefono: '+591 2 2770000',
      activa: true,
      horario_apertura: '09:00',
      horario_cierre: '20:00',
      total_empleados: 4,
      total_prendas_stock: 120,
      reservas_activas_conteo: 2,
      creado_en: '2026-09-20T10:00:00Z',
    },
    {
      id_sucursal: 20,
      nombre: 'Boutique Equipetrol',
      id_ciudad: 2,
      ciudad_nombre: 'Santa Cruz',
      direccion: 'Av. San Martin #500',
      telefono: '+591 3 3440000',
      activa: true,
      horario_apertura: '09:30',
      horario_cierre: '21:00',
      total_empleados: 5,
      total_prendas_stock: 180,
      reservas_activas_conteo: 4,
      creado_en: '2026-09-20T10:00:00Z',
    },
  ];

  const mockCategorias: CategoriaAdmin[] = [
    {
      id_categoria: 1,
      nombre: 'Vestidos de Alta Noche',
      id_categoria_padre: null,
      padre_nombre: null,
      total_productos: 12,
      total_subcategorias: 0,
    },
  ];

  const mockProductos: ProductoResumenAdmin[] = [
    {
      id_producto: 50,
      nombre: 'Vestido Gala Seda Obsidian',
      descripcion: 'Vestido exclusivo',
      precio_base: 450,
      id_categoria: 1,
      categoria_nombre: 'Vestidos de Alta Noche',
      id_coleccion: null,
      coleccion_nombre: null,
      imagen_url: null,
      modelo_ar_url: null,
      total_variantes: 1,
      stock_total: 20,
      activo: true,
      creado_en: '2026-09-20T12:00:00Z',
    },
  ];

  const mockVariantes: VarianteAdmin[] = [
    {
      id_variante: 201,
      id_producto: 50,
      sku: 'VES-OBS-M',
      id_talla: 2,
      talla_codigo: 'M',
      id_color: 1,
      color_nombre: 'Obsidian Black',
      color_hex: '#0F172A',
      precio_extra: 0,
      precio_final: 450,
      activo: true,
      stock_disponible: 18,
      creado_en: '2026-09-20T12:00:00Z',
    },
  ];

  const mockSucursalesService = {
    sucursales: signal<SucursalAdmin[]>(mockSucursales),
    cargarSucursales: vi.fn().mockReturnValue(of(mockSucursales)),
  };

  const mockAtributosService = {
    categorias: signal<CategoriaAdmin[]>(mockCategorias),
    cargarCategorias: vi.fn().mockReturnValue(of(mockCategorias)),
  };

  const mockProductosService = {
    productos: signal<ProductoResumenAdmin[]>(mockProductos),
    variantes: signal<VarianteAdmin[]>(mockVariantes),
    cargarProductos: vi.fn().mockReturnValue(of(mockProductos)),
    cargarProductoPorId: vi.fn().mockReturnValue(of({
      ...mockProductos[0],
      variantes: mockVariantes,
    } as ProductoDetalleAdmin)),
  };

  const mockLoginService = {
    usuarioActual: usuarioActualSignal,
  };

  beforeEach(async () => {
    usuarioActualSignal.set(mockAdminUser);
    inventarioSignal.set([mockItem1, mockItemAgotado]);
    kardexActualSignal.set(null);
    errorSignal.set(null);
    mensajeExitoSignal.set(null);
    vi.clearAllMocks();

    await TestBed.configureTestingModule({
      imports: [InventarioAdminComponent],
      providers: [
        provideRouter([]),
        { provide: InventarioAdminService, useValue: mockInventarioService },
        { provide: SucursalesAdminService, useValue: mockSucursalesService },
        { provide: AtributosAdminService, useValue: mockAtributosService },
        { provide: ProductosAdminService, useValue: mockProductosService },
        { provide: LoginService, useValue: mockLoginService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(InventarioAdminComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe instanciar el componente e inicializar datos del inventario (AC-17)', () => {
    expect(component).toBeTruthy();
    expect(mockInventarioService.cargarInventario).toHaveBeenCalled();
    expect(mockSucursalesService.cargarSucursales).toHaveBeenCalled();
    expect(mockAtributosService.cargarCategorias).toHaveBeenCalled();
    expect(mockProductosService.cargarProductos).toHaveBeenCalled();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Inventario y Existencias por Sucursal');
    expect(compiled.textContent).toContain('Vestido Gala Seda Obsidian');
    expect(compiled.textContent).toContain('Blazer Velvet Camel');
  });

  it('debe contener el enlace institucional de retorno hacia /admin (AC-18)', () => {
    const linkRetorno = fixture.debugElement.query(By.directive(RouterLink));
    expect(linkRetorno).toBeTruthy();
    const routerLinkInstance = linkRetorno.injector.get(RouterLink);
    expect(routerLinkInstance.href).toBe('/admin');
  });

  it('debe proveer un selector de sede libre con opcion "Todas las Sedes" para rol administrador (AC-19)', () => {
    expect(component.esAdmin()).toBe(true);
    expect(component.esEncargado()).toBe(false);

    const selectSucursal = fixture.nativeElement.querySelector(
      '#select-filtro-sucursal'
    ) as HTMLSelectElement;
    expect(selectSucursal).toBeTruthy();
    expect(selectSucursal.disabled).toBe(false);

    const options = Array.from(selectSucursal.options).map((o) => o.text);
    expect(options[0]).toBe('Todas las Sedes');
  });

  it('debe fijar y deshabilitar el selector de sucursal para rol encargado_sucursal (AC-19)', () => {
    usuarioActualSignal.set(mockEncargadoUser);
    fixture = TestBed.createComponent(InventarioAdminComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    expect(component.esAdmin()).toBe(false);
    expect(component.esEncargado()).toBe(true);
    expect(component.idSucursalEncargado()).toBe(10);

    const selectSucursal = fixture.nativeElement.querySelector(
      '#select-filtro-sucursal'
    ) as HTMLSelectElement;
    expect(selectSucursal).toBeTruthy();
    expect(selectSucursal.disabled).toBe(true);

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Boutique Calacoto Central');
  });

  it('debe filtrar reactivamente por busqueda de texto con debounce (AC-20)', async () => {
    const inputBusqueda = fixture.nativeElement.querySelector(
      '#input-busqueda-inventario'
    ) as HTMLInputElement;

    inputBusqueda.value = 'Obsidian';
    inputBusqueda.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    expect(component.busquedaTexto()).toBe('Obsidian');

    await new Promise((resolve) => setTimeout(resolve, 350));

    expect(mockInventarioService.cargarInventario).toHaveBeenCalledWith(
      expect.objectContaining({ q: 'Obsidian' })
    );
  });

  it('debe abrir el modal de stock inicial y enviar recepcion correctamente (AC-21)', () => {
    const btnCrear = fixture.nativeElement.querySelector('#btn-abrir-modal-crear') as HTMLButtonElement;
    btnCrear.click();
    fixture.detectChanges();

    expect(component.modalCrearAbierto()).toBe(true);

    component.formCrear.patchValue({
      id_sucursal: 10,
      id_producto: 50,
      id_variante: 201,
      cantidad_inicial: 25,
      stock_minimo: 5,
      stock_alerta: 10,
      referencia_documento: 'GR-2026-99',
      observacion: 'Recepcion de nueva coleccion',
    });

    component.guardarStockInicial();

    expect(mockInventarioService.crearStockInicial).toHaveBeenCalledWith(
      expect.objectContaining({
        id_sucursal: 10,
        id_variante: 201,
        cantidad_inicial: 25,
        stock_minimo: 5,
        stock_alerta: 10,
      })
    );
    expect(component.modalCrearAbierto()).toBe(false);
  });

  it('debe abrir el modal de ajuste fisico y validar motivo obligatorio minimo 5 caracteres (AC-22)', () => {
    component.abrirModalAjuste(mockItem1);
    fixture.detectChanges();

    expect(component.modalAjusteAbierto()).toBe(true);
    expect(component.itemSeleccionado()).toBe(mockItem1);

    // Formulario invalido por motivo vacio o menor a 5 caracteres
    component.formAjuste.patchValue({
      tipo_ajuste: 'incremento',
      cantidad: 5,
      motivo: 'abc', // 3 caracteres < 5
    });

    expect(component.formAjuste.valid).toBe(false);

    component.formAjuste.patchValue({
      motivo: 'Prenda encontrada en almacen secundario',
    });

    expect(component.formAjuste.valid).toBe(true);

    component.guardarAjuste();

    expect(mockInventarioService.ajustarStock).toHaveBeenCalledWith(
      101,
      expect.objectContaining({
        tipo_ajuste: 'incremento',
        cantidad: 5,
        motivo: 'Prenda encontrada en almacen secundario',
      })
    );
    expect(component.modalAjusteAbierto()).toBe(false);
  });

  it('debe impedir decrementos que superen la cantidad disponible en ajuste fisico (AC-22)', () => {
    component.abrirModalAjuste(mockItem1); // disponible = 18
    fixture.detectChanges();

    component.formAjuste.patchValue({
      tipo_ajuste: 'decremento',
      cantidad: 25, // 25 > 18
      motivo: 'Merma total reportada por auditoria',
    });

    component.guardarAjuste();

    expect(mockInventarioService.ajustarStock).not.toHaveBeenCalled();
    expect(component.errorBanner()).toContain('excede el saldo disponible');
  });

  it('debe abrir modal de transferencia excluyendo la sucursal de origen (AC-23)', () => {
    component.abrirModalTransferencia(mockItem1); // Origen = id 10 (Calacoto)
    fixture.detectChanges();

    expect(component.modalTransferenciaAbierto()).toBe(true);

    const destinos = component.sucursalesDestinoDisponibles();
    expect(destinos.some((s) => s.id_sucursal === 10)).toBe(false);
    expect(destinos.some((s) => s.id_sucursal === 20)).toBe(true);

    component.formTransferencia.patchValue({
      id_sucursal_destino: 20,
      cantidad: 4,
      motivo: 'Reabastecimiento boutique Equipetrol',
    });

    component.guardarTransferencia();

    expect(mockInventarioService.transferirMercaderia).toHaveBeenCalledWith(
      expect.objectContaining({
        id_sucursal_origen: 10,
        id_sucursal_destino: 20,
        id_variante: 201,
        cantidad: 4,
        motivo: 'Reabastecimiento boutique Equipetrol',
      })
    );
    expect(component.modalTransferenciaAbierto()).toBe(false);
  });

  it('debe deshabilitar el boton de transferir si la cantidad disponible es cero (AC-23)', () => {
    const btnTransferirAgotado = fixture.nativeElement.querySelector(
      '#btn-transferir-102'
    ) as HTMLButtonElement;

    expect(btnTransferirAgotado).toBeTruthy();
    expect(btnTransferirAgotado.disabled).toBe(true);
  });

  it('debe abrir el modal de Kardex y visualizar el historial de movimientos (AC-24)', () => {
    const btnKardex = fixture.nativeElement.querySelector(
      '#btn-kardex-101'
    ) as HTMLButtonElement;

    btnKardex.click();
    fixture.detectChanges();

    expect(component.modalKardexAbierto()).toBe(true);
    expect(mockInventarioService.cargarKardex).toHaveBeenCalledWith(101);

    // Mockeamos la llegada del kardex
    kardexActualSignal.set({
      id_inventario: 101,
      prenda_sku: 'VES-OBS-M',
      sucursal_nombre: 'Boutique Calacoto Central',
      saldo_actual: 18,
      movimientos: [
        {
          id_movimiento: 1,
          id_inventario: 101,
          tipo_movimiento: 'ingreso_proveedor',
          cantidad: 20,
          saldo_anterior: 0,
          saldo_nuevo: 20,
          motivo: 'Recepcion inicial lote #LOT-2026',
          referencia_documento: 'GR-1001',
          id_usuario: 1,
          usuario_nombre: 'Gustavo Vico',
          creado_en: '2026-09-21T10:00:00Z',
        },
      ],
    });
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Historial de Movimientos Kardex');
    expect(compiled.textContent).toContain('Recepcion inicial lote #LOT-2026');
    expect(compiled.textContent).toContain('+20');
  });

  it('debe capturar errores HTTP 409 y 422 en Luxury Banner contextual y permitir su descarte (AC-25)', () => {
    mockInventarioService.crearStockInicial.mockReturnValueOnce(
      throwError(() => new Error('Conflicto 409: Ya existe un registro de existencias para esta combinacion.'))
    );

    component.abrirModalCrear();
    component.formCrear.patchValue({
      id_sucursal: 10,
      id_producto: 50,
      id_variante: 201,
      cantidad_inicial: 10,
    });

    component.guardarStockInicial();
    fixture.detectChanges();

    expect(component.errorBanner()).toContain('Conflicto 409: Ya existe un registro de existencias');

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Alerta del Sistema de Stock');
    expect(compiled.textContent).toContain('Conflicto 409');

    // Descartar aviso
    component.descartarErrorBanner();
    fixture.detectChanges();

    expect(component.errorBanner()).toBeNull();
  });
});
