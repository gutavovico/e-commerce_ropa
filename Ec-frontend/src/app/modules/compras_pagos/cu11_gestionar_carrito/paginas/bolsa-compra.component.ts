import {
  ChangeDetectionStrategy,
  Component,
  OnDestroy,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { CommonModule, Location } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { CarritoService } from '../servicios/carrito.service';
import {
  BoutiqueRecogida,
  CarritoItem,
  TipoEntrega,
  VentaCreada,
} from '../modelos/carrito.model';

/** Ventana de cortesía de la bolsa, en minutos. Debe coincidir con el backend. */
const MINUTOS_VENTANA = 25;

/**
 * Pantalla de Bolsa de Compra y Checkout (CU11 + CU15).
 *
 * Es una vista secundaria del patrón Hub-and-Spoke: se declara fuera de `MainLayoutComponent`,
 * carece de la barra de navegación institucional y ofrece un retorno explícito mediante
 * `Location.back()`, que devuelve al origen real preservando filtros y scroll.
 */
@Component({
  selector: 'app-bolsa-compra',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './bolsa-compra.component.html',
  styleUrls: ['./bolsa-compra.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BolsaCompraComponent implements OnInit, OnDestroy {
  private readonly carritoService = inject(CarritoService);
  private readonly location = inject(Location);
  private readonly router = inject(Router);

  // --- Estado derivado del servicio ---
  protected readonly items = this.carritoService.items;
  protected readonly resumen = this.carritoService.resumen;
  protected readonly cargando = this.carritoService.cargando;
  protected readonly procesando = this.carritoService.procesando;
  protected readonly error = this.carritoService.error;
  protected readonly estaVacia = this.carritoService.estaVacia;
  protected readonly hayDescuento = this.carritoService.hayDescuento;
  protected readonly haySucursalesMultiples = this.carritoService.haySucursalesMultiples;
  protected readonly tipoEntrega = this.carritoService.tipoEntrega;
  protected readonly direccionEnvio = this.carritoService.direccionEnvio;
  protected readonly sucursalRetiro = this.carritoService.sucursalRetiro;
  protected readonly cuponAplicado = this.carritoService.cuponAplicado;

  // --- Estado local de la pantalla ---
  protected readonly boutiques = signal<BoutiqueRecogida[]>([]);
  protected readonly codigoCupon = signal<string>('');
  protected readonly lineaEnCurso = signal<number | null>(null);
  protected readonly ordenConfirmada = signal<VentaCreada | null>(null);
  protected readonly segundosRestantes = signal<number | null>(null);

  private temporizador: ReturnType<typeof setInterval> | null = null;

  /** Cuenta atrás en formato `MM:SS`, o null si no hay ventana activa. */
  protected readonly tiempoRestante = computed(() => {
    const segundos = this.segundosRestantes();
    if (segundos === null || segundos <= 0) return null;
    const minutos = Math.floor(segundos / 60);
    const resto = segundos % 60;
    return `${minutos}:${resto.toString().padStart(2, '0')}`;
  });

  protected readonly ventanaExpirada = computed(() => this.segundosRestantes() === 0);

  /** El botón de tramitar exige bolsa con prendas y los datos de entrega completos. */
  protected readonly puedeTramitar = computed(() => {
    if (this.estaVacia() || this.procesando()) return false;
    if (this.tipoEntrega() === 'domicilio') {
      return this.direccionEnvio().trim().length > 0;
    }
    return this.sucursalRetiro() !== null;
  });

  ngOnInit(): void {
    this.carritoService.cargarCarrito().subscribe({
      next: () => this.iniciarTemporizador(),
      error: () => {
        /* El mensaje ya quedó publicado en la señal `error` del servicio. */
      },
    });

    this.carritoService.obtenerBoutiques().subscribe({
      next: (lista) => this.boutiques.set(lista),
      error: () => this.boutiques.set([]),
    });
  }

  ngOnDestroy(): void {
    // Sin esta limpieza el intervalo sobrevive a la navegación y sigue disparando
    // detección de cambios sobre un componente ya destruido.
    this.detenerTemporizador();
  }

  // ---------------------------------------------------------------------
  // Navegación
  // ---------------------------------------------------------------------

  /** Retorno contextual al origen real, preservando filtros y scroll del catálogo. */
  protected volver(): void {
    this.location.back();
  }

  // ---------------------------------------------------------------------
  // CU11: modificación de la bolsa
  // ---------------------------------------------------------------------

  protected incrementar(item: CarritoItem): void {
    if (!this.puedeIncrementar(item)) return;
    this.cambiarCantidad(item, item.cantidad + 1);
  }

  protected decrementar(item: CarritoItem): void {
    if (item.cantidad <= 1) return;
    this.cambiarCantidad(item, item.cantidad - 1);
  }

  /** El botón «+» se detiene en las existencias reales de la boutique de expedición. */
  protected puedeIncrementar(item: CarritoItem): boolean {
    return item.cantidad < item.cantidad_maxima && !this.procesando();
  }

  protected eliminar(item: CarritoItem): void {
    this.lineaEnCurso.set(item.id_carrito_detalle);
    this.carritoService.eliminarItem(item.id_carrito_detalle).subscribe({
      next: () => {
        this.lineaEnCurso.set(null);
        this.refrescarTemporizador();
      },
      error: () => this.lineaEnCurso.set(null),
    });
  }

  private cambiarCantidad(item: CarritoItem, cantidad: number): void {
    this.lineaEnCurso.set(item.id_carrito_detalle);
    this.carritoService.actualizarCantidad(item.id_carrito_detalle, cantidad).subscribe({
      next: () => this.lineaEnCurso.set(null),
      error: () => this.lineaEnCurso.set(null),
    });
  }

  // ---------------------------------------------------------------------
  // CU15: entrega, cupón y tramitación
  // ---------------------------------------------------------------------

  protected seleccionarEntrega(tipo: TipoEntrega): void {
    this.tipoEntrega.set(tipo);
    this.error.set(null);
  }

  protected seleccionarBoutique(idSucursal: number): void {
    this.sucursalRetiro.set(idSucursal);
  }

  protected actualizarDireccion(valor: string): void {
    this.direccionEnvio.set(valor);
  }

  protected aplicarCupon(): void {
    const codigo = this.codigoCupon().trim();
    if (!codigo) return;
    // La validación real vive en el backend: aquí sólo se registra la intención. Un código
    // inexistente o caducado se rechaza al tramitar, con su mensaje de negocio.
    this.cuponAplicado.set(codigo);
  }

  protected retirarCupon(): void {
    this.cuponAplicado.set(null);
    this.codigoCupon.set('');
  }

  protected tramitarPedido(): void {
    if (!this.puedeTramitar()) return;

    this.carritoService.tramitarPedido().subscribe({
      next: (venta) => {
        this.ordenConfirmada.set(venta);
        this.detenerTemporizador();
      },
      error: () => {
        // Si el cupón fue el motivo del rechazo, se retira para que el cliente pueda reintentar.
        if (this.error()?.toLowerCase().includes('código')) {
          this.cuponAplicado.set(null);
        }
      },
    });
  }

  protected irACatalogo(): void {
    this.router.navigate(['/catalogo']);
  }

  // ---------------------------------------------------------------------
  // Temporizador de la ventana de cortesía
  // ---------------------------------------------------------------------

  private iniciarTemporizador(): void {
    this.detenerTemporizador();

    const expira = this.carritoService.expiraEn();
    if (!expira) {
      this.segundosRestantes.set(null);
      return;
    }

    const calcular = () => {
      const restante = Math.floor(
        (new Date(expira).getTime() - Date.now()) / 1000
      );
      this.segundosRestantes.set(Math.max(0, restante));
      if (restante <= 0) this.detenerTemporizador();
    };

    calcular();
    this.temporizador = setInterval(calcular, 1000);
  }

  /** Recalcula la ventana tras cambiar la bolsa: su inicio depende de la línea más antigua. */
  private refrescarTemporizador(): void {
    if (this.estaVacia()) {
      this.detenerTemporizador();
      this.segundosRestantes.set(null);
      return;
    }
    this.iniciarTemporizador();
  }

  private detenerTemporizador(): void {
    if (this.temporizador !== null) {
      clearInterval(this.temporizador);
      this.temporizador = null;
    }
  }
}
