import { MarcaTiendaComponent } from '../../../../../core/tenant/marca-tienda.component';
import {
  ChangeDetectionStrategy,
  Component,
  ViewEncapsulation,
  computed,
  input,
  output,
} from '@angular/core';
import { DatePipe } from '@angular/common';
import { ETIQUETA_METODO, VentaPos } from '../../modelos/punto-venta.dto';
import { ImportePipe } from '../../../../../core/tenant/moneda';

/**
 * Comprobante de 80 mm (CU32). Imprimible con `window.print()`: los estilos `@media print` ocultan
 * el resto de la página, por eso el componente no encapsula su hoja de estilos.
 * Todos los importes proceden del servidor tal cual (cadenas `Decimal`).
 */
@Component({
  selector: 'app-ticket-comprobante',
  standalone: true,
  imports: [ImportePipe, MarcaTiendaComponent, DatePipe],
  templateUrl: './ticket-comprobante.component.html',
  styleUrls: ['./ticket-comprobante.component.scss'],
  encapsulation: ViewEncapsulation.None,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TicketComprobanteComponent {
  readonly venta = input.required<VentaPos>();
  readonly descargandoPdf = input(false);

  readonly descargarPdf = output<void>();
  readonly cerrar = output<void>();

  /** Solo una venta pagada o anulada es comprobante (409 COMPROBANTE_NO_DISPONIBLE en otro caso). */
  readonly esComprobante = computed(() => this.venta().estado !== 'pendiente');
  readonly pagoConfirmado = computed(
    () => this.venta().pagos.find((p) => p.estado === 'confirmado') ?? null,
  );

  etiquetaMetodo(metodo: string): string {
    return ETIQUETA_METODO[metodo] ?? metodo;
  }

  imprimir(): void {
    window.print();
  }
}
