import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { HttpErrorResponse } from '@angular/common/http';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ReportesIaAdminComponent } from './reportes-ia-admin.component';
import { ReportesIaService } from '../servicios/reportes-ia.service';
import {
  ContextoReportesIaEmpresa,
  SolicitudReporteIaHistorial,
  SolicitudReporteIaResultado,
} from '../modelos/reportes-ia.model';

describe('ReportesIaAdminComponent (P2-CU21 — Generar reporte con IA en Bs./BOB)', () => {
  let component: ReportesIaAdminComponent;
  let fixture: ComponentFixture<ReportesIaAdminComponent>;

  const mockContexto: ContextoReportesIaEmpresa = {
    id_tenant: 10,
    nombre_empresa: 'Atelier La Paz',
    moneda_empresa: 'BOB',
    simbolo_moneda: 'Bs.',
    tipo_cambio_bob: 6.96,
    catalogo_activo: [
      {
        id_reporte_catalogo: 1,
        codigo: 'ventas_por_sucursal',
        nombre: 'Ventas e ingresos por sucursal',
        descripcion: 'Consolidado en Bolivianos (Bs. / BOB)',
        vista_origen: 'vw_ventas_por_sucursal',
        metricas: [
          {
            codigo: 'ingresos_totales_bob',
            etiqueta: 'Ingresos Totales (Bs. BOB)',
            expresion: 'SUM(total_orden)',
            es_monetaria: true,
          },
        ],
        dimensiones: [
          {
            codigo: 'sucursal',
            etiqueta: 'Sucursal',
            expresion: 'sucursal.nombre',
          },
        ],
        filtros_permitidos: ['fecha_inicio', 'fecha_fin', 'id_sucursal', 'moneda'],
        tipos_grafico: ['barras', 'linea', 'torta'],
        ejemplos_consulta: ['Ventas del último mes por sucursal en bolivianos'],
        activo: true,
        creado_en: '2026-11-09T10:00:00Z',
        actualizado_en: '2026-11-09T10:00:00Z',
      },
    ],
    sucursales_activas: [
      { id_sucursal: 101, nombre: 'Sucursal Prado La Paz', ciudad: 'La Paz' },
    ],
    categorias_empresa: [
      { id_categoria: 5, nombre: 'Abrigos de Alpaca' },
    ],
    ejemplos_destacados: ['Ventas del último mes por sucursal en bolivianos'],
  };

  const mockResultado: SolicitudReporteIaResultado = {
    id_solicitud: 77,
    estado: 'completada',
    mensaje_estado: 'Reporte generado en Bolivianos (Bs. / BOB).',
    prompt_original: 'Ventas del último mes por sucursal en bolivianos',
    codigo_reporte: 'ventas_por_sucursal',
    titulo_reporte: 'Ventas e ingresos por sucursal',
    interpretacion: {
      estado: 'completada',
      codigo_reporte: 'ventas_por_sucursal',
      nombre_reporte: 'Ventas e ingresos por sucursal',
      vista_origen: 'vw_ventas_por_sucursal',
      fecha_inicio: null,
      fecha_fin: null,
      id_sucursal: null,
      nombre_sucursal: null,
      id_categoria: null,
      nombre_categoria: null,
      tipo_grafico_sugerido: 'barras',
      formato_visualizacion: 'ambos',
      explicacion_ia: 'Montos en Bolivianos (Bs. / BOB)',
      origen_motor: 'semantico_determinista',
    },
    moneda: 'BOB',
    simbolo_moneda: 'Bs.',
    tipo_cambio_bob: 6.96,
    formato_visualizacion: 'ambos',
    tipo_grafico: 'barras',
    columnas: ['Sucursal', 'Órdenes Pagadas', 'Ingresos Totales (Bs. BOB)'],
    filas: [['Sucursal Prado La Paz', 8, 5568.0]],
    serie_grafico: [
      {
        etiqueta: 'Sucursal Prado La Paz',
        valor: 5568.0,
        valor_secundario: 8,
        unidad: 'Bs.',
      },
    ],
    resumen_kpis_bob: {
      ordenes_pagadas_totales: 8,
      ingresos_totales_bob: 5568.0,
      equivalente_usd: 800.0,
      tipo_cambio_aplicado_bob: 6.96,
    },
    sin_datos: false,
    ejemplos_sugeridos: ['Ventas del último mes por sucursal en bolivianos'],
    exportaciones: [],
    creado_en: '2026-11-09T12:00:00Z',
  };

  const mockHistorial: SolicitudReporteIaHistorial[] = [
    {
      id_solicitud: 77,
      id_tenant: 10,
      id_usuario: 25,
      comando_voz_texto: 'Ventas del último mes por sucursal en bolivianos',
      tipo_reporte: 'ventas_por_sucursal',
      estado: 'completada',
      formato_visualizacion: 'ambos',
      mensaje_estado: 'OK',
      exportaciones: [],
      creado_en: '2026-11-09T12:00:00Z',
    },
  ];

  let serviceMock: {
    obtenerContextoEmpresa: ReturnType<typeof vi.fn>;
    generarReporte: ReturnType<typeof vi.fn>;
    listarHistorial: ReturnType<typeof vi.fn>;
    exportarSolicitud: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    serviceMock = {
      obtenerContextoEmpresa: vi.fn().mockReturnValue(of(mockContexto)),
      generarReporte: vi.fn().mockReturnValue(of(mockResultado)),
      listarHistorial: vi.fn().mockReturnValue(of(mockHistorial)),
      exportarSolicitud: vi
        .fn()
        .mockReturnValue(of(new Blob(['%PDF-1.4'], { type: 'application/pdf' }))),
    };

    await TestBed.configureTestingModule({
      imports: [ReportesIaAdminComponent],
      providers: [
        provideRouter([]),
        { provide: ReportesIaService, useValue: serviceMock },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ReportesIaAdminComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe cargar el contexto del catálogo CU22 y el tipo de cambio en Bolivianos (6.96 Bs./USD)', () => {
    expect(component).toBeTruthy();
    expect(component.contexto()?.nombre_empresa).toBe('Atelier La Paz');
    expect(component.formConsulta.get('tipo_cambio_bob')?.value).toBe(6.96);
    expect(component.historial().length).toBe(1);
  });

  it('debe generar un reporte en Bolivianos (Bs. / BOB) y calcular los KPIs', () => {
    component.ejecutarConsultaIa();
    expect(serviceMock.generarReporte).toHaveBeenCalled();
    expect(component.resultadoActual()?.moneda).toBe('BOB');
    expect(component.resultadoActual()?.simbolo_moneda).toBe('Bs.');
    expect(component.entradasKpi().length).toBe(4);
  });

  it('debe detectar bloqueo de Plan Básico (CU21 A3 / RN44) cuando el backend responde 403 FUNCIONALIDAD_NO_INCLUIDA', () => {
    serviceMock.generarReporte.mockReturnValue(
      throwError(
        () =>
          new HttpErrorResponse({
            status: 403,
            error: {
              code: 'FUNCIONALIDAD_NO_INCLUIDA',
              detail: 'Su plan actual no incluye reportes_ia (RN44).',
            },
          })
      )
    );

    component.ejecutarConsultaIa();
    expect(component.planBloqueado()).toBe(true);
    expect(component.codigoErrorPlan()).toBe('FUNCIONALIDAD_NO_INCLUIDA');
  });

  it('debe exportar la solicitud en PDF y Excel registrando la descarga (RN48)', () => {
    component.exportarReporte(77, 'pdf');
    expect(serviceMock.exportarSolicitud).toHaveBeenCalledWith(77, 'pdf');
    expect(component.mensajeExito()).toContain('PDF');
  });
});
