/**
 * DTOs y tipos para el CU19: Consultar Asistente Inteligente (Chatbot).
 */

export interface MensajeChatbotPeticion {
  mensaje: string;
  canal: 'web' | 'movil';
  id_sucursal_preferida?: number | null;
}

export interface ProductoChatbotDto {
  id_producto: number;
  nombre: string;
  precio: string;
  categoria?: string | null;
  imagen_url?: string | null;
  disponible: boolean;
  sucursal_nombre?: string | null;
}

export interface SucursalChatbotDto {
  id_sucursal: number;
  nombre: string;
  direccion: string;
  horario: string;
}

export interface RespuestaChatbotDto {
  id_interaccion: number;
  respuesta: string;
  productos_sugeridos: ProductoChatbotDto[];
  sucursales_sugeridas: SucursalChatbotDto[];
  sugerencias_rapidas: string[];
}

export interface InteraccionHistorialDto {
  id_interaccion: number;
  mensaje_usuario: string;
  respuesta_ia?: string | null;
  canal: string;
  creado_en: string;
}

export interface MensajeBurbuja {
  id: string | number;
  emisor: 'usuario' | 'asistente';
  texto: string;
  hora: string;
  productos?: ProductoChatbotDto[];
  sucursales?: SucursalChatbotDto[];
}

