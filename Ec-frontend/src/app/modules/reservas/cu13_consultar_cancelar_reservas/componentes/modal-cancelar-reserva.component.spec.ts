import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { ModalCancelarReservaComponent } from './modal-cancelar-reserva.component';
import { Reserva } from '../modelos/reserva.model';

const RESERVA_MOCK: Reserva = {
  id_reserva: 1,
  codigo_reserva: 'RES-2026-0001',
  estado: 'pendiente',
  fecha_hora_atencion: '2026-10-02T15:30:00Z',
  creado_en: '2026-09-29T10:00:00Z',
  sucursal: { id_sucursal: 1, nombre: 'Atelier Serrano - Madrid', direccion: 'Calle Serrano 48' },
  items: [],
  total_prendas: 1,
  observacion: null,
  puede_cancelar: true,
};

describe('ModalCancelarReservaComponent', () => {
  let fixture: ComponentFixture<ModalCancelarReservaComponent>;
  let componente: ModalCancelarReservaComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ModalCancelarReservaComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ModalCancelarReservaComponent);
    componente = fixture.componentInstance;
    componente.reserva = RESERVA_MOCK;
    fixture.detectChanges();
  });

  it('muestra el código y la boutique de la reserva', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('RES-2026-0001');
    expect(compiled.textContent).toContain('Atelier Serrano - Madrid');
  });

  it('el botón de confirmar está deshabilitado sin un motivo válido', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const boton = compiled.querySelectorAll('button')[1] as HTMLButtonElement;
    expect(boton.disabled).toBe(true);
  });

  it('emite "confirmar" con el motivo recortado cuando es válido', () => {
    const spy = vi.spyOn(componente.confirmar, 'emit');

    (componente as any).actualizarMotivo('  No podré asistir ese día  ');
    fixture.detectChanges();

    (componente as any).onConfirmar();

    expect(spy).toHaveBeenCalledWith('No podré asistir ese día');
  });

  it('no emite "confirmar" con un motivo de menos de 3 caracteres', () => {
    const spy = vi.spyOn(componente.confirmar, 'emit');

    (componente as any).actualizarMotivo('no');
    (componente as any).onConfirmar();

    expect(spy).not.toHaveBeenCalled();
  });

  it('no emite "confirmar" con un motivo de más de 250 caracteres', () => {
    const spy = vi.spyOn(componente.confirmar, 'emit');

    (componente as any).actualizarMotivo('a'.repeat(251));
    (componente as any).onConfirmar();

    expect(spy).not.toHaveBeenCalled();
  });

  it('emite "cerrar" al pulsar "Mantener reserva"', () => {
    const spy = vi.spyOn(componente.cerrar, 'emit');
    (componente as any).onCerrar();
    expect(spy).toHaveBeenCalled();
  });

  it('mientras cancela, no emite ni "cerrar" ni "confirmar"', () => {
    componente.cancelando = true;
    fixture.detectChanges();
    const spyCerrar = vi.spyOn(componente.cerrar, 'emit');
    const spyConfirmar = vi.spyOn(componente.confirmar, 'emit');

    (componente as any).actualizarMotivo('Motivo válido de sobra');
    (componente as any).onCerrar();
    (componente as any).onConfirmar();

    expect(spyCerrar).not.toHaveBeenCalled();
    expect(spyConfirmar).not.toHaveBeenCalled();
  });

  it('muestra el mensaje de error del servidor cuando se indica', () => {
    componente.error = 'La reserva ya fue liquidada.';
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('La reserva ya fue liquidada.');
  });
});
