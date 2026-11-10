import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { RespaldosComponent } from './respaldos.component';
import { nombreDeArchivo } from '../../servicios/respaldos.service';

const EMPRESAS = [
  { id_tenant: 1, codigo: 'fashionstore', nombre: 'FASHION STORE' },
  { id_tenant: 2, codigo: 'menshopping', nombre: 'Menshopping' },
];

describe('RespaldosComponent (RNF18)', () => {
  let fixture: ComponentFixture<RespaldosComponent>;
  let http: HttpTestingController;
  const raiz = () => fixture.nativeElement as HTMLElement;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [RespaldosComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    fixture = TestBed.createComponent(RespaldosComponent);
    fixture.componentRef.setInput('empresas', EMPRESAS);
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:respaldo');
    vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined);
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
  });

  afterEach(() => {
    http.verify();
    vi.restoreAllMocks();
    TestBed.resetTestingModule();
  });

  it('AC-B3: por defecto descarga toda la plataforma y muestra lo que devolvió el servidor', () => {
    (raiz().querySelector('#btn-descargar-respaldo') as HTMLButtonElement).click();
    const peticion = http.expectOne((r) => r.url === '/api/v1/plataforma/respaldos');
    expect(peticion.request.params.has('id_tenant')).toBe(false);
    peticion.flush(new Blob(['-- respaldo']), {
      headers: {
        'Content-Disposition': 'attachment; filename="respaldo-plataforma-20261110-0436.sql"',
        'X-Respaldo-Tablas': '52',
        'X-Respaldo-Filas': '946',
      },
    });
    fixture.detectChanges();
    expect(raiz().querySelector('#resultado-respaldo')?.textContent).toContain('respaldo-plataforma-20261110-0436.sql · 52 tablas · 946 filas');
    expect(HTMLAnchorElement.prototype.click).toHaveBeenCalled();
  });

  it('AC-B4: con una empresa elegida envía su id_tenant', () => {
    (raiz().querySelector('#alcance-empresa') as HTMLInputElement).click();
    fixture.detectChanges();
    const selector = raiz().querySelector('#empresa-respaldo') as HTMLSelectElement;
    selector.value = '2';
    selector.dispatchEvent(new Event('change'));
    fixture.detectChanges();
    (raiz().querySelector('#btn-descargar-respaldo') as HTMLButtonElement).click();
    const peticion = http.expectOne((r) => r.url === '/api/v1/plataforma/respaldos');
    expect(peticion.request.params.get('id_tenant')).toBe('2');
    peticion.flush(new Blob(['-- respaldo']));
  });

  it('AC-B5: muestra el mensaje del servidor cuando el rol no es super administrador', async () => {
    (raiz().querySelector('#btn-descargar-respaldo') as HTMLButtonElement).click();
    http.expectOne((r) => r.url === '/api/v1/plataforma/respaldos').flush(
      new Blob([JSON.stringify({ detail: 'Acceso restringido al Super Administrador de la plataforma.', code: 'ACCESO_DENEGADO' })]),
      { status: 403, statusText: 'Forbidden' }
    );
    await vi.waitFor(() => {
      fixture.detectChanges();
      expect(raiz().querySelector('#error-respaldo')?.textContent).toContain('Acceso restringido');
    });
  });

  it('lee el nombre del archivo de Content-Disposition', () => {
    expect(nombreDeArchivo('attachment; filename="respaldo-menshopping-20261110-0436.sql"')).toBe('respaldo-menshopping-20261110-0436.sql');
    expect(nombreDeArchivo(null)).toBe('respaldo.sql');
  });
});
