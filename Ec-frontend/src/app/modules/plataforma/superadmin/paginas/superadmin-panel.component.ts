import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  FormBuilder,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { Router, RouterLink } from '@angular/router';
import { LoginService } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import { SuperadminService } from '../servicios/superadmin.service';
import {
  BitacoraPlataformaItem,
  CatalogoReporteItem,
  CiudadGlobal,
  ColorGlobal,
  EmpresaDetalle,
  EmpresaResumen,
  EstadoEmpresa,
  EstadoSuscripcion,
  FuncionalidadPlataforma,
  HistorialSuscripcionItem,
  MetricasPlataforma,
  PestanaSuperadmin,
  PlanDetalle,
  SuscripcionEmpresa,
  TallaGlobal,
  TipoOperacionSuscripcion,
} from '../modelos/superadmin.model';

@Component({
  selector: 'app-superadmin-panel',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule, RouterLink],
  templateUrl: './superadmin-panel.component.html',
  styleUrls: ['./superadmin-panel.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SuperadminPanelComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly superadminService = inject(SuperadminService);
  private readonly loginService = inject(LoginService);
  private readonly router = inject(Router);

  // Navegación principal por pestañas
  readonly pestanaActiva = signal<PestanaSuperadmin>('empresas');

  // Estado general de interfaz y retroalimentación
  readonly cargando = signal<boolean>(false);
  readonly procesandoAccion = signal<boolean>(false);
  readonly mensajeExito = signal<string | null>(null);
  readonly mensajeError = signal<string | null>(null);
  readonly advertenciasPlan = signal<string[]>([]);

  // Datos P2-CU05 (Empresas, Métricas y Bitácora)
  readonly metricas = signal<MetricasPlataforma | null>(null);
  readonly empresas = signal<EmpresaResumen[]>([]);
  readonly filtroEmpresaQ = signal<string>('');
  readonly filtroEmpresaEstado = signal<EstadoEmpresa | ''>('');
  readonly filtroEmpresaPlan = signal<number | null>(null);
  readonly mostrarModalNuevaEmpresa = signal<boolean>(false);
  readonly empresaEditando = signal<EmpresaResumen | null>(null);

  // Datos P2-CU06 (Planes y Funcionalidades)
  readonly funcionalidades = signal<FuncionalidadPlataforma[]>([]);
  readonly planes = signal<PlanDetalle[]>([]);
  readonly planEditando = signal<PlanDetalle | null>(null);
  readonly mostrarFormularioPlan = signal<boolean>(false);
  readonly funcionalidadesSeleccionadas = signal<string[]>([
    'productos',
    'ventas',
    'reservas',
    'operacion_offline',
    'reportes_convencionales',
  ]);

  // Datos P2-CU07 (Suscripciones e Historial)
  readonly suscripciones = signal<SuscripcionEmpresa[]>([]);
  readonly filtroSuscripcionEstado = signal<EstadoSuscripcion | ''>('');
  readonly suscripcionSeleccionada = signal<SuscripcionEmpresa | null>(null);
  readonly historialSuscripcion = signal<HistorialSuscripcionItem[]>([]);
  readonly mostrarModalOperacionSuscripcion = signal<boolean>(false);

  // Datos P2-CU08 (Catálogos Globales)
  readonly subPestanaCatalogo = signal<'ciudades' | 'tallas' | 'colores'>('ciudades');
  readonly ciudades = signal<CiudadGlobal[]>([]);
  readonly tallas = signal<TallaGlobal[]>([]);
  readonly colores = signal<ColorGlobal[]>([]);
  readonly ciudadEditando = signal<CiudadGlobal | null>(null);
  readonly tallaEditando = signal<TallaGlobal | null>(null);
  readonly colorEditando = signal<ColorGlobal | null>(null);

  // Datos P2-CU22 (Catálogo de Reportes Permitidos IA)
  readonly reportesCatalogo = signal<CatalogoReporteItem[]>([]);
  readonly vistasPermitidasCatalogo = signal<string[]>([]);
  readonly tiposGraficoCatalogo = signal<string[]>([]);
  readonly filtrosPermitidosCatalogo = signal<string[]>([]);
  readonly reporteCatalogoEditando = signal<CatalogoReporteItem | null>(null);
  readonly mostrarFormularioReporteCatalogo = signal<boolean>(false);
  readonly graficosReporteSeleccionados = signal<string[]>(['tabla', 'barras']);
  readonly filtrosReporteSeleccionados = signal<string[]>(['fecha_inicio', 'fecha_fin', 'id_sucursal', 'moneda']);

  // Bitácora global
  readonly bitacoraItems = signal<BitacoraPlataformaItem[]>([]);
  readonly bitacoraTotal = signal<number>(0);
  readonly bitacoraPagina = signal<number>(1);
  readonly bitacoraTotalPaginas = signal<number>(1);
  readonly filtroBitacoraTenant = signal<number | null>(null);
  readonly filtroBitacoraSoloPlataforma = signal<boolean>(false);
  readonly filtroBitacoraSeveridad = signal<string>('');
  readonly filtroBitacoraQ = signal<string>('');
  readonly eventoBitacoraExpandido = signal<number | null>(null);

  readonly planesActivos = computed(() => this.planes().filter((p) => p.activo));

  // Formularios reactivos
  readonly formNuevaEmpresa: FormGroup = this.fb.group({
    codigo: ['', [Validators.required, Validators.pattern(/^[a-z0-9-]{3,60}$/)]],
    nombre: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(150)]],
    correo_contacto: ['', [Validators.email]],
    telefono: ['', [Validators.maxLength(30)]],
    id_plan: [null as number | null, [Validators.required]],
    estado_suscripcion: ['activa', [Validators.required]],
    fecha_inicio: [this.hoyIso(), [Validators.required]],
    fecha_vencimiento: [this.unAnioDespuesIso(), [Validators.required]],
    admin_nombres: ['', [Validators.required, Validators.minLength(2)]],
    admin_apellidos: ['', [Validators.required, Validators.minLength(2)]],
    admin_email: ['', [Validators.required, Validators.email]],
    admin_password: ['', [Validators.required, Validators.minLength(8)]],
    admin_telefono: [''],
  });

  readonly formEditarEmpresa: FormGroup = this.fb.group({
    nombre: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(150)]],
    correo_contacto: ['', [Validators.email]],
    telefono: ['', [Validators.maxLength(30)]],
  });

  readonly formPlan: FormGroup = this.fb.group({
    nombre: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(60)]],
    precio_mensual: [0, [Validators.required, Validators.min(0)]],
    max_sucursales_activas: [2, [Validators.required, Validators.min(1)]],
    sin_limite_empleados: [true],
    max_empleados: [10, [Validators.min(1)]],
  });

  readonly formOperacionSuscripcion: FormGroup = this.fb.group({
    operacion: ['cambio_plan' as TipoOperacionSuscripcion, [Validators.required]],
    id_plan: [null as number | null],
    estado: ['activa'],
    fecha_inicio: [this.hoyIso()],
    fecha_vencimiento: [this.unAnioDespuesIso()],
    motivo: [''],
  });

  readonly formCiudad: FormGroup = this.fb.group({
    nombre: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(100)]],
    pais: ['Bolivia', [Validators.required, Validators.minLength(2), Validators.maxLength(100)]],
  });

  readonly formTalla: FormGroup = this.fb.group({
    codigo: ['', [Validators.required, Validators.minLength(1), Validators.maxLength(10)]],
    orden: [1, [Validators.required, Validators.min(0)]],
  });

  readonly formColor: FormGroup = this.fb.group({
    nombre: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(50)]],
    codigo_hex: ['#000000', [Validators.required, Validators.pattern(/^#[0-9A-Fa-f]{6}$/)]],
  });

  readonly formReporteCatalogo: FormGroup = this.fb.group({
    codigo: ['', [Validators.required, Validators.pattern(/^[a-z0-9_]{3,60}$/)]],
    nombre: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(120)]],
    descripcion: ['', [Validators.maxLength(500)]],
    vista_origen: ['vw_ventas_por_sucursal', [Validators.required]],
    metrica_codigo: ['ingresos_totales_bob', [Validators.required]],
    metrica_etiqueta: ['Ingresos Totales (Bs. BOB)', [Validators.required]],
    metrica_expresion: ['SUM(total_orden)', [Validators.required]],
    metrica_es_monetaria: [true],
    dimension_codigo: ['sucursal', [Validators.required]],
    dimension_etiqueta: ['Sucursal', [Validators.required]],
    dimension_expresion: ['sucursal.nombre', [Validators.required]],
    ejemplos_texto: ['Ventas del último mes por sucursal en Bs.\nIngresos por tienda en bolivianos'],
    activo: [true],
  });

  ngOnInit(): void {
    this.cargarDatosIniciales();
  }

  cambiarPestana(pestana: PestanaSuperadmin): void {
    this.limpiarMensajes();
    this.pestanaActiva.set(pestana);
    if (pestana === 'empresas') {
      this.cargarEmpresasYMetricas();
    } else if (pestana === 'planes') {
      this.cargarPlanesYFuncionalidades();
    } else if (pestana === 'suscripciones') {
      this.cargarSuscripciones();
    } else if (pestana === 'catalogos') {
      this.cargarCatalogosGlobales();
    } else if (pestana === 'reportes_ia') {
      this.cargarCatalogoReportesIa();
    } else if (pestana === 'bitacora') {
      this.cargarBitacora(1);
    }
  }

  cargarDatosIniciales(): void {
    this.cargarPlanesYFuncionalidades();
    this.cargarEmpresasYMetricas();
  }

  limpiarMensajes(): void {
    this.mensajeExito.set(null);
    this.mensajeError.set(null);
  }

  private extraerMensajeError(err: unknown): string {
    if (err instanceof HttpErrorResponse) {
      return (
        err.error?.detail ||
        err.error?.message ||
        `Error HTTP ${err.status}: no se pudo completar la operación.`
      );
    }
    if (err instanceof Error) {
      return err.message;
    }
    return 'Ocurrió un error inesperado al procesar la solicitud.';
  }

  private hoyIso(): string {
    return new Date().toISOString().slice(0, 10);
  }

  private unAnioDespuesIso(): string {
    const d = new Date();
    d.setFullYear(d.getFullYear() + 1);
    return d.toISOString().slice(0, 10);
  }

  // =========================================================================
  // P2-CU05: EMPRESAS Y SUPERVISIÓN
  // =========================================================================

  cargarEmpresasYMetricas(): void {
    this.cargando.set(true);
    this.superadminService.obtenerMetricas().subscribe({
      next: (m) => this.metricas.set(m),
      error: (err) => this.mensajeError.set(this.extraerMensajeError(err)),
    });
    this.filtrarEmpresas();
  }

  filtrarEmpresas(): void {
    this.cargando.set(true);
    this.superadminService
      .listarEmpresas({
        q: this.filtroEmpresaQ(),
        estado: this.filtroEmpresaEstado(),
        id_plan: this.filtroEmpresaPlan(),
      })
      .subscribe({
        next: (lista) => {
          this.empresas.set(lista);
          this.cargando.set(false);
        },
        error: (err) => {
          this.cargando.set(false);
          this.mensajeError.set(this.extraerMensajeError(err));
        },
      });
  }

  abrirModalNuevaEmpresa(): void {
    this.limpiarMensajes();
    const primerPlanActivo = this.planesActivos()[0]?.id_plan ?? null;
    this.formNuevaEmpresa.reset({
      codigo: '',
      nombre: '',
      correo_contacto: '',
      telefono: '',
      id_plan: primerPlanActivo,
      estado_suscripcion: 'activa',
      fecha_inicio: this.hoyIso(),
      fecha_vencimiento: this.unAnioDespuesIso(),
      admin_nombres: '',
      admin_apellidos: '',
      admin_email: '',
      admin_password: '',
      admin_telefono: '',
    });
    this.mostrarModalNuevaEmpresa.set(true);
  }

  cerrarModalNuevaEmpresa(): void {
    this.mostrarModalNuevaEmpresa.set(false);
  }

  guardarNuevaEmpresa(): void {
    if (this.formNuevaEmpresa.invalid) {
      this.formNuevaEmpresa.markAllAsTouched();
      this.mensajeError.set('Completa todos los campos obligatorios de la empresa y su administrador.');
      return;
    }

    const v = this.formNuevaEmpresa.getRawValue();
    this.procesandoAccion.set(true);
    this.limpiarMensajes();

    this.superadminService
      .registrarEmpresa({
        codigo: String(v.codigo).trim().toLowerCase(),
        nombre: String(v.nombre).trim(),
        correo_contacto: v.correo_contacto ? String(v.correo_contacto).trim() : null,
        telefono: v.telefono ? String(v.telefono).trim() : null,
        id_plan: Number(v.id_plan),
        estado_suscripcion: v.estado_suscripcion,
        fecha_inicio: v.fecha_inicio,
        fecha_vencimiento: v.fecha_vencimiento,
        admin_inicial: {
          nombres: String(v.admin_nombres).trim(),
          apellidos: String(v.admin_apellidos).trim(),
          email: String(v.admin_email).trim().toLowerCase(),
          password: String(v.admin_password),
          telefono: v.admin_telefono ? String(v.admin_telefono).trim() : null,
        },
      })
      .subscribe({
        next: (creada: EmpresaDetalle) => {
          this.procesandoAccion.set(false);
          this.mostrarModalNuevaEmpresa.set(false);
          this.mensajeExito.set(
            `Empresa «${creada.nombre}» (${creada.codigo}) creada exitosamente con su suscripción inicial.`
          );
          this.cargarEmpresasYMetricas();
        },
        error: (err) => {
          this.procesandoAccion.set(false);
          this.mensajeError.set(this.extraerMensajeError(err));
        },
      });
  }

  iniciarEdicionEmpresa(empresa: EmpresaResumen): void {
    this.limpiarMensajes();
    this.empresaEditando.set(empresa);
    this.formEditarEmpresa.reset({
      nombre: empresa.nombre,
      correo_contacto: empresa.correo_contacto ?? '',
      telefono: empresa.telefono ?? '',
    });
  }

  cancelarEdicionEmpresa(): void {
    this.empresaEditando.set(null);
  }

  guardarEdicionEmpresa(): void {
    const actual = this.empresaEditando();
    if (!actual || this.formEditarEmpresa.invalid) {
      this.formEditarEmpresa.markAllAsTouched();
      return;
    }
    const v = this.formEditarEmpresa.getRawValue();
    this.procesandoAccion.set(true);
    this.superadminService
      .actualizarEmpresa(actual.id_tenant, {
        nombre: String(v.nombre).trim(),
        correo_contacto: v.correo_contacto ? String(v.correo_contacto).trim() : null,
        telefono: v.telefono ? String(v.telefono).trim() : null,
      })
      .subscribe({
        next: (actualizada) => {
          this.procesandoAccion.set(false);
          this.empresaEditando.set(null);
          this.mensajeExito.set(`Datos de «${actualizada.nombre}» actualizados.`);
          this.cargarEmpresasYMetricas();
        },
        error: (err) => {
          this.procesandoAccion.set(false);
          this.mensajeError.set(this.extraerMensajeError(err));
        },
      });
  }

  cambiarEstadoEmpresa(empresa: EmpresaResumen, nuevoEstado: EstadoEmpresa): void {
    this.limpiarMensajes();
    this.procesandoAccion.set(true);
    this.superadminService
      .cambiarEstadoEmpresa(empresa.id_tenant, {
        estado: nuevoEstado,
        motivo: `Cambio de estado a ${nuevoEstado} desde el panel del Super Administrador`,
      })
      .subscribe({
        next: (actualizada) => {
          this.procesandoAccion.set(false);
          this.mensajeExito.set(
            `Estado de «${actualizada.nombre}» actualizado a «${actualizada.estado}».`
          );
          this.cargarEmpresasYMetricas();
        },
        error: (err) => {
          this.procesandoAccion.set(false);
          this.mensajeError.set(this.extraerMensajeError(err));
        },
      });
  }

  // =========================================================================
  // P2-CU06: PLANES Y FUNCIONALIDADES
  // =========================================================================

  cargarPlanesYFuncionalidades(): void {
    this.superadminService.listarFuncionalidades().subscribe({
      next: (f) => this.funcionalidades.set(f),
      error: (err) => this.mensajeError.set(this.extraerMensajeError(err)),
    });
    this.superadminService.listarPlanes(false).subscribe({
      next: (p) => this.planes.set(p),
      error: (err) => this.mensajeError.set(this.extraerMensajeError(err)),
    });
  }

  abrirNuevoPlan(): void {
    this.limpiarMensajes();
    this.advertenciasPlan.set([]);
    this.planEditando.set(null);
    this.funcionalidadesSeleccionadas.set([
      'productos',
      'ventas',
      'reservas',
      'operacion_offline',
      'reportes_convencionales',
    ]);
    this.formPlan.reset({
      nombre: '',
      precio_mensual: 0,
      max_sucursales_activas: 2,
      sin_limite_empleados: true,
      max_empleados: 10,
    });
    this.mostrarFormularioPlan.set(true);
  }

  iniciarEdicionPlan(plan: PlanDetalle): void {
    this.limpiarMensajes();
    this.advertenciasPlan.set([]);
    this.planEditando.set(plan);
    this.funcionalidadesSeleccionadas.set([...plan.codigos_funcionalidades]);
    this.formPlan.reset({
      nombre: plan.nombre,
      precio_mensual: Number(plan.precio_mensual),
      max_sucursales_activas: plan.max_sucursales_activas,
      sin_limite_empleados: plan.max_empleados === null,
      max_empleados: plan.max_empleados ?? 10,
    });
    this.mostrarFormularioPlan.set(true);
  }

  cerrarFormularioPlan(): void {
    this.mostrarFormularioPlan.set(false);
    this.planEditando.set(null);
  }

  toggleFuncionalidadPlan(codigo: string): void {
    const actuales = this.funcionalidadesSeleccionadas();
    if (actuales.includes(codigo)) {
      if (actuales.length <= 1) {
        return; // Un plan requiere al menos una funcionalidad
      }
      this.funcionalidadesSeleccionadas.set(actuales.filter((c) => c !== codigo));
    } else {
      this.funcionalidadesSeleccionadas.set([...actuales, codigo]);
    }
  }

  tieneFuncionalidadSeleccionada(codigo: string): boolean {
    return this.funcionalidadesSeleccionadas().includes(codigo);
  }

  guardarPlan(): void {
    if (this.formPlan.invalid || this.funcionalidadesSeleccionadas().length === 0) {
      this.formPlan.markAllAsTouched();
      this.mensajeError.set('Verifica los datos del plan y selecciona al menos una funcionalidad.');
      return;
    }

    const v = this.formPlan.getRawValue();
    const payload = {
      nombre: String(v.nombre).trim(),
      precio_mensual: Number(v.precio_mensual),
      max_sucursales_activas: Number(v.max_sucursales_activas),
      max_empleados: v.sin_limite_empleados ? null : Number(v.max_empleados),
      funcionalidades: this.funcionalidadesSeleccionadas(),
    };

    this.procesandoAccion.set(true);
    this.limpiarMensajes();
    const editando = this.planEditando();

    const peticion$ = editando
      ? this.superadminService.actualizarPlan(editando.id_plan, payload)
      : this.superadminService.crearPlan(payload);

    peticion$.subscribe({
      next: (planGuardado) => {
        this.procesandoAccion.set(false);
        this.mostrarFormularioPlan.set(false);
        this.planEditando.set(null);
        this.advertenciasPlan.set(planGuardado.advertencias ?? []);
        this.mensajeExito.set(`Plan «${planGuardado.nombre}» guardado correctamente.`);
        this.cargarPlanesYFuncionalidades();
      },
      error: (err) => {
        this.procesandoAccion.set(false);
        this.mensajeError.set(this.extraerMensajeError(err));
      },
    });
  }

  alternarEstadoPlan(plan: PlanDetalle): void {
    this.limpiarMensajes();
    this.procesandoAccion.set(true);
    this.superadminService.cambiarEstadoPlan(plan.id_plan, !plan.activo).subscribe({
      next: (actualizado) => {
        this.procesandoAccion.set(false);
        this.mensajeExito.set(
          `Plan «${actualizado.nombre}» ${actualizado.activo ? 'activado' : 'desactivado'}.`
        );
        this.cargarPlanesYFuncionalidades();
      },
      error: (err) => {
        this.procesandoAccion.set(false);
        this.mensajeError.set(this.extraerMensajeError(err));
      },
    });
  }

  // =========================================================================
  // P2-CU07: SUSCRIPCIONES E HISTORIAL
  // =========================================================================

  cargarSuscripciones(): void {
    this.cargando.set(true);
    this.superadminService
      .listarSuscripciones({
        estado: this.filtroSuscripcionEstado(),
      })
      .subscribe({
        next: (lista) => {
          this.suscripciones.set(lista);
          this.cargando.set(false);
        },
        error: (err) => {
          this.cargando.set(false);
          this.mensajeError.set(this.extraerMensajeError(err));
        },
      });
  }

  abrirGestionSuscripcion(susc: SuscripcionEmpresa): void {
    this.limpiarMensajes();
    this.suscripcionSeleccionada.set(susc);
    this.formOperacionSuscripcion.reset({
      operacion: 'cambio_plan',
      id_plan: susc.id_plan,
      estado: 'activa',
      fecha_inicio: susc.fecha_inicio,
      fecha_vencimiento: susc.fecha_vencimiento,
      motivo: '',
    });
    this.mostrarModalOperacionSuscripcion.set(true);
    this.superadminService.listarHistorialSuscripcion(susc.id_tenant).subscribe({
      next: (h) => this.historialSuscripcion.set(h),
      error: () => this.historialSuscripcion.set([]),
    });
  }

  cerrarGestionSuscripcion(): void {
    this.mostrarModalOperacionSuscripcion.set(false);
    this.suscripcionSeleccionada.set(null);
    this.historialSuscripcion.set([]);
  }

  ejecutarOperacionSuscripcion(): void {
    const susc = this.suscripcionSeleccionada();
    if (!susc || this.formOperacionSuscripcion.invalid) {
      return;
    }

    const v = this.formOperacionSuscripcion.getRawValue();
    this.procesandoAccion.set(true);
    this.limpiarMensajes();

    this.superadminService
      .operarSuscripcion(susc.id_tenant, {
        operacion: v.operacion,
        id_plan: v.id_plan ? Number(v.id_plan) : null,
        estado: v.estado,
        fecha_inicio: v.fecha_inicio || null,
        fecha_vencimiento: v.fecha_vencimiento || null,
        motivo: v.motivo ? String(v.motivo).trim() : null,
      })
      .subscribe({
        next: (actualizada) => {
          this.procesandoAccion.set(false);
          this.suscripcionSeleccionada.set(actualizada);
          this.mensajeExito.set(
            `Operación «${v.operacion}» aplicada a la suscripción de «${actualizada.nombre_empresa}».`
          );
          this.cargarSuscripciones();
          this.superadminService
            .listarHistorialSuscripcion(actualizada.id_tenant)
            .subscribe((h) => this.historialSuscripcion.set(h));
        },
        error: (err) => {
          this.procesandoAccion.set(false);
          this.mensajeError.set(this.extraerMensajeError(err));
        },
      });
  }

  // =========================================================================
  // P2-CU08: CATÁLOGOS GLOBALES (CIUDADES, TALLAS, COLORES)
  // =========================================================================

  cargarCatalogosGlobales(): void {
    this.superadminService.listarCiudades(false).subscribe({
      next: (c) => this.ciudades.set(c),
      error: (err) => this.mensajeError.set(this.extraerMensajeError(err)),
    });
    this.superadminService.listarTallas(false).subscribe({
      next: (t) => this.tallas.set(t),
      error: (err) => this.mensajeError.set(this.extraerMensajeError(err)),
    });
    this.superadminService.listarColores(false).subscribe({
      next: (col) => this.colores.set(col),
      error: (err) => this.mensajeError.set(this.extraerMensajeError(err)),
    });
  }

  // --- Ciudades ---

  editarCiudad(ciudad: CiudadGlobal): void {
    this.ciudadEditando.set(ciudad);
    this.formCiudad.reset({ nombre: ciudad.nombre, pais: ciudad.pais });
  }

  cancelarEdicionCiudad(): void {
    this.ciudadEditando.set(null);
    this.formCiudad.reset({ nombre: '', pais: 'Bolivia' });
  }

  guardarCiudad(): void {
    if (this.formCiudad.invalid) {
      this.formCiudad.markAllAsTouched();
      return;
    }
    const v = this.formCiudad.getRawValue();
    const editando = this.ciudadEditando();
    const payload = { nombre: String(v.nombre).trim(), pais: String(v.pais).trim() };
    this.procesandoAccion.set(true);
    this.limpiarMensajes();

    const obs$ = editando
      ? this.superadminService.actualizarCiudad(editando.id_ciudad, payload)
      : this.superadminService.crearCiudad(payload);

    obs$.subscribe({
      next: (c) => {
        this.procesandoAccion.set(false);
        this.cancelarEdicionCiudad();
        this.mensajeExito.set(`Ciudad «${c.nombre}» guardada correctamente.`);
        this.cargarCatalogosGlobales();
      },
      error: (err) => {
        this.procesandoAccion.set(false);
        this.mensajeError.set(this.extraerMensajeError(err));
      },
    });
  }

  alternarEstadoCiudad(ciudad: CiudadGlobal): void {
    this.limpiarMensajes();
    this.superadminService.cambiarEstadoCiudad(ciudad.id_ciudad, !ciudad.activo).subscribe({
      next: (c) => {
        this.mensajeExito.set(`Ciudad «${c.nombre}» ${c.activo ? 'activada' : 'desactivada'}.`);
        this.cargarCatalogosGlobales();
      },
      error: (err) => this.mensajeError.set(this.extraerMensajeError(err)),
    });
  }

  eliminarCiudad(ciudad: CiudadGlobal): void {
    this.limpiarMensajes();
    this.superadminService.eliminarCiudad(ciudad.id_ciudad).subscribe({
      next: (res) => {
        this.mensajeExito.set(res.mensaje);
        this.cargarCatalogosGlobales();
      },
      error: (err) => this.mensajeError.set(this.extraerMensajeError(err)),
    });
  }

  // --- Tallas ---

  editarTalla(talla: TallaGlobal): void {
    this.tallaEditando.set(talla);
    this.formTalla.reset({ codigo: talla.codigo, orden: talla.orden });
  }

  cancelarEdicionTalla(): void {
    this.tallaEditando.set(null);
    this.formTalla.reset({ codigo: '', orden: 1 });
  }

  guardarTalla(): void {
    if (this.formTalla.invalid) {
      this.formTalla.markAllAsTouched();
      return;
    }
    const v = this.formTalla.getRawValue();
    const editando = this.tallaEditando();
    const payload = { codigo: String(v.codigo).trim().toUpperCase(), orden: Number(v.orden) };
    this.procesandoAccion.set(true);
    this.limpiarMensajes();

    const obs$ = editando
      ? this.superadminService.actualizarTalla(editando.id_talla, payload)
      : this.superadminService.crearTalla(payload);

    obs$.subscribe({
      next: (t) => {
        this.procesandoAccion.set(false);
        this.cancelarEdicionTalla();
        this.mensajeExito.set(`Talla «${t.codigo}» guardada correctamente.`);
        this.cargarCatalogosGlobales();
      },
      error: (err) => {
        this.procesandoAccion.set(false);
        this.mensajeError.set(this.extraerMensajeError(err));
      },
    });
  }

  alternarEstadoTalla(talla: TallaGlobal): void {
    this.limpiarMensajes();
    this.superadminService.cambiarEstadoTalla(talla.id_talla, !talla.activo).subscribe({
      next: (t) => {
        this.mensajeExito.set(`Talla «${t.codigo}» ${t.activo ? 'activada' : 'desactivada'}.`);
        this.cargarCatalogosGlobales();
      },
      error: (err) => this.mensajeError.set(this.extraerMensajeError(err)),
    });
  }

  eliminarTalla(talla: TallaGlobal): void {
    this.limpiarMensajes();
    this.superadminService.eliminarTalla(talla.id_talla).subscribe({
      next: (res) => {
        this.mensajeExito.set(res.mensaje);
        this.cargarCatalogosGlobales();
      },
      error: (err) => this.mensajeError.set(this.extraerMensajeError(err)),
    });
  }

  // --- Colores ---

  editarColor(color: ColorGlobal): void {
    this.colorEditando.set(color);
    this.formColor.reset({
      nombre: color.nombre,
      codigo_hex: color.codigo_hex ?? '#000000',
    });
  }

  cancelarEdicionColor(): void {
    this.colorEditando.set(null);
    this.formColor.reset({ nombre: '', codigo_hex: '#000000' });
  }

  guardarColor(): void {
    if (this.formColor.invalid) {
      this.formColor.markAllAsTouched();
      return;
    }
    const v = this.formColor.getRawValue();
    const editando = this.colorEditando();
    const payload = {
      nombre: String(v.nombre).trim(),
      codigo_hex: String(v.codigo_hex).trim().toUpperCase(),
    };
    this.procesandoAccion.set(true);
    this.limpiarMensajes();

    const obs$ = editando
      ? this.superadminService.actualizarColor(editando.id_color, payload)
      : this.superadminService.crearColor(payload);

    obs$.subscribe({
      next: (c) => {
        this.procesandoAccion.set(false);
        this.cancelarEdicionColor();
        this.mensajeExito.set(`Color «${c.nombre}» guardado correctamente.`);
        this.cargarCatalogosGlobales();
      },
      error: (err) => {
        this.procesandoAccion.set(false);
        this.mensajeError.set(this.extraerMensajeError(err));
      },
    });
  }

  alternarEstadoColor(color: ColorGlobal): void {
    this.limpiarMensajes();
    this.superadminService.cambiarEstadoColor(color.id_color, !color.activo).subscribe({
      next: (c) => {
        this.mensajeExito.set(`Color «${c.nombre}» ${c.activo ? 'activado' : 'desactivado'}.`);
        this.cargarCatalogosGlobales();
      },
      error: (err) => this.mensajeError.set(this.extraerMensajeError(err)),
    });
  }

  eliminarColor(color: ColorGlobal): void {
    this.limpiarMensajes();
    this.superadminService.eliminarColor(color.id_color).subscribe({
      next: (res) => {
        this.mensajeExito.set(res.mensaje);
        this.cargarCatalogosGlobales();
      },
      error: (err) => this.mensajeError.set(this.extraerMensajeError(err)),
    });
  }

  // =========================================================================
  // P2-CU22: CATÁLOGO DE REPORTES PERMITIDOS CON IA
  // =========================================================================

  cargarCatalogoReportesIa(): void {
    this.cargando.set(true);
    this.superadminService.listarCatalogoReportes(false).subscribe({
      next: (meta) => {
        this.reportesCatalogo.set(meta.reportes);
        this.vistasPermitidasCatalogo.set(meta.vistas_permitidas);
        this.tiposGraficoCatalogo.set(meta.tipos_grafico_permitidos);
        this.filtrosPermitidosCatalogo.set(meta.filtros_permitidos);
        this.cargando.set(false);
      },
      error: (err) => {
        this.cargando.set(false);
        this.mensajeError.set(this.extraerMensajeError(err));
      },
    });
  }

  abrirNuevoReporteCatalogo(): void {
    this.limpiarMensajes();
    this.reporteCatalogoEditando.set(null);
    this.graficosReporteSeleccionados.set(['tabla', 'barras']);
    this.filtrosReporteSeleccionados.set(['fecha_inicio', 'fecha_fin', 'id_sucursal', 'moneda']);
    this.formReporteCatalogo.reset({
      codigo: '',
      nombre: '',
      descripcion: '',
      vista_origen: this.vistasPermitidasCatalogo()[0] || 'vw_ventas_por_sucursal',
      metrica_codigo: 'ingresos_totales_bob',
      metrica_etiqueta: 'Ingresos Totales (Bs. BOB)',
      metrica_expresion: 'SUM(total_orden)',
      metrica_es_monetaria: true,
      dimension_codigo: 'sucursal',
      dimension_etiqueta: 'Sucursal',
      dimension_expresion: 'sucursal.nombre',
      ejemplos_texto: 'Ventas del último mes por sucursal en Bs.',
      activo: true,
    });
    this.mostrarFormularioReporteCatalogo.set(true);
  }

  abrirEditarReporteCatalogo(rep: CatalogoReporteItem): void {
    this.limpiarMensajes();
    this.reporteCatalogoEditando.set(rep);
    this.graficosReporteSeleccionados.set([...rep.tipos_grafico]);
    this.filtrosReporteSeleccionados.set([...rep.filtros_permitidos]);
    const m0 = rep.metricas[0] ?? {
      codigo: 'valor',
      etiqueta: 'Valor',
      expresion: 'COUNT(*)',
      es_monetaria: false,
    };
    const d0 = rep.dimensiones[0] ?? {
      codigo: 'sucursal',
      etiqueta: 'Sucursal',
      expresion: 'sucursal.nombre',
    };
    this.formReporteCatalogo.reset({
      codigo: rep.codigo,
      nombre: rep.nombre,
      descripcion: rep.descripcion ?? '',
      vista_origen: rep.vista_origen,
      metrica_codigo: m0.codigo,
      metrica_etiqueta: m0.etiqueta,
      metrica_expresion: m0.expresion,
      metrica_es_monetaria: m0.es_monetaria,
      dimension_codigo: d0.codigo,
      dimension_etiqueta: d0.etiqueta,
      dimension_expresion: d0.expresion,
      ejemplos_texto: (rep.ejemplos_consulta ?? []).join('\n'),
      activo: rep.activo,
    });
    this.mostrarFormularioReporteCatalogo.set(true);
  }

  cerrarFormularioReporteCatalogo(): void {
    this.mostrarFormularioReporteCatalogo.set(false);
    this.reporteCatalogoEditando.set(null);
  }

  toggleGraficoReporteCatalogo(grafico: string): void {
    this.graficosReporteSeleccionados.update((actual) =>
      actual.includes(grafico) ? actual.filter((g) => g !== grafico) : [...actual, grafico]
    );
  }

  toggleFiltroReporteCatalogo(filtro: string): void {
    this.filtrosReporteSeleccionados.update((actual) =>
      actual.includes(filtro) ? actual.filter((f) => f !== filtro) : [...actual, filtro]
    );
  }

  guardarReporteCatalogo(): void {
    if (this.formReporteCatalogo.invalid) {
      this.formReporteCatalogo.markAllAsTouched();
      this.mensajeError.set('Completa todos los campos requeridos del reporte permitido (CU22).');
      return;
    }
    if (this.graficosReporteSeleccionados().length === 0) {
      this.mensajeError.set('Selecciona al menos un tipo de visualización o gráfico permitido (CU22 A2).');
      return;
    }

    const v = this.formReporteCatalogo.getRawValue();
    const editando = this.reporteCatalogoEditando();
    const ejemplos = String(v.ejemplos_texto || '')
      .split('\n')
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

    const payload = {
      codigo: String(v.codigo).trim().toLowerCase(),
      nombre: String(v.nombre).trim(),
      descripcion: v.descripcion ? String(v.descripcion).trim() : null,
      vista_origen: String(v.vista_origen).trim(),
      metricas: [
        {
          codigo: String(v.metrica_codigo).trim(),
          etiqueta: String(v.metrica_etiqueta).trim(),
          expresion: String(v.metrica_expresion).trim(),
          es_monetaria: Boolean(v.metrica_es_monetaria),
        },
      ],
      dimensiones: [
        {
          codigo: String(v.dimension_codigo).trim(),
          etiqueta: String(v.dimension_etiqueta).trim(),
          expresion: String(v.dimension_expresion).trim(),
        },
      ],
      filtros_permitidos: this.filtrosReporteSeleccionados(),
      tipos_grafico: this.graficosReporteSeleccionados(),
      ejemplos_consulta: ejemplos,
      activo: Boolean(v.activo),
    };

    this.procesandoAccion.set(true);
    this.limpiarMensajes();

    const obs$ = editando
      ? this.superadminService.actualizarReporteCatalogo(editando.id_reporte_catalogo, payload)
      : this.superadminService.crearReporteCatalogo(payload);

    obs$.subscribe({
      next: (guardado) => {
        this.procesandoAccion.set(false);
        this.cerrarFormularioReporteCatalogo();
        this.mensajeExito.set(
          `Reporte del catálogo «${guardado.nombre}» (${guardado.codigo}) guardado correctamente.`
        );
        this.cargarCatalogoReportesIa();
      },
      error: (err) => {
        this.procesandoAccion.set(false);
        this.mensajeError.set(this.extraerMensajeError(err));
      },
    });
  }

  alternarEstadoReporteCatalogo(rep: CatalogoReporteItem): void {
    this.limpiarMensajes();
    this.superadminService
      .cambiarEstadoReporteCatalogo(rep.id_reporte_catalogo, !rep.activo)
      .subscribe({
        next: (actualizado) => {
          this.mensajeExito.set(
            `Reporte «${actualizado.nombre}» ${
              actualizado.activo
                ? 'activado y disponible para CU21'
                : 'desactivado (se conservan las solicitudes históricas — CU22 A3)'
            }.`
          );
          this.cargarCatalogoReportesIa();
        },
        error: (err) => this.mensajeError.set(this.extraerMensajeError(err)),
      });
  }

  // =========================================================================
  // BITÁCORA DE PLATAFORMA
  // =========================================================================

  cargarBitacora(pagina = 1): void {
    this.cargando.set(true);
    this.bitacoraPagina.set(pagina);
    this.superadminService
      .listarBitacora({
        id_tenant: this.filtroBitacoraSoloPlataforma() ? null : this.filtroBitacoraTenant(),
        solo_plataforma: this.filtroBitacoraSoloPlataforma(),
        severidad: this.filtroBitacoraSeveridad(),
        q: this.filtroBitacoraQ(),
        pagina,
        limite: 20,
      })
      .subscribe({
        next: (res) => {
          this.bitacoraItems.set(res.items);
          this.bitacoraTotal.set(res.total);
          this.bitacoraPagina.set(res.pagina);
          this.bitacoraTotalPaginas.set(res.total_paginas);
          this.cargando.set(false);
        },
        error: (err) => {
          this.cargando.set(false);
          this.mensajeError.set(this.extraerMensajeError(err));
        },
      });
  }

  toggleDetalleBitacora(idBitacora: number): void {
    this.eventoBitacoraExpandido.update((actual) =>
      actual === idBitacora ? null : idBitacora
    );
  }

  cerrarSesion(): void {
    this.loginService.cerrarSesion().subscribe({
      next: () => this.router.navigate(['/login']),
      error: () => this.router.navigate(['/login']),
    });
  }
}
