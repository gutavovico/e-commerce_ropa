/**
 * P2-CU14 / CU19 · Contratos del backend (`/api/v1/sin-conexion`, `/api/v1/avisos`) y registros que la
 * app guarda en IndexedDB. Los importes llegan como cadena (FastAPI serializa `Decimal` así) y no se
 * convierten a `number`.
 */

// ------------------------------------------------------------------ API

export interface DispositivoDto {
  id_dispositivo: number;
  identificador: string;
  plataforma: 'pwa' | 'flutter';
  codigo_corto: string;
  registrado_en: string;
  ultima_descarga_en: string | null;
  operacion_offline_habilitada: boolean;
  dias_antiguedad_offline: number;
  horas_vencimiento_reserva: number;
  moneda: string;
}

export interface VarianteLocalDto {
  id_variante: number;
  sku: string;
  id_talla: number;
  id_color: number;
  precio: string;
}

export interface ProductoLocalDto {
  id_producto: number;
  nombre: string;
  descripcion: string | null;
  id_categoria: number;
  precio_base: string;
  imagen_url: string | null;
  variantes: VarianteLocalDto[];
}

export interface CatalogoLocalDto {
  generado_en: string;
  modo: 'completo' | 'indispensable';
  moneda: string;
  productos: ProductoLocalDto[];
  categorias: { id_categoria: number; nombre: string; id_categoria_padre: number | null }[];
  tallas: { id_talla: number; codigo: string; orden: number }[];
  colores: { id_color: number; nombre: string; codigo_hex: string | null }[];
  promociones: {
    id_promocion: number;
    nombre: string;
    tipo_descuento: string;
    valor_descuento: string;
    alcance: string;
    id_categoria: number | null;
    id_producto: number | null;
    productos: number[];
    fecha_fin: string;
  }[];
  sucursales: {
    id_sucursal: number;
    nombre: string;
    direccion: string;
    ciudad: string | null;
    horario_apertura: string | null;
    horario_cierre: string | null;
  }[];
  existencias: { id_variante: number; id_sucursal: number; cantidad_disponible: number }[];
}

export type EstadoServidor = 'confirmada' | 'rechazada' | 'en_conflicto';

export interface ResultadoOperacionDto {
  uuid: string;
  estado: EstadoServidor | 'reintentar';
  motivo: string | null;
  mensaje: string | null;
  codigo_reserva: string | null;
  id_reserva: number | null;
  id_venta: number | null;
  id_conflicto: number | null;
  repetida: boolean;
}

export interface LoteDto {
  id_sync_log: number;
  resultados: ResultadoOperacionDto[];
}

export interface OperacionServidorDto {
  uuid: string;
  tipo: string;
  estado: EstadoServidor;
  motivo: string | null;
  codigo_provisional: string | null;
  codigo_reserva: string | null;
  id_reserva: number | null;
  id_venta: number | null;
  registrada_en: string;
  recibida_en: string;
  estado_conflicto: string | null;
}

export interface AvisoDto {
  id_aviso: number;
  tipo: 'reserva_cancelada' | 'reembolso_aceptado' | 'reembolso_procesado';
  titulo: string;
  mensaje: string;
  id_reserva: number | null;
  id_venta: number | null;
  creado_en: string;
  leido: boolean;
}

export interface BandejaAvisosDto {
  no_leidos: number;
  avisos: AvisoDto[];
}

// ------------------------------------------------------------------ IndexedDB

/** Estados de RN36: los dos primeros solo existen en el dispositivo. */
export type EstadoOperacion = 'registrada_localmente' | 'enviada' | EstadoServidor;

export interface DispositivoLocal {
  /** `${codigoTienda}:${idCliente}`: el identificador es por cliente y tienda. */
  clave: string;
  codigo: string;
  idCliente: number;
  identificador: string;
  codigoCorto: string | null;
  /** Correlativo del código provisional `PROV-<corto>-<6 dígitos>` (RN34). */
  correlativo: number;
  parametros: Pick<
    DispositivoDto,
    'operacion_offline_habilitada' | 'dias_antiguedad_offline' | 'horas_vencimiento_reserva' | 'moneda'
  > | null;
}

export interface CatalogoGuardado {
  /** Código de la tienda: un catálogo por tienda (nunca se mezclan). */
  codigo: string;
  paquete: CatalogoLocalDto;
  guardadoEn: string;
}

export interface OperacionLocal {
  uuid: string;
  /** `${codigoTienda}:${idCliente}` */
  clave: string;
  tipo: 'reserva';
  idSucursal: number;
  registradaEn: string;
  codigoProvisional: string;
  datos: {
    fecha_hora_atencion: string;
    observacion?: string;
    items: { id_variante: number; cantidad: number }[];
  };
  estado: EstadoOperacion;
  motivo: string | null;
  mensaje: string | null;
  codigoReserva: string | null;
  estadoConflicto: string | null;
  /** Para mostrarla sin red: prenda, variante y sucursal tal como se eligieron. */
  resumen: { producto: string; variante: string; sucursal: string };
}
