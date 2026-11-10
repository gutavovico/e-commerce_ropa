import { MarcaTiendaComponent } from '../../../../core/tenant/marca-tienda.component';
import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  OnInit,
  computed,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { DatePipe } from '@angular/common';
import { Observable, Subject, Subscription, catchError, debounceTime, of, switchMap } from 'rxjs';
import { LoginService } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import {
  ClientePos,
  CuponPos,
  ETIQUETA_METODO,
  MetodoPagoCaja,
  PedidoWebEfectivo,
  PrevisualizacionPos,
  ReservaPos,
  SucursalOpcion,
  VariantePos,
  VentaPos,
  VentaPosIn,
} from '../modelos/punto-venta.dto';
import { PuntoVentaService } from '../servicios/punto-venta.service';
import { TicketComprobanteComponent } from '../componentes/ticket-comprobante/ticket-comprobante.component';
import { CambioPrendaComponent } from '../componentes/cambio-prenda/cambio-prenda.component';
import { ImportePipe, SimboloMonedaPipe } from '../../../../core/tenant/moneda';
import { MonedaService, formatearImporte } from '../../../../core/tenant/moneda';
import { ConectividadService } from '../../../../core/sin-conexion/conectividad.service';

type Pestana = 'nueva' | 'pendientes' | 'web' | 'cambios';

interface LineaCaja {
  variante: VariantePos;
  cantidad: number;
}

/**
 * CU31-CU32 — Punto de venta presencial.
 *
 * La página nunca calcula importes: los totales salen de `POST /pos/ventas/previsualizar` y el cambio
 * de la respuesta del cobro. El stock que muestra es el informado por el servidor.
 */
