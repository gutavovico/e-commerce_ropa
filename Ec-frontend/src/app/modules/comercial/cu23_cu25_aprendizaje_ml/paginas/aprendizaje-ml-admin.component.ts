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
import { RouterLink } from '@angular/router';
import { AprendizajeMlService } from '../servicios/aprendizaje-ml.service';
import {
  ConsultaPrediccionesMl,
  ConsultaSegmentosMl,
  DatasetMlItem,
  ModeloMlItem,
  OrigenDatosMl,
  PestanaAprendizajeMl,
  ResumenAprendizajeMl,
  SegmentoClienteMlItem,
  TipoModeloMl,
} from '../modelos/aprendizaje-ml.model';

@Component({
  selector: 'app-aprendizaje-ml-admin',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule, RouterLink],
  templateUrl: './aprendizaje-ml-admin.component.html',
  styleUrls: ['./aprendizaje-ml-admin.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AprendizajeMlAdminComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly mlService = inject(AprendizajeMlService);

  readonly pestanaActiva = signal<PestanaAprendizajeMl>('datos_modelos');
  readonly cargando = signal<boolean>(false);
  readonly procesando = signal<boolean>(false);

  readonly mensajeExito = signal<string | null>(null);
  readonly mensajeError = signal<string | null>(null);

  readonly resumen = signal<ResumenAprendizajeMl | null>(null);
  readonly datasetDetalle = signal<DatasetMlItem | null>(null);
  readonly consultaPredicciones = signal<ConsultaPrediccionesMl | null>(null);
  readonly consultaSegmentos = signal<ConsultaSegmentosMl | null>(null);
  readonly segmentoSeleccionado = signal<SegmentoClienteMlItem | null>(null);

  readonly variablesDatasetSeleccionadas = signal<string[]>([
    'precio_bob',
    'frecuencia_compra',
    'recencia_dias',
    'monto_acumulado_bob',
    'temporada_estacional',
    'sucursal_codificada',
  ]);

  // Filtros de Predicciones (P2-CU24)
  readonly filtroPredProducto = signal<number | null>(null);
  readonly filtroPredSucursal = signal<number | null>(null);
  readonly filtroPredPeriodo = signal<string>('');
  readonly tipoCambioBob = signal<number>(6.96);

  readonly formDataset: FormGroup = this.fb.group({
    nombre: [
      'Dataset Ventas & Clientas (Bolivianos Bs.)',
      [Validators.required, Validators.minLength(3), Validators.maxLength(140)],
    ],
    origen: ['sintetico' as OrigenDatosMl, [Validators.required]],
    cantidad_registros_sinteticos: [
      120,
      [Validators.required, Validators.min(20), Validators.max(2000)],
    ],
    horizonte_meses: [
      6,
      [Validators.required, Validators.min(1), Validators.max(24)],
    ],
  });

  readonly formModelo: FormGroup = this.fb.group({
    id_dataset: [null as number | null, [Validators.required]],
    nombre: [
      'Modelo Proyección de Demanda e Ingresos en Bs.',
      [Validators.required, Validators.minLength(3), Validators.maxLength(140)],
    ],
    tipo_modelo: ['supervisado' as TipoModeloMl, [Validators.required]],
    variable_objetivo: ['demanda_unidades'],
    numero_clusters: [3, [Validators.min(2), Validators.max(6)]],
    activar_inmediatamente: [true],
  });

  readonly datasetsDisponibles = computed(() => this.resumen()?.datasets ?? []);
  readonly modelosRegistrados = computed(() => this.resumen()?.modelos ?? []);

  ngOnInit(): void {
    this.cargarResumen();
  }

  cambiarPestana(pestana: PestanaAprendizajeMl): void {
    this.limpiarMensajes();
    this.pestanaActiva.set(pestana);
    if (pestana === 'datos_modelos') {
      this.cargarResumen();
    } else if (pestana === 'predicciones') {
      this.cargarPredicciones();
    } else if (pestana === 'segmentos') {
      this.cargarSegmentos();
    }
  }

  cargarResumen(): void {
    this.cargando.set(true);
    this.mlService.obtenerResumen().subscribe({
      next: (res) => {
        this.resumen.set(res);
        const tc = Number(res.tipo_cambio_bob) || 6.96;
        this.tipoCambioBob.set(tc);
        if (res.datasets.length > 0 && !this.formModelo.get('id_dataset')?.value) {
          this.formModelo.patchValue({ id_dataset: res.datasets[0].id_dataset });
        }
        this.cargando.set(false);
      },
      error: (err) => {
        this.cargando.set(false);
        this.mensajeError.set(this.extraerMensajeError(err));
      },
    });
  }

  toggleVariableDataset(codigo: string): void {
    this.variablesDatasetSeleccionadas.update((actual) =>
      actual.includes(codigo)
        ? actual.filter((v) => v !== codigo)
        : [...actual, codigo]
    );
  }

  crearDataset(): void {
    if (this.formDataset.invalid) {
      this.formDataset.markAllAsTouched();
      this.mensajeError.set('Completa los datos requeridos del conjunto de datos (CU23).');
      return;
    }
    if (this.variablesDatasetSeleccionadas().length === 0) {
      this.mensajeError.set('Selecciona al menos una variable para preprocesar (CU23 paso 3).');
      return;
    }

    const v = this.formDataset.getRawValue();
    this.procesando.set(true);
    this.limpiarMensajes();

    this.mlService
      .crearDataset({
        nombre: String(v.nombre).trim(),
        origen: v.origen,
        cantidad_registros_sinteticos: Number(v.cantidad_registros_sinteticos) || 120,
        horizonte_meses: Number(v.horizonte_meses) || 6,
        variables_seleccionadas: this.variablesDatasetSeleccionadas(),
        tipo_cambio_bob: this.tipoCambioBob(),
      })
      .subscribe({
        next: (ds) => {
          this.procesando.set(false);
          this.datasetDetalle.set(ds);
          this.formModelo.patchValue({ id_dataset: ds.id_dataset });
          this.mensajeExito.set(
            `Dataset «${ds.nombre}» (${ds.origen}) creado y preprocesado con ${ds.cantidad_registros} registros en Bolivianos (Bs. / BOB).`
          );
          this.cargarResumen();
        },
        error: (err) => {
          this.procesando.set(false);
          this.mensajeError.set(this.extraerMensajeError(err));
        },
      });
  }

  verPreprocesamientoDataset(ds: DatasetMlItem): void {
    this.datasetDetalle.set(ds);
  }

  entrenarModelo(): void {
    if (this.formModelo.invalid) {
      this.formModelo.markAllAsTouched();
      this.mensajeError.set('Selecciona un dataset y asigna un nombre al modelo (CU23).');
      return;
    }

    const v = this.formModelo.getRawValue();
    this.procesando.set(true);
    this.limpiarMensajes();

    this.mlService
      .entrenarModelo({
        id_dataset: Number(v.id_dataset),
        nombre: String(v.nombre).trim(),
        tipo_modelo: v.tipo_modelo,
        variable_objetivo:
          v.tipo_modelo === 'supervisado'
            ? String(v.variable_objetivo || '').trim()
            : null,
        variables_entrada: this.variablesDatasetSeleccionadas(),
        numero_clusters: Number(v.numero_clusters) || 3,
        activar_inmediatamente: Boolean(v.activar_inmediatamente),
        tipo_cambio_bob: this.tipoCambioBob(),
      })
      .subscribe({
        next: (mod) => {
          this.procesando.set(false);
          this.mensajeExito.set(
            `Modelo «${mod.nombre}» (${mod.tipo_modelo}) entrenado y evaluado con éxito (${
              mod.activo ? 'ACTIVADO' : 'EVALUADO'
            }).`
          );
          this.cargarResumen();
        },
        error: (err) => {
          this.procesando.set(false);
          this.mensajeError.set(this.extraerMensajeError(err));
        },
      });
  }

  activarModelo(mod: ModeloMlItem): void {
    this.limpiarMensajes();
    this.mlService.activarModelo(mod.id_modelo).subscribe({
      next: (act) => {
        this.mensajeExito.set(
          `Modelo «${act.nombre}» activado para analítica (${
            act.tipo_modelo === 'supervisado' ? 'Predicciones CU24' : 'Segmentos CU25'
          }).`
        );
        this.cargarResumen();
      },
      error: (err) => this.mensajeError.set(this.extraerMensajeError(err)),
    });
  }

  archivarModelo(mod: ModeloMlItem): void {
    this.limpiarMensajes();
    this.mlService.archivarModelo(mod.id_modelo).subscribe({
      next: (arch) => {
        this.mensajeExito.set(
          `Modelo «${arch.nombre}» archivado conservando sus métricas de evaluación (CU23 A5).`
        );
        this.cargarResumen();
      },
      error: (err) => this.mensajeError.set(this.extraerMensajeError(err)),
    });
  }

  // --- P2-CU24: Predicciones ---

  cargarPredicciones(): void {
    this.cargando.set(true);
    this.mlService
      .consultarPredicciones({
        id_producto: this.filtroPredProducto(),
        id_sucursal: this.filtroPredSucursal(),
        periodo: this.filtroPredPeriodo() || null,
        tipo_cambio_bob: this.tipoCambioBob(),
      })
      .subscribe({
        next: (res) => {
          this.consultaPredicciones.set(res);
          this.cargando.set(false);
        },
        error: (err) => {
          this.cargando.set(false);
          this.mensajeError.set(this.extraerMensajeError(err));
        },
      });
  }

  porcentajeProbabilidad(prob: number | string): number {
    const val = Number(prob) || 0;
    return Math.max(0, Math.min(100, Math.round(val * 100)));
  }

  // --- P2-CU25: Segmentos de Clientes ---

  cargarSegmentos(): void {
    this.cargando.set(true);
    this.mlService.consultarSegmentos(this.tipoCambioBob()).subscribe({
      next: (res) => {
        this.consultaSegmentos.set(res);
        this.segmentoSeleccionado.set(res.segmentos[0] ?? null);
        this.cargando.set(false);
      },
      error: (err) => {
        this.cargando.set(false);
        this.mensajeError.set(this.extraerMensajeError(err));
      },
    });
  }

  seleccionarSegmento(seg: SegmentoClienteMlItem): void {
    this.segmentoSeleccionado.set(seg);
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
        `Error HTTP ${err.status}: no se pudo completar la operación de Aprendizaje Automático.`
      );
    }
    return 'Error inesperado al comunicarse con el módulo de Aprendizaje Automático.';
  }
}

