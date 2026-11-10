/**
 * P2-CU18 · Contratos de `/api/v1/pos/cambios` (`cu18_cambio_prenda/esquemas.py`). Los importes son
 * cadenas (`Decimal`): se muestran con el pipe `importe` y nunca se calculan en el navegador.
 */
import { MetodoPagoCaja } from './punto-venta.dto';

export interface LineaCambiable {
  id_venta_detalle: number;
  id_variante: number;
  sku: string;
  nombre_producto: string;
  talla_codigo: string;
  color_nombre: string;
  vendidas: number;
  ya_cambiadas: number;
  cambiables: number;
  /** Lo pagado por unidad, con su parte del cupón (decisión F2). */
  valor_unitario: string;
}

export interface VentaCambiable {
  id_venta: number;
  numero_comprobante: string;
  fecha_venta: string;
  cliente_nombre: string | null;
  total: string;
  dias_transcurridos: number;
  plazo_dias: number;
  lineas: LineaCambiable[];
}

export interface CambioIn {
  id_venta: number;
  id_sucursal: number | null;
  devueltas: { id_venta_detalle: number; cantidad: number }[];
  nuevas: { id_variante: number; cantidad: number }[];
  cobro?: { metodo_pago: MetodoPagoCaja; monto_recibido?: string | null; referencia?: string | null } | null;
}

export interface LineaCambio {
  tipo: 'devuelta' | 'nueva';
  id_venta_detalle: number | null;
  id_variante: number;
  sku: string;
  nombre_producto: string;
  talla_codigo: string;
  color_nombre: string;
  cantidad: number;
  precio_unitario: string;
  subtotal: string;
  motivo_descuento: string | null;
}

export interface CambioPrevio {
  devueltas: LineaCambio[];
  nuevas: LineaCambio[];
  valor_devuelto: string;
  valor_nuevo: string;
  /** nuevo − devuelto: positivo, el cliente paga; negativo, se le devuelve en efectivo (F1). */
  diferencia: string;
}

export interface Cambio extends CambioPrevio {
  id_cambio: number;
  numero_comprobante: string;
  creado_en: string;
  id_venta: number;
  comprobante_venta: string;
  id_sucursal: number;
  nombre_sucursal: string;
  atendido_por: string | null;
  metodo_pago: string | null;
  monto_recibido: string | null;
  vuelto: string | null;
  referencia: string | null;
  devuelto_al_cliente: string;
}
