/**
 * Pruebas unitarias para TemporadasColeccionesAdminComponent (CU24).
 * Criterios # AC-14 a # AC-23.
 * Nomenclatura oficial: "Gestionar temporadas y colecciones"
 */

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, RouterLink } from '@angular/router';
import { By } from '@angular/platform-browser';
import { signal } from '@angular/core';
import { of, throwError } from 'rxjs';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { TemporadasColeccionesAdminComponent } from './temporadas-colecciones-admin.component';
import { TemporadasColeccionesAdminService } from '../servicios/temporadas-colecciones-admin.service';
import { LoginService } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import { UsuarioSesion } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/modelos/login.dto';
import {
  ColeccionItem,
  PestanaGestion,
  RespuestaPaginadaColecciones,
  RespuestaPaginadaTemporadas,
  TemporadaItem,
} from '../modelos/temporadas-colecciones.dto';

describe('TemporadasColeccionesAdminComponent (CU24)', () => {
  let fixture: ComponentFixture<TemporadasColeccionesAdminComponent>;
  let component: TemporadasColeccionesAdminComponent;

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

  const mockTemporada1: TemporadaItem = {
    id_temporada: 1,
    nombre: 'Otono - Invierno 2026',
    tipo: 'otono_invierno',
    anio: 2026,
    fecha_inicio: '2026-03-21',
    fecha_fin: '2026-06-20',
    estado_activo: true,
    total_colecciones: 2,
    creado_en: '2026-09-21T10:00:00Z',
    actualizado_en: '2026-09-21T10:00:00Z',
  };

  const mockTemporadaInactiva: TemporadaItem = {
    id_temporada: 2,
    nombre: 'Primavera - Verano 2025',
    tipo: 'primavera_verano',
    anio: 2025,
    fecha_inicio: '2025-09-21',
    fecha_fin: '2025-12-21',
    estado_activo: false,
    total_colecciones: 1,
    creado_en: '2025-09-20T10:00:00Z',
    actualizado_en: '2026-01-10T10:00:00Z',
  };

  const mockColeccion1: ColeccionItem = {
    id_coleccion: 1,
    id_temporada: 1,
    temporada_nombre: 'Otono - Invierno 2026',
    temporada_anio: 2026,
    nombre: 'Capsula Alpaca Real',
    descripcion: 'Prendas de alta gama en fibra de alpaca',
    estado_activo: true,
    total_productos: 5,
    creado_en: '2026-09-21T10:00:00Z',
    actualizado_en: '2026-09-21T10:00:00Z',
  };

  const mockListaTemporadas: RespuestaPaginadaTemporadas = {
    items: [mockTemporada1, mockTemporadaInactiva],
    total: 2,
    pagina: 1,
    limite: 10,
    total_paginas: 1,
  };

  const mockListaColecciones: RespuestaPaginadaColecciones = {
    items: [mockColeccion1],
    total: 1,
    pagina: 1,
    limite: 10,
    total_paginas: 1,
  };

  // Signals reactivos del servicio mock
  const pestanaActivaSignal = signal<PestanaGestion>('temporadas');
  const temporadasSignal = signal<TemporadaItem[]>([mockTemporada1, mockTemporadaInactiva]);
  const totalTemporadasSignal = signal<number>(2);
  const totalPaginasTemporadasSignal = signal<number>(1);
  const temporadasActivasSignal = signal<TemporadaItem[]>([mockTemporada1]);

  const coleccionesSignal = signal<ColeccionItem[]>([mockColeccion1]);
  const totalColeccionesSignal = signal<number>(1);
  const totalPaginasColeccionesSignal = signal<number>(1);

  const cargandoSignal = signal<boolean>(false);
  const guardandoSignal = signal<boolean>(false);
  const errorSignal = signal<string | null>(null);
  const mensajeExitoSignal = signal<string | null>(null);

  const mockServicio = {
    pestanaActiva: pestanaActivaSignal,
    temporadas: temporadasSignal,
    totalTemporadas: totalTemporadasSignal,
    totalPaginasTemporadas: totalPaginasTemporadasSignal,
    temporadasActivasParaSelector: temporadasActivasSignal,
    colecciones: coleccionesSignal,
    totalColecciones: totalColeccionesSignal,
    totalPaginasColecciones: totalPaginasColeccionesSignal,
    cargando: cargandoSignal,
    guardando: guardandoSignal,
    error: errorSignal,
    mensajeExito: mensajeExitoSignal,

    cambiarPestana: vi.fn().mockImplementation((p: PestanaGestion) => {
      pestanaActivaSignal.set(p);
    }),
    cargarTemporadas: vi.fn().mockReturnValue(of(mockListaTemporadas)),
    cargarTemporadasActivasParaSelector: vi.fn().mockReturnValue(of(mockListaTemporadas)),
    cargarColecciones: vi.fn().mockReturnValue(of(mockListaColecciones)),
    crearTemporada: vi.fn().mockReturnValue(of(mockTemporada1)),
    actualizarTemporada: vi.fn().mockReturnValue(of(mockTemporada1)),
    conmutarEstadoTemporada: vi.fn().mockReturnValue(of({ ...mockTemporada1, estado_activo: false })),
    crearColeccion: vi.fn().mockReturnValue(of(mockColeccion1)),
    actualizarColeccion: vi.fn().mockReturnValue(of(mockColeccion1)),
    conmutarEstadoColeccion: vi.fn().mockReturnValue(of({ ...mockColeccion1, estado_activo: false })),
    limpiarMensajes: vi.fn().mockImplementation(() => {
      errorSignal.set(null);
      mensajeExitoSignal.set(null);
    }),
  };

  const mockLoginService = {
    usuarioActual: usuarioActualSignal,
  };

  beforeEach(async () => {
    usuarioActualSignal.set(mockAdminUser);
    pestanaActivaSignal.set('temporadas');
    temporadasSignal.set([mockTemporada1, mockTemporadaInactiva]);
    coleccionesSignal.set([mockColeccion1]);
    cargandoSignal.set(false);
    guardandoSignal.set(false);
    errorSignal.set(null);
    mensajeExitoSignal.set(null);

    await TestBed.configureTestingModule({
      imports: [TemporadasColeccionesAdminComponent],
      providers: [
        provideRouter([]),
        { provide: TemporadasColeccionesAdminService, useValue: mockServicio },
        { provide: LoginService, useValue: mockLoginService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(TemporadasColeccionesAdminComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe crearse correctamente el componente (# AC-14)', () => {
    expect(component).toBeTruthy();
    expect(component.esAdmin()).toBe(true);
    expect(component.esEncargado()).toBe(false);
  });

  it('debe exhibir la denominacion oficial exacta en el titulo H1 y en las migas de pan (# AC-14)', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const h1 = compiled.querySelector('h1');
    expect(h1?.textContent?.trim()).toBe('Gestionar temporadas y colecciones');
    expect(compiled.textContent).toContain('GESTIONAR TEMPORADAS Y COLECCIONES');
    expect(compiled.textContent).toContain('Volver al Panel Principal');
  });

  it('debe mostrar botones de mutacion al administrador y ocultarlos al encargado (# AC-15)', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    // Administrador: boton de nueva temporada visible
    const btnNuevaTemp = compiled.querySelector('#btn-nueva-temporada');
    expect(btnNuevaTemp).toBeTruthy();

    // Cambiar a rol encargado
    usuarioActualSignal.set(mockEncargadoUser);
    fixture.detectChanges();

    expect(component.esAdmin()).toBe(false);
    expect(component.esEncargado()).toBe(true);

    const btnNuevaTempEncargado = compiled.querySelector('#btn-nueva-temporada');
    expect(btnNuevaTempEncargado).toBeNull();
    expect(compiled.textContent).toContain('Solo lectura');
  });

  it('debe permitir conmutar entre pestanas reactivas de Temporadas y Colecciones (# AC-16)', () => {
    const tabColecciones = fixture.debugElement.query(By.css('#tab-colecciones'));
    expect(tabColecciones).toBeTruthy();

    tabColecciones.triggerEventHandler('click', null);
    fixture.detectChanges();

    expect(mockServicio.cambiarPestana).toHaveBeenCalledWith('colecciones');
    expect(mockServicio.cargarColecciones).toHaveBeenCalled();
  });

  it('debe filtrar reactivamente por busqueda de texto con debounce (# AC-17)', async () => {
    vi.useFakeTimers();
    const inputBusqueda = fixture.debugElement.query(By.css('#input-busqueda-temporada'));
    expect(inputBusqueda).toBeTruthy();

    inputBusqueda.nativeElement.value = 'Invierno';
    inputBusqueda.nativeElement.dispatchEvent(new Event('input'));

    expect(component.busquedaTemporada()).toBe('Invierno');
    // Antes del debounce no debe haberse llamado con el filtro
    vi.advanceTimersByTime(350);

    expect(mockServicio.cargarTemporadas).toHaveBeenCalled();
    vi.useRealTimers();
  });

  it('debe abrir el modal de crear temporada y validar que fecha_fin > fecha_inicio (# AC-18)', () => {
    component.abrirModalCrearTemporada();
    fixture.detectChanges();

    expect(component.modalTemporadaAbierto()).toBe(true);
    expect(component.modoEdicionTemporada()).toBe(false);

    // Fechas invalidas: fin anterior al inicio
    component.formTemporada.patchValue({
      nombre: 'Temporada Rango Invalido',
      anio: 2026,
      fecha_inicio: '2026-10-01',
      fecha_fin: '2026-05-01',
    });
    component.formTemporada.markAllAsTouched();
    fixture.detectChanges();

    expect(component.formTemporada.errors?.['fechasInvalidas']).toBeTruthy();

    const compiled = fixture.nativeElement as HTMLElement;
    const btnGuardar = compiled.querySelector('#btn-guardar-temporada') as HTMLButtonElement;
    expect(btnGuardar.disabled).toBe(true);
    expect(compiled.textContent).toContain('estrictamente posterior a la fecha de inicio');
  });

  it('debe crear exitosamente una temporada con fechas validas (# AC-19)', () => {
    component.abrirModalCrearTemporada();
    fixture.detectChanges();

    component.formTemporada.patchValue({
      nombre: 'Primavera - Verano 2027',
      tipo: 'primavera_verano',
      anio: 2027,
      fecha_inicio: '2027-09-21',
      fecha_fin: '2027-12-21',
      estado_activo: true,
    });
    fixture.detectChanges();

    expect(component.formTemporada.valid).toBe(true);

    component.guardarTemporada();
    expect(mockServicio.crearTemporada).toHaveBeenCalled();
  });

  it('debe abrir el modal en modo edicion con datos precargados (# AC-20)', () => {
    component.abrirModalEditarTemporada(mockTemporada1);
    fixture.detectChanges();

    expect(component.modalTemporadaAbierto()).toBe(true);
    expect(component.modoEdicionTemporada()).toBe(true);
    expect(component.formTemporada.get('nombre')?.value).toBe('Otono - Invierno 2026');

    component.guardarTemporada();
    expect(mockServicio.actualizarTemporada).toHaveBeenCalledWith(
      1,
      expect.objectContaining({ nombre: 'Otono - Invierno 2026' })
    );
  });

  it('debe solicitar y confirmar la conmutacion de estado (baja logica) (# AC-21)', () => {
    component.solicitarConmutarEstado('temporada', 1, 'Otono - Invierno 2026', true);
    fixture.detectChanges();

    expect(component.modalConfirmarEstadoAbierto()).toBe(true);
    expect(component.elementoParaConmutar()?.estado_activo).toBe(true);

    component.confirmarConmutarEstado();
    expect(mockServicio.conmutarEstadoTemporada).toHaveBeenCalledWith(1, false);
  });

  it('debe gestionar creacion de coleccion vinculada a temporada matriz (# AC-22)', () => {
    component.cambiarPestana('colecciones');
    pestanaActivaSignal.set('colecciones');
    fixture.detectChanges();

    component.abrirModalCrearColeccion();
    fixture.detectChanges();

    expect(component.modalColeccionAbierto()).toBe(true);

    component.formColeccion.patchValue({
      id_temporada: 1,
      nombre: 'Capsula Lana Merina',
      descripcion: 'Tejidos premium',
    });
    fixture.detectChanges();

    expect(component.formColeccion.valid).toBe(true);

    component.guardarColeccion();
    expect(mockServicio.crearColeccion).toHaveBeenCalledWith(
      expect.objectContaining({
        id_temporada: 1,
        nombre: 'Capsula Lana Merina',
      })
    );
  });

  it('debe exhibir banner contextual de error y permitir cerrarlo (# AC-23)', () => {
    component.errorBanner.set('Conflicto: Ya existe una temporada con esa denominacion.');
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Atencion Requerida');
    expect(compiled.textContent).toContain('Conflicto: Ya existe una temporada con esa denominacion.');

    component.limpiarBanners();
    fixture.detectChanges();

    expect(component.errorBanner()).toBeNull();
  });
});
