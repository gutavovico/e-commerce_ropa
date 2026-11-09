import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { MiSuscripcionAdminComponent } from './mi-suscripcion-admin.component';
import { MiSuscripcionService } from '../servicios/mi-suscripcion.service';
import {
  IntentoPagoSuscripcion,
  MiSuscripcionResumen,
  PlanDisponibleEmpresa,
} from '../modelos/mi-suscripcion.model';

describe('MiSuscripcionAdminComponent (P2-CU09 y P2-CU10)', () => {
  let fixture: ComponentFixture<MiSuscripcionAdminComponent>;
  let component: MiSuscripcionAdminComponent;

  const mockResumen: MiSuscripcionResumen = {
    empresa: {
      id_tenant: 1,
      codigo: 'atelier-central',
      nombre: 'Atelier Central',
      estado: 'activa',
      moneda: 'EUR',
    },
    suscripcion: {
      id_suscripcion: 100,
      id_plan: 2,
      nombre_plan: 'Profesional',
      precio_mensual: '79.00',
      estado: 'activa',
      estado_efectivo: 'activa',
      fecha_inicio: '2026-11-01',
      fecha_vencimiento: '2026-12-01',
      dias_restantes: 22,
      vigente: true,
      proxima_a_vencer: false,
    },
    uso: {
      sucursales: { usados: 2, limite: 3, al_limite: false, excede_limite: false },
      empleados: { usados: 6, limite: 15, al_limite: false, excede_limite: false },
      sucursales_activas_detalle: [
        { id_sucursal: 1, nombre: 'Boutique Centro', direccion: 'Av. 1' },
        { id_sucursal: 2, nombre: 'Boutique Sur', direccion: 'Av. 2' },
      ],
    },
    funcionalidades_incluidas: [
      {
        codigo: 'productos',
        nombre: 'Catálogo de productos',
        descripcion: 'Prendas y variantes',
        planes_que_la_incluyen: [],
      },
    ],
    funcionalidades_no_incluidas: [
      {
        codigo: 'reportes_ia',
        nombre: 'Reportes con IA',
        descripcion: 'Reportes asistidos',
        planes_que_la_incluyen: ['Empresarial'],
      },
    ],
    historial: [
      {
        id_historial: 1,
        id_suscripcion: 100,
        evento: 'alta',
        detalle: { plan: 'Profesional', fecha_vencimiento: '2026-12-01' },
        id_usuario: 10,
        creado_en: '2026-11-01T10:00:00Z',
      },
    ],
  };

  const mockPlanes: PlanDisponibleEmpresa[] = [
    {
      id_plan: 1,
      nombre: 'Basico',
      precio_mensual: '29.00',
      max_sucursales_activas: 1,
      max_empleados: 5,
      funcionalidades: ['productos', 'ventas'],
      es_plan_actual: false,
      compatible_con_uso_actual: false,
      motivo_incompatibilidad:
        'La empresa tiene 2 sucursales activas (Boutique Centro, Boutique Sur) y el plan permite 1.',
    },
    {
      id_plan: 2,
      nombre: 'Profesional',
      precio_mensual: '79.00',
      max_sucursales_activas: 3,
      max_empleados: 15,
      funcionalidades: ['productos', 'ventas', 'reservas'],
      es_plan_actual: true,
      compatible_con_uso_actual: true,
      motivo_incompatibilidad: null,
    },
    {
      id_plan: 3,
      nombre: 'Empresarial',
      precio_mensual: '199.00',
      max_sucursales_activas: 10,
      max_empleados: null,
      funcionalidades: ['productos', 'ventas', 'reservas', 'reportes_ia'],
      es_plan_actual: false,
      compatible_con_uso_actual: true,
      motivo_incompatibilidad: null,
    },
  ];

  const mockIntento: IntentoPagoSuscripcion = {
    referencia: 'pi_sbx_1234567890',
    client_secret: 'pi_sbx_1234567890_secret_sbx',
    estado_pago: 'requires_confirmation',
    monto: '199.00',
    moneda: 'EUR',
    id_plan: 3,
    nombre_plan: 'Empresarial',
    meses: 1,
    operacion: 'cambio_plan',
    requiere_cobro: true,
  };

  let mockService: {
    obtenerMiSuscripcion: ReturnType<typeof vi.fn>;
    listarPlanesDisponibles: ReturnType<typeof vi.fn>;
    iniciarPago: ReturnType<typeof vi.fn>;
    confirmarCambioORenovacion: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    mockService = {
      obtenerMiSuscripcion: vi.fn().mockReturnValue(of(mockResumen)),
      listarPlanesDisponibles: vi.fn().mockReturnValue(of(mockPlanes)),
      iniciarPago: vi.fn().mockReturnValue(of(mockIntento)),
      confirmarCambioORenovacion: vi.fn().mockReturnValue(
        of({
          ...mockResumen,
          suscripcion: {
            ...mockResumen.suscripcion,
            id_plan: 3,
            nombre_plan: 'Empresarial',
            precio_mensual: '199.00',
          },
        })
      ),
    };

    await TestBed.configureTestingModule({
      imports: [MiSuscripcionAdminComponent],
      providers: [
        provideRouter([]),
        { provide: MiSuscripcionService, useValue: mockService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(MiSuscripcionAdminComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('AC-01/AC-08: debe cargar y mostrar el resumen de suscripción, uso y planes disponibles', () => {
    expect(component).toBeTruthy();
    expect(mockService.obtenerMiSuscripcion).toHaveBeenCalled();
    expect(mockService.listarPlanesDisponibles).toHaveBeenCalled();

    const html = (fixture.nativeElement as HTMLElement).textContent || '';
    expect(html).toContain('Atelier Central');
    expect(html).toContain('Plan Profesional');
    expect(html).toContain('Boutique Centro');
    expect(html).toContain('Reportes con IA');
  });

  it('AC-07/AC-08: debe iniciar y confirmar el pago con Stripe al cambiar al plan Empresarial', () => {
    component.seleccionarPlan(mockPlanes[2]);
    component.cambiarMeses(2);
    expect(component.importeEstimado()).toBe(398);

    component.iniciarPagoStripe();
    expect(mockService.iniciarPago).toHaveBeenCalledWith({
      id_plan: 3,
      meses: 2,
      metodo_pago: 'tarjeta',
    });
    expect(component.intentoPagoActivo()?.referencia).toBe('pi_sbx_1234567890');

    component.confirmarPagoStripe();
    expect(mockService.confirmarCambioORenovacion).toHaveBeenCalledWith({
      id_plan: 3,
      meses: 1,
      referencia_pago: 'pi_sbx_1234567890',
      escenario_prueba: 'exito',
    });
    expect(component.exito()).toContain('pi_sbx_1234567890');
  });

  it('AC-06 (CU10 A2): debe mostrar alerta de error y conservar el estado si Stripe rechaza el cobro', () => {
    mockService.confirmarCambioORenovacion.mockReturnValueOnce(
      throwError(() => ({
        error: {
          detail:
            'No se pudo completar el cobro en Stripe: La entidad emisora ha rechazado la tarjeta.',
        },
      }))
    );

    component.seleccionarPlan(mockPlanes[2]);
    component.iniciarPagoStripe();
    component.escenarioPrueba.set('rechazado');
    component.confirmarPagoStripe();

    expect(component.error()).toContain('La entidad emisora ha rechazado la tarjeta');
  });
});

