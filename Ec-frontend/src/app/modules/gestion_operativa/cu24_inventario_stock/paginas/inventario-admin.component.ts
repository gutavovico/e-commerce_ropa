import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  NonNullableFormBuilder,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { RouterLink } from '@angular/router';
import { InventarioAdminService } from '../servicios/inventario-admin.service';
import { SucursalesAdminService } from '../../cu21_sucursales_ciudades/servicios/sucursales-admin.service';
import { AtributosAdminService } from '../../cu23_categorias_tallas_colores/servicios/atributos-admin.service';
import { ProductosAdminService } from '../../cu22_prendas_productos/servicios/productos-admin.service';
import { LoginService } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import {
  EstadoStock,
  InventarioAjustePayload,
  InventarioCrearPayload,
  InventarioItemAdmin,
  TipoAjusteManual,
  TransferenciaPayload,
} from '../modelos/inventario.dto';

@Component({
  selector: 'app-inventario-admin',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './inventario-admin.component.html',
  styleUrls: ['./inventario-admin.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class InventarioAdminComponent implements OnInit {
  protected readonly inventarioService = inject(InventarioAdminService);
  protected readonly sucursalesService = inject(SucursalesAdminService);
  protected readonly atributosService = inject(AtributosAdminService);
  protected readonly productosService = inject(ProductosAdminService);
  private readonly loginService = inject(LoginService);
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly cdr = inject(ChangeDetectorRef);

  // --- Roles y Privilegios RBAC ---
  readonly usuario = computed(() => this.loginService.usuarioActual());
  readonly rolUsuario = computed(() =>
    String(this.usuario()?.rol || '').toLowerCase().trim()
  );
  readonly esAdmin = computed(() => this.rolUsuario() === 'administrador');
  readonly esEncargado = computed(() => this.rolUsuario() === 'encargado_sucursal');
  readonly idSucursalEncargado = computed(() => this.usuario()?.id_sucursal ?? null);

  readonly nombreSucursalEncargado = computed(() => {
    const id = this.idSucursalEncargado();
    if (!id) return '';
    const suc = this.sucursalesService.sucursales().find((s) => s.id_sucursal === id);
    return suc ? `${suc.nombre} (${suc.ciudad_nombre || ''})` : `Sucursal #${id}`;
  });

  // --- Filtros reactivos de consulta ---
  readonly busquedaTexto = signal<string>('');
  readonly filtroSucursal = signal<number | null>(null);
  readonly filtroCategoria = signal<number | null>(null);
  readonly filtroEstado = signal<string>('todos');
  readonly paginaActual = signal<number>(1);
  readonly limitePorPagina = signal<number>(10);

  // --- Modales y Formularios ---
  readonly modalCrearAbierto = signal<boolean>(false);
  readonly modalAjusteAbierto = signal<boolean>(false);
  readonly modalTransferenciaAbierto = signal<boolean>(false);
  readonly modalKardexAbierto = signal<boolean>(false);
  readonly itemSeleccionado = signal<InventarioItemAdmin | null>(null);

  // Luxury Banner de alertas contextuales
  readonly errorBanner = signal<string | null>(null);

  private debounceTimer: any = null;

  // Formulario 1: Alta de Stock Inicial (Recepcion)
  readonly formCrear = this.fb.group({
    id_sucursal: [null as number | null, [Validators.required]],
    id_producto: [null as number | null, [Validators.required]],
    id_variante: [null as number | null, [Validators.required]],
    cantidad_inicial: [1, [Validators.required, Validators.min(0)]],
    stock_minimo: [0, [Validators.required, Validators.min(0)]],
    stock_alerta: [5, [Validators.required, Validators.min(0)]],
    referencia_documento: [''],
    observacion: [''],
  });

  // Formulario 2: Ajuste Fisico Manual
  readonly formAjuste = this.fb.group({
    tipo_ajuste: ['incremento' as TipoAjusteManual, [Validators.required]],
    cantidad: [1, [Validators.required, Validators.min(1)]],
    motivo: ['', [Validators.required, Validators.minLength(5)]],
    referencia_documento: [''],
  });

  // Formulario 3: Transferencia Inter-Sucursal
  readonly formTransferencia = this.fb.group({
    id_sucursal_destino: [null as number | null, [Validators.required]],
    cantidad: [1, [Validators.required, Validators.min(1)]],
    motivo: ['', [Validators.required, Validators.minLength(5)]],
  });

  // Sucursales destino disponibles para transferencia (excluye la de origen)
  readonly sucursalesDestinoDisponibles = computed(() => {
    const item = this.itemSeleccionado();
    const todas = this.sucursalesService.sucursales();
    if (!item) return todas.filter((s) => s.activa !== false);
    return todas.filter(
      (s) => s.activa !== false && s.id_sucursal !== item.id_sucursal
    );
  });

  // Variantes del producto seleccionado en el modal de creacion
  readonly variantesDisponibles = computed(() => this.productosService.variantes());

  ngOnInit(): void {
    if (this.esEncargado() && this.idSucursalEncargado()) {
      this.filtroSucursal.set(this.idSucursalEncargado());
    }

    this.cargarCatalogosBase();
    this.aplicarFiltros();

    // Al seleccionar producto en alta inicial, cargar sus variantes dinamicamente
    this.formCrear.get('id_producto')?.valueChanges.subscribe((idProd) => {
      if (idProd) {
        this.productosService.cargarProductoPorId(Number(idProd)).subscribe();
        this.formCrear.patchValue({ id_variante: null });
        this.cdr.markForCheck();
      }
    });
  }

  cargarCatalogosBase(): void {
    this.sucursalesService.cargarSucursales().subscribe();
    this.atributosService.cargarCategorias().subscribe();
    this.productosService.cargarProductos({ limite: 100, activo: true }).subscribe();
  }

  // --- Filtros y Paginacion ---

  onBuscarInput(evento: Event): void {
    const valor = (evento.target as HTMLInputElement).value;
    this.busquedaTexto.set(valor);
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }
    this.debounceTimer = setTimeout(() => {
      this.paginaActual.set(1);
      this.aplicarFiltros();
    }, 300);
  }

  onCambiarFiltroSucursal(evento: Event): void {
    if (this.esEncargado()) return;
    const valor = (evento.target as HTMLSelectElement).value;
    this.filtroSucursal.set(valor ? Number(valor) : null);
    this.paginaActual.set(1);
    this.aplicarFiltros();
  }

  onCambiarFiltroCategoria(evento: Event): void {
    const valor = (evento.target as HTMLSelectElement).value;
    this.filtroCategoria.set(valor ? Number(valor) : null);
    this.paginaActual.set(1);
    this.aplicarFiltros();
  }

  onCambiarFiltroEstado(evento: Event): void {
    const estado = (evento.target as HTMLSelectElement).value;
    this.filtroEstado.set(estado);
    this.paginaActual.set(1);
    this.aplicarFiltros();
  }

  aplicarFiltros(): void {
    const idSucursal = this.esEncargado()
      ? this.idSucursalEncargado()
      : this.filtroSucursal();

    this.inventarioService
      .cargarInventario({
        q: this.busquedaTexto() || undefined,
        id_sucursal: idSucursal || undefined,
        id_categoria: this.filtroCategoria() || undefined,
        estado_stock:
          this.filtroEstado() !== 'todos' ? this.filtroEstado() : undefined,
        pagina: this.paginaActual(),
        limite: this.limitePorPagina(),
      })
      .subscribe();
  }

  cambiarPagina(nuevaPagina: number): void {
    if (nuevaPagina < 1 || nuevaPagina > this.inventarioService.totalPaginas()) {
      return;
    }
    this.paginaActual.set(nuevaPagina);
    this.aplicarFiltros();
  }

  // --- Modal 1: Alta de Stock Inicial (Recepcion) ---

  abrirModalCrear(): void {
    this.errorBanner.set(null);
    const idSucursalDefault = this.esEncargado()
      ? this.idSucursalEncargado()
      : this.filtroSucursal() || null;

    this.formCrear.reset({
      id_sucursal: idSucursalDefault,
      id_producto: null,
      id_variante: null,
      cantidad_inicial: 1,
      stock_minimo: 0,
      stock_alerta: 5,
      referencia_documento: '',
      observacion: '',
    });

    this.modalCrearAbierto.set(true);
    this.cdr.markForCheck();
  }

  cerrarModalCrear(): void {
    this.modalCrearAbierto.set(false);
    this.errorBanner.set(null);
  }

  guardarStockInicial(): void {
    if (this.formCrear.invalid) {
      this.formCrear.markAllAsTouched();
      return;
    }

    this.errorBanner.set(null);
    const formVals = this.formCrear.getRawValue();

    if (!formVals.id_sucursal || !formVals.id_variante) {
      this.errorBanner.set('Debe seleccionar una boutique y una variante de prenda valida.');
      return;
    }

    const payload: InventarioCrearPayload = {
      id_sucursal: Number(formVals.id_sucursal),
      id_variante: Number(formVals.id_variante),
      cantidad_inicial: Number(formVals.cantidad_inicial),
      stock_minimo: Number(formVals.stock_minimo),
      stock_alerta: Number(formVals.stock_alerta),
      referencia_documento: formVals.referencia_documento.trim() || undefined,
      observacion: formVals.observacion.trim() || undefined,
    };

    this.inventarioService.crearStockInicial(payload).subscribe({
      next: () => {
        this.cerrarModalCrear();
        this.aplicarFiltros();
      },
      error: (err) => {
        this.errorBanner.set(err.message);
        this.cdr.markForCheck();
      },
    });
  }

  // --- Modal 2: Ajuste Fisico Manual ---

  abrirModalAjuste(item: InventarioItemAdmin): void {
    this.errorBanner.set(null);
    this.itemSeleccionado.set(item);

    this.formAjuste.reset({
      tipo_ajuste: 'incremento',
      cantidad: 1,
      motivo: '',
      referencia_documento: '',
    });

    this.modalAjusteAbierto.set(true);
    this.cdr.markForCheck();
  }

  cerrarModalAjuste(): void {
    this.modalAjusteAbierto.set(false);
    this.itemSeleccionado.set(null);
    this.errorBanner.set(null);
  }

  guardarAjuste(): void {
    if (this.formAjuste.invalid) {
      this.formAjuste.markAllAsTouched();
      return;
    }

    const item = this.itemSeleccionado();
    if (!item) return;

    this.errorBanner.set(null);
    const formVals = this.formAjuste.getRawValue();

    if (
      formVals.tipo_ajuste === 'decremento' &&
      Number(formVals.cantidad) > item.cantidad_disponible
    ) {
      this.errorBanner.set(
        `El decremento solicitado (${formVals.cantidad}) excede el saldo disponible actual (${item.cantidad_disponible} unidades).`
      );
      return;
    }

    const payload: InventarioAjustePayload = {
      tipo_ajuste: formVals.tipo_ajuste,
      cantidad: Number(formVals.cantidad),
      motivo: formVals.motivo.trim(),
      referencia_documento: formVals.referencia_documento.trim() || undefined,
    };

    this.inventarioService.ajustarStock(item.id_inventario, payload).subscribe({
      next: () => {
        this.cerrarModalAjuste();
        this.aplicarFiltros();
      },
      error: (err) => {
        this.errorBanner.set(err.message);
        this.cdr.markForCheck();
      },
    });
  }

  // --- Modal 3: Transferencia Inter-Sucursal ---

  abrirModalTransferencia(item: InventarioItemAdmin): void {
    if (item.cantidad_disponible <= 0) {
      return;
    }

    this.errorBanner.set(null);
    this.itemSeleccionado.set(item);

    this.formTransferencia.reset({
      id_sucursal_destino: null,
      cantidad: 1,
      motivo: '',
    });

    // Validar tope segun stock disponible
    this.formTransferencia
      .get('cantidad')
      ?.setValidators([
        Validators.required,
        Validators.min(1),
        Validators.max(item.cantidad_disponible),
      ]);
    this.formTransferencia.get('cantidad')?.updateValueAndValidity();

    this.modalTransferenciaAbierto.set(true);
    this.cdr.markForCheck();
  }

  cerrarModalTransferencia(): void {
    this.modalTransferenciaAbierto.set(false);
    this.itemSeleccionado.set(null);
    this.errorBanner.set(null);
  }

  guardarTransferencia(): void {
    if (this.formTransferencia.invalid) {
      this.formTransferencia.markAllAsTouched();
      return;
    }

    const item = this.itemSeleccionado();
    if (!item) return;

    this.errorBanner.set(null);
    const formVals = this.formTransferencia.getRawValue();

    if (!formVals.id_sucursal_destino) {
      this.errorBanner.set('Debe seleccionar la sucursal de destino.');
      return;
    }

    if (Number(formVals.id_sucursal_destino) === item.id_sucursal) {
      this.errorBanner.set('La sucursal de destino no puede ser la misma de origen.');
      return;
    }

    if (Number(formVals.cantidad) > item.cantidad_disponible) {
      this.errorBanner.set(
        `La cantidad a transferir (${formVals.cantidad}) excede el disponible (${item.cantidad_disponible}).`
      );
      return;
    }

    const payload: TransferenciaPayload = {
      id_sucursal_origen: item.id_sucursal,
      id_sucursal_destino: Number(formVals.id_sucursal_destino),
      id_variante: item.id_variante,
      cantidad: Number(formVals.cantidad),
      motivo: formVals.motivo.trim(),
    };

    this.inventarioService.transferirMercaderia(payload).subscribe({
      next: () => {
        this.cerrarModalTransferencia();
        this.aplicarFiltros();
      },
      error: (err) => {
        this.errorBanner.set(err.message);
        this.cdr.markForCheck();
      },
    });
  }

  // --- Modal 4: Kardex de Movimientos ---

  abrirModalKardex(item: InventarioItemAdmin): void {
    this.errorBanner.set(null);
    this.itemSeleccionado.set(item);
    this.modalKardexAbierto.set(true);
    this.inventarioService.cargarKardex(item.id_inventario).subscribe({
      error: (err) => {
        this.errorBanner.set(err.message);
        this.cdr.markForCheck();
      },
    });
    this.cdr.markForCheck();
  }

  cerrarModalKardex(): void {
    this.modalKardexAbierto.set(false);
    this.itemSeleccionado.set(null);
  }

  // --- Helpers de Diseno y Formato Editorial ---

  obtenerClaseBadgeEstado(estado: EstadoStock | string): string {
    switch (estado) {
      case 'optimo':
        return 'bg-emerald-50 text-emerald-800 border-emerald-200';
      case 'alerta_baja':
        return 'bg-[#FAF7F2] text-[#AD8C63] border-[#ECE4D8]';
      case 'agotado':
        return 'bg-rose-50 text-rose-800 border-rose-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  }

  obtenerDotColorEstado(estado: EstadoStock | string): string {
    switch (estado) {
      case 'optimo':
        return 'bg-emerald-500';
      case 'alerta_baja':
        return 'bg-[#AD8C63]';
      case 'agotado':
        return 'bg-rose-500';
      default:
        return 'bg-slate-400';
    }
  }

  obtenerEtiquetaEstado(estado: EstadoStock | string): string {
    switch (estado) {
      case 'optimo':
        return 'Optimo';
      case 'alerta_baja':
        return 'Alerta de Reposicion';
      case 'agotado':
        return 'Agotado';
      default:
        return 'Sin definir';
    }
  }

  obtenerEtiquetaMovimiento(tipo: string): string {
    switch (tipo) {
      case 'ingreso_proveedor':
        return 'Ingreso Proveedor';
      case 'ajuste_positivo':
        return 'Ajuste Positivo';
      case 'ajuste_negativo':
        return 'Ajuste Negativo';
      case 'transferencia_salida':
        return 'Traspaso (Salida)';
      case 'transferencia_entrada':
        return 'Traspaso (Entrada)';
      case 'venta_confirmada':
      case 'venta':
        return 'Venta Despachada';
      case 'cancelacion_pedido':
      case 'devolucion':
        return 'Reingreso / Devolucion';
      case 'reserva':
        return 'Reserva de Pedido';
      case 'liberacion_reserva':
        return 'Liberacion Reserva';
      default:
        return tipo.replace(/_/g, ' ');
    }
  }

  esMovimientoPositivo(tipo: string, variacion: number): boolean {
    if (variacion > 0) return true;
    return (
      tipo === 'ingreso_proveedor' ||
      tipo === 'ajuste_positivo' ||
      tipo === 'transferencia_entrada' ||
      tipo === 'cancelacion_pedido' ||
      tipo === 'devolucion'
    );
  }

  descartarErrorBanner(): void {
    this.errorBanner.set(null);
    this.inventarioService.limpiarMensajes();
  }
}
