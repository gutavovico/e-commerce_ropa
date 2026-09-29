import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter, Router } from '@angular/router';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { of } from 'rxjs';
import { EntregaReservasComponent } from './entrega-reservas.component';
import { CajaService } from '../../servicios/caja.service';
import { LoginService } from '../../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import {
  ReservaPendienteCaja,
} from '../../modelos/caja.dto';

describe('EntregaReservasComponent [CU18: Atender entrega de reserva en boutique]', () => {
  let component: EntregaReservasComponent;
  let fixture: ComponentFixture<EntregaReservasComponent>;
  let cajaService: CajaService;
  let router: Router;

  const mockReserva: ReservaPendienteCaja = {
    id_reserva: 42,
    codigo_reserva: 'RES-2026-0042',
    id_cliente: 15,
    cliente_nombre: 'Valeria Rios',
    cliente_telefono: '79876543',
    id_sucursal: 1,
    nombre_sucursal: 'Boutique Central',
    fecha_hora_atencion: '2026-09-28T16:00:00Z',
    estado: 'confirmada',
    canal_origen: 'web',
    observacion: 'Prueba de gala',
    prendas: [
      {
        id_reserva_detalle: 1,
        id_variante: 8,
        sku: 'BLU-01',
        nombre_producto: 'Blusa Lino',
        talla: 'M',
        color: 'Blanco',
        cantidad: 1,
        precio_unitario: 320,
        ubicacion_percha: 'Percha Fitting 3',
      },
    ],
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EntregaReservasComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([
          { path: 'caja/reservas', component: EntregaReservasComponent },
          { path: 'caja/cobro', component: class DummyCobroComponent {} },
          { path: 'admin', component: class DummyAdminComponent {} },
        ]),
        CajaService,
        LoginService,
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(EntregaReservasComponent);
    component = fixture.componentInstance;
    cajaService = TestBed.inject(CajaService);
    router = TestBed.inject(Router);

    vi.spyOn(cajaService, 'buscarReservasPendientes').mockImplementation(() => {
      (cajaService as any)._reservasPendientes.set([mockReserva]);
      return of({ total: 1, items: [mockReserva] });
    });

    fixture.detectChanges();
  });

  it('debe crearse e inicializarse con el titulo oficial Atender entrega de reserva en boutique', () => {
    expect(component).toBeTruthy();
    const h1 = fixture.nativeElement.querySelector('h1');
    expect(h1?.textContent?.trim()).toBe('Atender entrega de reserva en boutique');
  });

  it('debe listar las reservas activas cargadas desde el servicio', () => {
    expect(component.reservas().length).toBe(1);
    const li = fixture.nativeElement.querySelector('li');
    expect(li?.textContent).toContain('RES-2026-0042');
    expect(li?.textContent).toContain('Valeria Rios');
  });

  it('debe seleccionar una reserva y mostrar el detalle de prendas apartadas y percha', () => {
    component.seleccionarReserva(mockReserva);
    fixture.detectChanges();

    expect(component.reservaSeleccionada()?.id_reserva).toBe(42);
    const detalleTexto = fixture.nativeElement.textContent;
    expect(detalleTexto).toContain('Blusa Lino');
    expect(detalleTexto).toContain('Percha Fitting 3');
  });

  it('debe confirmar la entrega mediante click real en el DOM sobre #btn-confirmar-entrega-reserva', () => {
    vi.spyOn(cajaService, 'confirmarEntrega').mockReturnValue(
      of({
        id_reserva: 42,
        codigo_reserva: 'RES-2026-0042',
        estado: 'atendida',
        mensaje: 'Entrega confirmada',
      })
    );

    component.seleccionarReserva(mockReserva);
    fixture.detectChanges();

    const btnConfirmar = fixture.nativeElement.querySelector('#btn-confirmar-entrega-reserva');
    expect(btnConfirmar).toBeTruthy();

    btnConfirmar.click();
    fixture.detectChanges();

    expect(cajaService.confirmarEntrega).toHaveBeenCalledWith(42, {
      observaciones: undefined,
    });
    expect(component.mensajeExito()).toContain('atendida con exito');
  });

  it('debe marcar no asistio mediante click real en el DOM sobre #btn-marcar-no-asistio-reserva', () => {
    vi.spyOn(cajaService, 'marcarNoAsistio').mockReturnValue(
      of({
        id_reserva: 42,
        codigo_reserva: 'RES-2026-0042',
        estado: 'cancelada',
        items_liberados: 1,
        mensaje: 'Inasistencia asentada',
      })
    );

    component.seleccionarReserva(mockReserva);
    fixture.detectChanges();

    const btnNoAsistio = fixture.nativeElement.querySelector('#btn-marcar-no-asistio-reserva');
    expect(btnNoAsistio).toBeTruthy();

    btnNoAsistio.click();
    fixture.detectChanges();

    expect(cajaService.marcarNoAsistio).toHaveBeenCalledWith(42);
    expect(component.mensajeExito()).toContain('cancelada por inasistencia');
  });

  it('debe convertir la reserva a venta y redirigir a caja mediante click sobre #btn-convertir-venta-reserva', () => {
    vi.spyOn(cajaService, 'convertirAVenta').mockReturnValue(
      of({
        id_venta: 110,
        numero_comprobante: 'FS-2026-000110',
        id_reserva: 42,
        total: 320,
        estado_venta: 'pendiente',
        mensaje: 'Venta creada',
      })
    );

    component.seleccionarReserva(mockReserva);
    fixture.detectChanges();

    const btnConvertir = fixture.nativeElement.querySelector('#btn-convertir-venta-reserva');
    expect(btnConvertir).toBeTruthy();

    btnConvertir.click();
    fixture.detectChanges();

    expect(cajaService.convertirAVenta).toHaveBeenCalledWith(42);
    expect(component.mensajeExito()).toContain('FS-2026-000110');
  });

  it('debe navegar hacia /caja/cobro mediante directiva dual en pestana de navegacion', () => {
    const navigateSpy = vi.spyOn(router, 'navigateByUrl');
    const tabCobro = fixture.nativeElement.querySelector('a[href="/caja/cobro"]');
    expect(tabCobro).toBeTruthy();

    tabCobro.click();

    expect(navigateSpy).toHaveBeenCalledWith('/caja/cobro');
  });
});
