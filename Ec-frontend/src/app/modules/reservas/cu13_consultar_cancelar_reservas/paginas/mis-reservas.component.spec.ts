import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Location } from '@angular/common';
import { provideRouter } from '@angular/router';
import { signal } from '@angular/core';
import { of, throwError } from 'rxjs';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { MisReservasComponent } from './mis-reservas.component';
import { MisReservasService } from '../servicios/mis-reservas.service';
import { MisReservas, Reserva } from '../modelos/reserva.model';

const RESERVA_PROXIMA: Reserva = {
  id_reserva: 1,
  codigo_reserva: 'RES-2026-0001',
  estado: 'pendiente',
  fecha_hora_atencion: '2026-10-02T15:30:00Z',
  creado_en: '2026-09-29T10:00:00Z',
  sucursal: { id_sucursal: 1, nombre: 'Atelier Serrano - Madrid', direccion: 'Calle Serrano 48' },
  items: [
    {
      id_variante: 7,
      nombre_producto: 'Blusa de satén fluido',
      talla_codigo: '38',
      color_nombre: 'Champagne',
      color_hex: '#E8DFCF',
      imagen_url: null,
      cantidad: 1,
      precio_unitario: '310.00',
    },
  ],
  total_prendas: 1,
  observacion: null,
  puede_cancelar: true,
};

const RESERVA_HISTORIAL: Reserva = {
  ...RESERVA_PROXIMA,
  id_reserva: 2,
  codigo_reserva: 'RES-2026-0002',
  estado: 'vencida',
  puede_cancelar: false,
};

const RESPUESTA_MOCK: MisReservas = {
  resumen: {
    activas: 1,
    proxima: {
      id_reserva: 1,
      fecha_hora_atencion: '2026-10-02T15:30:00Z',
      nombre_sucursal: 'Atelier Serrano - Madrid',
    },
  },
  proximas: [RESERVA_PROXIMA],
  historial: [RESERVA_HISTORIAL],
};

describe('MisReservasComponent (CU13/CU14)', () => {
  let fixture: ComponentFixture<MisReservasComponent>;
  let componente: MisReservasComponent;
  let mockService: any;
  let mockLocation: { back: ReturnType<typeof vi.fn> };

  beforeEach(async () => {
    mockService = {
      misReservas: signal<MisReservas | null>(RESPUESTA_MOCK),
      cargando: signal(false),
      cancelando: signal(false),
      error: signal<string | null>(null),
      cargarMisReservas: vi.fn().mockReturnValue(of(RESPUESTA_MOCK)),
      cancelarReserva: vi.fn().mockReturnValue(of(RESERVA_PROXIMA)),
    };

    mockLocation = { back: vi.fn() };

    await TestBed.configureTestingModule({
      imports: [MisReservasComponent],
      providers: [
        provideRouter([]),
        { provide: MisReservasService, useValue: mockService },
        { provide: Location, useValue: mockLocation },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(MisReservasComponent);
    componente = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('carga mis reservas al iniciar', () => {
    expect(mockService.cargarMisReservas).toHaveBeenCalled();
  });

  it('muestra el resumen y la reserva próxima en la pestaña activa por defecto', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('1 reserva activa');
    expect(compiled.textContent).toContain('RES-2026-0001');
    expect(compiled.textContent).toContain('Blusa de satén fluido');
    expect(compiled.textContent).toContain('Atelier Serrano - Madrid');
  });

  it('el botón "Volver" llama a Location.back()', () => {
    (componente as any).volver();
    expect(mockLocation.back).toHaveBeenCalled();
  });

  it('cambia a la pestaña Historial y muestra la reserva vencida', () => {
    (componente as any).seleccionarPestana('historial');
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('RES-2026-0002');
    expect(compiled.textContent).toContain('Vencida');
  });

  it('solo muestra "Cancelar reserva" cuando puede_cancelar es true', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    // En "próximas" (puede_cancelar: true) debe verse el botón.
    expect(compiled.textContent).toContain('Cancelar reserva');

    (componente as any).seleccionarPestana('historial');
    fixture.detectChanges();
    // En "historial" (puede_cancelar: false) no debe verse.
    const compiladoHistorial = fixture.nativeElement as HTMLElement;
    const botones = Array.from(compiladoHistorial.querySelectorAll('button')).map(
      (b) => b.textContent?.trim()
    );
    expect(botones).not.toContain('Cancelar reserva');
  });

  it('abrir la cancelación muestra el modal con la reserva seleccionada', () => {
    (componente as any).abrirCancelacion(RESERVA_PROXIMA);
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('app-modal-cancelar-reserva')).not.toBeNull();
  });

  it('confirmar la cancelación llama al servicio y cierra el modal al terminar', () => {
    (componente as any).abrirCancelacion(RESERVA_PROXIMA);
    (componente as any).confirmarCancelacion('No podré asistir ese día');

    expect(mockService.cancelarReserva).toHaveBeenCalledWith(1, 'No podré asistir ese día');
    expect((componente as any).reservaACancelar()).toBeNull();
  });

  it('un error al cancelar mantiene el modal abierto para reintentar', () => {
    mockService.cancelarReserva = vi.fn().mockReturnValue(throwError(() => new Error('fallo')));

    (componente as any).abrirCancelacion(RESERVA_PROXIMA);
    (componente as any).confirmarCancelacion('Motivo cualquiera');

    expect((componente as any).reservaACancelar()).not.toBeNull();
  });

  it('muestra el estado de carga mientras no hay reservas todavía', () => {
    mockService.misReservas.set(null);
    mockService.cargando.set(true);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelectorAll('.animate-pulse').length).toBeGreaterThan(0);
  });

  it('muestra el estado vacío con salida al catálogo cuando no hay reservas próximas', () => {
    mockService.misReservas.set({
      resumen: { activas: 0, proxima: null },
      proximas: [],
      historial: [],
    });
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Aún no tienes citas de probador agendadas');
    expect(compiled.textContent).toContain('Explorar Catálogo');
  });

  it('muestra un estado de error con reintento cuando la carga falla sin datos previos', () => {
    mockService.misReservas.set(null);
    mockService.error.set('No fue posible conectar con el atelier.');
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('No fue posible conectar con el atelier.');
    expect(compiled.textContent).toContain('Reintentar');
  });
});
