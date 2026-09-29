import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';
import { CommonModule, Location } from '@angular/common';
import { RouterLink } from '@angular/router';

import { Reserva } from '../modelos/reserva.model';
import { MisReservasService } from '../servicios/mis-reservas.service';
import { ModalCancelarReservaComponent } from '../componentes/modal-cancelar-reserva.component';

type Pestana = 'proximas' | 'historial';

const ETIQUETAS_ESTADO: Record<string, string> = {
  pendiente: 'Pendiente de confirmación',
  confirmada: 'Confirmada',
  en_atencion: 'En atención',
  atendida: 'Atendida',
  cancelada: 'Cancelada',
  vencida: 'Vencida',
};

/** HEX del design system (`fashionstore-tokens.md`): Tailwind CDN no trae estos tokens
 * semánticos configurados, así que se usan como valores arbitrarios de color (permitido; la
 * restricción de la constitución de frontend es solo sobre espaciados y dimensiones). */
const ESTILOS_BADGE: Record<string, string> = {
  pendiente: 'bg-[#EDEEF0] text-[#45474A]',
  confirmada: 'bg-[#ECDECB] text-[#6B6152]',
  en_atencion: 'bg-[#1B1C1D] text-white',
  atendida: 'bg-[#E8E8EA] text-[#1A1C1D]',
  cancelada: 'bg-[#FFDAD6] text-[#93000A]',
  vencida: 'bg-[#D9DADC] text-[#75777A]',
};

@Component({
  selector: 'app-mis-reservas',
  standalone: true,
  imports: [CommonModule, RouterLink, ModalCancelarReservaComponent],
  templateUrl: './mis-reservas.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MisReservasComponent implements OnInit {
  private readonly location = inject(Location);
  protected readonly service = inject(MisReservasService);

  protected readonly cargando = this.service.cargando;
  protected readonly error = this.service.error;
  protected readonly misReservas = this.service.misReservas;

  protected readonly pestanaActiva = signal<Pestana>('proximas');
  protected readonly reservaACancelar = signal<Reserva | null>(null);

  protected readonly proximas = computed(() => this.misReservas()?.proximas ?? []);
  protected readonly historial = computed(() => this.misReservas()?.historial ?? []);
  protected readonly resumen = computed(
    () => this.misReservas()?.resumen ?? { activas: 0, proxima: null }
  );
  protected readonly listaActiva = computed(() =>
    this.pestanaActiva() === 'proximas' ? this.proximas() : this.historial()
  );

  ngOnInit(): void {
    this.cargar();
  }

  protected cargar(): void {
    this.service.cargarMisReservas().subscribe({ error: () => undefined });
  }

  protected volver(): void {
    this.location.back();
  }

  protected seleccionarPestana(pestana: Pestana): void {
    this.pestanaActiva.set(pestana);
  }

  protected etiquetaEstado(estado: string): string {
    return ETIQUETAS_ESTADO[estado] ?? estado;
  }

  protected claseBadge(estado: string): string {
    return ESTILOS_BADGE[estado] ?? ESTILOS_BADGE['pendiente'];
  }

  /** `Intl` nativo del navegador: evita depender del registro de locale `es` de Angular. */
  protected formatearFecha(iso: string): string {
    const texto = new Intl.DateTimeFormat('es-ES', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
    }).format(new Date(iso));
    return texto.charAt(0).toUpperCase() + texto.slice(1);
  }

  protected formatearHora(iso: string): string {
    return new Intl.DateTimeFormat('es-ES', { hour: '2-digit', minute: '2-digit' }).format(
      new Date(iso)
    );
  }

  protected abrirCancelacion(reserva: Reserva): void {
    this.reservaACancelar.set(reserva);
  }

  protected cerrarCancelacion(): void {
    this.reservaACancelar.set(null);
  }

  protected confirmarCancelacion(motivo: string): void {
    const reserva = this.reservaACancelar();
    if (!reserva) return;

    this.service.cancelarReserva(reserva.id_reserva, motivo).subscribe({
      next: () => this.cerrarCancelacion(),
      error: () => {
        // El mensaje queda en `service.error()`; el modal permanece abierto para reintentar.
      },
    });
  }
}
