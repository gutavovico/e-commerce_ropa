import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ActivatedRouteSnapshot, Router, RouterStateSnapshot, UrlTree, provideRouter } from '@angular/router';
import { firstValueFrom, isObservable, of } from 'rxjs';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { TenantService } from './tenant.service';
import { TIENDA_FASHION } from './tenant.testing';
import { RegistroEnTiendaComponent } from './registro-en-tienda.component';
import { authInterceptor } from '../interceptors/auth.interceptor';
import { tenantGuard } from '../guards/tenant.guard';
import { LoginService } from '../../modules/autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import { UsuarioSesion } from '../../modules/autenticacion_seguridad/cu02_iniciar_sesion/modelos/login.dto';

/** Pruebas de P2-CU02 en la web (spec §B.4). Las respuestas son payloads literales del backend. */

const CLIENTE: UsuarioSesion = {
  id_usuario: 2, email: 'clienta@ejemplo.com', nombres: 'Ana', apellidos: 'Pérez', rol: 'cliente', token: 'x.y.z',
};
const CAJERO_OTRA_EMPRESA: UsuarioSesion = {
  id_usuario: 30, email: 'cajero@menshopping.com', nombres: 'Luis', apellidos: 'Gil', rol: 'cajero', token: 'x.y.z',
  tenant: { codigo: 'menshopping', nombre: 'Menshopping' },
};

describe('P2-CU02 · portal de tienda (web)', () => {
  let tenant: TenantService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    tenant = TestBed.inject(TenantService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
    localStorage.clear();
    sessionStorage.clear();
  });

  // ------------------------------------------------------------------ TenantService.ruta
  it('antepone el código de la tienda a las rutas del cliente dentro del portal', () => {
    tenant.tenantActual.set(TIENDA_FASHION);
    expect(tenant.ruta('/bolsa')).toEqual(['/', 'fashionstore', 'bolsa']);
    expect(tenant.ruta(['/productos', 5])).toEqual(['/', 'fashionstore', 'productos', 5]);
    expect(tenant.ruta('/')).toEqual(['/', 'fashionstore']);
  });

  it('fuera de un portal devuelve la ruta sin prefijo', () => {
    expect(tenant.ruta('/login')).toEqual(['/login']);
    expect(tenant.ruta(['/productos', 5])).toEqual(['/productos', 5]);
  });

  it('al navegar fuera del portal se olvida la tienda', async () => {
    tenant.tenantActual.set(TIENDA_FASHION);
    TestBed.inject(Router).resetConfig([{ path: 'login', children: [] }]);
    await TestBed.inject(Router).navigateByUrl('/login');
    expect(tenant.tenantActual()).toBeNull();
  });

  // ------------------------------------------------------------------ authInterceptor
  it('envía X-Tenant a la API solo dentro del portal', () => {
    const cliente = TestBed.inject(HttpClient);
    cliente.get('/api/v1/productos').subscribe();
    expect(http.expectOne('/api/v1/productos').request.headers.has('X-Tenant')).toBe(false);

    tenant.tenantActual.set(TIENDA_FASHION);
    cliente.get('/api/v1/productos').subscribe();
    expect(http.expectOne('/api/v1/productos').request.headers.get('X-Tenant')).toBe('fashionstore');
  });

  it('un 403 CLIENTE_NO_REGISTRADO pide «Registrarme en esta tienda»', () => {
    tenant.tenantActual.set(TIENDA_FASHION);
    TestBed.inject(HttpClient).get('/api/v1/carrito').subscribe({ error: () => undefined });
    http.expectOne('/api/v1/carrito').flush(
      { detail: 'Para comprar o reservar en esta tienda primero debes registrarte en ella.', code: 'CLIENTE_NO_REGISTRADO' },
      { status: 403, statusText: 'Forbidden' }
    );
    expect(tenant.registroSolicitado()).toBe(true);
  });

  // ------------------------------------------------------------------ tenantGuard
  async function ejecutarGuard(codigo: string): Promise<boolean | UrlTree> {
    const ruta = { paramMap: new Map([['codigo', codigo]]) } as unknown as ActivatedRouteSnapshot;
    const resultado = TestBed.runInInjectionContext(() => tenantGuard(ruta, {} as RouterStateSnapshot));
    const valor = isObservable(resultado) ? firstValueFrom(resultado) : Promise.resolve(resultado);
    return (await valor) as boolean | UrlTree;
  }

  it('tienda inexistente → directorio con aviso', async () => {
    const promesa = ejecutarGuard('no-existe');
    http.expectOne('/api/v1/tenants/no-existe').flush(
      { detail: 'No existe la tienda «no-existe».', code: 'TENANT_NO_ENCONTRADO' },
      { status: 404, statusText: 'Not Found' }
    );
    const destino = (await promesa) as UrlTree;
    expect(TestBed.inject(Router).serializeUrl(destino)).toBe('/?aviso=tienda-inexistente');
  });

  it('tienda disponible → entra y la fija como actual', async () => {
    const promesa = ejecutarGuard('fashionstore');
    http.expectOne('/api/v1/tenants/fashionstore').flush({ codigo: 'fashionstore', nombre: 'FASHION STORE' });
    expect(await promesa).toBe(true);
    expect(tenant.tenantActual()).toEqual(TIENDA_FASHION);
  });

  it('A5: un empleado de otra empresa va a su panel', async () => {
    TestBed.inject(LoginService).usuarioActual.set(CAJERO_OTRA_EMPRESA);
    const destino = (await ejecutarGuard('fashionstore')) as UrlTree;
    expect(TestBed.inject(Router).serializeUrl(destino)).toBe('/admin/pos');
  });

  // ------------------------------------------------------------------ RegistroEnTiendaComponent
  it('«Registrarme en esta tienda» registra la cuenta actual y actualiza sus tiendas', () => {
    TestBed.inject(LoginService).usuarioActual.set(CLIENTE);
    tenant.tenantActual.set(TIENDA_FASHION);
    tenant.misEmpresas.set([]);

    const fixture = TestBed.createComponent(RegistroEnTiendaComponent);
    fixture.detectChanges();
    const boton = Array.from((fixture.nativeElement as HTMLElement).querySelectorAll('button'))
      .find((b) => b.textContent?.includes('Registrarme en esta tienda'));
    expect(boton).toBeDefined();

    boton!.click();
    const peticion = http.expectOne('/api/v1/mis-empresas');
    expect(peticion.request.method).toBe('POST');
    expect(peticion.request.headers.get('X-Tenant')).toBe('fashionstore');
    peticion.flush({ empresa: { codigo: 'fashionstore', nombre: 'FASHION STORE' }, registrado_ahora: true });

    expect(tenant.misEmpresas()).toEqual([TIENDA_FASHION]);
    expect(tenant.estaRegistradoEnTienda()).toBe(true);
  });

  it('el aviso no aparece para un cliente ya registrado en la tienda', () => {
    TestBed.inject(LoginService).usuarioActual.set(CLIENTE);
    tenant.tenantActual.set(TIENDA_FASHION);
    tenant.misEmpresas.set([TIENDA_FASHION]);
    const fixture = TestBed.createComponent(RegistroEnTiendaComponent);
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).textContent?.trim()).toBe('');
    expect(of(true)).toBeTruthy();
  });
});
