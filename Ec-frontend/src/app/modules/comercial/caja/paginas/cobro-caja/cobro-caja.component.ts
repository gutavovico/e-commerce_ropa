/**
 * Componente Standalone para [CU17] Registrar cobro en caja.
 * Diseno editorial de mostrador POS bajo estetica institucional Obsidian & Camel.
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
  CobroCajaRequest,
  CobroCajaResponse,
  MetodoPagoCaja,
  OrdenPendiente,
} from '../../modelos/caja.dto';

@Component({
  selector: 'app-cobro-caja',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './cobro-caja.component.html',
  styleUrls: ['./cobro-caja.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CobroCajaComponent implements OnInit {
  protected readonly cajaService = inject(CajaService);
  protected readonly loginService = inject(LoginService);
  private readonly router = inject(Router);

  // Estados locales con Signals
  readonly terminoBusqueda = signal<string>('');
  readonly metodoSeleccionado = signal<MetodoPagoCaja>('efectivo');
  readonly montoRecibido = signal<number>(0);
  readonly observaciones = signal<string>('');
  readonly comprobanteExito = signal<CobroCajaResponse | null>(null);

  // Derivaciones reactivas
  readonly ordenSeleccionada = this.cajaService.ordenSeleccionada;
  readonly ordenes = this.cajaService.ordenesPendientes;
  readonly cargando = this.cajaService.cargando;
  readonly errorMensaje = this.cajaService.error;

  readonly usuario = computed(() => this.loginService.usuarioActual());
  readonly sucursalId = computed(() => this.usuario()?.id_sucursal ?? null);
  readonly cajeroNombre = computed(() => {
    const u = this.usuario();
    if (!u) return 'Operador de Caja';
    const nom = `${u.nombres || ''} ${u.apellidos || ''}`.trim();
    return nom || u.email || 'Operador de Caja';
  });

  // Calculadora reactiva de cambio
  readonly cambioDevuelto = computed(() => {
    const total = this.ordenSeleccionada()?.total ?? 0;
    const recibido = this.montoRecibido();
    if (recibido >= total) {
      return Number((recibido - total).toFixed(2));
    }
    return 0;
  });

  readonly montoSuficiente = computed(() => {
    if (this.metodoSeleccionado() !== 'efectivo') {
      return true;
    }
    const total = this.ordenSeleccionada()?.total ?? 0;
    return this.montoRecibido() >= total && total > 0;
  });

  readonly puedeCobrar = computed(() => {
    if (!this.ordenSeleccionada()) return false;
    if (this.cargando()) return false;
    if (this.metodoSeleccionado() === 'efectivo') {
      return this.montoSuficiente();
    }
    return true;
  });

  ngOnInit(): void {
    this.cargarOrdenes();
  }

  cargarOrdenes(): void {
    this.cajaService.buscarOrdenesPendientes(this.terminoBusqueda()).subscribe();
  }

  onBuscar(event?: Event): void {
    if (event) {
      event.preventDefault();
    }
    this.cargarOrdenes();
  }

  seleccionarOrden(orden: OrdenPendiente): void {
    this.comprobanteExito.set(null);
    this.cajaService.seleccionarOrden(orden);
    this.montoRecibido.set(orden.total);
    this.observaciones.set('');
    this.metodoSeleccionado.set('efectivo');
  }

  cancelarSeleccion(): void {
    this.cajaService.seleccionarOrden(null);
    this.comprobanteExito.set(null);
  }

  cambiarMetodo(metodo: MetodoPagoCaja): void {
    this.metodoSeleccionado.set(metodo);
    if (metodo !== 'efectivo' && this.ordenSeleccionada()) {
      this.montoRecibido.set(this.ordenSeleccionada()!.total);
    }
  }

  onMontoRecibidoChange(valor: number): void {
    this.montoRecibido.set(Number(valor) || 0);
  }

  confirmarCobro(event?: Event): void {
    if (event) {
      event.preventDefault();
    }
    const orden = this.ordenSeleccionada();
    if (!orden || !this.puedeCobrar()) {
      return;
    }

    const payload: CobroCajaRequest = {
      id_venta: orden.id_venta,
      monto_recibido: this.metodoSeleccionado() === 'efectivo'
        ? Number(this.montoRecibido())
        : Number(orden.total),
      metodo_pago: this.metodoSeleccionado(),
      observaciones: this.observaciones().trim() || undefined,
    };

    this.cajaService.cobrarOrden(orden.id_venta, payload).subscribe({
      next: (resp) => {
        this.comprobanteExito.set(resp);
      },
      error: () => {
        // El error ya queda registrado en cajaService.error
      },
    });
  }

  nuevaOperacion(): void {
    this.comprobanteExito.set(null);
    this.cajaService.seleccionarOrden(null);
    this.cargarOrdenes();
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
