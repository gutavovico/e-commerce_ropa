import { TenantService } from '../../../../../core/tenant/tenant.service';
import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
  computed,
  inject,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import {
  DisponibilidadSucursalItem,
  ProductoDetalle,
  ReservaConfirmacion,
  ReservaCrearPayload,
  VarianteDetalle,
} from '../../modelos/producto-detalle.model';
import { ReservaService } from '../../servicios/reserva.service';
import { LoginService } from '../../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import { ImportePipe } from '../../../../../core/tenant/moneda';
import { SinConexionService } from '../../../../../core/sin-conexion/sin-conexion.service';
import { FranjaCita, franjasDeCita } from '../../../../../core/sin-conexion/franjas-cita';

@Component({
  selector: 'app-modal-reserva-boutique',
  standalone: true,
  imports: [ImportePipe, CommonModule],
  templateUrl: './modal-reserva-boutique.component.html',
  styleUrls: ['./modal-reserva-boutique.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ModalReservaBoutiqueComponent {
  private readonly reservaService = inject(ReservaService);
  private readonly loginService = inject(LoginService);
  private readonly router = inject(Router);
  private readonly portal = inject(TenantService);
  private readonly sinConexion = inject(SinConexionService);

  @Input({ required: true }) producto!: ProductoDetalle;
  @Input({ required: true }) varianteSeleccionada!: VarianteDetalle;
  @Input() sucursales: DisponibilidadSucursalItem[] = [];

  @Output() cerrar = new EventEmitter<void>();
  @Output() reservaConfirmada = new EventEmitter<ReservaConfirmacion>();

  protected readonly sucursalSeleccionadaId = signal<number>(1);
  /**
   * P2-CU15 (RN25): solo horas anteriores al vencimiento de la reserva (las horas de la empresa desde
   * ahora). Antes se ofrecían franjas fijas («VIERNES 12:00H») y la cita se enviaba siempre para
   * mañana a las 11:30, sin relación con la franja elegida.
   */
  protected readonly franjasHorarias: FranjaCita[] = franjasDeCita(new Date(), this.sinConexion.horasVencimiento(), 6);
  protected readonly horarioSeleccionado = signal<string | null>(this.franjasHorarias[0]?.iso ?? null);
  protected readonly horasVencimiento = this.sinConexion.horasVencimiento;

  protected readonly cargando = signal<boolean>(false);
  protected readonly error = signal<string | null>(null);
  protected readonly exito = signal<ReservaConfirmacion | null>(null);

  /** El backend devuelve las líneas apartadas, no un total: se deriva sumando cantidades. */
  protected readonly totalPrendas = computed(() =>
    (this.exito()?.items ?? []).reduce((suma, item) => suma + item.cantidad, 0)
  );

  protected seleccionarSucursal(id: number): void {
    this.sucursalSeleccionadaId.set(id);
    this.error.set(null);
  }

  protected seleccionarHorario(horario: string): void {
    this.horarioSeleccionado.set(horario);
  }

  protected confirmarReserva(): void {
    // Validar autenticación
    if (!this.loginService.estaAutenticado()) {
      this.error.set(
        'Debes iniciar sesión para agendar tu cita privada de fitting en boutique.'
      );
      setTimeout(() => {
        this.cerrar.emit();
        this.router.navigate(this.portal.ruta(['/login']), {
          queryParams: { returnUrl: `/productos/${this.producto.id_producto}` },
        });
      }, 1500);
      return;
    }

    this.cargando.set(true);
    this.error.set(null);

    if (!this.varianteSeleccionada?.id_variante) {
      this.error.set('Por favor, selecciona una variante válida para agendar la cita.');
      this.cargando.set(false);
      return;
    }

    const franja = this.franjasHorarias.find((f) => f.iso === this.horarioSeleccionado());
    if (!franja) {
      this.error.set('Elige la hora de tu visita.');
      this.cargando.set(false);
      return;
    }

    const talla = this.varianteSeleccionada.talla_codigo || 'Única';
    const color = this.varianteSeleccionada.color_nombre || 'Estándar';
    const nombreProd = this.producto?.nombre || 'Prenda de alta costura';
    const sucursalId = this.sucursalSeleccionadaId() || (this.sucursales?.[0]?.id_sucursal ?? 1);

    const payload: ReservaCrearPayload = {
      id_sucursal: sucursalId,
      fecha_hora_atencion: franja.iso,
      canal_origen: 'web',
      observacion: `Cita privada de prueba presencial para ${nombreProd} (Talla: ${talla}, Color: ${color}) (${franja.etiqueta})`,
      items: [
        {
          id_variante: this.varianteSeleccionada.id_variante,
          cantidad: 1,
        },
      ],
    };

    this.reservaService.crearReservaBoutique(payload).subscribe({
      next: (res) => {
        this.cargando.set(false);
        this.exito.set(res);
        this.reservaConfirmada.emit(res);
      },
      error: (err) => {
        this.cargando.set(false);
        if (err.status === 409) {
          // P2-CU15 A3: el servidor propone las sucursales que sí tienen la prenda.
          const alternativas: { nombre: string }[] = err.error?.alternativas ?? [];
          this.error.set(
            'Lo sentimos, las existencias para esta talla acaban de agotarse en la boutique seleccionada.' +
              (alternativas.length ? ` Disponible en: ${alternativas.map((a) => a.nombre).join(', ')}.` : '')
          );
        } else if (err.status === 401) {
          this.error.set(
            'Tu sesión ha expirado. Por favor inicia sesión nuevamente.'
          );
        } else {
          this.error.set(
            err.error?.detail ||
              'No fue posible formalizar la reserva. Por favor intenta de nuevo.'
          );
        }
      },
    });
  }

  protected cerrarModal(): void {
    this.cerrar.emit();
  }
}
