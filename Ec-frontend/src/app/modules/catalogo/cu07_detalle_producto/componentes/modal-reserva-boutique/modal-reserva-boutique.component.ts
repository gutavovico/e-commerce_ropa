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

@Component({
  selector: 'app-modal-reserva-boutique',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './modal-reserva-boutique.component.html',
  styleUrls: ['./modal-reserva-boutique.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ModalReservaBoutiqueComponent {
  private readonly reservaService = inject(ReservaService);
  private readonly loginService = inject(LoginService);
  private readonly router = inject(Router);

  @Input({ required: true }) producto!: ProductoDetalle;
  @Input({ required: true }) varianteSeleccionada!: VarianteDetalle;
  @Input() sucursales: DisponibilidadSucursalItem[] = [];

  @Output() cerrar = new EventEmitter<void>();
  @Output() reservaConfirmada = new EventEmitter<ReservaConfirmacion>();

  protected readonly sucursalSeleccionadaId = signal<number>(1);
  protected readonly horarioSeleccionado = signal<string>('MAÑANA 11:30H');
  protected readonly franjasHorarias = [
    'MAÑANA 11:30H',
    'MAÑANA 16:30H',
    'VIERNES 12:00H',
  ];

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
        this.router.navigate(['/login'], {
          queryParams: { returnUrl: `/productos/${this.producto.id_producto}` },
        });
      }, 1500);
      return;
    }

    this.cargando.set(true);
    this.error.set(null);

    // Calcular fecha futura acorde a la franja seleccionada
    const fechaAtencion = new Date();
    fechaAtencion.setDate(fechaAtencion.getDate() + 1);
    fechaAtencion.setHours(11, 30, 0, 0);

    const payload: ReservaCrearPayload = {
      id_sucursal: this.sucursalSeleccionadaId(),
      fecha_hora_atencion: fechaAtencion.toISOString(),
      canal_origen: 'web',
      observacion: `Cita privada de prueba presencial para ${this.producto.nombre} (Talla: ${this.varianteSeleccionada.talla_codigo}, Color: ${this.varianteSeleccionada.color_nombre}) en franja ${this.horarioSeleccionado()}`,
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
          this.error.set(
            'Lo sentimos, las existencias para esta talla acaban de agotarse en la boutique seleccionada.'
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
