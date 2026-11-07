/**
 * DTOs e interfaces TypeScript para CU04 (Gestionar Perfil) y CU17 (Consultar Historial de Compras).
 * Mapeo estricto 1:1 con los esquemas Pydantic del backend de FastAPI.
 */

export interface ResumenAtelier {
  visitas_registradas: number;
  boutiques_visitadas: number;
  preferencia_textil: string;
  estatus_membresia: string;
}

export interface PerfilCliente {
  // Identidad y Cuenta
  id_usuario: number;
  numero_socio: string;
  email: string;
  rol: string;
  fecha_registro: string;
  miembro_desde: string;
  ultimo_acceso?: string | null;

  // Datos Personales
  nombres: string;
  apellidos: string;
  telefono?: string | null;

  // Preferencias y Datos de Cliente
  fecha_nacimiento?: string | null;
  genero?: string | null;
  talla_preferida?: string | null;
  ciudad_preferida?: number | null;
  acepta_marketing: boolean;

  // Resumen Haute Couture
  resumen_atelier: ResumenAtelier;
}

export interface PerfilClienteActualizar {
  nombres?: string;
  apellidos?: string;
  telefono?: string | null;
  fecha_nacimiento?: string | null;
  genero?: string | null;
  talla_preferida?: string | null;
  ciudad_preferida?: number | null;
  acepta_marketing?: boolean;
}

export interface ItemHistorialCompra {
  id_venta_detalle: number;
  id_producto: number;
  id_variante: number;
  sku: string;
  nombre_producto: string;
  imagen_url?: string | null;
  talla: string;
  color: string;
  color_hex?: string | null;
  cantidad: number;
  precio_unitario: string | number;
  subtotal_linea: string | number;
  nombre_sucursal?: string | null;
}

export interface PedidoHistorico {
  id_venta: number;
  numero_comprobante: string;
  fecha_venta: string;
  tipo_venta: string;
  estado: string;
  tipo_entrega: string;
  nombre_sucursal?: string | null;
  nombre_sucursal_retiro?: string | null;
  direccion_envio?: string | null;
  codigo_promocion?: string | null;
  subtotal: string | number;
  descuento: string | number;
  total: string | number;
  metodo_pago?: string | null;
  referencia_pasarela?: string | null;
  items: ItemHistorialCompra[];
}

export interface HistorialCompras {
  total_pedidos: number;
  pedidos_completados: number;
  pedidos: PedidoHistorico[];
}
