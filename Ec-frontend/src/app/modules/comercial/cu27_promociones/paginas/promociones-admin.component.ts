/**
 * Componente de Gestion Administrativa para CU27: Gestionar promociones.
 * Nomenclatura oficial: "Gestionar promociones"
 */

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
  AbstractControl,
  NonNullableFormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  ValidatorFn,
  Validators,
} from '@angular/forms';
import { RouterLink } from '@angular/router';
import { PromocionesAdminService } from '../servicios/promociones-admin.service';
import { LoginService } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import {
  AlcancePromocion,
  EstadoVigencia,
  PromocionActualizarDto,
  PromocionCrearDto,
  PromocionItem,
  TipoDescuento,
} from '../modelos/promociones.dto';

export const validadorPromocion: ValidatorFn = (
  control: AbstractControl
): ValidationErrors | null => {
  const fechaInicio = control.get('fecha_inicio')?.value;
  const fechaFin = control.get('fecha_fin')?.value;
  const tipoDescuento = control.get('tipo_descuento')?.value;
  const valorDescuento = control.get('valor_descuento')?.value;
  const alcance = control.get('alcance')?.value;
  const idCategoria = control.get('id_categoria')?.value;
  const idProducto = control.get('id_producto')?.value;

  const errores: Record<string, string> = {};

  if (fechaInicio && fechaFin) {
    const dInicio = new Date(fechaInicio);
    const dFin = new Date(fechaFin);
    if (dFin <= dInicio) {
      errores['fechasInvalidas'] =
        'La fecha de finalizacion debe ser estrictamente posterior a la fecha de inicio.';
    }
  }

  if (tipoDescuento === 'porcentaje') {
    if (valorDescuento !== null && valorDescuento !== undefined) {
      const v = Number(valorDescuento);
      if (v < 1 || v > 100) {
        errores['porcentajeInvalido'] =
          'El porcentaje de descuento debe situarse entre el 1.00% y el 100.00%.';
      }
    }
  } else if (tipoDescuento === 'monto_fijo') {
    if (valorDescuento !== null && valorDescuento !== undefined) {
      const v = Number(valorDescuento);
      if (v <= 0) {
        errores['montoInvalido'] =
          'El monto fijo de descuento debe ser estrictamente mayor a 0.';
      }
    }
  }

  if (alcance === 'categoria' && !idCategoria) {
    errores['categoriaRequerida'] =
      'Debe seleccionar una categoria para el alcance por categoria.';
  }

  if (alcance === 'producto' && !idProducto) {
    errores['productoRequerido'] =
      'Debe seleccionar un producto para el alcance por producto.';
  }

  return Object.keys(errores).length > 0 ? errores : null;
};

