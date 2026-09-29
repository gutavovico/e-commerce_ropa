/** Espejo de `ReservaOut` del backend (CU13/CU14). Importes como `string`: FastAPI serializa
 * `Decimal` como cadena JSON y este cliente no los convierte a número. */

export type EstadoReserva =
  | 'pendiente'
  | 'confirmada'
  | 'en_atencion'
  | 'atendida'
  | 'cancelada'
  | 'vencida';

export interface ReservaItem {
  id_variante: number;
  nombre_producto: string;
  talla_codigo: string;
  color_nombre: string;
  color_hex: string | null;
  imagen_url: string | null;
  cantidad: number;
  precio_unitario: string;
}

export interface SucursalReserva {
  id_sucursal: number;
  nombre: string;
  direccion: string;
}

export interface Reserva {
  id_reserva: number;
  codigo_reserva: string;
  estado: EstadoReserva;
  fecha_hora_atencion: string;
  creado_en: string;
  sucursal: SucursalReserva;
  items: ReservaItem[];
  total_prendas: number;
  observacion: string | null;
  /** Decidido en el servidor: el cliente no debe derivar por su cuenta si es cancelable. */
  puede_cancelar: boolean;
}

export interface ResumenProximaReserva {
  id_reserva: number;
  fecha_hora_atencion: string;
  nombre_sucursal: string;
}

export interface ResumenReservas {
  activas: number;
  proxima: ResumenProximaReserva | null;
}

export interface MisReservas {
  resumen: ResumenReservas;
  proximas: Reserva[];
  historial: Reserva[];
}
