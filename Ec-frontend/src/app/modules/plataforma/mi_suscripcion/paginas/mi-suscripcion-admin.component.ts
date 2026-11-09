import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import { MarcaTiendaComponent } from '../../../../core/tenant/marca-tienda.component';
import {
  EscenarioPruebaStripe,
  IntentoPagoSuscripcion,
  MiSuscripcionResumen,
  PlanDisponibleEmpresa,
} from '../modelos/mi-suscripcion.model';
import { MiSuscripcionService } from '../servicios/mi-suscripcion.service';

@Component({
  selector: 'app-mi-suscripcion-admin',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, MarcaTiendaComponent],
  templateUrl: './mi-suscripcion-admin.component.html',
  styleUrls: ['./mi-suscripcion-admin.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MiSuscripcionAdminComponent implements OnInit {
  private readonly suscripcionService = inject(MiSuscripcionService);

  readonly cargando = signal(false);
  readonly procesandoPago = signal(false);
  readonly error = signal<string | null>(null);
  readonly exito = signal<string | null>(null);

  readonly resumen = signal<MiSuscripcionResumen | null>(null);
  readonly planesDisponibles = signal<PlanDisponibleEmpresa[]>([]);

  // Estado del selector de plan y pasarela Stripe (P2-CU10)
  readonly planSeleccionadoId = signal<number | null>(null);
  readonly mesesSeleccionados = signal<number>(1);
  readonly escenarioPrueba = signal<EscenarioPruebaStripe>('exito');
  readonly intentoPagoActivo = signal<IntentoPagoSuscripcion | null>(null);

  readonly planSeleccionado = computed(() => {
    const id = this.planSeleccionadoId();
    if (!id) return null;
    return this.planesDisponibles().find((p) => p.id_plan === id) ?? null;
  });

  readonly importeEstimado = computed(() => {
    const plan = this.planSeleccionado();
    if (!plan) return 0;
    const precio = Number(plan.precio_mensual) || 0;
    return +(precio * this.mesesSeleccionados()).toFixed(2);
  });

  readonly tasaCambioBob = computed(() => 1);

  readonly importeEstimadoBob = computed(() => this.importeEstimado());

  convertirABob(monto: number | string | undefined): string {
    const valor = Number(monto) || 0;
    return valor.toFixed(2);
  }

  readonly porcentajeUsoSucursales = computed(() => {
    const uso = this.resumen()?.uso.sucursales;
    if (!uso || !uso.limite || uso.limite <= 0) return 0;
    return Math.min(100, Math.round((uso.usados / uso.limite) * 100));
  });

  readonly porcentajeUsoEmpleados = computed(() => {
    const uso = this.resumen()?.uso.empleados;
    if (!uso || uso.limite === null || uso.limite <= 0) return 20;
    return Math.min(100, Math.round((uso.usados / uso.limite) * 100));
  });

  ngOnInit(): void {
    this.cargarDatos();
  }

  cargarDatos(): void {
    this.cargando.set(true);
    this.error.set(null);

    forkJoin({
      resumen: this.suscripcionService.obtenerMiSuscripcion(),
      planes: this.suscripcionService.listarPlanesDisponibles(),
    }).subscribe({
      next: ({ resumen, planes }) => {
        this.resumen.set(resumen);
        this.planesDisponibles.set(planes);
        if (!this.planSeleccionadoId()) {
          this.planSeleccionadoId.set(resumen.suscripcion.id_plan);
        }
        this.cargando.set(false);
      },
      error: (err) => {
        this.cargando.set(false);
        this.error.set(this.extraerMensajeError(err));
      },
    });
  }

  seleccionarPlan(plan: PlanDisponibleEmpresa): void {
    this.error.set(null);
    this.exito.set(null);
    this.intentoPagoActivo.set(null);
    this.planSeleccionadoId.set(plan.id_plan);
  }

  cambiarMeses(meses: number): void {
    this.mesesSeleccionados.set(meses);
    this.intentoPagoActivo.set(null);
  }

  iniciarPagoStripe(): void {
    const plan = this.planSeleccionado();
    if (!plan) return;

    this.procesandoPago.set(true);
    this.error.set(null);
    this.exito.set(null);

    this.suscripcionService
      .iniciarPago({
        id_plan: plan.id_plan,
        meses: this.mesesSeleccionados(),
        metodo_pago: 'tarjeta',
      })
      .subscribe({
        next: (intento) => {
          this.procesandoPago.set(false);
          this.intentoPagoActivo.set(intento);
        },
        error: (err) => {
          this.procesandoPago.set(false);
          this.error.set(this.extraerMensajeError(err));
        },
      });
  }

  confirmarPagoStripe(): void {
    const intento = this.intentoPagoActivo();
    if (!intento) return;

    this.procesandoPago.set(true);
    this.error.set(null);
    this.exito.set(null);

    this.suscripcionService
      .confirmarCambioORenovacion({
        id_plan: intento.id_plan,
        meses: intento.meses,
        referencia_pago: intento.referencia,
        escenario_prueba: this.escenarioPrueba(),
      })
      .subscribe({
        next: (nuevoResumen) => {
          this.procesandoPago.set(false);
          this.resumen.set(nuevoResumen);
          this.intentoPagoActivo.set(null);
          const accionTexto =
            intento.operacion === 'renovacion'
              ? `Suscripción renovada exitosamente en el plan ${intento.nombre_plan}`
              : `Cambio al plan ${intento.nombre_plan} aplicado exitosamente`;
          this.exito.set(`${accionTexto} (Ref. Stripe: ${intento.referencia}).`);
          this.suscripcionService.listarPlanesDisponibles().subscribe({
            next: (planes) => this.planesDisponibles.set(planes),
          });
        },
        error: (err) => {
          this.procesandoPago.set(false);
          this.error.set(this.extraerMensajeError(err));
        },
      });
  }

  cancelarIntentoPago(): void {
    this.intentoPagoActivo.set(null);
    this.error.set(null);
  }

  formatearDetalleHistorial(detalle: Record<string, unknown> | null): string {
    if (!detalle) return 'Sin detalles adicionales';
    const partes: string[] = [];
    if (detalle['plan_anterior'] && detalle['plan_nuevo']) {
      partes.push(`Plan: ${detalle['plan_anterior']} → ${detalle['plan_nuevo']}`);
    } else if (detalle['plan']) {
      partes.push(`Plan: ${detalle['plan']}`);
    }
    if (detalle['fecha_vencimiento']) {
      partes.push(`Vence: ${detalle['fecha_vencimiento']}`);
    }
    if (detalle['monto'] && detalle['moneda']) {
      partes.push(`Cobro: ${detalle['monto']} ${detalle['moneda']}`);
    }
    if (detalle['referencia_stripe']) {
      partes.push(`Stripe: ${detalle['referencia_stripe']}`);
    }
    return partes.length > 0 ? partes.join(' · ') : JSON.stringify(detalle);
  }

  private extraerMensajeError(err: unknown): string {
    const httpErr = err as {
      error?: { detail?: string; message?: string; error?: { message?: string } };
      message?: string;
    };
    return (
      httpErr?.error?.error?.message ||
      httpErr?.error?.detail ||
      httpErr?.error?.message ||
      httpErr?.message ||
      'Ocurrió un error al procesar la solicitud de suscripción.'
    );
  }
}

