import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter, Router } from '@angular/router';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { of } from 'rxjs';
import { CobroCajaComponent } from './cobro-caja.component';
import { CajaService } from '../../servicios/caja.service';
import { LoginService } from '../../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import {
  CobroCajaResponse,
  OrdenPendiente,
} from '../../modelos/caja.dto';

describe('CobroCajaComponent [CU17: Registrar cobro en caja]', () => {
  let component: CobroCajaComponent;
  let fixture: ComponentFixture<CobroCajaComponent>;
  let cajaService: CajaService;
  let router: Router;

  const mockOrden: OrdenPendiente = {
    id_venta: 101,
    numero_comprobante: 'FS-2026-000101',
    fecha_venta: '2026-09-28T14:00:00Z',
    id_sucursal: 1,
    nombre_sucursal: 'Boutique Central',
    cliente_nombre: 'Luciana Mendoza',
    tipo_venta: 'presencial',
    estado: 'pendiente',
    subtotal: 500,
    descuento: 0,
    total: 500,
    detalles: [
      {
        id_venta_detalle: 1,
        id_variante: 10,
        sku: 'VES-01',
        nombre_producto: 'Vestido Seda',
        talla: 'M',
        color: 'Negro',
        cantidad: 1,
        precio_unitario: 500,
        subtotal_linea: 500,
      },
    ],
  };

  const mockCobroResponse: CobroCajaResponse = {
    id_pago: 201,
    id_venta: 101,
    numero_comprobante: 'FS-2026-000101',
    monto_total: 500,
    monto_recibido: 600,
    cambio_devuelto: 100,
    metodo_pago: 'efectivo',
    estado_venta: 'pagada',
    estado_pago: 'confirmado',
    cajero_nombre: 'Tony Cajero',
    fecha_cobro: '2026-09-28T14:30:00Z',
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CobroCajaComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([
          { path: 'caja/cobro', component: CobroCajaComponent },
          { path: 'caja/reservas', component: class DummyComponent {} },
          { path: 'admin', component: class DummyAdminComponent {} },
        ]),
        CajaService,
        LoginService,
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(CobroCajaComponent);
    component = fixture.componentInstance;
    cajaService = TestBed.inject(CajaService);
    router = TestBed.inject(Router);

    vi.spyOn(cajaService, 'buscarOrdenesPendientes').mockImplementation(() => {
      (cajaService as any)._ordenesPendientes.set([mockOrden]);
      return of({ total: 1, items: [mockOrden] });
    });

    fixture.detectChanges();
  });

  it('debe crearse e inicializarse con el titulo oficial Registrar cobro en caja', () => {
    expect(component).toBeTruthy();
    const h1 = fixture.nativeElement.querySelector('h1');
    expect(h1?.textContent?.trim()).toBe('Registrar cobro en caja');
  });

  it('debe listar las ordenes pendientes cargadas desde el servicio', () => {
    expect(component.ordenes().length).toBe(1);
    const li = fixture.nativeElement.querySelector('li');
    expect(li?.textContent).toContain('FS-2026-000101');
    expect(li?.textContent).toContain('Luciana Mendoza');
  });

  it('debe seleccionar una orden y calcular reactivamente el cambio a devolver', () => {
    component.seleccionarOrden(mockOrden);
    fixture.detectChanges();

    expect(component.ordenSeleccionada()?.id_venta).toBe(101);
    expect(component.montoRecibido()).toBe(500);
    expect(component.cambioDevuelto()).toBe(0);

    // Entregar 700 BOB
    component.onMontoRecibidoChange(700);
    expect(component.cambioDevuelto()).toBe(200);
    expect(component.montoSuficiente()).toBe(true);
    expect(component.puedeCobrar()).toBe(true);

    // Entregar 400 BOB (monto insuficiente)
    component.onMontoRecibidoChange(400);
    expect(component.cambioDevuelto()).toBe(0);
    expect(component.montoSuficiente()).toBe(false);
    expect(component.puedeCobrar()).toBe(false);
  });

  it('debe despachar el cobro mediante click real en el DOM sobre #btn-confirmar-cobro-caja', () => {
    vi.spyOn(cajaService, 'cobrarOrden').mockReturnValue(of(mockCobroResponse));

    component.seleccionarOrden(mockOrden);
    component.onMontoRecibidoChange(600);
    fixture.detectChanges();

    const btnCobro = fixture.nativeElement.querySelector('#btn-confirmar-cobro-caja');
    expect(btnCobro).toBeTruthy();
    expect(btnCobro.disabled).toBe(false);

    // Despacho de clic real en el DOM
    btnCobro.click();
    fixture.detectChanges();

    expect(cajaService.cobrarOrden).toHaveBeenCalledWith(101, {
      id_venta: 101,
      monto_recibido: 600,
      metodo_pago: 'efectivo',
      observaciones: undefined,
    });

    expect(component.comprobanteExito()?.numero_comprobante).toBe('FS-2026-000101');
  });

  it('debe navegar hacia /caja/reservas mediante directiva dual en pestana de navegacion', () => {
    const navigateSpy = vi.spyOn(router, 'navigateByUrl');
    const tabReservas = fixture.nativeElement.querySelector('a[href="/caja/reservas"]');
    expect(tabReservas).toBeTruthy();

    tabReservas.click();

    expect(navigateSpy).toHaveBeenCalledWith('/caja/reservas');
  });
});
