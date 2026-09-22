/**
 * Modelos e interfaces TypeScript para CU07, CU08, CU09 y CU12
 * Detalle de Producto de Alta Costura, Variantes, Disponibilidad y Reservas en Boutique.
 */

export interface GaleriaToma {
  url: string;
  etiqueta: 'FRONTAL' | 'TEXTURA SEDA' | 'ESPALDA' | 'COSTURA' | string;
  orden: number;
}

export interface ComposicionNoble {
  cuerpo_principal: string;
  forro_interior: string;
  tecnica_textil: string;
  descripcion_confeccion: string;
  instrucciones_cuidado: string[];
}

export interface ColorResumen {
  id_color: number;
  nombre: string;
  codigo_hex: string;
  disponible: boolean;
  imagen_url?: string;
}

export interface TallaResumen {
  id_talla: number;
  codigo: string;
  orden: number;
  disponible: boolean;
  stock_total: number;
}

export interface VarianteDetalle {
  id_variante: number;
  id_producto: number;
  id_talla: number;
  talla_codigo: string;
  talla_orden: number;
  id_color: number;
  color_nombre: string;
  color_hex: string;
  sku: string;
  precio_extra: number | string;
  precio_final_variante: number | string;
  stock_total_disponible: number;
  tiene_stock: boolean;
  imagen_url?: string;
}

export interface PrendaComplementaria {
  id_producto: number;
  nombre: string;
  subtitulo_atelier: string;
  categoria: string;
  precio_base: number | string;
  precio_final: number | string;
  imagen_url: string;
}

export interface ProductoDetalle {
  id_producto: number;
  nombre: string;
  descripcion: string;
  precio_base: number | string;
  precio_final: number | string;
  tiene_descuento: boolean;
  descuento_monto: number | string;
  porcentaje_descuento: number | null;
  cuotas_info: string;
  subtitulo_atelier: string;
  linea_confeccion: string;
  etiqueta_badge: string;
  sku_base: string;
  rating_promedio: number;
  total_resenas: number;
  beneficio_membresia: string;
  categoria_id: number;
  categoria_nombre: string;
  coleccion_id: number | null;
  coleccion_nombre: string | null;
  imagen_principal: string;
  galeria: GaleriaToma[];
  modelo_ar_url: string | null;
  modelo_info: string;
  composicion: ComposicionNoble;
  colores_disponibles: ColorResumen[];
  tallas_disponibles: TallaResumen[];
  variantes: VarianteDetalle[];
  piezas_look_complementario: PrendaComplementaria[];
  total_guardados: number;
}

export interface DisponibilidadSucursalItem {
  id_sucursal: number;
  nombre: string;
  ciudad: string;
  direccion: string;
  telefono?: string | null;
  horario_apertura: string;
  horario_cierre: string;
  cantidad_disponible: number;
  cantidad_reservada: number;
  estado_stock: 'disponible' | 'ultimas_unidades' | 'agotada' | string;
  badge_stock: string;
  citas_disponibles_texto: string;
  permite_reserva_directa: boolean;
}

export interface DisponibilidadSucursales {
  id_producto: number;
  id_variante?: number | null;
  sku?: string | null;
  sucursales: DisponibilidadSucursalItem[];
  total_disponible_global: number;
}

export interface ReservaItemPayload {
  id_variante: number;
  cantidad: number;
}

export interface ReservaCrearPayload {
  id_sucursal: number;
  fecha_hora_atencion: string;
  canal_origen: 'web' | 'movil';
  observacion?: string;
  items: ReservaItemPayload[];
}

export interface ReservaItemConfirmado {
  id_reserva_detalle: number | null;
  id_variante: number;
  sku: string;
  nombre_producto: string;
  talla_codigo: string;
  color_nombre: string;
  cantidad: number;
  precio_unitario: string;
}

/**
 * Espejo exacto de `ReservaCreadaOut` (Ec-backend/app/modules/reservas/cu12_reservar_prendas/esquemas.py).
 * Los nombres deben coincidir campo a campo con el backend: cuando no lo hacían, el modal
 * imprimía el código y la nota de cortesía en blanco sin que ningún test lo detectara.
 */
export interface ReservaConfirmacion {
  id_reserva: number;
  codigo_reserva: string;
  id_sucursal: number;
  nombre_sucursal: string;
  direccion_sucursal: string;
  fecha_hora_atencion: string;
  estado: string;
  canal_origen: string;
  items: ReservaItemConfirmado[];
  mensaje_confirmacion: string;
  cortesias_incluidas: string[];
  creado_en: string;
}