@Component({
  selector: 'app-punto-venta',
  standalone: true,
  imports: [ImportePipe, SimboloMonedaPipe, MarcaTiendaComponent, FormsModule, RouterLink, DatePipe, TicketComprobanteComponent, CambioPrendaComponent],
  templateUrl: './punto-venta.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PuntoVentaComponent implements OnInit {
  private readonly servicio = inject(PuntoVentaService);
  private readonly loginService = inject(LoginService);
  private readonly monedas = inject(MonedaService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly router = inject(Router);
  /** CU16 A4 y CU17 A4: la caja opera siempre con conexión. */
  readonly enLinea = inject(ConectividadService).enLinea;

  private readonly campoPrenda = viewChild<ElementRef<HTMLInputElement>>('campoPrenda');

  readonly metodos: { valor: MetodoPagoCaja; etiqueta: string }[] = (
    ['efectivo', 'tarjeta_debito', 'tarjeta_credito', 'qr', 'transferencia'] as MetodoPagoCaja[]
  ).map((valor) => ({ valor, etiqueta: ETIQUETA_METODO[valor] }));

  // --- Contexto -----------------------------------------------------------
  private readonly rol = computed(() =>
    String(this.loginService.usuarioActual()?.rol ?? '').toLowerCase().trim(),
  );
  readonly esAdmin = computed(() => this.rol() === 'administrador' || this.rol() === 'admin');
  /** El cajero tiene la caja como espacio propio: sin panel corporativo, con cierre de sesión. */
  readonly esCajero = computed(() => this.rol() === 'cajero');
  readonly nombreUsuario = computed(() => {
    const u = this.loginService.usuarioActual();
    return `${u?.nombres ?? ''} ${u?.apellidos ?? ''}`.trim() || (u?.email ?? '');
  });
  readonly cerrandoSesion = signal(false);
  readonly sucursales = signal<SucursalOpcion[]>([]);
  /** El administrador elige sucursal (D9); cajero y encargado, solo si tienen más de una
   *  autorizada (P2-CU03, RN07). Con una sola, el servidor usa su sucursal principal. */
  readonly idSucursal = signal<number | null>(null);
  readonly eligeSucursal = computed(() => this.esAdmin() || this.sucursales().length > 1);
  readonly sucursalLista = computed(() => !this.eligeSucursal() || this.idSucursal() !== null);

  readonly pestana = signal<Pestana>('nueva');
  readonly error = signal<string | null>(null);
  readonly aviso = signal<string | null>(null);

  // --- Nueva venta --------------------------------------------------------
  /** Mínimo de caracteres para buscar prendas y clientes. */
  readonly minimoBusqueda = 2;

  readonly textoPrenda = signal('');
  readonly buscandoPrendas = signal(false);
  /** `null`: aún no se ha buscado; `[]`: sin coincidencias. */
  readonly resultadosPrendas = signal<VariantePos[] | null>(null);
  readonly lineas = signal<LineaCaja[]>([]);

  readonly textoCliente = signal('');
  readonly buscandoClientes = signal(false);
  readonly resultadosClientes = signal<ClientePos[] | null>(null);
  readonly cliente = signal<ClientePos | null>(null);

  readonly reservasCliente = signal<ReservaPos[] | null>(null);
  readonly cargandoReservasCliente = signal(false);
  readonly referenciaReserva = signal('');
  readonly cargandoReserva = signal(false);
  readonly reserva = signal<ReservaPos | null>(null);
  readonly excluidas = signal<number[]>([]);

  readonly cupon = signal('');
  readonly cuponAplicado = signal<string | null>(null);
  readonly cupones = signal<CuponPos[] | null>(null);
  readonly buscandoCupones = signal(false);
  readonly mostrarCupones = signal(false);

  private readonly busquedaPrenda$ = new Subject<string>();
  private readonly busquedaCliente$ = new Subject<string>();
  private readonly busquedaCupon$ = new Subject<string>();

  readonly previsualizacion = signal<PrevisualizacionPos | null>(null);
  readonly calculando = signal(false);
  readonly registrando = signal(false);
  private previsualizacionEnCurso: Subscription | null = null;

  readonly hayContenido = computed(() => this.lineas().length > 0 || this.reserva() !== null);

  // --- Cobro y comprobante ------------------------------------------------
  readonly ventaEnCobro = signal<VentaPos | null>(null);
  readonly metodoPago = signal<MetodoPagoCaja>('efectivo');
  readonly montoRecibido = signal('');
  readonly referenciaPago = signal('');
  readonly cobrando = signal(false);
  readonly ventaTicket = signal<VentaPos | null>(null);
  readonly descargandoPdf = signal(false);

  readonly esEfectivo = computed(() => this.metodoPago() === 'efectivo');
  readonly esTarjeta = computed(
    () => this.metodoPago() === 'tarjeta_debito' || this.metodoPago() === 'tarjeta_credito',
  );

  // --- Pendientes y del día -----------------------------------------------
  readonly pendientes = signal<VentaPos[]>([]);
  readonly ventasHoy = signal<VentaPos[]>([]);
  readonly cargandoListas = signal(false);
  readonly ventaAnulando = signal<VentaPos | null>(null);
  readonly motivoAnulacion = signal('');
  readonly anulando = signal(false);

  // --- Pedidos web --------------------------------------------------------
  readonly pedidosWeb = signal<PedidoWebEfectivo[]>([]);
  readonly cargandoPedidos = signal(false);
  readonly procesandoPedido = signal<number | null>(null);

  constructor() {
    // Búsquedas incrementales: se espera a que el cajero deje de teclear y la última sustituye a las
    // anteriores (switchMap), de modo que una respuesta lenta nunca pisa a una más reciente.
    this.busquedaPrenda$
      .pipe(
        debounceTime(300),
        switchMap((texto) =>
          this.buscarConEstado(texto, this.buscandoPrendas, (t) =>
            this.servicio.buscarVariantes(t, this.idSucursal()),
          ),
        ),
        takeUntilDestroyed(),
      )
      .subscribe((resultado) => this.resultadosPrendas.set(resultado));

    this.busquedaCliente$
      .pipe(
        debounceTime(300),
        switchMap((texto) =>
          this.buscarConEstado(texto, this.buscandoClientes, (t) => this.servicio.buscarClientes(t)),
        ),
        takeUntilDestroyed(),
      )
      .subscribe((resultado) => this.resultadosClientes.set(resultado));

    this.busquedaCupon$
      .pipe(
        debounceTime(250),
        switchMap((texto) => this.buscarConEstado(texto, this.buscandoCupones, (t) => this.servicio.listarCupones(t), 0)),
        takeUntilDestroyed(),
      )
      .subscribe((resultado) => this.cupones.set(resultado));
  }

  /** Lanza la búsqueda si hay texto suficiente; ante error lo muestra y deja la lista vacía. */
  private buscarConEstado<T>(
    texto: string,
    cargando: { set(valor: boolean): void },
    consulta: (texto: string) => Observable<T[]>,
    minimo = this.minimoBusqueda,
  ): Observable<T[] | null> {
    const limpio = texto.trim();
    if (limpio.length < minimo) {
      cargando.set(false);
      return of(null);
    }
    cargando.set(true);
    return consulta(limpio).pipe(
      catchError((e) => {
        this.mostrarError(e, 'No se pudo completar la búsqueda.');
        return of([] as T[]);
      }),
      switchMap((resultado) => {
        cargando.set(false);
        return of(resultado);
      }),
    );
  }

  ngOnInit(): void {
    if (this.esAdmin()) {
      this.servicio
        .listarSucursales()
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({
          next: (lista) => this.sucursales.set(lista),
          error: (e) => this.mostrarError(e, 'No se pudieron cargar las sucursales.'),
        });
    } else {
      this.servicio
        .misSucursales()
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({
          next: (lista) => {
            if (lista.length <= 1) return;
            this.sucursales.set(lista.map((s) => ({ id_sucursal: s.id_sucursal, nombre: s.nombre })));
            // Empieza en la principal, que es donde ya operaba
            this.seleccionarSucursal(lista.find((s) => s.es_principal)?.id_sucursal ?? lista[0].id_sucursal);
          },
          error: (e) => this.mostrarError(e, 'No se pudieron cargar tus sucursales.'),
        });
    }
    this.enfocarBuscador();
  }

  // =========================================================================
  // Contexto y pestañas
  // =========================================================================

  seleccionarSucursal(valor: string | number | null): void {
    const id = valor ? Number(valor) : null;
    if (id === this.idSucursal()) return;
    this.idSucursal.set(id);
    this.limpiarVenta();
    this.ventaEnCobro.set(null);
    this.ventaTicket.set(null);
    this.recargarPestana();
  }

  cambiarPestana(pestana: Pestana): void {
    this.pestana.set(pestana);
    this.error.set(null);
    this.recargarPestana();
  }

  private recargarPestana(): void {
    if (!this.sucursalLista()) return;
    if (this.pestana() === 'pendientes') this.cargarListas();
    if (this.pestana() === 'web') this.cargarPedidosWeb();
    if (this.pestana() === 'nueva') this.enfocarBuscador();
  }

  cerrarError(): void {
    this.error.set(null);
    this.enfocarBuscador();
  }

  // =========================================================================
  // Nueva venta (CU31)
  // =========================================================================

  /** Busca por nombre, categoría o SKU mientras el cajero escribe. */
  alEscribirPrenda(texto: string): void {
    this.textoPrenda.set(texto);
    if (texto.trim().length < this.minimoBusqueda) this.resultadosPrendas.set(null);
    this.busquedaPrenda$.next(texto);
  }

  limpiarBusquedaPrenda(): void {
    this.alEscribirPrenda('');
    this.enfocarBuscador();
  }

  /** Unidades de la variante ya añadidas en caja (para avisar antes de superar el stock). */
  cantidadEnVenta(idVariante: number): number {
    return this.lineas().find((l) => l.variante.id_variante === idVariante)?.cantidad ?? 0;
  }

  agregarVariante(variante: VariantePos): void {
    this.error.set(null);
    const existente = this.lineas().find((l) => l.variante.id_variante === variante.id_variante);
    const cantidad = (existente?.cantidad ?? 0) + 1;
    if (variante.disponible_en_sucursal < cantidad) {
      this.error.set(
        `Sin stock suficiente de ${variante.nombre_producto} (${variante.talla_codigo}/${variante.color_nombre}) en esta boutique: disponibles ${variante.disponible_en_sucursal}.`,
      );
      return;
    }
    if (existente) {
      this.lineas.update((ls) =>
        ls.map((l) => (l.variante.id_variante === variante.id_variante ? { variante, cantidad } : l)),
      );
    } else {
      this.lineas.update((ls) => [...ls, { variante, cantidad: 1 }]);
    }
    this.previsualizar();
  }

  cambiarCantidad(idVariante: number, valor: number | string): void {
    const cantidad = Math.trunc(Number(valor));
    const linea = this.lineas().find((l) => l.variante.id_variante === idVariante);
    if (!linea || !Number.isFinite(cantidad)) return;
    if (cantidad < 1) {
      this.quitarLinea(idVariante);
      return;
    }
    if (cantidad > linea.variante.disponible_en_sucursal) {
      this.error.set(`Solo hay ${linea.variante.disponible_en_sucursal} unidades disponibles.`);
      this.lineas.update((ls) => [...ls]);
      return;
    }
    this.lineas.update((ls) =>
      ls.map((l) => (l.variante.id_variante === idVariante ? { ...l, cantidad } : l)),
    );
    this.previsualizar();
  }

  quitarLinea(idVariante: number): void {
    this.lineas.update((ls) => ls.filter((l) => l.variante.id_variante !== idVariante));
    this.previsualizar();
    this.enfocarBuscador();
  }

  /** Busca clientes registrados por nombre, apellidos o correo mientras se escribe. */
  alEscribirCliente(texto: string): void {
    this.textoCliente.set(texto);
    if (texto.trim().length < this.minimoBusqueda) this.resultadosClientes.set(null);
    this.busquedaCliente$.next(texto);
  }

  /** Al elegir un cliente se consultan sus reservas activas en esta boutique. */
  seleccionarCliente(cliente: ClientePos): void {
    this.cliente.set(cliente);
    this.textoCliente.set('');
    this.resultadosClientes.set(null);
    this.cargarReservasCliente(cliente.id_cliente);
    this.previsualizar();
  }

  private cargarReservasCliente(idCliente: number): void {
    this.reservasCliente.set(null);
    this.cargandoReservasCliente.set(true);
    this.servicio
      .reservasDeCliente(idCliente, this.idSucursal())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (reservas) => {
          this.cargandoReservasCliente.set(false);
          // Si en el intervalo se cambió de cliente, la respuesta ya no aplica.
          if (this.cliente()?.id_cliente === idCliente) this.reservasCliente.set(reservas);
        },
        error: (e) => {
          this.cargandoReservasCliente.set(false);
          this.mostrarError(e, 'No se pudieron consultar las reservas del cliente.');
        },
      });
  }

  /** Sin cliente, la venta se registra como presencial sin cuenta. */
  ventaSinRegistro(): void {
    if (this.reserva()?.cliente) return; // La reserva fija al cliente.
    this.cliente.set(null);
    this.reservasCliente.set(null);
    this.alEscribirCliente('');
    this.previsualizar();
  }

  cargarReserva(referenciaElegida?: string): void {
    const referencia = (referenciaElegida ?? this.referenciaReserva()).trim();
    if (!referencia || this.cargandoReserva() || !this.sucursalLista()) return;
    this.cargandoReserva.set(true);
    this.error.set(null);
    this.servicio
      .consultarReserva(referencia, this.idSucursal())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (reserva) => {
          this.cargandoReserva.set(false);
          this.reserva.set(reserva);
          this.excluidas.set([]);
          if (reserva.cliente) {
            this.cliente.set(reserva.cliente);
            this.textoCliente.set('');
            this.resultadosClientes.set(null);
          }
          this.previsualizar();
          this.enfocarBuscador();
        },
        error: (e) => {
          this.cargandoReserva.set(false);
          this.mostrarError(e, 'No se pudo cargar la reserva.');
        },
      });
  }

  quitarReserva(): void {
    this.reserva.set(null);
    this.excluidas.set([]);
    this.referenciaReserva.set('');
    this.previsualizar();
  }

  estaExcluida(idVariante: number): boolean {
    return this.excluidas().includes(idVariante);
  }

  alternarExclusion(idVariante: number): void {
    this.excluidas.update((ids) =>
      ids.includes(idVariante) ? ids.filter((id) => id !== idVariante) : [...ids, idVariante],
    );
    this.previsualizar();
  }

  /** Al entrar al campo se listan todos los cupones vigentes (texto vacío). */
  abrirCupones(): void {
    this.mostrarCupones.set(true);
    if (this.cupones() === null) this.busquedaCupon$.next(this.cupon());
  }

  cerrarCupones(): void {
    this.mostrarCupones.set(false);
  }

  /** Filtra por código o nombre del cupón; vacío, vuelve a mostrarlos todos. */
  alEscribirCupon(texto: string): void {
    this.cupon.set(texto);
    this.mostrarCupones.set(true);
    this.busquedaCupon$.next(texto);
  }

  elegirCupon(cupon: CuponPos): void {
    this.cupon.set(cupon.codigo);
    this.mostrarCupones.set(false);
    this.aplicarCupon();
  }

  aplicarCupon(): void {
    this.cuponAplicado.set(this.cupon().trim().toUpperCase() || null);
    this.mostrarCupones.set(false);
    this.previsualizar();
  }

  quitarCupon(): void {
    this.cupon.set('');
    this.cuponAplicado.set(null);
    this.previsualizar();
  }

  /** Describe el cupón tal como lo define la promoción (no es un importe calculado). */
  etiquetaCupon(cupon: CuponPos): string {
    return cupon.tipo_descuento === 'monto_fijo'
      ? formatearImporte(cupon.valor_descuento, this.monedas.actual())
      : `${cupon.valor_descuento} %`;
  }

  private cuerpoVenta(): VentaPosIn {
    return {
      id_sucursal: this.eligeSucursal() ? this.idSucursal() : null,
      id_cliente: this.cliente()?.id_cliente ?? null,
      reserva: this.reserva()?.codigo ?? null,
      codigo_cupon: this.cuponAplicado(),
      lineas: this.lineas().map((l) => ({ id_variante: l.variante.id_variante, cantidad: l.cantidad })),
      lineas_reserva_excluidas: this.excluidas(),
    };
  }

  /** Recalcula los totales en el servidor; la última petición reemplaza a las anteriores. */
  private previsualizar(): void {
    this.previsualizacionEnCurso?.unsubscribe();
    if (!this.hayContenido()) {
      this.previsualizacion.set(null);
      this.calculando.set(false);
      return;
    }
    this.calculando.set(true);
    this.previsualizacionEnCurso = this.servicio
      .previsualizar(this.cuerpoVenta())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (resultado) => {
          this.calculando.set(false);
          this.previsualizacion.set(resultado);
        },
        error: (e) => {
          this.calculando.set(false);
          this.previsualizacion.set(null);
          this.mostrarError(e, 'No se pudieron calcular los totales.');
        },
      });
  }

  registrarVenta(): void {
    if (!this.enLinea() || !this.previsualizacion() || this.registrando() || this.calculando()) return;
    this.registrando.set(true);
    this.error.set(null);
    this.servicio
      .registrarVenta(this.cuerpoVenta())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (venta) => {
          this.registrando.set(false);
          this.limpiarVenta();
          this.abrirCobro(venta);
          this.aviso.set(`Venta ${venta.numero_comprobante} registrada: pendiente de cobro.`);
        },
        error: (e) => {
          this.registrando.set(false);
          this.mostrarError(e, 'No se pudo registrar la venta.');
        },
      });
  }

  limpiarVenta(): void {
    this.previsualizacionEnCurso?.unsubscribe();
    this.lineas.set([]);
    this.textoPrenda.set('');
    this.resultadosPrendas.set(null);
    this.cliente.set(null);
    this.textoCliente.set('');
    this.resultadosClientes.set(null);
    this.reservasCliente.set(null);
    this.reserva.set(null);
    this.referenciaReserva.set('');
    this.excluidas.set([]);
    this.cupon.set('');
    this.cuponAplicado.set(null);
    this.previsualizacion.set(null);
    this.calculando.set(false);
    this.enfocarBuscador();
  }

  // =========================================================================
  // Cobro (CU32)
  // =========================================================================

  abrirCobro(venta: VentaPos): void {
    this.ventaEnCobro.set(venta);
    this.ventaTicket.set(null);
    this.metodoPago.set('efectivo');
    this.montoRecibido.set('');
    this.referenciaPago.set('');
    this.pestana.set('nueva');
  }

  cancelarCobro(): void {
    this.ventaEnCobro.set(null);
    this.enfocarBuscador();
  }

  /** `aprobado = false` registra el rechazo del datáfono: la venta sigue pendiente. */
  cobrar(aprobado = true): void {
    const venta = this.ventaEnCobro();
    if (!this.enLinea() || !venta || this.cobrando()) return;
    const monto = this.montoRecibido().trim().replace(',', '.');
    this.cobrando.set(true);
    this.error.set(null);
    this.servicio
      .cobrar(venta.id_venta, {
        metodo_pago: this.metodoPago(),
        monto_recibido: this.esEfectivo() && monto ? monto : null,
        referencia: this.esEfectivo() ? null : this.referenciaPago().trim() || null,
        aprobado,
      })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (actualizada) => {
          this.cobrando.set(false);
          if (actualizada.estado === 'pagada') {
            this.ventaEnCobro.set(null);
            this.ventaTicket.set(actualizada);
            this.aviso.set(`Venta ${actualizada.numero_comprobante} cobrada.`);
          } else {
            this.ventaEnCobro.set(actualizada);
            this.referenciaPago.set('');
            this.aviso.set('Cobro rechazado por el datáfono: la venta sigue pendiente.');
          }
        },
        error: (e) => {
          this.cobrando.set(false);
          this.mostrarError(e, 'No se pudo registrar el cobro.');
        },
      });
  }

  verTicket(venta: VentaPos): void {
    this.ventaTicket.set(venta);
  }

  cerrarTicket(): void {
    this.ventaTicket.set(null);
    this.enfocarBuscador();
  }

  descargarPdf(): void {
    const venta = this.ventaTicket();
    if (!venta || this.descargandoPdf()) return;
    this.descargandoPdf.set(true);
    this.servicio
      .descargarComprobante(venta.id_venta)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (blob) => {
          this.descargandoPdf.set(false);
          const url = URL.createObjectURL(blob);
          const enlace = document.createElement('a');
          enlace.href = url;
          enlace.download = `${venta.numero_comprobante}.pdf`;
          enlace.click();
          setTimeout(() => URL.revokeObjectURL(url), 0);
        },
        error: (e) => {
          this.descargandoPdf.set(false);
          this.mostrarError(e, 'No se pudo descargar el comprobante.');
        },
      });
  }

  // =========================================================================
  // Pendientes y ventas del día
  // =========================================================================

  cargarListas(): void {
    this.cargandoListas.set(true);
    const id = this.idSucursal();
    let restantes = 2;
    const terminar = () => {
      restantes -= 1;
      if (restantes === 0) this.cargandoListas.set(false);
    };
    this.servicio
      .listarVentas(id, { estado: 'pendiente', soloHoy: false })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (ventas) => {
          this.pendientes.set(ventas);
          terminar();
        },
        error: (e) => {
          terminar();
          this.mostrarError(e, 'No se pudieron cargar las ventas pendientes.');
        },
      });
    this.servicio
      .listarVentas(id, { soloHoy: true })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (ventas) => {
          this.ventasHoy.set(ventas);
          terminar();
        },
        error: (e) => {
          terminar();
          this.mostrarError(e, 'No se pudieron cargar las ventas del día.');
        },
      });
  }

  pedirAnulacion(venta: VentaPos): void {
    this.ventaAnulando.set(venta);
    this.motivoAnulacion.set('');
  }

  cancelarAnulacion(): void {
    this.ventaAnulando.set(null);
  }

  confirmarAnulacion(): void {
    const venta = this.ventaAnulando();
    const motivo = this.motivoAnulacion().trim();
    if (!venta || motivo.length < 3 || this.anulando()) return;
    this.anulando.set(true);
    this.servicio
      .anular(venta.id_venta, motivo)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (anulada) => {
          this.anulando.set(false);
          this.ventaAnulando.set(null);
          if (this.ventaEnCobro()?.id_venta === anulada.id_venta) this.ventaEnCobro.set(null);
          this.aviso.set(`Venta ${anulada.numero_comprobante} anulada; el stock retenido se liberó.`);
          this.cargarListas();
        },
        error: (e) => {
          this.anulando.set(false);
          this.mostrarError(e, 'No se pudo anular la venta.');
        },
      });
  }

  // =========================================================================
  // Pedidos web por cobrar (CU16)
  // =========================================================================

  cargarPedidosWeb(): void {
    this.cargandoPedidos.set(true);
    this.servicio
      .listarPedidosWebEfectivo(this.idSucursal())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (pedidos) => {
          this.cargandoPedidos.set(false);
          this.pedidosWeb.set(pedidos);
        },
        error: (e) => {
          this.cargandoPedidos.set(false);
          this.mostrarError(e, 'No se pudieron cargar los pedidos web.');
        },
      });
  }

  confirmarPedidoWeb(pedido: PedidoWebEfectivo): void {
    this.procesarPedidoWeb(pedido, true);
  }

  cancelarPedidoWeb(pedido: PedidoWebEfectivo): void {
    this.procesarPedidoWeb(pedido, false);
  }

  private procesarPedidoWeb(pedido: PedidoWebEfectivo, confirmar: boolean): void {
    if (this.procesandoPedido() !== null) return;
    this.procesandoPedido.set(pedido.id_pago);
    const peticion = confirmar
      ? this.servicio.confirmarPedidoWeb(pedido.id_pago)
      : this.servicio.cancelarPedidoWeb(pedido.id_pago);
    peticion.pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.procesandoPedido.set(null);
        this.aviso.set(
          confirmar
            ? `Pedido ${pedido.numero_comprobante} cobrado en efectivo.`
            : `Pedido ${pedido.numero_comprobante} cancelado.`,
        );
        this.cargarPedidosWeb();
      },
      error: (e) => {
        this.procesandoPedido.set(null);
        this.mostrarError(e, 'No se pudo procesar el pedido web.');
      },
    });
  }

  // =========================================================================
  // Utilidades
  // =========================================================================

  cerrarSesion(): void {
    if (this.cerrandoSesion()) return;
    this.cerrandoSesion.set(true);
    this.loginService.cerrarSesion().subscribe({
      next: () => this.router.navigate(['/login']),
      error: () => this.router.navigate(['/login']),
      complete: () => this.cerrandoSesion.set(false),
    });
  }

  etiquetaMetodo(metodo: string): string {
    return ETIQUETA_METODO[metodo] ?? metodo;
  }

  /** Devuelve el foco al buscador de prendas tras cada operación de la venta. */
  enfocarBuscador(): void {
    if (this.pestana() !== 'nueva') return;
    setTimeout(() => this.campoPrenda()?.nativeElement.focus(), 0);
  }

  private mostrarError(error: unknown, porDefecto: string): void {
    this.aviso.set(null);
    this.error.set(PuntoVentaService.mensajeError(error, porDefecto));
  }
}
