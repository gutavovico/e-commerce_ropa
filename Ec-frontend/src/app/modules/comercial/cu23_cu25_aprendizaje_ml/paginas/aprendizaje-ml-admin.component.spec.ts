import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { AprendizajeMlAdminComponent } from './aprendizaje-ml-admin.component';
import { AprendizajeMlService } from '../servicios/aprendizaje-ml.service';
import {
  ConsultaPrediccionesMl,
  ConsultaSegmentosMl,
  DatasetMlItem,
  ModeloMlItem,
  ResumenAprendizajeMl,
} from '../modelos/aprendizaje-ml.model';

describe('AprendizajeMlAdminComponent (P2-CU23, P2-CU24 y P2-CU25 en Bolivianos Bs./BOB)', () => {
  let component: AprendizajeMlAdminComponent;
  let fixture: ComponentFixture<AprendizajeMlAdminComponent>;

  const mockDataset: DatasetMlItem = {
    id_dataset: 1,
    id_tenant: 10,
    nombre: 'Dataset Sintético Invierno Bs.',
    origen: 'sintetico',
    cantidad_registros: 120,
    variables_seleccionadas: ['precio_bob', 'frecuencia_compra'],
    parametros_generacion: { moneda: 'BOB', tipo_cambio_bob: '6.96' },
    resumen_preprocesamiento: {
      limpieza_nulos: { metodo: 'mediana_num_y_moda_categorica' },
    },
    muestra_datos: [{ fila: 1, precio_bob: 696.0, moneda: 'BOB' }],
    creado_en: '2026-11-09T12:00:00Z',
  };

  const mockModeloSup: ModeloMlItem = {
    id_modelo: 10,
    id_tenant: 10,
    id_dataset: 1,
    nombre: 'Modelo Demanda Invierno Bs.',
    tipo_modelo: 'supervisado',
    algoritmo: 'RandomForestRegressor',
    variable_objetivo: 'demanda_unidades',
    variables_entrada: ['precio_bob', 'frecuencia_compra'],
    origen_datos: 'sintetico',
    estado: 'activo',
    activo: true,
    motivo_error: null,
    metricas_entrenamiento: { r2: 0.91, rmse: 3.8 },
    metricas_validacion: { r2: 0.89, rmse: 4.1 },
    metricas_prueba: { r2: 0.88, rmse: 4.3 },
    creado_en: '2026-11-09T12:05:00Z',
    actualizado_en: '2026-11-09T12:05:00Z',
  };

  const mockResumen: ResumenAprendizajeMl = {
    id_tenant: 10,
    nombre_empresa: 'Atelier La Paz',
    moneda: 'BOB',
    simbolo_moneda: 'Bs.',
    tipo_cambio_bob: 6.96,
    registros_reales_ventas: 18,
    registros_reales_clientes: 12,
    variables_disponibles: [
      { codigo: 'precio_bob', etiqueta: 'Precio Unitario en Bolivianos (Bs. BOB)' },
    ],
    variables_objetivo_supervisado: [
      { codigo: 'demanda_unidades', etiqueta: 'Demanda Esperada (Unidades)' },
    ],
    productos_empresa: [
      { id_producto: 1, nombre: 'Abrigo Alpaca', precio_bob: 850.0 },
    ],
    sucursales_empresa: [
      { id_sucursal: 101, nombre: 'Sucursal Prado' },
    ],
    datasets: [mockDataset],
    modelos: [mockModeloSup],
    modelo_supervisado_activo: mockModeloSup,
    modelo_no_supervisado_activo: null,
  };

  const mockPredicciones: ConsultaPrediccionesMl = {
    tiene_modelo_activo: true,
    mensaje_estado: 'Mostrando predicciones en Bolivianos (Bs. / BOB).',
    aviso_datos_sinteticos: true,
    mensaje_datos_sinteticos: 'Entrenado con datos sintéticos (CU24 A3).',
    moneda: 'BOB',
    simbolo_moneda: 'Bs.',
    tipo_cambio_bob: 6.96,
    modelo_activo: mockModeloSup,
    periodos_disponibles: ['proximo_mes', 'proximo_trimestre'],
    resumen_kpis_bob: {
      demanda_total_unidades: 24,
      ingresos_proyectados_bob: 16704.0,
      equivalente_proyectado_usd: 2400.0,
      probabilidad_media: 0.86,
    },
    predicciones: [
      {
        id_prediccion: 1,
        id_modelo: 10,
        id_producto: 1,
        nombre_producto: 'Abrigo Alpaca',
        id_sucursal: 101,
        nombre_sucursal: 'Sucursal Prado',
        periodo: 'proximo_mes',
        demanda_esperada: 24,
        ingresos_esperados_bob: 16704.0,
        equivalente_usd: 2400.0,
        probabilidad: 0.86,
        nivel_confianza: 'ALTA',
      },
    ],
  };

  const mockSegmentos: ConsultaSegmentosMl = {
    tiene_modelo_activo: true,
    mensaje_estado: 'Segmentos en Bolivianos (Bs. / BOB).',
    aviso_datos_sinteticos: true,
    mensaje_datos_sinteticos: 'Entrenado con datos sintéticos (CU25 A3).',
    moneda: 'BOB',
    simbolo_moneda: 'Bs.',
    tipo_cambio_bob: 6.96,
    modelo_activo: null,
    total_clientes_segmentados: 15,
    segmentos: [
      {
        id_segmento: 1,
        id_modelo: 20,
        codigo_grupo: 'SEG-VIP',
        nombre_grupo: 'Clientas VIP',
        descripcion: 'Alta frecuencia y ticket en Bs.',
        cantidad_clientes: 15,
        porcentaje_clientes: 100.0,
        sin_clientes: false,
        caracteristicas: {
          ticket_promedio_bob: 1480.0,
          frecuencia_mensual_media: 4.2,
        },
        clientes_muestra: [
          {
            id_usuario: 1001,
            nombre_completo: 'Valeria Rojas',
            email: 'valeria@ejemplo.bo',
            compras_realizadas: 6,
            reservas_realizadas: 2,
            monto_total_bob: 5420.0,
          },
        ],
      },
    ],
  };

  let serviceMock: {
    obtenerResumen: ReturnType<typeof vi.fn>;
    crearDataset: ReturnType<typeof vi.fn>;
    entrenarModelo: ReturnType<typeof vi.fn>;
    activarModelo: ReturnType<typeof vi.fn>;
    archivarModelo: ReturnType<typeof vi.fn>;
    consultarPredicciones: ReturnType<typeof vi.fn>;
    consultarSegmentos: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    serviceMock = {
      obtenerResumen: vi.fn().mockReturnValue(of(mockResumen)),
      crearDataset: vi.fn().mockReturnValue(of(mockDataset)),
      entrenarModelo: vi.fn().mockReturnValue(of(mockModeloSup)),
      activarModelo: vi.fn().mockReturnValue(of(mockModeloSup)),
      archivarModelo: vi.fn().mockReturnValue(of({ ...mockModeloSup, activo: false, estado: 'archivado' })),
      consultarPredicciones: vi.fn().mockReturnValue(of(mockPredicciones)),
      consultarSegmentos: vi.fn().mockReturnValue(of(mockSegmentos)),
    };

    await TestBed.configureTestingModule({
      imports: [AprendizajeMlAdminComponent],
      providers: [
        provideRouter([]),
        { provide: AprendizajeMlService, useValue: serviceMock },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AprendizajeMlAdminComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe cargar el resumen de CU23 con moneda en Bolivianos (Bs. / BOB)', () => {
    expect(component).toBeTruthy();
    expect(component.resumen()?.nombre_empresa).toBe('Atelier La Paz');
    expect(component.tipoCambioBob()).toBe(6.96);
    expect(component.datasetsDisponibles().length).toBe(1);
    expect(component.modelosRegistrados().length).toBe(1);
  });

  it('debe crear un dataset preprocesado y entrenar un modelo supervisado (CU23)', () => {
    component.crearDataset();
    expect(serviceMock.crearDataset).toHaveBeenCalled();
    expect(component.datasetDetalle()?.id_dataset).toBe(1);

    component.entrenarModelo();
    expect(serviceMock.entrenarModelo).toHaveBeenCalled();
  });

  it('debe consultar las predicciones en Bolivianos con probabilidad en [0, 1] (CU24 · RN50)', () => {
    component.cambiarPestana('predicciones');
    expect(serviceMock.consultarPredicciones).toHaveBeenCalled();
    expect(component.consultaPredicciones()?.tiene_modelo_activo).toBe(true);
    expect(component.consultaPredicciones()?.aviso_datos_sinteticos).toBe(true);
    expect(component.porcentajeProbabilidad(0.86)).toBe(86);
  });

  it('debe consultar los segmentos de clientes en Bolivianos (CU25)', () => {
    component.cambiarPestana('segmentos');
    expect(serviceMock.consultarSegmentos).toHaveBeenCalled();
    expect(component.consultaSegmentos()?.segmentos.length).toBe(1);
    expect(component.segmentoSeleccionado()?.codigo_grupo).toBe('SEG-VIP');
  });
});

