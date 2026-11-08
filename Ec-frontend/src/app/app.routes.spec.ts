import { TestBed } from '@angular/core/testing';
import { Route, provideRouter } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { provideLocationMocks } from '@angular/common/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ViewportScroller } from '@angular/common';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { routes } from './app.routes';
import { cajeroACajaGuard } from './core/guards/role.guard';
import { tenantGuard } from './core/guards/tenant.guard';
import { authGuard } from './core/guards/auth.guard';
import { MainLayoutComponent } from './core/layouts/main-layout/main-layout.component';
import { PortalComponent } from './core/layouts/portal/portal.component';
import { LandingPageComponent } from './public/landing/landing.component';
import { DirectorioComponent } from './modules/plataforma/directorio/paginas/directorio.component';

/**
 * Guardia de enrutamiento.
 *
 * - 2026-09-22: la landing quedó inalcanzable porque el layout (path vacío) se declaró antes que
 *   ella. Angular resuelve las rutas en orden; la compilación seguía correcta y ningún test lo veía.
 * - P2-CU02: la raíz `/` es el directorio de tiendas y el cliente navega en `/{codigo}/...`. La ruta
 *   `:codigo` captura cualquier primer segmento, así que debe ir después de todas las rutas fijas.
 */
const portal = (): Route | undefined => routes.find((ruta) => ruta.path === ':codigo');
const hijosDelPortal = (): Route[] => portal()?.children ?? [];
const layout = (): Route | undefined =>
  hijosDelPortal().find((ruta) => ruta.path === '' && ruta.component === MainLayoutComponent);

describe('app.routes', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideRouter(routes),
        provideLocationMocks(),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: ViewportScroller, useValue: { scrollToAnchor: vi.fn() } },
      ],
    });
  });

  it('P2-CU02: la URL raíz resuelve al directorio de tiendas', async () => {
    const harness = await RouterTestingHarness.create('/');
    expect(harness.routeDebugElement?.componentInstance).toBeInstanceOf(DirectorioComponent);
    TestBed.inject(HttpTestingController).match(() => true);
  });

  it('P2-CU02: la landing de cada tienda es el hijo vacío del portal', async () => {
    const landing = hijosDelPortal().find((r) => r.path === '' && !!r.loadComponent);
    expect(landing).toBeDefined();
    expect(await landing!.loadComponent!()).toBe(LandingPageComponent);
  });

  it('P2-CU02: el directorio usa pathMatch full y va antes que el portal', () => {
    const indiceDirectorio = routes.findIndex((r) => r.path === '' && r.pathMatch === 'full');
    const indicePortal = routes.findIndex((r) => r.path === ':codigo');
    expect(indiceDirectorio).toBe(0);
    expect(indicePortal).toBeGreaterThan(indiceDirectorio);
  });

  it('P2-CU02: el portal va después de todas las rutas fijas y antes del comodín', () => {
    const indicePortal = routes.findIndex((r) => r.path === ':codigo');
    const fijas = routes
      .map((r, i) => ({ path: r.path ?? '', i }))
      .filter(({ path }) => path !== ':codigo' && path !== '**');
    for (const { path, i } of fijas) {
      expect(i, `la ruta '${path}' debe declararse antes de ':codigo'`).toBeLessThan(indicePortal);
    }
    expect(routes.findIndex((r) => r.path === '**')).toBe(routes.length - 1);
  });

  it('P2-CU02: el portal valida la tienda con tenantGuard y aporta solo el aviso de registro', () => {
    expect(portal()?.component).toBe(PortalComponent);
    expect(portal()?.canActivate).toContain(tenantGuard);
  });

  it('P2-CU02 (A14): las rutas antiguas del cliente redirigen al directorio', () => {
    for (const path of ['inicio', 'catalogo', 'bolsa', 'reservas', 'productos/:id', 'pago/:idVenta', 'registro']) {
      const ruta = routes.find((r) => r.path === path);
      expect(ruta?.redirectTo, path).toBe('');
    }
  });

  it('dentro del portal, la landing va antes del layout y usa pathMatch full', () => {
    const hijos = hijosDelPortal();
    const indiceLanding = hijos.findIndex((r) => r.path === '' && !!r.loadComponent);
    const indiceLayout = hijos.findIndex((r) => r.path === '' && r.component === MainLayoutComponent);
    expect(indiceLanding).toBeGreaterThanOrEqual(0);
    expect(indiceLanding).toBeLessThan(indiceLayout);
    // Sin `full`, el path vacío haría de prefijo y absorbería /inicio, /catalogo, etc.
    expect(hijos[indiceLanding].pathMatch).toBe('full');
  });

  it('las 4 pantallas raíz siguen colgando del layout principal (Hub-and-Spoke)', () => {
    const rutasHijas = (layout()?.children ?? []).map((hija) => hija.path);
    expect(rutasHijas).toEqual(expect.arrayContaining(['inicio', 'buscar', 'catalogo', 'perfil']));
  });

  it('/bolsa y /reservas son hojas del portal, fuera del layout y protegidas', () => {
    const hijasDelLayout = (layout()?.children ?? []).map((hija) => hija.path);
    for (const path of ['bolsa', 'reservas']) {
      expect(hijasDelLayout).not.toContain(path);
      const hoja = hijosDelPortal().find((r) => r.path === path);
      expect(hoja?.canActivate).toContain(authGuard);
    }
  });

  it('P2-CU02: el portal tiene su login, registro y recuperación de acceso', () => {
    const paths = hijosDelPortal().map((r) => r.path);
    expect(paths).toEqual(expect.arrayContaining(['login', 'registro', 'recuperar-password']));
  });

  it('CU31-CU32: /admin/pos se declara al nivel raíz, perezosa y con guard de autenticación y roles', () => {
    const pos = routes.find((ruta) => ruta.path === 'admin/pos');
    expect(pos).toBeDefined();
    expect(pos?.loadComponent).toBeDefined();
    expect(pos?.canActivate?.length).toBe(2);
  });

  it('CU31-CU32: el panel /admin y sus rutas sin guard de rol desvían al cajero a su caja', () => {
    for (const path of ['admin', 'admin/atributos', 'admin/productos']) {
      const ruta = routes.find((r) => r.path === path);
      expect(ruta?.canActivate).toContain(cajeroACajaGuard);
    }
  });

  it('existe una ruta comodín al final que evita la pantalla en blanco ante una URL desconocida', () => {
    const comodin = routes.find((ruta) => ruta.path === '**');
    expect(comodin).toBeDefined();
    expect(routes[routes.length - 1]).toBe(comodin);
  });
});
