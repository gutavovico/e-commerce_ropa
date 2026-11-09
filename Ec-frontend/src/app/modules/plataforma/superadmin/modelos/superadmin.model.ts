/**
 * Modelos e interfaces TypeScript estrictas para el Panel del Super Administrador SaaS (P2-CU05 a P2-CU08).
 */

export type EstadoEmpresa = 'activa' | 'suspendida' | 'baja';
export type EstadoSuscripcion = 'prueba' | 'activa' | 'vencida' | 'suspendida' | 'cancelada';
export type TipoOperacionSuscripcion =
  | 'alta'
  | 'cambio_plan'
  | 'renovacion'
  | 'suspension'
  | 'reactivacion'
  | 'cancelacion';

export type PestanaSuperadmin =
  | 'empresas'
  | 'planes'
  | 'suscripciones'
  | 'catalogos'
  | 'reportes_ia'
  | 'bitacora';

export interface SuscripcionResumenEmpresa {
  id_suscripcion: number;
  id_plan: number;
  nombre_plan: string;
  estado: EstadoSuscripcion;
  fecha_inicio: string;
  fecha_vencimiento: string;
  vigente: boolean;
}

export interface IndicadoresEmpresa {
  sucursales_activas: number;
  sucursales_totales: number;
  empleados_activos: number;
  productos_activos: number;
  ventas_pagadas_cantidad: number;
  ventas_pagadas_monto: number | string;
  reservas_totales: number;
}

export interface EmpresaResumen {
  id_tenant: number;
  codigo: string;
  nombre: string;
  correo_contacto: string | null;
  telefono: string | null;
  estado: EstadoEmpresa;
  creado_en: string;
  suscripcion_actual: SuscripcionResumenEmpresa | null;
  indicadores: IndicadoresEmpresa;
}

export interface EmpresaDetalle extends EmpresaResumen {
  admin_email: string | null;
  admin_nombre: string | null;
}

export interface AdminInicialEmpresaPeticion {
  nombres: string;
  apellidos: string;
  email: string;
  password: string;
  telefono?: string | null;
}

export interface EmpresaCrearPeticion {
  codigo: string;
  nombre: string;
  correo_contacto?: string | null;
  telefono?: string | null;
  id_plan: number;
  estado_suscripcion: 'prueba' | 'activa';
  fecha_inicio: string;
  fecha_vencimiento: string;
  admin_inicial: AdminInicialEmpresaPeticion;
}

export interface EmpresaActualizarPeticion {
  nombre: string;
  correo_contacto?: string | null;
  telefono?: string | null;
}

export interface CambiarEstadoEmpresaPeticion {
  estado: EstadoEmpresa;
  motivo?: string | null;
}

export interface MetricasPorEmpresaItem {
  id_tenant: number;
  codigo: string;
  nombre: string;
  estado_empresa: EstadoEmpresa;
  nombre_plan: string | null;
  estado_suscripcion: string | null;
  sucursales_activas: number;
  empleados_activos: number;
  productos_activos: number;
  ventas_pagadas_cantidad: number;
  ventas_pagadas_monto: number | string;
}

export interface MetricasPlataforma {
  empresas_totales: number;
  empresas_activas: number;
  empresas_suspendidas: number;
  empresas_baja: number;
  suscripciones_vigentes: number;
  suscripciones_vencidas_o_suspendidas: number;
  sucursales_activas_totales: number;
  empleados_activos_totales: number;
  ventas_pagadas_totales: number;
  monto_ventas_pagadas_total: number | string;
  desglose_empresas: MetricasPorEmpresaItem[];
}

export interface BitacoraPlataformaItem {
  id_bitacora: number;
  id_tenant: number | null;
  codigo_empresa: string | null;
  nombre_empresa: string | null;
  id_usuario: number | null;
  usuario_nombre: string | null;
  accion: string;
  tabla_modulo: string;
  direccion_ip: string | null;
  severidad: string;
  tiene_payload: boolean;
  payload_anterior: Record<string, unknown> | null;
  payload_nuevo: Record<string, unknown> | null;
  creado_en: string;
}

export interface BitacoraPlataformaListado {
  items: BitacoraPlataformaItem[];
  total: number;
  pagina: number;
  limite: number;
  total_paginas: number;
}

