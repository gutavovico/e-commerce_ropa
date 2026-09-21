import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, RouterLink } from '@angular/router';
import { By } from '@angular/platform-browser';
import { signal } from '@angular/core';
import { of, throwError } from 'rxjs';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ProveedoresAdminComponent } from './proveedores-admin.component';
import { ProveedoresAdminService } from '../servicios/proveedores-admin.service';
import { LoginService } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import { UsuarioSesion } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/modelos/login.dto';
import {
  FiltrosProveedores,
  ListaPaginadaProveedores,
  ProveedorItemAdmin,
} from '../modelos/proveedor.dto';

describe('ProveedoresAdminComponent (CU25)', () => {
  let fixture: ComponentFixture<ProveedoresAdminComponent>;
  let component: ProveedoresAdminComponent;

  const mockAdminUser: UsuarioSesion = {
    id_usuario: 1,
    email: 'admin.director@fashionstore.com',
    nombres: 'Elena',
    apellidos: 'Montes',
    rol: 'administrador',
    token: 'jwt-token-admin',
  };

  const usuarioActualSignal = signal<UsuarioSesion | null>(mockAdminUser);

  const mockProveedor1: ProveedorItemAdmin = {
    id_proveedor: 10,
    razon_social: 'Textiles Andinos S.A.',
    nit_rut: '1028475029',
    rubro: 'Confeccion y Sastreria',
    contacto_nombre: 'Carlos Gomez',
    telefono: '+591 2 2441122',
    email: 'carlos@textilesandinos.bo',
    direccion: 'Av. Industrial 450',
    ciudad: 'La Paz',
    estado_activo: true,
    creado_en: '2026-09-20T10:00:00Z',
    actualizado_en: '2026-09-20T10:00:00Z',
  };

  const mockProveedorInactivo: ProveedorItemAdmin = {
    id_proveedor: 11,
    razon_social: 'Botones y Avios del Sur S.R.L.',
    nit_rut: '9876543210',
    rubro: 'Avios y Merceria',
    contacto_nombre: 'Ana Morales',
    telefono: '+591 4 4556677',
    email: 'ana@aviosdelsur.com',
    direccion: 'Calle Comercio 123',
    ciudad: 'Cochabamba',
    estado_activo: false,
    creado_en: '2026-09-18T10:00:00Z',
    actualizado_en: '2026-09-21T09:00:00Z',
  };

  const mockListaPaginada: ListaPaginadaProveedores = {
    items: [mockProveedor1, mockProveedorInactivo],
    total: 2,
    pagina: 1,
    limite: 10,
    total_paginas: 1,
  };

  // Signals reactivos del servicio
  const proveedoresSignal = signal<ProveedorItemAdmin[]>([
    mockProveedor1,
    mockProveedorInactivo,
  ]);
  const totalRegistrosSignal = signal<number>(2);
  const paginaActualSignal = signal<number>(1);
  const totalPaginasSignal = signal<number>(1);
  const cargandoSignal = signal<boolean>(false);
  const guardandoSignal = signal<boolean>(false);
  const errorSignal = signal<string | null>(null);
  const mensajeExitoSignal = signal<string | null>(null);
  const filtrosSignal = signal<FiltrosProveedores>({ pagina: 1, limite: 10 });

  const mockProveedoresService = {
    proveedores: proveedoresSignal,
    totalRegistros: totalRegistrosSignal,
    paginaActual: paginaActualSignal,
    totalPaginas: totalPaginasSignal,
    cargando: cargandoSignal,
    guardando: guardandoSignal,
    error: errorSignal,
    mensajeExito: mensajeExitoSignal,
    filtros: filtrosSignal,

    cargarProveedores: vi.fn().mockReturnValue(of(mockListaPaginada)),
    listarProveedores: vi.fn().mockReturnValue(of(mockListaPaginada)),
    crearProveedor: vi.fn().mockReturnValue(of(mockProveedor1)),
    actualizarProveedor: vi.fn().mockReturnValue(of(mockProveedor1)),
    cambiarEstadoProveedor: vi.fn().mockReturnValue(
      of({
        ...mockProveedor1,
        estado_activo: false,
      })
    ),
    limpiarMensajes: vi.fn().mockImplementation(() => {
      errorSignal.set(null);
      mensajeExitoSignal.set(null);
    }),
  };

  const mockLoginService = {
    usuarioActual: usuarioActualSignal,
  };

  beforeEach(async () => {
    vi.clearAllMocks();
    proveedoresSignal.set([mockProveedor1, mockProveedorInactivo]);
    totalRegistrosSignal.set(2);
    paginaActualSignal.set(1);
    totalPaginasSignal.set(1);
    cargandoSignal.set(false);
    guardandoSignal.set(false);
    errorSignal.set(null);
    mensajeExitoSignal.set(null);

    await TestBed.configureTestingModule({
      imports: [ProveedoresAdminComponent],
      providers: [
        provideRouter([]),
        { provide: ProveedoresAdminService, useValue: mockProveedoresService },
        { provide: LoginService, useValue: mockLoginService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ProveedoresAdminComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe crearse e inicializarse correctamente el componente (AC-12)', () => {
    expect(component).toBeTruthy();
    expect(mockProveedoresService.cargarProveedores).toHaveBeenCalled();
    expect(component.esAdmin()).toBe(true);
  });

  it('debe contener el boton de retorno al panel principal con routerLink=/admin (AC-12)', () => {
    const links = fixture.debugElement.queryAll(By.directive(RouterLink));
    const hrefs = links.map((link) => link.injector.get(RouterLink).href);
    expect(hrefs).toContain('/admin');
  });

  it('debe filtrar reactivamente por busqueda de texto con debounce de 300 ms (AC-13)', async () => {
    const inputBusqueda = fixture.nativeElement.querySelector(
      '#input-busqueda-proveedores'
    ) as HTMLInputElement;

    mockProveedoresService.cargarProveedores.mockClear();
    inputBusqueda.value = 'Andinos';
    inputBusqueda.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    expect(component.busquedaTexto()).toBe('Andinos');

    await new Promise((resolve) => setTimeout(resolve, 350));

    expect(mockProveedoresService.cargarProveedores).toHaveBeenCalledWith(
      expect.objectContaining({
        q: 'Andinos',
        pagina: 1,
      })
    );
  });

  it('debe filtrar reactivamente al cambiar el selector de estado (AC-13)', () => {
    mockProveedoresService.cargarProveedores.mockClear();
    component.alCambiarFiltroEstado('activos');

    expect(component.filtroEstado()).toBe('activos');
    expect(mockProveedoresService.cargarProveedores).toHaveBeenCalledWith(
      expect.objectContaining({
        estado_activo: true,
        pagina: 1,
      })
    );
  });

  it('debe filtrar reactivamente al seleccionar un rubro textil (AC-13)', () => {
    mockProveedoresService.cargarProveedores.mockClear();
    component.alCambiarFiltroRubro('Telas y Tejidos');

    expect(component.filtroRubro()).toBe('Telas y Tejidos');
    expect(mockProveedoresService.cargarProveedores).toHaveBeenCalledWith(
      expect.objectContaining({
        rubro: 'Telas y Tejidos',
        pagina: 1,
      })
    );
  });

  it('debe renderizar las filas de proveedores con sus respectivos datos y badges de estado (AC-14)', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Textiles Andinos S.A.');
    expect(compiled.textContent).toContain('1028475029');
    expect(compiled.textContent).toContain('Confeccion y Sastreria');
    expect(compiled.textContent).toContain('Carlos Gomez');
    expect(compiled.textContent).toContain('Botones y Avios del Sur S.R.L.');
    expect(compiled.textContent).toContain('Activo');
    expect(compiled.textContent).toContain('Inactivo');
  });

  it('debe abrir el modal de alta con formulario limpio y validaciones sincronas (AC-15)', () => {
    component.abrirModalCrear();
    expect(component.modalCrearAbierto()).toBe(true);
    expect(component.formCrear.valid).toBe(false);

    // Razon social requerida (min 3)
    component.formCrear.controls.razon_social.setValue('AB');
    expect(component.formCrear.controls.razon_social.invalid).toBe(true);

    component.formCrear.controls.razon_social.setValue('Textilera Moderna S.R.L.');
    expect(component.formCrear.controls.razon_social.valid).toBe(true);

    // NIT requerido (min 5)
    component.formCrear.controls.nit_rut.setValue('123');
    expect(component.formCrear.controls.nit_rut.invalid).toBe(true);

    component.formCrear.controls.nit_rut.setValue('1029384756');
    expect(component.formCrear.controls.nit_rut.valid).toBe(true);

    // Contacto requerido (min 3)
    component.formCrear.controls.contacto_nombre.setValue('Ma');
    expect(component.formCrear.controls.contacto_nombre.invalid).toBe(true);

    component.formCrear.controls.contacto_nombre.setValue('Mario Casas');
    expect(component.formCrear.controls.contacto_nombre.valid).toBe(true);

    // Email con formato valido
    component.formCrear.controls.email.setValue('correo-invalido');
    expect(component.formCrear.controls.email.invalid).toBe(true);

    component.formCrear.controls.email.setValue('contacto@moderna.bo');
    expect(component.formCrear.controls.email.valid).toBe(true);
  });

  it('debe enviar el payload correcto al guardar un nuevo proveedor y recargar el listado (AC-15)', () => {
    component.abrirModalCrear();
    component.formCrear.patchValue({
      razon_social: 'Fabrica de Hilados del Valle',
      nit_rut: '5544332211',
      rubro: 'Telas y Tejidos',
      contacto_nombre: 'Valeria Rivas',
      telefono: '+591 71234567',
      email: 'valeria@hilados.bo',
      ciudad: 'Cochabamba',
      direccion: 'Parque Industrial Lote 5',
    });

    component.guardarNuevoProveedor();

    expect(mockProveedoresService.crearProveedor).toHaveBeenCalledWith(
      expect.objectContaining({
        razon_social: 'Fabrica de Hilados del Valle',
        nit_rut: '5544332211',
        rubro: 'Telas y Tejidos',
        contacto_nombre: 'Valeria Rivas',
        direccion: 'Parque Industrial Lote 5',
      })
    );
    expect(component.modalCrearAbierto()).toBe(false);
  });

  it('debe abrir el modal de edicion con los datos precargados del proveedor seleccionado (AC-16)', () => {
    component.abrirModalEditar(mockProveedor1);

    expect(component.modalEditarAbierto()).toBe(true);
    expect(component.proveedorSeleccionado()?.id_proveedor).toBe(10);
    expect(component.formEditar.controls.razon_social.value).toBe(
      'Textiles Andinos S.A.'
    );
    expect(component.formEditar.controls.nit_rut.value).toBe('1028475029');
    expect(component.formEditar.controls.contacto_nombre.value).toBe('Carlos Gomez');
    expect(component.formEditar.controls.ciudad.value).toBe('La Paz');
  });

  it('debe enviar la actualizacion con el payload modificado al confirmar edicion (AC-16)', () => {
    component.abrirModalEditar(mockProveedor1);
    component.formEditar.patchValue({
      telefono: '+591 2 2999888',
      direccion: 'Nueva Zona Franca Galpon 4',
    });

    component.guardarEdicionProveedor();

    expect(mockProveedoresService.actualizarProveedor).toHaveBeenCalledWith(
      10,
      expect.objectContaining({
        razon_social: 'Textiles Andinos S.A.',
        telefono: '+591 2 2999888',
        direccion: 'Nueva Zona Franca Galpon 4',
      })
    );
    expect(component.modalEditarAbierto()).toBe(false);
  });

  it('debe abrir el modal de confirmacion y conmutar el estado de baja logica / reactivacion (AC-17)', () => {
    component.abrirModalConfirmarEstado(mockProveedor1);
    expect(component.modalConfirmarEstadoAbierto()).toBe(true);
    expect(component.proveedorSeleccionado()?.id_proveedor).toBe(10);

    component.confirmarCambioEstado();

    expect(mockProveedoresService.cambiarEstadoProveedor).toHaveBeenCalledWith(
      10,
      false
    );
    expect(component.modalConfirmarEstadoAbierto()).toBe(false);
  });

  it('debe capturar errores HTTP 409 o 422 de forma no destructiva en el Luxury Banner preservando el formulario (AC-18)', () => {
    mockProveedoresService.crearProveedor.mockReturnValueOnce(
      throwError(() => ({
        status: 409,
        message: 'El NIT/RUT o la razon social ya se encuentran registrados.',
      }))
    );

    component.abrirModalCrear();
    component.formCrear.patchValue({
      razon_social: 'Textiles Andinos S.A.',
      nit_rut: '1028475029',
      rubro: 'Confeccion y Sastreria',
      contacto_nombre: 'Carlos Gomez',
      telefono: '+591 2 2441122',
      email: 'carlos@textilesandinos.bo',
      direccion: 'Av. Industrial 450',
      ciudad: 'La Paz',
    });

    component.guardarNuevoProveedor();

    expect(component.modalCrearAbierto()).toBe(true);
    expect(component.errorBanner()).toContain('registrados');
    expect(component.formCrear.controls.razon_social.value).toBe(
      'Textiles Andinos S.A.'
    );
  });

  it('debe manejar estados de carga, paginacion y empty state (AC-19)', () => {
    // 1. Estado de carga
    cargandoSignal.set(true);
    proveedoresSignal.set([]);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Cargando directorio de proveedores...');

    // 2. Empty state
    cargandoSignal.set(false);
    proveedoresSignal.set([]);
    fixture.detectChanges();
    expect(compiled.textContent).toContain('No se encontraron proveedores');

    // 3. Paginacion
    totalPaginasSignal.set(3);
    paginaActualSignal.set(1);
    component.paginaSiguiente();
    expect(component.paginaActual()).toBe(2);

    component.paginaAnterior();
    expect(component.paginaActual()).toBe(1);
  });
});
