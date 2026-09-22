import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { provideLocationMocks } from '@angular/common/testing';
import { ViewportScroller } from '@angular/common';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { routes } from './app.routes';
import { LandingPageComponent } from './public/landing/landing.component';
import { MainLayoutComponent } from './core/layouts/main-layout/main-layout.component';

/**
 * Guardia de enrutamiento.
 *
 * Contexto (2026-09-22): la landing page dejó de ser accesible al introducirse
 * `{ path: '', component: MainLayoutComponent, children: [...] }` por delante de
 * `{ path: '', loadComponent: landing, pathMatch: 'full' }`. Angular resuelve las rutas en
 * orden, así que la URL raíz entraba en el layout y, al no existir ningún hijo con `path: ''`,
 * la landing quedaba inalcanzable. La compilación seguía siendo correcta y ningún test lo veía.
 */
describe('app.routes', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideRouter(routes),
        provideLocationMocks(),
        { provide: ViewportScroller, useValue: { scrollToAnchor: vi.fn() } },
      ],
    });
  });

  it('la URL raíz resuelve al landing page público', async () => {
    const harness = await RouterTestingHarness.create('/');

    expect(harness.routeDebugElement?.componentInstance).toBeInstanceOf(
      LandingPageComponent
    );
  });

  it('declara la landing antes del layout principal, que comparte el path vacío', () => {
    const indiceLanding = routes.findIndex(
      (ruta) => ruta.path === '' && !!ruta.loadComponent
    );
    const indiceLayout = routes.findIndex(
      (ruta) => ruta.path === '' && ruta.component === MainLayoutComponent
    );

    expect(indiceLanding).toBeGreaterThanOrEqual(0);
    expect(indiceLayout).toBeGreaterThanOrEqual(0);
    expect(indiceLanding).toBeLessThan(indiceLayout);
  });

  it('la landing usa pathMatch full para no capturar el resto de secciones', () => {
    const landing = routes.find((ruta) => ruta.path === '' && !!ruta.loadComponent);

    // Sin `full`, el path vacío haría de prefijo y absorbería /inicio, /catalogo, etc.
    expect(landing?.pathMatch).toBe('full');
  });

  it('las 4 pantallas raíz siguen colgando del layout principal', () => {
    const layout = routes.find(
      (ruta) => ruta.path === '' && ruta.component === MainLayoutComponent
    );
    const rutasHijas = (layout?.children ?? []).map((hija) => hija.path);

    expect(rutasHijas).toEqual(
      expect.arrayContaining(['inicio', 'buscar', 'catalogo', 'perfil'])
    );
  });

  it('declara /bolsa como pantalla secundaria, fuera del layout principal', () => {
    // Patrón Hub-and-Spoke: sólo las 4 pantallas raíz cuelgan de MainLayoutComponent y muestran
    // la barra de navegación institucional. La bolsa es una hoja y debe carecer de ella.
    const layout = routes.find(
      (ruta) => ruta.path === '' && ruta.component === MainLayoutComponent
    );
    const hijasDelLayout = (layout?.children ?? []).map((hija) => hija.path);
    expect(hijasDelLayout).not.toContain('bolsa');

    const bolsa = routes.find((ruta) => ruta.path === 'bolsa');
    expect(bolsa).toBeDefined();
    expect(bolsa?.loadComponent).toBeDefined();
  });

  it('protege /bolsa con el guard de autenticación', () => {
    // La bolsa es de cada cliente: sin sesión no hay carrito que mostrar.
    const bolsa = routes.find((ruta) => ruta.path === 'bolsa');
    expect(bolsa?.canActivate).toBeDefined();
    expect(bolsa?.canActivate?.length).toBeGreaterThan(0);
  });

  it('existe una ruta comodín que evita la pantalla en blanco ante una URL desconocida', () => {
    const comodin = routes.find((ruta) => ruta.path === '**');

    expect(comodin).toBeDefined();
    // Debe ir en último lugar o capturaría todo lo declarado a continuación.
    expect(routes[routes.length - 1]).toBe(comodin);
  });
});
