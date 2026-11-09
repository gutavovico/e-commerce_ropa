import { ChangeDetectionStrategy, Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { DatePipe } from '@angular/common';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { MarcaTiendaComponent } from '../../../../core/tenant/marca-tienda.component';
import { ParametrosEmpresaService } from '../servicios/parametros-empresa.service';
import { ParametrosEmpresa, RANGOS_PARAMETROS, ZONAS_HORARIAS } from '../modelos/parametros-empresa.dto';
import { MONEDAS, Moneda } from '../../../../core/tenant/moneda';
import { LoginService } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';

/** Texto de CU11 A2, mostrado antes de desactivar la operación sin conexión. */
export const AVISO_DESACTIVAR_OFFLINE =
  'Los dispositivos de los clientes ya no podrán registrar reservas nuevas sin internet. ' +
  'Las operaciones pendientes se conservan y se sincronizarán.';

/**
 * P2-CU11 · Configurar parámetros de la empresa (`/admin/configuracion`).
 * Spec: `.specs/finalized/P2-CU11-parametros-empresa/spec.md` §4.
 */
@Component({
  selector: 'app-parametros-empresa',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, DatePipe, MarcaTiendaComponent],
  templateUrl: './parametros-empresa.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ParametrosEmpresaComponent implements OnInit {
  readonly servicio = inject(ParametrosEmpresaService);
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly destroyRef = inject(DestroyRef);
  private readonly loginService = inject(LoginService);

  readonly rangos = RANGOS_PARAMETROS;
  readonly monedas = MONEDAS;
  readonly zonas = ZONAS_HORARIAS;
  readonly aviso = AVISO_DESACTIVAR_OFFLINE;

  readonly error = signal<string | null>(null);
  readonly exito = signal<string | null>(null);
  /** CU11 A2: confirmación pendiente al apagar la operación sin conexión. */
  readonly confirmandoDesactivar = signal(false);

  readonly form = this.fb.group({
    moneda: ['BOB' as Moneda, [Validators.required]],
    zona_horaria: ['America/La_Paz', [Validators.required]],
    horas_vencimiento_reserva: [
      RANGOS_PARAMETROS.horas_vencimiento_reserva.porDefecto as number,
      [Validators.required, Validators.min(1), Validators.max(168)],
    ],
    dias_cambio_prenda: [
      RANGOS_PARAMETROS.dias_cambio_prenda.porDefecto as number,
      [Validators.required, Validators.min(0), Validators.max(90)],
    ],
    operacion_offline_habilitada: [true],
    dias_antiguedad_offline: [
      RANGOS_PARAMETROS.dias_antiguedad_offline.porDefecto as number,
      [Validators.required, Validators.min(1), Validators.max(30)],
    ],
  });

  ngOnInit(): void {
    this.servicio
      .cargar()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (p) => this.aplicar(p),
        error: (e: Error) => this.error.set(e.message),
      });
  }

  /** Interruptor: al apagarlo se pide confirmación (A2); al encenderlo, no. */
  alternarOffline(evento: Event): void {
    const marcado = (evento.target as HTMLInputElement).checked;
    if (!marcado && this.servicio.parametros()?.operacion_offline_habilitada) {
      (evento.target as HTMLInputElement).checked = true;
      this.confirmandoDesactivar.set(true);
      return;
    }
    this.fijarOffline(marcado);
  }

  confirmarDesactivar(): void {
    this.confirmandoDesactivar.set(false);
    this.fijarOffline(false);
  }

  cancelarDesactivar(): void {
    this.confirmandoDesactivar.set(false);
  }

  guardar(): void {
    this.exito.set(null);
    this.error.set(null);
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.servicio
      .guardar(this.form.getRawValue())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (p) => {
          this.aplicar(p);
          this.loginService.actualizarMonedaEmpresa?.(p.moneda);
          this.exito.set('Configuración guardada. Rige para las operaciones nuevas.');
        },
        error: (e: Error) => this.error.set(e.message),
      });
  }

  invalido(campo: 'horas_vencimiento_reserva' | 'dias_cambio_prenda' | 'dias_antiguedad_offline'): boolean {
    const control = this.form.controls[campo];
    return control.invalid && (control.touched || control.dirty);
  }

  private fijarOffline(valor: boolean): void {
    this.form.controls.operacion_offline_habilitada.setValue(valor);
    this.form.controls.operacion_offline_habilitada.markAsDirty();
    const dias = this.form.controls.dias_antiguedad_offline;
    if (valor) dias.enable();
    else dias.disable();
  }

  /** El formulario refleja siempre lo que devolvió el servidor. */
  private aplicar(p: ParametrosEmpresa): void {
    this.form.reset({
      moneda: p.moneda,
      zona_horaria: p.zona_horaria,
      horas_vencimiento_reserva: p.horas_vencimiento_reserva,
      dias_cambio_prenda: p.dias_cambio_prenda,
      operacion_offline_habilitada: p.operacion_offline_habilitada,
      dias_antiguedad_offline: p.dias_antiguedad_offline,
    });
    if (p.operacion_offline_habilitada) this.form.controls.dias_antiguedad_offline.enable();
    else this.form.controls.dias_antiguedad_offline.disable();
    // M3: con ventas o pagos la moneda no cambia (se sigue enviando la actual)
    if (p.moneda_bloqueada) this.form.controls.moneda.disable();
    else this.form.controls.moneda.enable();
  }
}
