/**
 * Pruebas unitarias para VozReconocimientoService [CU31].
 */

import { TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { VozReconocimientoService } from './voz-reconocimiento.service';

class MockSpeechRecognition {
  continuous = false;
  interimResults = false;
  lang = 'es-BO';
  onstart: (() => void) | null = null;
  onresult: ((event: any) => void) | null = null;
  onerror: ((event: any) => void) | null = null;
  onend: (() => void) | null = null;

  start = vi.fn(() => {
    if (this.onstart) this.onstart();
  });
  stop = vi.fn(() => {
    if (this.onend) this.onend();
  });
  abort = vi.fn();
}

describe('VozReconocimientoService', () => {
  let service: VozReconocimientoService;
  let originalSpeechRecognition: any;
  let originalWebkitSpeechRecognition: any;

  beforeEach(() => {
    originalSpeechRecognition = (window as any).SpeechRecognition;
    originalWebkitSpeechRecognition = (window as any).webkitSpeechRecognition;

    (window as any).SpeechRecognition = MockSpeechRecognition;
    (window as any).webkitSpeechRecognition = MockSpeechRecognition;

    TestBed.configureTestingModule({
      providers: [VozReconocimientoService],
    });

    service = TestBed.inject(VozReconocimientoService);
  });

  afterEach(() => {
    (window as any).SpeechRecognition = originalSpeechRecognition;
    (window as any).webkitSpeechRecognition = originalWebkitSpeechRecognition;
    vi.restoreAllMocks();
  });

  it('debe crearse e inicializarse detectando soporte de Web Speech API', () => {
    expect(service).toBeTruthy();
    expect(service.soportaVoz()).toBe(true);
    expect(service.escuchando()).toBe(false);
    expect(service.transcripcion()).toBe('');
    expect(service.errorVoz()).toBeNull();
  });

  it('debe iniciar la escucha y actualizar la senal escuchando a true', () => {
    service.iniciarEscucha();
    expect(service.escuchando()).toBe(true);
    expect(service.errorVoz()).toBeNull();
  });

  it('debe procesar resultados de voz y actualizar la senal transcripcion', () => {
    service.iniciarEscucha();
    const mockRecInstance = (service as any).recognition;

    const mockEvent = {
      resultIndex: 0,
      results: [
        [{ transcript: 'descargar reporte de ventas' }],
      ],
    };

    mockRecInstance.onresult(mockEvent);
    expect(service.transcripcion()).toBe('descargar reporte de ventas');
  });

  it('debe capturar errores del microfono y reflejarlos en errorVoz', () => {
    service.iniciarEscucha();
    const mockRecInstance = (service as any).recognition;

    mockRecInstance.onerror({ error: 'not-allowed' });
    expect(service.errorVoz()).toBe('not-allowed');
    expect(service.escuchando()).toBe(false);
  });

  it('debe detener la escucha activa', () => {
    service.iniciarEscucha();
    expect(service.escuchando()).toBe(true);

    service.detenerEscucha();
    expect(service.escuchando()).toBe(false);
  });

  it('debe reiniciar el estado de transcripcion y errores', () => {
    service.asignarTextoManual('consulta inventario');
    expect(service.transcripcion()).toBe('consulta inventario');

    service.reiniciar();
    expect(service.transcripcion()).toBe('');
    expect(service.errorVoz()).toBeNull();
  });

  it('debe permitir cambiar el idioma de reconocimiento', () => {
    service.cambiarIdioma('es-ES');
    expect(service.idioma()).toBe('es-ES');
  });
});
