/**
 * Modelos e interfaces TypeScript estrictas para P2-CU23, P2-CU24 y P2-CU25
 * (Aprendizaje Automático / ML en Bolivianos Bs. / BOB).
 */

export type OrigenDatosMl = 'sintetico' | 'real' | 'mixto';
export type TipoModeloMl = 'supervisado' | 'no_supervisado';
export type EstadoModeloMl =
  | 'entrenando'
  | 'evaluado'
  | 'activo'
  | 'archivado'
  | 'fallido';
export type PestanaAprendizajeMl = 'datos_modelos' | 'predicciones' | 'segmentos';

export interface VariableDisponibleMl {
  codigo: string;
  etiqueta: string;
}

export interface ProductoEmpresaMl {
  id_producto: number;
  nombre: string;
  precio_bob: number;
}

export interface SucursalEmpresaMl {
  id_sucursal: number;
  nombre: string;
}

export interface DatasetMlItem {
  id_dataset: number;
  id_tenant: number;
  nombre: string;
  origen: OrigenDatosMl;
  cantidad_registros: number;
  variables_seleccionadas: string[];
  parametros_generacion: Record<string, unknown>;
  resumen_preprocesamiento: Record<string, Record<string, unknown>>;
  muestra_datos: Record<string, unknown>[];
  creado_en: string;
}

export interface CrearDatasetMlPeticion {
  nombre: string;
  origen: OrigenDatosMl;
  cantidad_registros_sinteticos: number;
  horizonte_meses: number;
  variables_seleccionadas: string[];
  tipo_cambio_bob: number;
}

export interface ModeloMlItem {
  id_modelo: number;
  id_tenant: number;
  id_dataset: number;
  nombre: string;
  tipo_modelo: TipoModeloMl;
  algoritmo: string;
  variable_objetivo: string | null;
  variables_entrada: string[];
  origen_datos: OrigenDatosMl;
  estado: EstadoModeloMl;
  activo: boolean;
  motivo_error: string | null;
  metricas_entrenamiento: Record<string, number | string>;
  metricas_validacion: Record<string, number | string>;
  metricas_prueba: Record<string, number | string>;
  creado_en: string;
  actualizado_en: string;
}

export interface EntrenarModeloMlPeticion {
  id_dataset: number;
  nombre: string;
  tipo_modelo: TipoModeloMl;
  algoritmo?: string | null;
  variable_objetivo?: string | null;
  variables_entrada: string[];
  numero_clusters: number;
  activar_inmediatamente: boolean;
  forzar_fallo_entrenamiento?: boolean;
  tipo_cambio_bob: number;
}

export interface ResumenAprendizajeMl {
  id_tenant: number;
  nombre_empresa: string;
  moneda: string;
  simbolo_moneda: string;
  tipo_cambio_bob: number | string;
  registros_reales_ventas: number;
  registros_reales_clientes: number;
  variables_disponibles: VariableDisponibleMl[];
  variables_objetivo_supervisado: VariableDisponibleMl[];
  productos_empresa: ProductoEmpresaMl[];
  sucursales_empresa: SucursalEmpresaMl[];
  datasets: DatasetMlItem[];
  modelos: ModeloMlItem[];
  modelo_supervisado_activo: ModeloMlItem | null;
  modelo_no_supervisado_activo: ModeloMlItem | null;
}

export interface PrediccionMlItem {
  id_prediccion: number;
  id_modelo: number;
  id_producto: number | null;
  nombre_producto: string;
  id_sucursal: number | null;
  nombre_sucursal: string;
  periodo: string;
  demanda_esperada: number;
  ingresos_esperados_bob: number | string;
  equivalente_usd: number | string;
  probabilidad: number | string;
  nivel_confianza: string;
}

export interface ConsultaPrediccionesMl {
  tiene_modelo_activo: boolean;
  mensaje_estado: string;
  aviso_datos_sinteticos: boolean;
  mensaje_datos_sinteticos: string | null;
  moneda: string;
  simbolo_moneda: string;
  tipo_cambio_bob: number | string;
  modelo_activo: ModeloMlItem | null;
  periodos_disponibles: string[];
  resumen_kpis_bob: Record<string, number | string>;
  predicciones: PrediccionMlItem[];
}

export interface ClienteMuestraSegmento {
  id_usuario: number;
  nombre_completo: string;
  email: string;
  compras_realizadas: number;
  reservas_realizadas: number;
  monto_total_bob: number;
}

export interface SegmentoClienteMlItem {
  id_segmento: number;
  id_modelo: number;
  codigo_grupo: string;
  nombre_grupo: string;
  descripcion: string;
  cantidad_clientes: number;
  porcentaje_clientes: number;
  sin_clientes: boolean;
  caracteristicas: Record<string, number | string>;
  clientes_muestra: ClienteMuestraSegmento[];
}

export interface ConsultaSegmentosMl {
  tiene_modelo_activo: boolean;
  mensaje_estado: string;
  aviso_datos_sinteticos: boolean;
  mensaje_datos_sinteticos: string | null;
  moneda: string;
  simbolo_moneda: string;
  tipo_cambio_bob: number | string;
  modelo_activo: ModeloMlItem | null;
  total_clientes_segmentados: number;
  segmentos: SegmentoClienteMlItem[];
}

