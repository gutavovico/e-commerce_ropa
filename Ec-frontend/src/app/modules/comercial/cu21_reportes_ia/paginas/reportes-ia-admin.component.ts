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
import { ReportesIaService } from '../servicios/reportes-ia.service';
import {
  ContextoReportesIaEmpresa,
  FormatoVisualizacionIa,
  PuntoGraficoReporte,
  SolicitudReporteIaHistorial,
  SolicitudReporteIaResultado,
} from '../modelos/reportes-ia.model';

@Component({
  selector: 'app-reportes-ia-admin',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule, RouterLink],
  templateUrl: './reportes-ia-admin.component.html',
  styleUrls: ['./reportes-ia-admin.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ReportesIaAdminComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly reportesIaService = inject(ReportesIaService);

  readonly cargandoContexto = signal<boolean>(false);
  readonly generandoReporte = signal<boolean>(false);
  readonly exportandoFormato = signal<'pdf' | 'excel' | null>(null);
  readonly escuchandoVoz = signal<boolean>(false);

  readonly mensajeExito = signal<string | null>(null);
  readonly mensajeError = signal<string | null>(null);
  readonly planBloqueado = signal<boolean>(false);
  readonly codigoErrorPlan = signal<string | null>(null);

  readonly contexto = signal<ContextoReportesIaEmpresa | null>(null);
  readonly resultadoActual = signal<SolicitudReporteIaResultado | null>(null);
  readonly historial = signal<SolicitudReporteIaHistorial[]>([]);
  readonly vistaGraficoActiva = signal<'barras' | 'linea' | 'torta' | 'tabla'>('barras');

  readonly formConsulta: FormGroup = this.fb.group({
    prompt_texto: [
      'Ventas del último mes por sucursal en bolivianos con gráfico de barras',
      [Validators.required, Validators.minLength(2), Validators.maxLength(500)],
    ],
    codigo_reporte_forzado: [''],
    formato_preferido: ['ambos' as FormatoVisualizacionIa],
    fecha_inicio: [''],
    fecha_fin: [''],
    id_sucursal: [null as number | null],
    id_categoria: [null as number | null],
    tipo_cambio_bob: [6.96, [Validators.required, Validators.min(1)]],
  });

  readonly maxValorSerie = computed(() => {
    const serie = this.resultadoActual()?.serie_grafico ?? [];
    if (serie.length === 0) {
      return 1;
    }
    return Math.max(...serie.map((p) => Number(p.valor) || 0), 1);
  });

  readonly totalValorSerie = computed(() => {
    const serie = this.resultadoActual()?.serie_grafico ?? [];
    const suma = serie.reduce((acc, p) => acc + (Number(p.valor) || 0), 0);
    return suma > 0 ? suma : 1;
  });

  readonly entradasKpi = computed(() => {
    const kpis = this.resultadoActual()?.resumen_kpis_bob ?? {};
    return Object.entries(kpis).map(([clave, valor]) => ({
      etiqueta: this.formatearEtiquetaKpi(clave),
      esMonetarioBob: clave.includes('_bob'),
      esUsd: clave.includes('_usd'),
      valor,
    }));
  });

  ngOnInit(): void {
    this.cargarContextoEHistorial();
  }

  cargarContextoEHistorial(): void {
    this.cargandoContexto.set(true);
    this.limpiarMensajes();
    this.planBloqueado.set(false);

    this.reportesIaService.obtenerContextoEmpresa().subscribe({
      next: (ctx) => {
        this.contexto.set(ctx);
        const tc = Number(ctx.tipo_cambio_bob) || 6.96;
        this.formConsulta.patchValue({ tipo_cambio_bob: tc });
        this.cargandoContexto.set(false);
        this.cargarHistorial();
      },
      error: (err) => {
        this.cargandoContexto.set(false);
        this.manejarErrorHttp(err);
      },
    });
  }

  cargarHistorial(): void {
    this.reportesIaService.listarHistorial().subscribe({
      next: (items) => this.historial.set(items),
      error: () => {
        // Silencioso si ya se mostró error principal
      },
    });
  }

  usarEjemploPrompt(ejemplo: string): void {
    this.formConsulta.patchValue({ prompt_texto: ejemplo });
    this.ejecutarConsultaIa();
  }

  seleccionarReporteCatalogo(codigo: string, ejemplo?: string): void {
    this.formConsulta.patchValue({
      codigo_reporte_forzado: codigo,
      prompt_texto:
        ejemplo ||
        this.formConsulta.get('prompt_texto')?.value ||
        `Generar reporte ${codigo} en bolivianos`,
    });
  }

  iniciarDictadoVoz(): void {
    this.limpiarMensajes();
    const win = window as unknown as Record<string, unknown>;
    const SpeechRecognitionCtor =
      win['SpeechRecognition'] || win['webkitSpeechRecognition'];

    if (!SpeechRecognitionCtor) {
      // CU21 A4: fallo de transcripción o navegador sin soporte de voz
      this.mensajeError.set(
        'Su navegador no dispone de reconocimiento de voz activo (CU21 A4). Puede escribir o editar su solicitud directamente en el cuadro de texto.'
      );
      return;
    }

    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const recognition: any = new (SpeechRecognitionCtor as any)();
      recognition.lang = 'es-BO';
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      this.escuchandoVoz.set(true);

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      recognition.onresult = (event: any) => {
        const textoTranscrito =
          event?.results?.[0]?.[0]?.transcript?.trim() ?? '';
        this.escuchandoVoz.set(false);
        if (textoTranscrito) {
          this.formConsulta.patchValue({ prompt_texto: textoTranscrito });
          this.mensajeExito.set(
            `Solicitud transcrita por voz: «${textoTranscrito}». Puede revisarla o ejecutarla.`
          );
        } else {
          this.mensajeError.set(
            'No se pudo transcribir el audio con claridad (CU21 A4). Intente nuevamente o escriba su solicitud.'
          );
        }
      };

      recognition.onerror = () => {
        this.escuchandoVoz.set(false);
        this.mensajeError.set(
          'No fue posible completar la transcripción de voz (CU21 A4). Puede escribir su consulta en texto.'
        );
      };

      recognition.onend = () => {
        this.escuchandoVoz.set(false);
      };

      recognition.start();
    } catch {
      this.escuchandoVoz.set(false);
      this.mensajeError.set(
        'Error al iniciar el micrófono (CU21 A4). Escriba su solicitud en el campo de texto.'
      );
    }
  }

  ejecutarConsultaIa(): void {
    if (this.formConsulta.invalid) {
      this.formConsulta.markAllAsTouched();
      this.mensajeError.set(
        'Escribe o dicta una solicitud en lenguaje natural para generar el reporte.'
      );
      return;
    }

    const v = this.formConsulta.getRawValue();
    this.generandoReporte.set(true);
    this.limpiarMensajes();

    this.reportesIaService
      .generarReporte({
        prompt_texto: String(v.prompt_texto).trim(),
        codigo_reporte_forzado: v.codigo_reporte_forzado
          ? String(v.codigo_reporte_forzado)
          : null,
        formato_preferido: v.formato_preferido || 'ambos',
        fecha_inicio: v.fecha_inicio ? String(v.fecha_inicio) : null,
        fecha_fin: v.fecha_fin ? String(v.fecha_fin) : null,
        id_sucursal: v.id_sucursal ? Number(v.id_sucursal) : null,
        id_categoria: v.id_categoria ? Number(v.id_categoria) : null,
        tipo_cambio_bob: Number(v.tipo_cambio_bob) || 6.96,
      })
      .subscribe({
        next: (res) => {
          this.generandoReporte.set(false);
          this.resultadoActual.set(res);
          if (res.tipo_grafico) {
            this.vistaGraficoActiva.set(res.tipo_grafico);
          }
          this.cargarHistorial();
        },
        error: (err) => {
          this.generandoReporte.set(false);
          this.manejarErrorHttp(err);
        },
      });
  }

  cambiarVistaGrafico(vista: 'barras' | 'linea' | 'torta' | 'tabla'): void {
    this.vistaGraficoActiva.set(vista);
  }

  porcentajeBarra(punto: PuntoGraficoReporte): number {
    const max = this.maxValorSerie();
    const pct = Math.round(((Number(punto.valor) || 0) / max) * 100);
    return Math.max(4, Math.min(100, pct));
  }

  porcentajeParticipacion(punto: PuntoGraficoReporte): number {
    const total = this.totalValorSerie();
    return Number((((Number(punto.valor) || 0) / total) * 100).toFixed(1));
  }

  exportarReporte(idSolicitud: number, formato: 'pdf' | 'excel'): void {
    this.exportandoFormato.set(formato);
    this.limpiarMensajes();

    this.reportesIaService.exportarSolicitud(idSolicitud, formato).subscribe({
      next: (blob) => {
        this.exportandoFormato.set(null);
        const ext = formato === 'pdf' ? 'pdf' : 'xlsx';
        const nombre = `reporte_ia_${idSolicitud}_bolivianos.${ext}`;
        this.descargarBlob(blob, nombre);
        this.mensajeExito.set(
          `Reporte #${idSolicitud} exportado en formato ${formato.toUpperCase()} con montos en Bolivianos (Bs. / BOB) (RN48).`
        );
        this.cargarHistorial();
      },
      error: (err) => {
        this.exportandoFormato.set(null);
        this.manejarErrorHttp(err);
      },
    });
  }

  limpiarMensajes(): void {
    this.mensajeExito.set(null);
    this.mensajeError.set(null);
  }

  private descargarBlob(blob: Blob, nombreArchivo: string): void {
    if (typeof window === 'undefined' || !window.URL?.createObjectURL) {
      return;
    }
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = nombreArchivo;
    a.click();
    window.URL.revokeObjectURL(url);
  }

  private manejarErrorHttp(err: unknown): void {
    if (err instanceof HttpErrorResponse) {
      const code = err.error?.code || err.error?.error?.code || null;
      const detail =
        err.error?.detail ||
        err.error?.error?.message ||
        err.error?.message ||
        `Error HTTP ${err.status} al procesar la solicitud de reporte con IA.`;

      if (
        err.status === 403 &&
        (code === 'FUNCIONALIDAD_NO_INCLUIDA' ||
          code === 'SUSCRIPCION_NO_VIGENTE' ||
          String(detail).toLowerCase().includes('plan') ||
          String(detail).toLowerCase().includes('suscrip'))
      ) {
        this.planBloqueado.set(true);
        this.codigoErrorPlan.set(code || 'FUNCIONALIDAD_NO_INCLUIDA');
      }
      this.mensajeError.set(String(detail));
      return;
    }
    this.mensajeError.set('Error inesperado al comunicarse con el asistente de reportes IA.');
  }

  private formatearEtiquetaKpi(clave: string): string {
    const mapa: Record<string, string> = {
      ordenes_pagadas_totales: 'Órdenes Pagadas',
      ingresos_totales_bob: 'Ingresos Totales (Bs. BOB)',
      equivalente_usd: 'Equivalente Referencial (USD)',
      tipo_cambio_aplicado_bob: 'Tipo de Cambio (Bs./USD)',
      unidades_totales_vendidas: 'Unidades Vendidas',
      unidades_disponibles_totales: 'Stock Disponible (Unid.)',
      unidades_reservadas_totales: 'Stock Reservado (Unid.)',
      valor_inventario_total_bob: 'Valorización Inventario (Bs. BOB)',
      reservas_totales: 'Total Reservas',
      prendas_reservadas_totales: 'Prendas Reservadas',
    };
    return mapa[clave] || clave.replace(/_/g, ' ').toUpperCase();
  }
}

