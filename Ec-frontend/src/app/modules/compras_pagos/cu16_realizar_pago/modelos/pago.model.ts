export type MetodoPago = 'tarjeta_credito' | 'tarjeta_debito' | 'qr' | 'pasarela_digital';

export interface PagoItem {
  id_variante: number;
  sku: string;
  nombre_producto: string;
  talla_codigo: string;
  color_nombre: string;
  imagen_url?: string | null;
  cantidad: number;
  precio_unitario: number | string;
  subtotal_linea: number | string;
  nombre_sucursal?: string | null;
}

export interface ResumenPago {
  id_venta: number;
  numero_comprobante: string;
  estado: string;
  subtotal: number | string;
  descuento: number | string;
  total: number | string;
  iva_incluido: number | string;
  moneda: string;
  total_prendas: number;
  items: PagoItem[];
  tipo_entrega: string;
  direccion_envio?: string | null;
  nombre_sucursal_retiro?: string | null;
  nombre_cliente?: string | null;
  fecha_venta: string;
  expira_en: string;
  segundos_restantes: number;
  metodos_disponibles: string[];
}

export type EscenarioPrueba = 'aprobado' | 'rechazado' | 'fondos_insuficientes';

/**
 * Payload de `POST /pagos/intentos`. No lleva ningún dato de tarjeta: el backend nunca recibe el
 * PAN ni el CVV (revisado el 2026-09-28). Ver la nota de §A.2 en `spec.md` de CU16.
 */
export interface PagoIniciarIn {
  id_venta: number;
  metodo_pago: MetodoPago;
  clave_idempotencia?: string | null;
  /** Solo tiene efecto cuando el backend está en modo simulador (sin `STRIPE_SECRET_KEY` real). */
  escenario_prueba?: EscenarioPrueba | null;
}

export interface PagoIntentoOut {
  id_pago: number;
  client_secret: string | null;
  ya_confirmado: boolean;
  confirmacion: PagoConfirmado | null;
}

export interface PagoConfirmado {
  id_pago: number;
  id_venta: number;
  numero_comprobante: string;
  estado_pago: string;
  estado_venta: string;
  metodo_pago: string;
  referencia_pasarela?: string | null;
  monto: number | string;
  moneda: string;
  marca_tarjeta?: string | null;
  ultimos_digitos?: string | null;
  confirmado_en?: string | null;
  mensaje_confirmacion: string;
}
