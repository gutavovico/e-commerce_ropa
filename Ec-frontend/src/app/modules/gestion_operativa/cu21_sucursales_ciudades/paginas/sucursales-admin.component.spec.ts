import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { signal } from '@angular/core';
import { of, throwError } from 'rxjs';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { SucursalesAdminComponent, validarCoherenciaHorarios } from './sucursales-admin.component';
import { SucursalesAdminService } from '../servicios/sucursales-admin.service';
import { Ciudad, SucursalAdmin } from '../modelos/sucursal.model';
import { FormControl, FormGroup } from '@angular/forms';

describe('SucursalesAdminComponent (CU21)', () => {
  let fixture: ComponentFixture<SucursalesAdminComponent>;
  let component: SucursalesAdminComponent;

  const mockCiudades: Ciudad[] = [
    {
      id_ciudad: 1,
      nombre: 'Madrid',
      pais: 'Espana',
      creado_en: '2026-01-10T10:00:00Z',
      total_sucursales: 2,
    },
    {
      id_ciudad: 2,
      nombre: 'Barcelona',
      pais: 'Espana',
      creado_en: '2026-01-12T11:00:00Z',
      total_sucursales: 1,
    },
  ];

  const mockSucursales: SucursalAdmin[] = [
    {
      id_sucursal: 10,
      id_ciudad: 1,
      ciudad_nombre: 'Madrid',
      nombre: 'Boutique Serrano Haute Couture',
      direccion: 'Calle de Serrano 45',
      telefono: '+34 910 123 456',
      horario_apertura: '10:00',
      horario_cierre: '20:30',
      activa: true,
      creado_en: '2026-01-15T09:00:00Z',
      total_empleados: 8,
      total_prendas_stock: 120,
      reservas_activas_conteo: 3,
    },
    {
      id_sucursal: 20,
      id_ciudad: 2,
      ciudad_nombre: 'Barcelona',
      nombre: 'Atelier Paseo de Gracia',
      direccion: 'Passeig de Gracia 88',
      telefono: '+34 934 987 654',
      horario_apertura: '10:30',
      horario_cierre: '21:00',
      activa: false,
      creado_en: '2026-01-20T10:00:00Z',
      total_empleados: 0,
      total_prendas_stock: 0,
      reservas_activas_conteo: 0,
    },
  ];

  let mockService: any;

  beforeEach(async () => {
    mockService = {
      ciudades: signal<Ciudad[]>([...mockCiudades]),
      sucursales: signal<SucursalAdmin[]>([...mockSucursales]),
      cargando: signal<boolean>(false),
      guardando: signal<boolean>(false),
      error: signal<string | null>(null),
      mensajeExito: signal<string | null>(null),

      cargarCiudades: vi.fn().mockReturnValue(of(mockCiudades)),
      cargarSucursales: vi.fn().mockReturnValue(of(mockSucursales)),
      crearCiudad: vi.fn().mockReturnValue(of(mockCiudades[0])),
      actualizarCiudad: vi.fn().mockReturnValue(of(mockCiudades[0])),
      eliminarCiudad: vi.fn().mockReturnValue(of({ mensaje: 'Ciudad eliminada' })),
      crearSucursal: vi.fn().mockReturnValue(of(mockSucursales[0])),
      actualizarSucursal: vi.fn().mockReturnValue(of(mockSucursales[0])),
      cambiarEstado: vi.fn().mockReturnValue(of(mockSucursales[0])),
      eliminarSucursal: vi.fn().mockReturnValue(of({ mensaje: 'Sucursal eliminada' })),
      limpiarMensajes: vi.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [SucursalesAdminComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        { provide: SucursalesAdminService, useValue: mockService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(SucursalesAdminComponent);
    component = fixture.componentInstance;
  });

  it('debe inicializarse y cargar los catalogos territoriales y de sucursales', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
    expect(mockService.cargarCiudades).toHaveBeenCalled();
    expect(mockService.cargarSucursales).toHaveBeenCalled();
    expect(component.totalBoutiques()).toBe(2);
    expect(component.totalActivas()).toBe(1);
    expect(component.totalInactivas()).toBe(1);
  });

  it('debe alternar de pestaña entre boutiques y ciudades', () => {
    expect(component.pestanaActiva()).toBe('boutiques');
    component.cambiarPestana('ciudades');
    expect(component.pestanaActiva()).toBe('ciudades');
    component.cambiarPestana('boutiques');
    expect(component.pestanaActiva()).toBe('boutiques');
  });

  it('debe filtrar reactivamente sucursales por ciudad, texto y estado', () => {
    fixture.detectChanges();

    // Sin filtros: ambas presentes
    expect(component.sucursalesFiltradas().length).toBe(2);

    // Filtro por ciudad Madrid (id 1)
    component.actualizarFiltroCiudad(1);
    expect(component.sucursalesFiltradas().length).toBe(1);
    expect(component.sucursalesFiltradas()[0].ciudad_nombre).toBe('Madrid');

    // Filtro por estado inactiva
    component.actualizarFiltroCiudad(null);
    component.actualizarFiltroEstado('inactiva');
    expect(component.sucursalesFiltradas().length).toBe(1);
    expect(component.sucursalesFiltradas()[0].id_sucursal).toBe(20);

    // Filtro por texto
    component.actualizarFiltroEstado('todos');
    component.actualizarFiltroBusqueda('Serrano');
    expect(component.sucursalesFiltradas().length).toBe(1);
    expect(component.sucursalesFiltradas()[0].nombre).toContain('Serrano');
  });

  it('debe validar la coherencia horaria rechazando cierre menor o igual que apertura', () => {
    const formInvalido = new FormGroup(
      {
        horario_apertura: new FormControl('20:00'),
        horario_cierre: new FormControl('10:00'),
      },
      { validators: [validarCoherenciaHorarios] }
    );

    expect(formInvalido.errors?.['horarioInvalido']).toBe(true);

    const formIgual = new FormGroup(
      {
        horario_apertura: new FormControl('10:00'),
        horario_cierre: new FormControl('10:00'),
      },
      { validators: [validarCoherenciaHorarios] }
    );

    expect(formIgual.errors?.['horarioInvalido']).toBe(true);

    const formValido = new FormGroup(
      {
        horario_apertura: new FormControl('10:00'),
        horario_cierre: new FormControl('20:00'),
      },
      { validators: [validarCoherenciaHorarios] }
    );

    expect(formValido.errors).toBeNull();
  });

  it('debe abrir modal para nueva boutique y enviar formulario valido', () => {
    fixture.detectChanges();
    component.abrirModalNuevaBoutique();
    expect(component.modalBoutiqueAbierto()).toBe(true);
    expect(component.boutiqueEnEdicion()).toBeNull();

    component.formularioBoutique.setValue({
      id_ciudad: 1,
      nombre: 'Boutique Salamanca Atelier',
      direccion: 'Calle Goya 15',
      telefono: '+34 912 345 678',
      horario_apertura: '10:00',
      horario_cierre: '20:30',
    });

    component.guardarBoutique();
    expect(mockService.crearSucursal).toHaveBeenCalledWith({
      id_ciudad: 1,
      nombre: 'Boutique Salamanca Atelier',
      direccion: 'Calle Goya 15',
      telefono: '+34 912 345 678',
      horario_apertura: '10:00',
      horario_cierre: '20:30',
    });
    expect(component.modalBoutiqueAbierto()).toBe(false);
  });

  it('debe abrir modal para editar boutique con valores iniciales cargados', () => {
    fixture.detectChanges();
    const boutique = mockSucursales[0];
    component.abrirModalEditarBoutique(boutique);

    expect(component.modalBoutiqueAbierto()).toBe(true);
    expect(component.boutiqueEnEdicion()).toEqual(boutique);
    expect(component.formularioBoutique.value.nombre).toBe(boutique.nombre);

    component.formularioBoutique.patchValue({ nombre: 'Boutique Serrano Renovada' });
    component.guardarBoutique();

    expect(mockService.actualizarSucursal).toHaveBeenCalledWith(10, expect.objectContaining({
      nombre: 'Boutique Serrano Renovada',
    }));
    expect(component.modalBoutiqueAbierto()).toBe(false);
  });

  it('debe capturar error 409 y mostrar notificacion sin cerrar el modal ni limpiar datos (AC-14)', () => {
    fixture.detectChanges();
    mockService.crearSucursal.mockReturnValue(
      throwError(() => new Error('Ya existe una boutique con este nombre en la misma ciudad.'))
    );

    component.abrirModalNuevaBoutique();
    component.formularioBoutique.setValue({
      id_ciudad: 1,
      nombre: 'Boutique Serrano Haute Couture',
      direccion: 'Calle de Serrano 45',
      telefono: '+34 910 123 456',
      horario_apertura: '10:00',
      horario_cierre: '20:30',
    });

    component.guardarBoutique();

    expect(component.notificacionConflicto()).toContain('Ya existe una boutique');
    expect(component.modalBoutiqueAbierto()).toBe(true);
    expect(component.formularioBoutique.value.nombre).toBe('Boutique Serrano Haute Couture');
  });

  it('debe alternar estado de sucursal llamando al servicio', () => {
    fixture.detectChanges();
    const sucursal = mockSucursales[0]; // activa: true
    component.alternarEstadoSucursal(sucursal);

    expect(mockService.cambiarEstado).toHaveBeenCalledWith(10, false);
  });

  it('debe gestionar apertura y guardado de modal para nueva ciudad', () => {
    fixture.detectChanges();
    component.abrirModalNuevaCiudad();
    expect(component.modalCiudadAbierto()).toBe(true);

    component.formularioCiudad.setValue({
      nombre: 'Valencia',
      pais: 'Espana',
    });

    component.guardarCiudad();
    expect(mockService.crearCiudad).toHaveBeenCalledWith({
      nombre: 'Valencia',
      pais: 'Espana',
    });
    expect(component.modalCiudadAbierto()).toBe(false);
  });

  it('debe solicitar y confirmar eliminacion de boutique o ciudad', () => {
    fixture.detectChanges();

    // Solicitar eliminacion de boutique
    component.solicitarEliminacion('boutique', 10, 'Boutique Serrano');
    expect(component.modalEliminarAbierto()).toBe(true);
    expect(component.elementoAEliminar()?.id).toBe(10);

    component.confirmarEliminacion();
    expect(mockService.eliminarSucursal).toHaveBeenCalledWith(10);
    expect(component.modalEliminarAbierto()).toBe(false);

    // Solicitar eliminacion de ciudad
    component.solicitarEliminacion('ciudad', 2, 'Barcelona');
    component.confirmarEliminacion();
    expect(mockService.eliminarCiudad).toHaveBeenCalledWith(2);
  });

  it('debe incluir el enlace de retorno al Panel Principal (/admin)', () => {
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Volver al Panel Principal');
  });
});
