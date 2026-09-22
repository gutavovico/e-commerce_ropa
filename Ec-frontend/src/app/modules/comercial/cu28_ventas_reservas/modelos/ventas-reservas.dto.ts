/**
 * DTOs y Modelos TypeScript para CU28: Consultar ventas y reservas.
 * Nomenclatura oficial: "Consultar ventas y reservas"
 *
 * Contratos alineados con los esquemas Pydantic v2 del backend
 * (app/modules/comercial/cu28_ventas_reservas/esquemas.py).
 */

// ---------------------------------------------------------------------------
// Tipos Literales
// ---------------------------------------------------------------------------

export type TipoOperacionFiltro = 'venta' | 'reserva' | 'todas';

export type CriterioOrdenTransaccion =
  | 'creado_en_desc'
  | 'creado_en_asc'
  | 'total_desc'
  | 'total_asc'
  | 'fecha_desc';

export type CanalOrigenFiltro = 'web' | 'movil' | 'sucursal' | 'todos';

export type TipoOperacion = 'venta' | 'reserva';

// ---------------------------------------------------------------------------
// Filtros de Consulta (Entrada)
// ---------------------------------------------------------------------------

export interface TransaccionFiltros {
  q?: string;
  tipo_operacion?: TipoOperacionFiltro;
  estado?: string;
  id_sucursal?: number | null;
  fecha_desde?: string | null;
  fecha_hasta?: string | null;
  metodo_pago?: string | null;
  canal_origen?: CanalOrigenFiltro;
  ordenar_por?: CriterioOrdenTransaccion;
  pagina?: number;
  limite?: number;
}

// ---------------------------------------------------------------------------
// Lineas de Detalle y Pagos
// ---------------------------------------------------------------------------

export interface LineaDetalle {
  id_detalle: number;
  id_variante: number;
  sku: string;
  nombre_producto: string;
  talla: string;
  color: string;
  codigo_hex: string | null;
  cantidad: number;
  precio_unitario: number;
  subtotal_linea: number;
  imagen_url: string | null;
}

export interface PagoItem {
  id_pago: number;
  metodo_pago: string;
  monto: number;
  estado: string;
  referencia_pasarela: string | null;
  creado_en: string;
  confirmado_en: string | null;
}

// ---------------------------------------------------------------------------
// Resumen de Transaccion (Tabla Maestra)
// ---------------------------------------------------------------------------

export interface TransaccionResumenItem {
  id_transaccion: number;
  tipo_operacion: TipoOperacion;
  codigo_comprobante: string;
  fecha: string;
  id_cliente: number | null;
  nombre_cliente: string;
  email_cliente: string | null;
  telefono_cliente: string | null;
  id_sucursal: number;
  nombre_sucursal: string;
  ciudad_sucursal: string;
  canal: string;
  estado: string;
  total_monto: number;
  cantidad_items: number;
}

// ---------------------------------------------------------------------------
// Metricas Consolidadas (KPIs)
// ---------------------------------------------------------------------------

export interface MetricasTransaccionales {
  monto_total_facturado: number;
  total_ventas_concluidas: number;
  reservas_activas: number;
  ticket_promedio: number;
}

// ---------------------------------------------------------------------------
// Respuesta Paginada Unificada
// ---------------------------------------------------------------------------

export interface RespuestaPaginadaTransacciones {
  items: TransaccionResumenItem[];
  metricas: MetricasTransaccionales;
  total: number;
  pagina: number;
  limite: number;
  total_paginas: number;
}

// ---------------------------------------------------------------------------
// Detalle Completo de Venta
// ---------------------------------------------------------------------------

export interface VentaDetalleCompleto {
  id_venta: number;
  numero_comprobante: string;
  fecha_venta: string;
  estado: string;
  tipo_venta: string;
  subtotal: number;
  descuento: number;
  total: number;
  id_sucursal: number;
  nombre_sucursal: string;
  ciudad_sucursal: string;
  id_cliente: number | null;
  nombre_cliente: string;
  email_cliente: string | null;
  telefono_cliente: string | null;
  cajero_nombre: string | null;
  lineas: LineaDetalle[];
  pagos: PagoItem[];
}

// ---------------------------------------------------------------------------
// Detalle Completo de Reserva
// ---------------------------------------------------------------------------

export interface ReservaDetalleCompleto {
  id_reserva: number;
  codigo_reserva: string;
  fecha_hora_atencion: string;
  creado_en: string;
  estado: string;
  canal_origen: string;
  observacion: string | null;
  id_sucursal: number;
  nombre_sucursal: string;
  ciudad_sucursal: string;
  id_cliente: number;
  nombre_cliente: string;
  email_cliente: string | null;
  telefono_cliente: string | null;
  atendido_por_nombre: string | null;
  lineas: LineaDetalle[];
}

// ---------------------------------------------------------------------------
// Opciones de Sucursal (selector auxiliar)
// ---------------------------------------------------------------------------

export interface SucursalOpcion {
  id_sucursal: number;
  nombre: string;
  ciudad: string;
}
