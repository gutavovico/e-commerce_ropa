/**
 * Pruebas unitarias para PromocionesAdminComponent (CU27).
 * Criterios # AC-14 a # AC-22.
 * Nomenclatura oficial: "Gestionar promociones"
 */

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, RouterLink } from '@angular/router';
import { By } from '@angular/platform-browser';
import { signal } from '@angular/core';
import { of, throwError } from 'rxjs';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { PromocionesAdminComponent } from './promociones-admin.component';
import { PromocionesAdminService } from '../servicios/promociones-admin.service';
import { LoginService } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import { UsuarioSesion } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/modelos/login.dto';
import {
  MetricasPromociones,
  PromocionItem,
  RespuestaPaginadaPromociones,
} from '../modelos/promociones.dto';

describe('PromocionesAdminComponent (CU27)', () => {
  let fixture: ComponentFixture<PromocionesAdminComponent>;
  let component: PromocionesAdminComponent;

  const mockAdminUser: UsuarioSesion = {
    id_usuario: 1,
    email: 'admin.director@fashionstore.com',
    nombres: 'Elena',
    apellidos: 'Montes',
    rol: 'administrador',
    token: 'jwt-token-admin',
  };

  const mockEncargadoUser: UsuarioSesion = {
    id_usuario: 2,
    email: 'encargado.sucursal@fashionstore.com',
    nombres: 'Mario',
    apellidos: 'Suarez',
    rol: 'encargado_sucursal',
    token: 'jwt-token-encargado',
  };

  const usuarioActualSignal = signal<UsuarioSesion | null>(mockAdminUser);

  const mockMetricas: MetricasPromociones = {
    promociones_activas: 5,
    cupones_vigentes: 3,
    descuento_promedio: 20.0,
    usos_totales: 120,
  };

  const mockPromoVigente: PromocionItem = {
    id_promocion: 1,
    nombre: 'Black Velvet VIP',
    descripcion: 'Descuento exclusivo en alta costura',
    codigo_cupon: 'VELVET25',
    tipo_descuento: 'porcentaje',
    valor_descuento: 25.0,
    fecha_inicio: '2026-01-01T00:00:00',
    fecha_fin: '2026-12-31T23:59:59',
    tope_descuento: 150.0,
    limite_usos: 200,
    usos_actuales: 45,
    alcance: 'global',
    id_categoria: null,
    id_producto: null,
    estado_activo: true,
    creado_en: '2026-09-21T10:00:00Z',
    actualizado_en: '2026-09-21T10:00:00Z',
  };

  const mockPromoExpirada: PromocionItem = {
    id_promocion: 2,
    nombre: 'Cyber Flash',
    descripcion: 'Monto fijo temporal',
    codigo_cupon: null,
    tipo_descuento: 'monto_fijo',
    valor_descuento: 50.0,
    fecha_inicio: '2025-01-01T00:00:00',
    fecha_fin: '2025-01-15T23:59:59',
    tope_descuento: null,
    limite_usos: 50,
    usos_actuales: 50,
    alcance: 'categoria',
    id_categoria: 10,
    id_producto: null,
    estado_activo: false,
    creado_en: '2025-01-01T10:00:00Z',
    actualizado_en: '2025-01-16T10:00:00Z',
  };

  const mockRespuestaPaginada: RespuestaPaginadaPromociones = {
    items: [mockPromoVigente, mockPromoExpirada],
    total: 2,
    pagina: 1,
    limite: 10,
    total_paginas: 1,
    metricas: mockMetricas,
  };

  // Signals del servicio simulado
  const promocionesSignal = signal<PromocionItem[]>([mockPromoVigente, mockPromoExpirada]);
  const metricasSignal = signal<MetricasPromociones | null>(mockMetricas);
  const totalPromocionesSignal = signal<number>(2);
  const totalPaginasSignal = signal<number>(1);
  const cargandoSignal = signal<boolean>(false);
  const guardandoSignal = signal<boolean>(false);
  const errorSignal = signal<string | null>(null);
  const mensajeExitoSignal = signal<string | null>(null);

  const mockServicio = {
    promociones: promocionesSignal,
    metricas: metricasSignal,
    totalPromociones: totalPromocionesSignal,
    totalPaginas: totalPaginasSignal,
    cargando: cargandoSignal,
    guardando: guardandoSignal,
    error: errorSignal,
    mensajeExito: mensajeExitoSignal,

    filtros: signal({
      q: '',
      tipo_descuento: 'todos',
      estado_activo: 'todos',
      alcance: 'todos',
      pagina: 1,
      limite: 10,
      ordenar_por: 'creado_en_desc',
    }),

    listarPromociones: vi.fn().mockReturnValue(of(mockRespuestaPaginada)),
    obtenerPromocionPorId: vi.fn().mockReturnValue(of(mockPromoVigente)),
    crearPromocion: vi.fn().mockReturnValue(of(mockPromoVigente)),
    actualizarPromocion: vi.fn().mockReturnValue(of(mockPromoVigente)),
    conmutarEstado: vi.fn().mockReturnValue(of({ ...mockPromoVigente, estado_activo: false })),
    cargarAuxiliares: vi.fn(),
  };

  const mockLoginService = {
    usuarioActual: usuarioActualSignal,
  };

  beforeEach(async () => {
    usuarioActualSignal.set(mockAdminUser);
    promocionesSignal.set([mockPromoVigente, mockPromoExpirada]);
    metricasSignal.set(mockMetricas);
    totalPromocionesSignal.set(2);
    totalPaginasSignal.set(1);
    cargandoSignal.set(false);
    guardandoSignal.set(false);
    errorSignal.set(null);
    mensajeExitoSignal.set(null);

    await TestBed.configureTestingModule({
      imports: [PromocionesAdminComponent],
      providers: [
        provideRouter([]),
        { provide: PromocionesAdminService, useValue: mockServicio },
        { provide: LoginService, useValue: mockLoginService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(PromocionesAdminComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe crearse correctamente el componente y cargar los datos iniciales (# AC-15)', () => {
    expect(component).toBeTruthy();
    expect(mockServicio.listarPromociones).toHaveBeenCalled();
    expect(mockServicio.cargarAuxiliares).toHaveBeenCalled();
  });

  it('debe renderizar la cabecera institucional H1 "Gestionar promociones" y el boton de retorno (# AC-15)', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const h1 = compiled.querySelector('h1');
    expect(h1?.textContent?.trim()).toBe('Gestionar promociones');

    const breadcrumb = compiled.querySelector('nav');
    expect(breadcrumb?.textContent).toContain('GESTIONAR PROMOCIONES');

    const btnVolver = compiled.querySelector('#btn-volver-dashboard') as HTMLAnchorElement;
    expect(btnVolver).toBeTruthy();
    expect(btnVolver.getAttribute('routerLink')).toBe('/admin');
  });

  it('debe renderizar el boton "Nueva Promocion" para administradores y ocultarlo para encargados (# AC-15, # AC-14)', () => {
    let btnCrear = fixture.nativeElement.querySelector('#btn-abrir-crear-promocion');
    expect(btnCrear).toBeTruthy();

    // Cambiar a rol encargado_sucursal
    usuarioActualSignal.set(mockEncargadoUser);
    fixture.detectChanges();

    btnCrear = fixture.nativeElement.querySelector('#btn-abrir-crear-promocion');
    expect(btnCrear).toBeNull();
  });

  it('debe renderizar las 4 tarjetas de metricas cuantitativas (# AC-16)', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Promociones Activas');
    expect(compiled.textContent).toContain('Cupones Vigentes');
    expect(compiled.textContent).toContain('Descuento Promedio');
    expect(compiled.textContent).toContain('Usos Acumulados');

    expect(compiled.textContent).toContain('5');
    expect(compiled.textContent).toContain('3');
    expect(compiled.textContent).toContain('20.0%');
    expect(compiled.textContent).toContain('120');
  });

  it('debe renderizar la tabla maestra con las promociones y badges de vigencia (# AC-18)', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Black Velvet VIP');
    expect(compiled.textContent).toContain('VELVET25');
    expect(compiled.textContent).toContain('25% OFF');
    expect(compiled.textContent).toContain('Vigente');

    expect(compiled.textContent).toContain('Cyber Flash');
    expect(compiled.textContent).toContain('$50.00');
    expect(compiled.textContent).toContain('Expirada');
  });

  it('debe abrir el modal de creacion y validar fechas sincronicas (# AC-19)', () => {
    component.abrirModalCrear();
    expect(component.modalAbierto()).toBe(true);
    expect(component.modoEdicion()).toBe(false);

    // Fechas invalidas: fecha_fin anterior a fecha_inicio
    component.formPromocion.patchValue({
      nombre: 'Promo Test',
      tipo_descuento: 'porcentaje',
      valor_descuento: 15,
      fecha_inicio: '2026-11-20T10:00',
      fecha_fin: '2026-11-10T10:00',
      alcance: 'global',
    });

    expect(component.formPromocion.errors?.['fechasInvalidas']).toBeTruthy();
    expect(component.formPromocion.invalid).toBe(true);

    // Corregir fechas
    component.formPromocion.patchValue({
      fecha_fin: '2026-11-25T10:00',
    });
    expect(component.formPromocion.errors).toBeNull();
  });

  it('debe validar el rango de porcentaje (1 a 100) en el formulario (# AC-19)', () => {
    component.abrirModalCrear();
    component.formPromocion.patchValue({
      nombre: 'Promo 150%',
      tipo_descuento: 'porcentaje',
      valor_descuento: 150,
      fecha_inicio: '2026-10-01T10:00',
      fecha_fin: '2026-10-15T10:00',
      alcance: 'global',
    });

    expect(component.formPromocion.errors?.['porcentajeInvalido']).toBeTruthy();
  });

  it('debe validar que alcance por categoria exija id_categoria (# AC-19)', () => {
    component.abrirModalCrear();
    component.formPromocion.patchValue({
      nombre: 'Promo Categoria',
      tipo_descuento: 'porcentaje',
      valor_descuento: 20,
      fecha_inicio: '2026-10-01T10:00',
      fecha_fin: '2026-10-15T10:00',
      alcance: 'categoria',
      id_categoria: null,
    });

    expect(component.formPromocion.errors?.['categoriaRequerida']).toBeTruthy();
  });

  it('debe abrir el modal de confirmacion y conmutar el estado logico (# AC-20)', () => {
    component.abrirModalConmutar(mockPromoVigente);
    expect(component.modalConfirmarEstadoAbierto()).toBe(true);
    expect(component.promocionParaConmutar()?.id_promocion).toBe(1);

    component.confirmarConmutacion();
    expect(mockServicio.conmutarEstado).toHaveBeenCalledWith(1, false);
    expect(component.modalConfirmarEstadoAbierto()).toBe(false);
  });

  it('debe capturar colisiones de cupon duplicado (HTTP 409) en un Luxury Banner (# AC-21)', () => {
    mockServicio.crearPromocion.mockReturnValueOnce(
      throwError(() => new Error('Conflicto: Ya existe un cupon con este codigo.'))
    );

    component.abrirModalCrear();
    component.formPromocion.patchValue({
      nombre: 'Promo Duplicada',
      codigo_cupon: 'VELVET25',
      tipo_descuento: 'porcentaje',
      valor_descuento: 25,
      fecha_inicio: '2026-11-01T10:00',
      fecha_fin: '2026-11-30T10:00',
      alcance: 'global',
    });

    component.guardarPromocion();
    expect(component.errorBanner()).toContain('Conflicto');
  });

  it('debe aplicar filtros reactivos y debounce en la busqueda (# AC-17)', () => {
    vi.useFakeTimers();

    const event = {
      target: { value: 'Velvet' },
    } as unknown as Event;

    component.onBusquedaInput(event);
    expect(component.busquedaTexto()).toBe('Velvet');

    // Adelantar 300 ms del temporizador de debounce
    vi.advanceTimersByTime(300);

    expect(mockServicio.listarPromociones).toHaveBeenCalled();
    vi.useRealTimers();
  });

  it('debe resetear todos los filtros a sus valores predeterminados (# AC-17)', () => {
    component.busquedaTexto.set('Filtro anterior');
    component.filtroTipoDescuento.set('monto_fijo');
    component.filtroEstado.set('inactivas');
    component.filtroAlcance.set('categoria');

    component.resetearFiltros();

    expect(component.busquedaTexto()).toBe('');
    expect(component.filtroTipoDescuento()).toBe('todos');
    expect(component.filtroEstado()).toBe('todos');
    expect(component.filtroAlcance()).toBe('todos');
  });

  it('debe mostrar el estado de carga y estado vacio (# AC-22)', () => {
    cargandoSignal.set(true);
    fixture.detectChanges();

    let compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Sincronizando campanas comerciales...');

    cargandoSignal.set(false);
    promocionesSignal.set([]);
    fixture.detectChanges();

    compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('No se encontraron promociones');
  });
});