@Component({
  selector: 'app-promociones-admin',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './promociones-admin.component.html',
  styleUrls: ['./promociones-admin.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PromocionesAdminComponent implements OnInit {
  protected readonly servicio = inject(PromocionesAdminService);
  private readonly loginService = inject(LoginService);
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly cdr = inject(ChangeDetectorRef);

  // --- Seguridad y RBAC ---
  readonly usuario = computed(() => this.loginService.usuarioActual());
  readonly rolUsuario = computed(() =>
    String(this.usuario()?.rol || '').toLowerCase().trim()
  );
  readonly esAdmin = computed(
    () => this.rolUsuario() === 'administrador' || this.rolUsuario() === 'admin'
  );
  readonly esEncargado = computed(
    () => this.rolUsuario() === 'encargado_sucursal'
  );

  // --- Estado Reactivo de Consulta ---
  readonly promociones = computed(() => this.servicio.promociones());
  readonly metricas = computed(() => this.servicio.metricas());
  readonly totalPromociones = computed(() => this.servicio.totalPromociones());
  readonly totalPaginas = computed(() => this.servicio.totalPaginas());
  readonly cargando = computed(() => this.servicio.cargando());
  readonly guardando = computed(() => this.servicio.guardando());
  readonly errorServicio = computed(() => this.servicio.error());
  readonly mensajeExitoServicio = computed(() => this.servicio.mensajeExito());

  // --- Filtros Reactivos ---
  readonly busquedaTexto = signal<string>('');
  readonly filtroTipoDescuento = signal<TipoDescuento | 'todos'>('todos');
  readonly filtroEstado = signal<'todos' | 'activas' | 'inactivas'>('todos');
  readonly filtroAlcance = signal<AlcancePromocion | 'todos'>('todos');
  readonly filtroOrden = signal<string>('creado_en_desc');
  readonly paginaActual = signal<number>(1);

  // --- Estado de Modales ---
  readonly modalAbierto = signal<boolean>(false);
  readonly modoEdicion = signal<boolean>(false);
  readonly promocionEnEdicion = signal<PromocionItem | null>(null);

  readonly modalConfirmarEstadoAbierto = signal<boolean>(false);
  readonly promocionParaConmutar = signal<PromocionItem | null>(null);

  // --- Banners Contextuales (Luxury Banners) ---
  readonly errorBanner = signal<string | null>(null);
  readonly mensajeExitoBanner = signal<string | null>(null);

  private debounceTimer: any = null;

  // --- Formulario Reactivo ---
  readonly formPromocion = this.fb.group(
    {
      nombre: ['', [Validators.required, Validators.minLength(3)]],
      descripcion: [''],
      codigo_cupon: [''],
      tipo_descuento: ['porcentaje' as TipoDescuento, [Validators.required]],
      valor_descuento: [10, [Validators.required, Validators.min(0.01)]],
      fecha_inicio: ['', [Validators.required]],
      fecha_fin: ['', [Validators.required]],
      tope_descuento: [null as number | null],
      limite_usos: [null as number | null],
      alcance: ['global' as AlcancePromocion, [Validators.required]],
      id_categoria: [null as number | null],
      id_producto: [null as number | null],
      estado_activo: [true],
    },
    { validators: [validadorPromocion] }
  );

  ngOnInit(): void {
    this.cargarDatos();
    this.servicio.cargarAuxiliares();
  }

  cargarDatos(): void {
    this.servicio
      .listarPromociones({
        q: this.busquedaTexto(),
        tipo_descuento: this.filtroTipoDescuento(),
        estado_activo: this.filtroEstado(),
        alcance: this.filtroAlcance(),
        ordenar_por: this.filtroOrden(),
        pagina: this.paginaActual(),
        limite: 10,
      })
      .subscribe({
        error: (err) => {
          this.mostrarError(err.message || 'Error al cargar promociones.');
        },
      });
  }

  onBusquedaInput(event: Event): void {
    const valor = (event.target as HTMLInputElement).value;
    this.busquedaTexto.set(valor);

    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }
    this.debounceTimer = setTimeout(() => {
      this.paginaActual.set(1);
      this.cargarDatos();
    }, 300);
  }

  onFiltroTipoChange(event: Event): void {
    const valor = (event.target as HTMLSelectElement).value as TipoDescuento | 'todos';
    this.filtroTipoDescuento.set(valor);
    this.paginaActual.set(1);
    this.cargarDatos();
  }

  onFiltroEstadoChange(event: Event): void {
    const valor = (event.target as HTMLSelectElement).value as 'todos' | 'activas' | 'inactivas';
    this.filtroEstado.set(valor);
    this.paginaActual.set(1);
    this.cargarDatos();
  }

  onFiltroAlcanceChange(event: Event): void {
    const valor = (event.target as HTMLSelectElement).value as AlcancePromocion | 'todos';
    this.filtroAlcance.set(valor);
    this.paginaActual.set(1);
    this.cargarDatos();
  }

  resetearFiltros(): void {
    this.busquedaTexto.set('');
    this.filtroTipoDescuento.set('todos');
    this.filtroEstado.set('todos');
    this.filtroAlcance.set('todos');
    this.filtroOrden.set('creado_en_desc');
    this.paginaActual.set(1);
    this.cargarDatos();
  }

  cambiarPagina(nuevaPagina: number): void {
    if (nuevaPagina < 1 || nuevaPagina > this.totalPaginas()) {
      return;
    }
    this.paginaActual.set(nuevaPagina);
    this.cargarDatos();
  }

  // --- Manejo de Modal de Creacion / Edicion ---
  abrirModalCrear(): void {
    this.modoEdicion.set(false);
    this.promocionEnEdicion.set(null);
    this.limpiarBanners();

    // Fechas por defecto: hoy y en 30 dias
    const hoy = new Date();
    const proximoMes = new Date();
    proximoMes.setDate(hoy.getDate() + 30);

    const formatoFecha = (d: Date) => d.toISOString().slice(0, 16);

    this.formPromocion.reset({
      nombre: '',
      descripcion: '',
      codigo_cupon: '',
      tipo_descuento: 'porcentaje',
      valor_descuento: 15,
      fecha_inicio: formatoFecha(hoy),
      fecha_fin: formatoFecha(proximoMes),
      tope_descuento: null,
      limite_usos: null,
      alcance: 'global',
      id_categoria: null,
      id_producto: null,
      estado_activo: true,
    });

    this.modalAbierto.set(true);
  }

  abrirModalEditar(promocion: PromocionItem): void {
    this.modoEdicion.set(true);
    this.promocionEnEdicion.set(promocion);
    this.limpiarBanners();

    const formatoFecha = (str: string) => {
      if (!str) return '';
      const d = new Date(str);
      return !isNaN(d.getTime()) ? d.toISOString().slice(0, 16) : str.slice(0, 16);
    };

    this.formPromocion.reset({
      nombre: promocion.nombre,
      descripcion: promocion.descripcion || '',
      codigo_cupon: promocion.codigo_cupon || '',
      tipo_descuento: promocion.tipo_descuento,
      valor_descuento: promocion.valor_descuento,
      fecha_inicio: formatoFecha(promocion.fecha_inicio),
      fecha_fin: formatoFecha(promocion.fecha_fin),
      tope_descuento: promocion.tope_descuento,
      limite_usos: promocion.limite_usos,
      alcance: promocion.alcance,
      id_categoria: promocion.id_categoria,
      id_producto: promocion.id_producto,
      estado_activo: promocion.estado_activo,
    });

    this.modalAbierto.set(true);
  }

  cerrarModal(): void {
    this.modalAbierto.set(false);
    this.promocionEnEdicion.set(null);
    this.formPromocion.reset();
  }

  guardarPromocion(): void {
    if (this.formPromocion.invalid) {
      this.formPromocion.markAllAsTouched();
      return;
    }

    const val = this.formPromocion.getRawValue();

    const payload: PromocionCrearDto = {
      nombre: val.nombre.trim(),
      descripcion: val.descripcion ? val.descripcion.trim() : null,
      codigo_cupon: val.codigo_cupon ? val.codigo_cupon.trim().toUpperCase() : null,
      tipo_descuento: val.tipo_descuento,
      valor_descuento: Number(val.valor_descuento),
      fecha_inicio: new Date(val.fecha_inicio).toISOString(),
      fecha_fin: new Date(val.fecha_fin).toISOString(),
      tope_descuento:
        val.tipo_descuento === 'porcentaje' && val.tope_descuento
          ? Number(val.tope_descuento)
          : null,
      limite_usos: val.limite_usos ? Number(val.limite_usos) : null,
      alcance: val.alcance,
      id_categoria: val.alcance === 'categoria' && val.id_categoria ? Number(val.id_categoria) : null,
      id_producto: val.alcance === 'producto' && val.id_producto ? Number(val.id_producto) : null,
      estado_activo: val.estado_activo,
    };

    if (this.modoEdicion() && this.promocionEnEdicion()) {
      const id = this.promocionEnEdicion()!.id_promocion;
      this.servicio.actualizarPromocion(id, payload as PromocionActualizarDto).subscribe({
        next: (act) => {
          this.mostrarExito(`Promocion "${act.nombre}" actualizada con exito.`);
          this.cerrarModal();
          this.cargarDatos();
        },
        error: (err) => {
          this.mostrarError(err.message || 'Error al actualizar promocion.');
        },
      });
    } else {
      this.servicio.crearPromocion(payload).subscribe({
        next: (nueva) => {
          this.mostrarExito(`Promocion "${nueva.nombre}" creada satisfactoriamente.`);
          this.cerrarModal();
          this.cargarDatos();
        },
        error: (err) => {
          this.mostrarError(err.message || 'Error al crear promocion.');
        },
      });
    }
  }

  // --- Manejo de Modal de Conmutacion de Estado ---
  abrirModalConmutar(promocion: PromocionItem): void {
    this.promocionParaConmutar.set(promocion);
    this.modalConfirmarEstadoAbierto.set(true);
  }

  cerrarModalConmutar(): void {
    this.modalConfirmarEstadoAbierto.set(false);
    this.promocionParaConmutar.set(null);
  }

  confirmarConmutacion(): void {
    const promo = this.promocionParaConmutar();
    if (!promo) return;

    const nuevoEstado = !promo.estado_activo;
    this.servicio.conmutarEstado(promo.id_promocion, nuevoEstado).subscribe({
      next: (act) => {
        const accion = act.estado_activo ? 'reactivada' : 'desactivada';
        this.mostrarExito(`Promocion "${act.nombre}" ${accion} correctamente.`);
        this.cerrarModalConmutar();
        this.cargarDatos();
      },
      error: (err) => {
        this.mostrarError(err.message || 'Error al conmutar estado de la promocion.');
      },
    });
  }

  // --- Calculo de Vigencia Cromatica ---
  calcularVigencia(p: PromocionItem): EstadoVigencia {
    const ahora = new Date().getTime();
    const inicio = new Date(p.fecha_inicio).getTime();
    const fin = new Date(p.fecha_fin).getTime();

    if (ahora < inicio) return 'proxima';
    if (ahora > fin) return 'expirada';
    return 'vigente';
  }

  // --- Banners Contextuales ---
  mostrarError(mensaje: string): void {
    this.errorBanner.set(mensaje);
    this.mensajeExitoBanner.set(null);
    this.cdr.markForCheck();
  }

  mostrarExito(mensaje: string): void {
    this.mensajeExitoBanner.set(mensaje);
    this.errorBanner.set(null);
    this.cdr.markForCheck();
  }

  limpiarBanners(): void {
    this.errorBanner.set(null);
    this.mensajeExitoBanner.set(null);
  }
}
