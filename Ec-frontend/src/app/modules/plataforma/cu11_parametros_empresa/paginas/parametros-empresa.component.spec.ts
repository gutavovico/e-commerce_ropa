import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { ParametrosEmpresaComponent, AVISO_DESACTIVAR_OFFLINE } from './parametros-empresa.component';
import { LoginService } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import { signal } from '@angular/core';

/** Payload literal de GET /api/v1/admin/configuracion (P2-CU11). */
const RESPUESTA = {
  moneda: 'EUR',
  zona_horaria: 'Europe/Madrid',
  horas_vencimiento_reserva: 24,
  dias_cambio_prenda: 15,
  operacion_offline_habilitada: true,
  dias_antiguedad_offline: 7,
  actualizado_en: '2026-11-08T00:00:00Z',
};

describe('ParametrosEmpresaComponent (P2-CU11)', () => {
  let fixture: ComponentFixture<ParametrosEmpresaComponent>;
  let component: ParametrosEmpresaComponent;
  let http: HttpTestingController;

  const raiz = () => fixture.nativeElement as HTMLElement;
  const texto = () => raiz().textContent ?? '';
  const escribir = (id: string, valor: number) => {
    const input = raiz().querySelector(`#${id}`) as HTMLInputElement;
    input.value = String(valor);
    input.dispatchEvent(new Event('input'));
    fixture.detectChanges();
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ParametrosEmpresaComponent],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: LoginService, useValue: { usuarioActual: signal(null) } },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(ParametrosEmpresaComponent);
    component = fixture.componentInstance;
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    http.expectOne('/api/v1/admin/configuracion').flush(RESPUESTA);
    fixture.detectChanges();
  });

  afterEach(() => http.verify());

  it('muestra los parámetros; moneda y zona horaria son de solo lectura', () => {
    expect(raiz().querySelector('#config-moneda')?.textContent).toContain('EUR');
    expect(raiz().querySelector('#config-zona')?.textContent).toContain('Europe/Madrid');
    expect(raiz().querySelector('input#config-moneda')).toBeNull();
    expect((raiz().querySelector('#config-horas') as HTMLInputElement).value).toBe('24');
    expect((raiz().querySelector('#config-dias-cambio') as HTMLInputElement).value).toBe('15');
    expect((raiz().querySelector('#config-offline') as HTMLInputElement).checked).toBe(true);
    expect(texto()).toContain('Volver al Panel Principal');
  });

  it('guarda los cuatro editables y refleja la respuesta del servidor', () => {
    escribir('config-horas', 48);
    (raiz().querySelector('#btn-guardar-config') as HTMLButtonElement).click();

    const req = http.expectOne('/api/v1/admin/configuracion');
    expect(req.request.method).toBe('PUT');
    expect(req.request.body).toEqual({
      horas_vencimiento_reserva: 48,
      dias_cambio_prenda: 15,
      operacion_offline_habilitada: true,
      dias_antiguedad_offline: 7,
    });
    req.flush({ ...RESPUESTA, horas_vencimiento_reserva: 48, actualizado_en: '2026-11-09T12:00:00Z' });
    fixture.detectChanges();

    expect(raiz().querySelector('#config-exito')?.textContent).toContain('Rige para las operaciones nuevas');
    expect(component.servicio.parametros()?.horas_vencimiento_reserva).toBe(48);
  });

  it('no envía valores fuera de rango (A1)', () => {
    escribir('config-horas', 0);
    escribir('config-dias-cambio', -1);
    (raiz().querySelector('#btn-guardar-config') as HTMLButtonElement).click();
    fixture.detectChanges();
    http.expectNone('/api/v1/admin/configuracion');
    expect(texto()).toContain('Indique entre 1 y 168 horas');
    expect(texto()).toContain('Indique entre 0 y 90 días');
  });

  it('pide confirmación al desactivar la operación sin conexión (A2) y la envía al confirmar', () => {
    const interruptor = raiz().querySelector('#config-offline') as HTMLInputElement;
    interruptor.click();
    fixture.detectChanges();
    expect(raiz().querySelector('#config-aviso-offline')?.textContent).toContain(AVISO_DESACTIVAR_OFFLINE);
    expect(interruptor.checked).toBe(true);
    expect((raiz().querySelector('#btn-guardar-config') as HTMLButtonElement).disabled).toBe(true);

    (raiz().querySelector('#btn-confirmar-desactivar') as HTMLButtonElement).click();
    fixture.detectChanges();
    expect(raiz().querySelector('#config-aviso-offline')).toBeNull();
    expect((raiz().querySelector('#config-dias-offline') as HTMLInputElement).disabled).toBe(true);

    (raiz().querySelector('#btn-guardar-config') as HTMLButtonElement).click();
    const req = http.expectOne('/api/v1/admin/configuracion');
    expect(req.request.body.operacion_offline_habilitada).toBe(false);
    expect(req.request.body.dias_antiguedad_offline).toBe(7);
    req.flush({ ...RESPUESTA, operacion_offline_habilitada: false });
  });

  it('cancelar el aviso mantiene la operación sin conexión', () => {
    (raiz().querySelector('#config-offline') as HTMLInputElement).click();
    fixture.detectChanges();
    component.cancelarDesactivar();
    fixture.detectChanges();
    expect(component.form.controls.operacion_offline_habilitada.value).toBe(true);
    expect(raiz().querySelector('#config-aviso-offline')).toBeNull();
  });

  it('muestra el mensaje del servidor si la suscripción no está vigente', () => {
    (raiz().querySelector('#btn-guardar-config') as HTMLButtonElement).click();
    http.expectOne('/api/v1/admin/configuracion').flush(
      { detail: 'La suscripción de la empresa no está vigente. Renueve el plan para continuar.', code: 'SUSCRIPCION_NO_VIGENTE' },
      { status: 403, statusText: 'Forbidden' },
    );
    fixture.detectChanges();
    expect(raiz().querySelector('#config-error')?.textContent).toContain('no está vigente');
  });
});
