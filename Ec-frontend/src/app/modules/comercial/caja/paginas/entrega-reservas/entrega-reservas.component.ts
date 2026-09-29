/**
 * Componente Standalone para [CU18] Atender entrega de reserva en boutique.
 * Gestion de citas en fitting room, entrega de prendas, liberacion de stock y conversion a venta.
 */

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
import { Router, RouterLink } from '@angular/router';
import { CajaService } from '../../servicios/caja.service';
import { LoginService } from '../../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import {
  ReservaPendienteCaja,
} from '../../modelos/caja.dto';

@Component({
  selector: 'app-entrega-reservas',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './entrega-reservas.component.html',
  styleUrls: ['./entrega-reservas.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EntregaReservasComponent implements OnInit {
  protected readonly cajaService = inject(CajaService);
  protected readonly loginService = inject(LoginService);
  private readonly router = inject(Router);

  // Estados locales
  readonly terminoBusqueda = signal<string>('');
  readonly observacionesEntrega = signal<string>('');
  readonly mensajeExito = signal<string | null>(null);

  // Derivaciones reactivas
  readonly reservas = this.cajaService.reservasPendientes;
  readonly reservaSeleccionada = this.cajaService.reservaSeleccionada;
  readonly cargando = this.cajaService.cargando;
  readonly errorMensaje = this.cajaService.error;

  readonly usuario = computed(() => this.loginService.usuarioActual());
  readonly sucursalId = computed(() => this.usuario()?.id_sucursal ?? null);
  readonly cajeroNombre = computed(() => {
    const u = this.usuario();
    if (!u) return 'Operador de Mostrador';
    const nom = `${u.nombres || ''} ${u.apellidos || ''}`.trim();
    return nom || u.email || 'Operador de Mostrador';
  });

  ngOnInit(): void {
    this.cargarReservas();
  }

  cargarReservas(): void {
    this.cajaService.buscarReservasPendientes(this.terminoBusqueda()).subscribe();
  }

  onBuscar(event?: Event): void {
    if (event) {
      event.preventDefault();
    }
    this.cargarReservas();
  }

  seleccionarReserva(reserva: ReservaPendienteCaja): void {
    this.mensajeExito.set(null);
    this.cajaService.seleccionarReserva(reserva);
    this.observacionesEntrega.set('');
  }

  cancelarSeleccion(): void {
    this.cajaService.seleccionarReserva(null);
  }

  confirmarEntrega(event?: Event): void {
    if (event) {
      event.preventDefault();
    }
    const res = this.reservaSeleccionada();
    if (!res || this.cargando()) return;

    this.cajaService
      .confirmarEntrega(res.id_reserva, {
        observaciones: this.observacionesEntrega().trim() || undefined,
      })
      .subscribe({
        next: (resp) => {
          this.mensajeExito.set(
            `Reserva ${resp.codigo_reserva} atendida con exito. Fitting concluido.`
          );
        },
      });
  }

  marcarNoAsistio(event?: Event): void {
    if (event) {
      event.preventDefault();
    }
    const res = this.reservaSeleccionada();
    if (!res || this.cargando()) return;

    this.cajaService.marcarNoAsistio(res.id_reserva).subscribe({
      next: (resp) => {
        this.mensajeExito.set(
          `Reserva ${resp.codigo_reserva} cancelada por inasistencia. Se liberaron ${resp.items_liberados} prenda(s) al stock disponible.`
        );
      },
    });
  }

  convertirAVenta(event?: Event): void {
    if (event) {
      event.preventDefault();
    }
    const res = this.reservaSeleccionada();
    if (!res || this.cargando()) return;

    this.cajaService.convertirAVenta(res.id_reserva).subscribe({
      next: (resp) => {
        this.mensajeExito.set(
          `Reserva convertida a venta ${resp.numero_comprobante}. Redirigiendo a caja para cobro...`
        );
        // Navegacion fluida hacia CU17 con busqueda precargada
        setTimeout(() => {
          this.router.navigate(['/caja/cobro']);
        }, 1200);
      },
    });
  }

  cerrarMensajeExito(): void {
    this.mensajeExito.set(null);
  }

  cerrarAlertaError(): void {
    this.cajaService.limpiarError();
  }

  navegar(ruta: string, event?: Event): void {
    if (event) {
      event.preventDefault();
    }
    this.router.navigateByUrl(ruta).then((exito) => {
      if (!exito) {
        this.router.navigate([ruta]);
      }
    });
  }
}
