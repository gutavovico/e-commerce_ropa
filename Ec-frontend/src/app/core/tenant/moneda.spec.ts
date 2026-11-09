import { TestBed } from '@angular/core/testing';
import { Component, signal } from '@angular/core';
import { describe, expect, it, beforeEach } from 'vitest';
import { ImportePipe, MonedaService, SimboloMonedaPipe, formatearImporte, simboloMoneda } from './moneda';
import { TenantService } from './tenant.service';
import { LoginService } from '../../modules/autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';

/** Fix de P2-CU11 (M6, M8): formato boliviano y moneda de la tienda actual. */
describe('moneda de la tienda', () => {
  it('formatea importes con separadores de Bolivia y el símbolo de la moneda', () => {
    expect(formatearImporte('1234.5', 'BOB')).toBe('Bs 1.234,50');
    expect(formatearImporte('120.00')).toBe('Bs 120,00');
    expect(formatearImporte(98765.43, 'USD')).toBe('US$ 98.765,43');
    expect(formatearImporte('-5', 'BOB')).toBe('-Bs 5,00');
    expect(formatearImporte(null)).toBe('');
    expect(formatearImporte('no-es-numero')).toBe('');
    expect(simboloMoneda('USD')).toBe('US$');
  });

  describe('MonedaService y pipes', () => {
    const tenantActual = signal<{ codigo: string; nombre: string; moneda?: 'BOB' | 'USD' } | null>(null);
    const usuarioActual = signal<{ tenant?: { codigo: string; nombre: string; moneda?: 'BOB' | 'USD' } } | null>(null);

    @Component({
      standalone: true,
      imports: [ImportePipe, SimboloMonedaPipe],
      template: `<span id="a">{{ '1500' | importe }}</span><span id="b">{{ '10' | importe: 'USD' }}</span><span id="c">{{ '' | simboloMoneda }}</span>`,
    })
    class Anfitrion {}

    beforeEach(() => {
      tenantActual.set(null);
      usuarioActual.set(null);
      TestBed.configureTestingModule({
        providers: [
          { provide: TenantService, useValue: { tenantActual } },
          { provide: LoginService, useValue: { usuarioActual } },
        ],
      });
    });

    it('usa la moneda del portal, si no la del empleado, y si no BOB', () => {
      const servicio = TestBed.inject(MonedaService);
      expect(servicio.actual()).toBe('BOB');
      usuarioActual.set({ tenant: { codigo: 'b', nombre: 'B', moneda: 'USD' } });
      expect(servicio.actual()).toBe('USD');
      tenantActual.set({ codigo: 'fashionstore', nombre: 'FASHION STORE', moneda: 'BOB' });
      expect(servicio.actual()).toBe('BOB');
    });

    it('el pipe usa la moneda de la tienda o la que se le indique', () => {
      tenantActual.set({ codigo: 'b', nombre: 'B', moneda: 'USD' });
      const fixture = TestBed.createComponent(Anfitrion);
      fixture.detectChanges();
      const el = fixture.nativeElement as HTMLElement;
      expect(el.querySelector('#a')?.textContent).toBe('US$ 1.500,00');
      expect(el.querySelector('#b')?.textContent).toBe('US$ 10,00');
      expect(el.querySelector('#c')?.textContent).toBe('US$');

      tenantActual.set({ codigo: 'fashionstore', nombre: 'FASHION STORE', moneda: 'BOB' });
      fixture.detectChanges();
      expect(el.querySelector('#a')?.textContent).toBe('Bs 1.500,00');
    });
  });
});
