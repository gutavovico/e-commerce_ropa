/**
 * Suite de Pruebas Unitarias para CU29: Visualizar indicadores empresariales.
 * Nomenclatura oficial: "Visualizar indicadores empresariales"
 */

import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { signal } from '@angular/core';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { of } from 'rxjs';
import { IndicadoresAdminComponent } from './indicadores-admin.component';
import { IndicadoresAdminService } from '../servicios/indicadores-admin.service';
import { LoginService } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import { UsuarioSesion } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/modelos/login.dto';
import {
  ComparativaSucursales,
  DashboardIndicadoresCompleto,
  DistribucionVentas,
  ItemRankingProducto,
  RankingProductos,
  ResumenEjecutivo,
  SerieTemporalIngresos,
  SucursalDesempeno,
  SucursalOpcion,
} from '../modelos/indicadores.dto';

describe('IndicadoresAdminComponent', () => {
  let fixture: ComponentFixture<IndicadoresAdminComponent>;
  let component: IndicadoresAdminComponent;

  const mockAdmin: UsuarioSesion = {
    id_usuario: 99,
    email: 'admin.director@fashionstore.com',
    nombres: 'Elena',
    apellidos: 'Montes',
    rol: 'administrador',
    token: 'jwt-token-valido',
  };

  const mockEncargado: UsuarioSesion = {
    id_usuario: 88,
    email: 'encargado.sur@fashionstore.com',
    nombres: 'Rodrigo',
    apellidos: 'Paz',
    rol: 'encargado_sucursal',
    token: 'jwt-token-encargado',
    id_sucursal: 2,
  };

  const mockResumen: ResumenEjecutivo = {
    periodo_inicio: '2026-08-20',
    periodo_fin: '2026-09-20',
    ingresos_totales: 85400.0,
    variacion_porcentual: 14.5,
    total_transacciones: 36,
    variacion_porcentual_transacciones: 8.2,
    margen_estimado: 29890.0,
    ticket_promedio: 2372.22,
    variacion_porcentual_ticket: 5.8,
    unidades_vendidas: 112,
    variacion_porcentual_unidades: 10.0,
  };

  const mockSerie: SerieTemporalIngresos = {
    agrupacion: 'diaria',
    puntos: [
      {
        etiqueta_tiempo: '20 Sep',
        fecha_inicio: '2026-09-20',
        monto_ingresos: 4200.0,
        cantidad_ordenes: 3,
      },
      {
        etiqueta_tiempo: '21 Sep',
        fecha_inicio: '2026-09-21',
        monto_ingresos: 6800.0,
        cantidad_ordenes: 5,
      },
      {
        etiqueta_tiempo: '22 Sep',
        fecha_inicio: '2026-09-22',
        monto_ingresos: 5100.0,
        cantidad_ordenes: 4,
      },
    ],
  };

  const mockTopProductos: ItemRankingProducto[] = [
    {
      id_producto: 1,
      nombre_producto: 'Abrigo Cashmere Atelier',
      sku_referencia: 'ABR-001',
      categoria_nombre: 'Abrigos',
      unidades_vendidas: 12,
      monto_total_generado: 24000.0,
      porcentaje_contribucion: 28.1,
    },
    {
      id_producto: 2,
      nombre_producto: 'Vestido Seda Noir',
      sku_referencia: 'VES-002',
      categoria_nombre: 'Vestidos',
      unidades_vendidas: 8,
      monto_total_generado: 16000.0,
      porcentaje_contribucion: 18.7,
    },
  ];

  const mockDistribucion: DistribucionVentas = {
    por_canal: [
      {
        canal_codigo: 'presencial',
        canal_nombre: 'Presencial Boutique',
        monto_facturado: 52000.0,
        total_ordenes: 22,
        porcentaje_participacion: 60.9,
      },
      {
        canal_codigo: 'digital_web',
        canal_nombre: 'Web Oficial',
        monto_facturado: 33400.0,
        total_ordenes: 14,
        porcentaje_participacion: 39.1,
      },
    ],
    por_categoria: [
      {
        id_categoria: 1,
        nombre_categoria: 'Abrigos',
        monto_facturado: 45000.0,
        unidades_vendidas: 25,
        porcentaje_participacion: 52.7,
      },
      {
        id_categoria: 2,
        nombre_categoria: 'Vestidos',
        monto_facturado: 40400.0,
        unidades_vendidas: 30,
        porcentaje_participacion: 47.3,
      },
    ],
  };

  const mockComparativa: SucursalDesempeno[] = [
    {
      id_sucursal: 1,
      nombre_sucursal: 'Boutique Central',
      ciudad: 'La Paz',
      monto_facturado: 55000.0,
      total_ventas: 24,
      ticket_promedio: 2291.67,
      porcentaje_red: 64.4,
    },
    {
      id_sucursal: 2,
      nombre_sucursal: 'Boutique Sur',
      ciudad: 'Cochabamba',
      monto_facturado: 30400.0,
      total_ventas: 12,
      ticket_promedio: 2533.33,
      porcentaje_red: 35.6,
    },
  ];

  const mockSucursalesAux: SucursalOpcion[] = [
    { id_sucursal: 1, nombre: 'Boutique Central', ciudad: 'La Paz' },
    { id_sucursal: 2, nombre: 'Boutique Sur', ciudad: 'Cochabamba' },
  ];

  const mockDashboard: DashboardIndicadoresCompleto = {
    resumen: mockResumen,
    serie_temporal: mockSerie,
    top_productos: { limite: 5, productos: mockTopProductos },
    distribucion: mockDistribucion,
    comparativa_sucursales: { sucursales: mockComparativa },
  };

  let usuarioActualSignal = signal<UsuarioSesion | null>(mockAdmin);
  let cargandoSignal = signal<boolean>(false);
  let errorSignal = signal<string | null>(null);
  let resumenSignal = signal<ResumenEjecutivo | null>(mockResumen);
  let serieTemporalSignal = signal<SerieTemporalIngresos | null>(mockSerie);
  let topProductosSignal = signal<ItemRankingProducto[]>(mockTopProductos);
  let distribucionSignal = signal<DistribucionVentas | null>(mockDistribucion);
  let comparativaSignal = signal<SucursalDesempeno[]>(mockComparativa);
  let sucursalesSignal = signal<SucursalOpcion[]>(mockSucursalesAux);

  const mockServicio = {
    cargando: cargandoSignal,
    error: errorSignal,
    resumen: resumenSignal,
    serieTemporal: serieTemporalSignal,
    topProductos: topProductosSignal,
    distribucion: distribucionSignal,
    comparativa: comparativaSignal,
    sucursales: sucursalesSignal,
    consultarDashboardConsolidado: vi.fn().mockReturnValue(of(mockDashboard)),
    cargarSucursalesAuxiliares: vi.fn(),
    limpiarError: vi.fn(() => errorSignal.set(null)),
  };

  const mockLoginService = {
    usuarioActual: usuarioActualSignal,
  };

  beforeEach(async () => {
    usuarioActualSignal.set(mockAdmin);
    cargandoSignal.set(false);
    errorSignal.set(null);
    resumenSignal.set(mockResumen);
    serieTemporalSignal.set(mockSerie);
    topProductosSignal.set(mockTopProductos);
    distribucionSignal.set(mockDistribucion);
    comparativaSignal.set(mockComparativa);
    sucursalesSignal.set(mockSucursalesAux);

    vi.clearAllMocks();

    await TestBed.configureTestingModule({
      imports: [IndicadoresAdminComponent],
      providers: [
        provideRouter([]),
        { provide: IndicadoresAdminService, useValue: mockServicio },
        { provide: LoginService, useValue: mockLoginService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(IndicadoresAdminComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe inicializarse correctamente y compilar sin errores', () => {
    expect(component).toBeTruthy();
  });

  it('debe renderizar el titulo institucional "Visualizar indicadores empresariales" y migas de pan', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const h1 = compiled.querySelector('h1');
    expect(h1).toBeTruthy();
    expect(h1?.textContent?.trim()).toContain('Visualizar indicadores empresariales');

    const breadcrumb = compiled.querySelector('nav[aria-label="Breadcrumb"]');
    expect(breadcrumb?.textContent).toContain('VISUALIZAR INDICADORES EMPRESARIALES');

    const btnVolver = compiled.querySelector('#btn-volver-dashboard-indicadores');
    expect(btnVolver).toBeTruthy();
    expect(btnVolver?.getAttribute('routerLink')).toBe('/admin');
  });

  it('debe renderizar las 4 tarjetas de KPIs ejecutivos con sus valores formateados', () => {
    const compiled = fixture.nativeElement as HTMLElement;

    const kpiIngresos = compiled.querySelector('#kpi-ingresos-totales');
    expect(kpiIngresos?.textContent).toContain('85');

    const kpiTransacciones = compiled.querySelector('#kpi-total-transacciones');
    expect(kpiTransacciones?.textContent?.trim()).toBe('36');

    const kpiMargen = compiled.querySelector('#kpi-margen-estimado');
    expect(kpiMargen?.textContent).toContain('29');

    const kpiTicket = compiled.querySelector('#kpi-ticket-promedio');
    expect(kpiTicket?.textContent).toContain('2');

    const badgeVariacion = compiled.querySelector('#badge-variacion-ingresos');
    expect(badgeVariacion?.textContent).toContain('+14.5%');
  });

  it('debe conmutar reactivamente de periodo al hacer clic en un boton de temporalidad', () => {
    const btn7d = fixture.nativeElement.querySelector(
      '#btn-periodo-7d'
    ) as HTMLButtonElement;
    expect(btn7d).toBeTruthy();

    btn7d.click();
    fixture.detectChanges();

    expect(component.periodoSeleccionado()).toBe('7d');
    expect(mockServicio.consultarDashboardConsolidado).toHaveBeenCalled();
  });

  it('debe desplegar campos de fecha y validar inconsistencias en periodo personalizado', () => {
    const btnPersonalizado = fixture.nativeElement.querySelector(
      '#btn-periodo-personalizado'
    ) as HTMLButtonElement;
    btnPersonalizado.click();
    fixture.detectChanges();

    expect(component.periodoSeleccionado()).toBe('personalizado');

    // Fechas vacias
    component.aplicarPeriodoPersonalizado();
    fixture.detectChanges();
    expect(component.errorFechas()).toContain('Debe ingresar ambas fechas');

    // Fechas inconsistentes (desde > hasta)
    component.fechaDesde.set('2026-09-25');
    component.fechaHasta.set('2026-09-20');
    component.aplicarPeriodoPersonalizado();
    fixture.detectChanges();
    expect(component.errorFechas()).toContain('Rango inconsistente');

    // Fechas consistentes
    component.fechaDesde.set('2026-09-01');
    component.fechaHasta.set('2026-09-20');
    component.aplicarPeriodoPersonalizado();
    fixture.detectChanges();
    expect(component.errorFechas()).toBeNull();
    expect(mockServicio.consultarDashboardConsolidado).toHaveBeenCalled();
  });

  it('debe permitir seleccionar sucursales al rol administrador y cargar sedes auxiliares', () => {
    expect(component.esAdmin()).toBe(true);
    expect(mockServicio.cargarSucursalesAuxiliares).toHaveBeenCalled();

    const select = fixture.nativeElement.querySelector(
      '#select-sucursal-indicadores'
    ) as HTMLSelectElement;
    expect(select).toBeTruthy();

    select.value = '1';
    select.dispatchEvent(new Event('change'));
    fixture.detectChanges();

    expect(component.idSucursalFiltro()).toBe(1);
    expect(mockServicio.consultarDashboardConsolidado).toHaveBeenCalled();
  });

  it('debe bloquear el selector de sucursales y mostrar badge para encargado_sucursal', () => {
    usuarioActualSignal.set(mockEncargado);
    fixture.detectChanges();

    expect(component.esEncargado()).toBe(true);
    expect(component.esAdmin()).toBe(false);

    const select = fixture.nativeElement.querySelector('#select-sucursal-indicadores');
    expect(select).toBeFalsy();

    const textContent = fixture.nativeElement.textContent;
    expect(textContent).toContain('Sede asignada');
    expect(textContent).toContain('Boutique Sur');
  });

  it('debe renderizar la grafica SVG nativa con puntos cronologicos', () => {
    const svg = fixture.nativeElement.querySelector(
      'svg[aria-label="Grafico de ingresos temporales"]'
    );
    expect(svg).toBeTruthy();

    const circles = svg.querySelectorAll('circle');
    expect(circles.length).toBe(3);

    // Activacion de tooltip al hacer hover en un punto
    component.activarPunto(component.puntosGraficoCalculados()[0]);
    fixture.detectChanges();
    expect(component.puntoActivo()).toBeTruthy();
    expect(fixture.nativeElement.textContent).toContain('20 Sep');
  });

  it('debe renderizar el ranking Top 5 de prendas y las distribuciones de canales', () => {
    const textContent = fixture.nativeElement.textContent;
    expect(textContent).toContain('Top 5 Prendas mas Comercializadas');
    expect(textContent).toContain('Abrigo Cashmere Atelier');
    expect(textContent).toContain('ABR-001');

    expect(textContent).toContain('Canales de Distribucion');
    expect(textContent).toContain('Presencial Boutique');
    expect(textContent).toContain('Web Oficial');
  });

  it('debe mostrar comparativa de sucursales a administradores y ocultarla a encargados', () => {
    // Caso 1: Administrador
    expect(component.esAdmin()).toBe(true);
    let tabla = fixture.nativeElement.querySelector('table[aria-label="Tabla de sucursales"]');
    expect(tabla).toBeTruthy();
    expect(fixture.nativeElement.textContent).toContain('Boutique Central');

    // Caso 2: Encargado
    usuarioActualSignal.set(mockEncargado);
    fixture.detectChanges();

    tabla = fixture.nativeElement.querySelector('table[aria-label="Tabla de sucursales"]');
    expect(tabla).toBeFalsy();
  });

  it('debe mostrar Luxury Banner ante anomalias o errores del servicio', () => {
    errorSignal.set('No se pudo establecer conexion con el servidor analitico.');
    fixture.detectChanges();

    const banner = fixture.nativeElement.querySelector('.bg-rose-50');
    expect(banner).toBeTruthy();
    expect(banner.textContent).toContain('Aviso de Excepcion Semantica');
    expect(banner.textContent).toContain('No se pudo establecer conexion con el servidor analitico.');

    // Limpiar banner
    component.limpiarError();
    expect(mockServicio.limpiarError).toHaveBeenCalled();
  });
});
