import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { signal } from '@angular/core';
import { afterEach, describe, expect, it } from 'vitest';
import { PerfilEmpleadoComponent } from './perfil-empleado.component';
import { LoginService } from '../../cu02_iniciar_sesion/servicios/login.service';

/** Payloads literales de GET /api/v1/mi-perfil-empleado. */
const ADMIN = {
  id_usuario: 40,
  email: 'admin@menshopping.com',
  nombres: 'Administración',
  apellidos: 'Menshopping',
  telefono: null,
  rol: 'administrador',
  empresa: { codigo: 'menshopping', nombre: 'Menshopping', moneda: 'BOB' },
  todas_las_sucursales: true,
  sucursales: [],
  ultimo_acceso: null,
};
const CAJERO = {
  ...ADMIN,
  id_usuario: 42,
  email: 'cajero.santacruz@menshopping.com',
  rol: 'cajero',
  todas_las_sucursales: false,
  sucursales: [{ id_sucursal: 7, nombre: 'Menshopping Santa Cruz', es_principal: true }],
};

describe('PerfilEmpleadoComponent', () => {
  let fixture: ComponentFixture<PerfilEmpleadoComponent>;
  let http: HttpTestingController;
  const raiz = () => fixture.nativeElement as HTMLElement;
  const texto = (sel: string) => raiz().querySelector(sel)?.textContent ?? '';

  async function crear(perfil: object): Promise<void> {
    await TestBed.configureTestingModule({
      imports: [PerfilEmpleadoComponent],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: LoginService, useValue: { usuarioActual: signal(null) } },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(PerfilEmpleadoComponent);
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    http.expectOne('/api/v1/mi-perfil-empleado').flush(perfil);
    fixture.detectChanges();
  }

  afterEach(() => {
    http.verify();
    TestBed.resetTestingModule();
  });

  it('muestra la empresa del empleado, sin textos fijos de otra tienda', async () => {
    await crear(ADMIN);
    expect(texto('#perfil-empresa')).toContain('Menshopping');
    expect(texto('#perfil-empresa')).toContain('BOB');
    expect(texto('#perfil-rol')).toContain('Administrador');
    expect(texto('#perfil-sucursales')).toContain('Todas las sucursales');
    expect(raiz().textContent?.toLowerCase()).not.toContain('fashion store');
    expect(raiz().querySelector('#btn-volver-perfil')?.getAttribute('href')).toBe('/admin');
  });

  it('el cajero ve sus sucursales y vuelve a la caja', async () => {
    await crear(CAJERO);
    expect(texto('#perfil-sucursales')).toContain('Menshopping Santa Cruz');
    expect(texto('#perfil-sucursales')).toContain('principal');
    expect(raiz().querySelector('#btn-volver-perfil')?.getAttribute('href')).toBe('/admin/pos');
  });

  it('guarda sus datos con PATCH y refleja la respuesta', async () => {
    await crear(ADMIN);
    const tel = raiz().querySelector('#perfil-input-telefono') as HTMLInputElement;
    tel.value = '+591 70000000';
    tel.dispatchEvent(new Event('input'));
    (raiz().querySelector('#btn-guardar-datos') as HTMLButtonElement).click();
    const req = http.expectOne('/api/v1/mi-perfil-empleado');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body.telefono).toBe('+591 70000000');
    req.flush({ ...ADMIN, telefono: '+591 70000000' });
    fixture.detectChanges();
    expect(texto('#perfil-exito')).toContain('Datos guardados');
  });

  it('cambia la contraseña solo si las nuevas coinciden', async () => {
    await crear(ADMIN);
    const escribir = (id: string, v: string) => {
      const el = raiz().querySelector(id) as HTMLInputElement;
      el.value = v;
      el.dispatchEvent(new Event('input'));
    };
    escribir('#perfil-contrasena-actual', 'ClaveActual2026');
    escribir('#perfil-contrasena-nueva', 'NuevaClave2027');
    escribir('#perfil-contrasena-repetir', 'Distinta2027');
    (raiz().querySelector('#btn-cambiar-contrasena') as HTMLButtonElement).click();
    fixture.detectChanges();
    http.expectNone('/api/v1/mi-perfil-empleado/contrasena');
    expect(raiz().querySelector('#perfil-no-coinciden')).toBeTruthy();

    escribir('#perfil-contrasena-repetir', 'NuevaClave2027');
    (raiz().querySelector('#btn-cambiar-contrasena') as HTMLButtonElement).click();
    const req = http.expectOne('/api/v1/mi-perfil-empleado/contrasena');
    expect(req.request.body).toEqual({ contrasena_actual: 'ClaveActual2026', contrasena_nueva: 'NuevaClave2027' });
    req.flush(null, { status: 204, statusText: 'No Content' });
    fixture.detectChanges();
    expect(texto('#perfil-exito')).toContain('Contraseña cambiada');
  });

  it('muestra el error del servidor si la contraseña actual no es correcta', async () => {
    await crear(ADMIN);
    for (const [id, v] of [['#perfil-contrasena-actual', 'Mala1234'], ['#perfil-contrasena-nueva', 'NuevaClave2027'], ['#perfil-contrasena-repetir', 'NuevaClave2027']]) {
      const el = raiz().querySelector(id) as HTMLInputElement;
      el.value = v;
      el.dispatchEvent(new Event('input'));
    }
    (raiz().querySelector('#btn-cambiar-contrasena') as HTMLButtonElement).click();
    http.expectOne('/api/v1/mi-perfil-empleado/contrasena').flush(
      { detail: 'La contraseña actual no es correcta.', code: 'CONTRASENA_ACTUAL_INCORRECTA' },
      { status: 400, statusText: 'Bad Request' },
    );
    fixture.detectChanges();
    expect(texto('#perfil-error')).toContain('La contraseña actual no es correcta');
  });
});
