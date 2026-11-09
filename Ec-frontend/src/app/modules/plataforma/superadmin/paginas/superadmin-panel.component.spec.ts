import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { SuperadminPanelComponent } from './superadmin-panel.component';
import { SuperadminService } from '../servicios/superadmin.service';
import { LoginService } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import {
  CiudadGlobal,
  ColorGlobal,
  EmpresaDetalle,
  EmpresaResumen,
  FuncionalidadPlataforma,
  MetricasPlataforma,
  PlanDetalle,
  SuscripcionEmpresa,
  TallaGlobal,
} from '../modelos/superadmin.model';

describe('SuperadminPanelComponent (P2-CU05 a P2-CU08)', () => {
  let component: SuperadminPanelComponent;
  let fixture: ComponentFixture<SuperadminPanelComponent>;

  const mockMetricas: MetricasPlataforma = {
    empresas_totales: 2,
    empresas_activas: 2,
    empresas_suspendidas: 0,
    empresas_baja: 0,
    suscripciones_vigentes: 2,
    suscripciones_vencidas_o_suspendidas: 0,
    sucursales_activas_totales: 3,
    empleados_activos_totales: 8,
    ventas_pagadas_totales: 25,
    monto_ventas_pagadas_total: '4200.00',
    desglose_empresas: [],
  };

  const mockEmpresas: EmpresaResumen[] = [
    {
      id_tenant: 1,
      codigo: 'fashionstore',
      nombre: 'FASHION STORE',
      correo_contacto: 'contacto@fashionstore.com',
      telefono: '+34 91 000 0000',
      estado: 'activa',
      creado_en: '2026-11-08T00:00:00Z',
      suscripcion_actual: {
        id_suscripcion: 1,
        id_plan: 2,
        nombre_plan: 'Profesional',
        estado: 'activa',
        fecha_inicio: '2026-11-08',
        fecha_vencimiento: '2027-11-08',
        vigente: true,
      },
      indicadores: {
        sucursales_activas: 2,
        sucursales_totales: 2,
        empleados_activos: 5,
        productos_activos: 40,
        ventas_pagadas_cantidad: 20,
        ventas_pagadas_monto: '3500.00',
        reservas_totales: 6,
      },
    },
  ];

  const mockFuncionalidades: FuncionalidadPlataforma[] = [
    { codigo: 'productos', nombre: 'Gestión de productos', descripcion: null },
    { codigo: 'ventas', nombre: 'Ventas', descripcion: null },
    { codigo: 'reportes_ia', nombre: 'Reportes generativos con IA', descripcion: null },
  ];

  const mockPlanes: PlanDetalle[] = [
    {
      id_plan: 1,
      nombre: 'Básico',
      precio_mensual: '29.00',
      max_sucursales_activas: 2,
      max_empleados: 10,
      activo: true,
      creado_en: '2026-11-08T00:00:00Z',
      funcionalidades: [mockFuncionalidades[0], mockFuncionalidades[1]],
      codigos_funcionalidades: ['productos', 'ventas'],
      empresas_suscritas_vigentes: 1,
      empresas_suscritas_totales: 1,
      advertencias: [],
    },
  ];

  const mockSuscripciones: SuscripcionEmpresa[] = [
    {
      id_suscripcion: 1,
      id_tenant: 1,
      codigo_empresa: 'fashionstore',
      nombre_empresa: 'FASHION STORE',
      estado_empresa: 'activa',
      id_plan: 1,
      nombre_plan: 'Básico',
      precio_mensual: '29.00',
      estado: 'activa',
      fecha_inicio: '2026-11-08',
      fecha_vencimiento: '2027-11-08',
      vigente: true,
      sucursales_activas: 2,
      max_sucursales_activas: 2,
      empleados_activos: 4,
      max_empleados: 10,
      creado_en: '2026-11-08T00:00:00Z',
    },
  ];

  const mockCiudades: CiudadGlobal[] = [
    {
      id_ciudad: 1,
      nombre: 'Santa Cruz de la Sierra',
      pais: 'Bolivia',
      activo: true,
      creado_en: '2026-11-08T00:00:00Z',
      sucursales_asociadas: 2,
    },
  ];

  const mockTallas: TallaGlobal[] = [
    { id_talla: 1, codigo: 'M', orden: 2, activo: true, variantes_asociadas: 5 },
  ];

  const mockColores: ColorGlobal[] = [
    { id_color: 1, nombre: 'Negro', codigo_hex: '#000000', activo: true, variantes_asociadas: 3 },
  ];

  const mockSuperadminService = {
    obtenerMetricas: vi.fn(() => of(mockMetricas)),
    listarEmpresas: vi.fn(() => of(mockEmpresas)),
    registrarEmpresa: vi.fn(),
    actualizarEmpresa: vi.fn(),
    cambiarEstadoEmpresa: vi.fn(),
    listarFuncionalidades: vi.fn(() => of(mockFuncionalidades)),
    listarPlanes: vi.fn(() => of(mockPlanes)),
    crearPlan: vi.fn(),
    actualizarPlan: vi.fn(),
    cambiarEstadoPlan: vi.fn(),
    listarSuscripciones: vi.fn(() => of(mockSuscripciones)),
    listarHistorialSuscripcion: vi.fn(() => of([])),
    operarSuscripcion: vi.fn(),
    listarCiudades: vi.fn(() => of(mockCiudades)),
    crearCiudad: vi.fn(),
    actualizarCiudad: vi.fn(),
    cambiarEstadoCiudad: vi.fn(),
    eliminarCiudad: vi.fn(),
    listarTallas: vi.fn(() => of(mockTallas)),
    crearTalla: vi.fn(),
    actualizarTalla: vi.fn(),
    cambiarEstadoTalla: vi.fn(),
    eliminarTalla: vi.fn(),
    listarColores: vi.fn(() => of(mockColores)),
    crearColor: vi.fn(),
    actualizarColor: vi.fn(),
    cambiarEstadoColor: vi.fn(),
    eliminarColor: vi.fn(),
    listarBitacora: vi.fn(() =>
      of({ items: [], total: 0, pagina: 1, limite: 20, total_paginas: 1 })
    ),
  };

  const mockLoginService = {
    cerrarSesion: vi.fn(() => of({})),
  };

  beforeEach(async () => {
    vi.clearAllMocks();
    await TestBed.configureTestingModule({
      imports: [SuperadminPanelComponent],
      providers: [
        provideRouter([]),
        { provide: SuperadminService, useValue: mockSuperadminService },
        { provide: LoginService, useValue: mockLoginService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(SuperadminPanelComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe inicializar cargando métricas, empresas, planes y funcionalidades (P2-CU05, P2-CU06)', () => {
    expect(component).toBeTruthy();
    expect(mockSuperadminService.obtenerMetricas).toHaveBeenCalled();
    expect(mockSuperadminService.listarEmpresas).toHaveBeenCalled();
    expect(mockSuperadminService.listarPlanes).toHaveBeenCalled();
    expect(component.empresas().length).toBe(1);
    expect(component.metricas()?.empresas_totales).toBe(2);
  });

  it('P2-CU05: debe registrar una nueva empresa con su suscripción y administrador inicial', () => {
    const creada: EmpresaDetalle = {
      ...mockEmpresas[0],
      id_tenant: 5,
      codigo: 'atelier-milano',
      nombre: 'Atelier Milano',
      admin_email: 'admin@milano.com',
      admin_nombre: 'Lucía Rossi',
    };
    mockSuperadminService.registrarEmpresa.mockReturnValue(of(creada));

    component.abrirModalNuevaEmpresa();
    component.formNuevaEmpresa.setValue({
      codigo: 'atelier-milano',
      nombre: 'Atelier Milano',
      correo_contacto: 'info@milano.com',
      telefono: '70011223',
      id_plan: 1,
      estado_suscripcion: 'activa',
      fecha_inicio: '2026-11-09',
      fecha_vencimiento: '2027-11-09',
      admin_nombres: 'Lucía',
      admin_apellidos: 'Rossi',
      admin_email: 'admin@milano.com',
      admin_password: 'Password123!',
      admin_telefono: '',
    });

    component.guardarNuevaEmpresa();

    expect(mockSuperadminService.registrarEmpresa).toHaveBeenCalled();
    expect(component.mostrarModalNuevaEmpresa()).toBe(false);
    expect(component.mensajeExito()).toContain('Atelier Milano');
  });

  it('P2-CU06 (A1): al editar un plan muestra advertencias si hay empresas por encima del nuevo límite', () => {
    const planConAdvertencia: PlanDetalle = {
      ...mockPlanes[0],
      max_sucursales_activas: 1,
      advertencias: [
        "La empresa 'FASHION STORE' (fashionstore) tiene 2 sucursales activas (nuevo límite: 1).",
      ],
    };
    mockSuperadminService.actualizarPlan.mockReturnValue(of(planConAdvertencia));

    component.iniciarEdicionPlan(mockPlanes[0]);
    component.formPlan.patchValue({ max_sucursales_activas: 1 });
    component.guardarPlan();

    expect(mockSuperadminService.actualizarPlan).toHaveBeenCalled();
    expect(component.advertenciasPlan().length).toBe(1);
    expect(component.advertenciasPlan()[0]).toContain('FASHION STORE');
  });

  it('P2-CU07: debe cambiar a la pestaña de suscripciones y ejecutar una operación de renovación', () => {
    component.cambiarPestana('suscripciones');
    expect(mockSuperadminService.listarSuscripciones).toHaveBeenCalled();

    const renovada: SuscripcionEmpresa = {
      ...mockSuscripciones[0],
      fecha_vencimiento: '2028-11-08',
    };
    mockSuperadminService.operarSuscripcion.mockReturnValue(of(renovada));

    component.abrirGestionSuscripcion(mockSuscripciones[0]);
    component.formOperacionSuscripcion.patchValue({
      operacion: 'renovacion',
      fecha_vencimiento: '2028-11-08',
    });
    component.ejecutarOperacionSuscripcion();

    expect(mockSuperadminService.operarSuscripcion).toHaveBeenCalledWith(
      1,
      expect.objectContaining({ operacion: 'renovacion', fecha_vencimiento: '2028-11-08' })
    );
  });

  it('P2-CU08 (A2): debe cargar catálogos globales y permitir desactivar una ciudad en uso', () => {
    component.cambiarPestana('catalogos');
    expect(mockSuperadminService.listarCiudades).toHaveBeenCalled();
    expect(mockSuperadminService.listarTallas).toHaveBeenCalled();
    expect(mockSuperadminService.listarColores).toHaveBeenCalled();

    mockSuperadminService.cambiarEstadoCiudad.mockReturnValue(
      of({ ...mockCiudades[0], activo: false })
    );
    component.alternarEstadoCiudad(mockCiudades[0]);

    expect(mockSuperadminService.cambiarEstadoCiudad).toHaveBeenCalledWith(1, false);
    expect(component.mensajeExito()).toContain('desactivada');
  });
});

