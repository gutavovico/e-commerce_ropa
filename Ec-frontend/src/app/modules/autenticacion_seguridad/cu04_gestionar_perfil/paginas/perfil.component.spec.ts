import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter, Router } from '@angular/router';
import { signal } from '@angular/core';
import { of } from 'rxjs';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { PerfilComponent } from './perfil.component';
import { PerfilService } from '../servicios/perfil.service';
import { LoginService } from '../../cu02_iniciar_sesion/servicios/login.service';
import { PerfilCliente } from '../modelos/perfil.dto';
import { MisReservasService } from '../../../reservas/cu13_consultar_cancelar_reservas/servicios/mis-reservas.service';

describe('PerfilComponent (CU04)', () => {
  const mockPerfil: PerfilCliente = {
    id_usuario: 8402,
    numero_socio: '#8402',
    email: 'ana.valenzuela@studio.es',
    rol: 'cliente',
    fecha_registro: '2021-10-15T12:00:00Z',
    miembro_desde: 'Octubre 2021',
    nombres: 'Ana',
    apellidos: 'Valenzuela',
    telefono: '+34 612 884 901',
    talla_preferida: '38',
    genero: 'femenino',
    acepta_marketing: true,
    resumen_atelier: {
      visitas_registradas: 32,
      boutiques_visitadas: 4,
      preferencia_textil: '100% Seda & Lana',
      estatus_membresia: 'Nivel Platino',
    },
  };

  let mockPerfilService: any;
  let mockLoginService: any;
  let mockMisReservasService: any;
  let router: Router;

  beforeEach(async () => {
    mockPerfilService = {
      perfil: signal<PerfilCliente | null>(mockPerfil),
      cargando: signal<boolean>(false),
      guardando: signal<boolean>(false),
      error: signal<string | null>(null),
      mensajeExito: signal<string | null>(null),
      modalEdicionAbierto: signal<boolean>(false),
      pedidos: signal<any[]>([]),
      cargarPerfil: vi.fn().mockReturnValue(of(mockPerfil)),
      actualizarPerfil: vi.fn().mockReturnValue(of(mockPerfil)),
      abrirModalEdicion: vi.fn(),
      cerrarModalEdicion: vi.fn(),
      limpiarMensajes: vi.fn(),
    };

    mockLoginService = {
      cerrarSesion: vi.fn().mockReturnValue(of(void 0)),
    };

    mockMisReservasService = {
      resumen: signal({ activas: 0, proxima: null }),
      cargando: signal(false),
      cargarMisReservas: vi.fn().mockReturnValue(
        of({ resumen: { activas: 0, proxima: null }, proximas: [], historial: [] })
      ),
    };

    await TestBed.configureTestingModule({
      imports: [PerfilComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        { provide: PerfilService, useValue: mockPerfilService },
        { provide: LoginService, useValue: mockLoginService },
        { provide: MisReservasService, useValue: mockMisReservasService },
      ],
    }).compileComponents();

    router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockImplementation(() => Promise.resolve(true));
  });

  it('debe instanciar el componente correctamente', () => {
    const fixture = TestBed.createComponent(PerfilComponent);
    const comp = fixture.componentInstance;
    expect(comp).toBeTruthy();
  });

  it('debe cargar los datos del perfil al inicializarse', () => {
    const fixture = TestBed.createComponent(PerfilComponent);
    fixture.detectChanges();
    expect(mockPerfilService.cargarPerfil).toHaveBeenCalled();
  });

  it('debe abrir y cerrar el modal de edición de datos', () => {
    const fixture = TestBed.createComponent(PerfilComponent);
    const comp = fixture.componentInstance;
    comp.abrirModal();
    expect(mockPerfilService.abrirModalEdicion).toHaveBeenCalled();

    comp.cerrarModal();
    expect(mockPerfilService.cerrarModalEdicion).toHaveBeenCalled();
  });

  it('debe llamar a cerrarSesion y redirigir a /login', () => {
    const fixture = TestBed.createComponent(PerfilComponent);
    const comp = fixture.componentInstance;
    comp.cerrarSesion();
    expect(mockLoginService.cerrarSesion).toHaveBeenCalled();
    expect(router.navigate).toHaveBeenCalledWith(['/login']);
  });

  it('carga el resumen de reservas al iniciar', () => {
    const fixture = TestBed.createComponent(PerfilComponent);
    fixture.detectChanges();
    expect(mockMisReservasService.cargarMisReservas).toHaveBeenCalled();
  });

  it('la tarjeta de reservas muestra el resumen real y enlaza a /reservas, sin literales de bolsa', () => {
    mockMisReservasService.resumen.set({
      activas: 2,
      proxima: { id_reserva: 5, fecha_hora_atencion: '2026-10-05T16:00:00Z', nombre_sucursal: 'Atelier Serrano - Madrid' },
    });

    const fixture = TestBed.createComponent(PerfilComponent);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Mis Reservas');
    expect(compiled.textContent).toContain('2 reservas activas');
    expect(compiled.textContent).toContain('Atelier Serrano - Madrid');
    expect(compiled.textContent).toContain('VER MIS RESERVAS');
    // El literal de la bolsa que ocultaba una bolsa siempre vacía ya no existe.
    expect(compiled.textContent).not.toContain('Bolsa de Compra');
    expect(compiled.textContent).not.toContain('3 Artículos seleccionados');
    expect(compiled.textContent).not.toContain('IR AL CHECKOUT');

    const enlace = compiled.querySelector('a[routerLink="/reservas"]');
    expect(enlace).not.toBeNull();
  });

  it('la tarjeta de reservas muestra su estado vacío cuando no hay citas agendadas', () => {
    const fixture = TestBed.createComponent(PerfilComponent);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Sin citas agendadas');
  });
});