// --- P2-CU06: Planes y Funcionalidades ---

export interface FuncionalidadPlataforma {
  codigo: string;
  nombre: string;
  descripcion: string | null;
}

export interface PlanDetalle {
  id_plan: number;
  nombre: string;
  precio_mensual: number | string;
  max_sucursales_activas: number;
  max_empleados: number | null;
  activo: boolean;
  creado_en: string;
  funcionalidades: FuncionalidadPlataforma[];
  codigos_funcionalidades: string[];
  empresas_suscritas_vigentes: number;
  empresas_suscritas_totales: number;
  advertencias: string[];
}

export interface PlanGuardarPeticion {
  nombre: string;
  precio_mensual: number;
  max_sucursales_activas: number;
  max_empleados: number | null;
  funcionalidades: string[];
}

// --- P2-CU07: Suscripciones de Empresas ---

export interface SuscripcionEmpresa {
  id_suscripcion: number;
  id_tenant: number;
  codigo_empresa: string;
  nombre_empresa: string;
  estado_empresa: EstadoEmpresa;
  id_plan: number;
  nombre_plan: string;
  precio_mensual: number | string;
  estado: EstadoSuscripcion;
  fecha_inicio: string;
  fecha_vencimiento: string;
  vigente: boolean;
  sucursales_activas: number;
  max_sucursales_activas: number;
  empleados_activos: number;
  max_empleados: number | null;
  creado_en: string;
}

export interface OperacionSuscripcionPeticion {
  operacion: TipoOperacionSuscripcion;
  id_plan?: number | null;
  estado?: 'prueba' | 'activa' | null;
  fecha_inicio?: string | null;
  fecha_vencimiento?: string | null;
  motivo?: string | null;
}

export interface HistorialSuscripcionItem {
  id_historial: number;
  id_tenant: number;
  id_suscripcion: number;
  evento: string;
  detalle: Record<string, unknown> | null;
  id_usuario: number | null;
  creado_en: string;
}

// --- P2-CU08: Catálogos Globales ---

export interface CiudadGlobal {
  id_ciudad: number;
  nombre: string;
  pais: string;
  activo: boolean;
  creado_en: string;
  sucursales_asociadas: number;
}

export interface CiudadGlobalPeticion {
  nombre: string;
  pais: string;
}

export interface TallaGlobal {
  id_talla: number;
  codigo: string;
  orden: number;
  activo: boolean;
  variantes_asociadas: number;
}

export interface TallaGlobalPeticion {
  codigo: string;
  orden: number;
}

export interface ColorGlobal {
  id_color: number;
  nombre: string;
  codigo_hex: string | null;
  activo: boolean;
  variantes_asociadas: number;
}

export interface ColorGlobalPeticion {
  nombre: string;
  codigo_hex: string;
}

export interface EliminacionCatalogoRespuesta {
  eliminado: boolean;
  mensaje: string;
}

// --- P2-CU22: Catálogo de Reportes Permitidos con IA ---

export interface MetricaReporteCatalogo {
  codigo: string;
  etiqueta: string;
  expresion: string;
  es_monetaria: boolean;
}

export interface DimensionReporteCatalogo {
  codigo: string;
  etiqueta: string;
  expresion: string;
}

export interface CatalogoReporteItem {
  id_reporte_catalogo: number;
  codigo: string;
  nombre: string;
  descripcion: string | null;
  vista_origen: string;
  metricas: MetricaReporteCatalogo[];
  dimensiones: DimensionReporteCatalogo[];
  filtros_permitidos: string[];
  tipos_grafico: string[];
  ejemplos_consulta: string[];
  activo: boolean;
  creado_en: string;
  actualizado_en: string;
}

export interface CatalogoReporteGuardarPeticion {
  codigo: string;
  nombre: string;
  descripcion: string | null;
  vista_origen: string;
  metricas: MetricaReporteCatalogo[];
  dimensiones: DimensionReporteCatalogo[];
  filtros_permitidos: string[];
  tipos_grafico: string[];
  ejemplos_consulta: string[];
  activo: boolean;
}

export interface MetadatosCatalogoReportes {
  vistas_permitidas: string[];
  tipos_grafico_permitidos: string[];
  filtros_permitidos: string[];
  reportes: CatalogoReporteItem[];
}


