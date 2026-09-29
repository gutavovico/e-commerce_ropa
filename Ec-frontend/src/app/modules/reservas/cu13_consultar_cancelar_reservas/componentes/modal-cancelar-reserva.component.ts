import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { Reserva } from '../modelos/reserva.model';

/** Motivo obligatorio de CU13 (paso 4), 3-250 caracteres — espejo de `ReservaCancelarIn`. */
const MOTIVO_MIN = 3;
const MOTIVO_MAX = 250;

@Component({
  selector: 'app-modal-cancelar-reserva',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './modal-cancelar-reserva.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ModalCancelarReservaComponent {
  @Input({ required: true }) reserva!: Reserva;
  @Input() cancelando = false;
  @Input() error: string | null = null;

  @Output() cerrar = new EventEmitter<void>();
  @Output() confirmar = new EventEmitter<string>();

  protected readonly motivo = signal('');
  protected readonly motivoMax = MOTIVO_MAX;

  protected get motivoValido(): boolean {
    const longitud = this.motivo().trim().length;
    return longitud >= MOTIVO_MIN && longitud <= MOTIVO_MAX;
  }

  protected actualizarMotivo(valor: string): void {
    this.motivo.set(valor);
  }

  protected onConfirmar(): void {
    if (!this.motivoValido || this.cancelando) return;
    this.confirmar.emit(this.motivo().trim());
  }

  protected onCerrar(): void {
    if (this.cancelando) return;
    this.cerrar.emit();
  }
}
