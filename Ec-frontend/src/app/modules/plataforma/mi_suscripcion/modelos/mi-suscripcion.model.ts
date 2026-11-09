/**
 * Modelos y contratos TypeScript para P2-CU09 (Consultar suscripción y uso)
 * y P2-CU10 (Cambiar de plan y renovar suscripción con Stripe).
 */

export interface EmpresaSuscripcionInfo {
  id_tenant: number;
  codigo: string;
  nombre: string;
  estado: string;
  moneda: string;
  simbolo_moneda?: string;
  tipo_cambio_bob?: number | string;
}

export interface SuscripcionEmpresaDetalle {
  id_suscripcion: number;
  id_plan: number;
  nombre_plan: string;
  precio_mensual: number | string;
  precio_mensual_bob?: number | string;
  estado: string;
  estado_efectivo: string;
  fecha_inicio: string;
  fecha_vencimiento: string;
  dias_restantes: number;
  vigente: boolean;
  proxima_a_vencer: boolean;
}

export interface UsoRecursoPlan {
  usados: number;
  limite: number | null;
  al_limite: boolean;
  excede_limite: boolean;
}

export interface SucursalActivaResumen {
  id_sucursal: number;
  nombre: string;
  direccion: string | null;
}

export interface UsoPlanEmpresa {
  sucursales: UsoRecursoPlan;
  empleados: UsoRecursoPlan;
  sucursales_activas_detalle: SucursalActivaResumen[];
}

export interface FuncionalidadPlanEmpresa {
  codigo: string;
  nombre: string;
  descripcion: string | null;
  planes_que_la_incluyen: string[];
}

export interface HistorialMiSuscripcion {
  id_historial: number;
  id_suscripcion: number;
  evento: string;
  detalle: Record<string, unknown> | null;
  id_usuario: number | null;
  creado_en: string;
}

export interface MiSuscripcionResumen {
  empresa: EmpresaSuscripcionInfo;
  suscripcion: SuscripcionEmpresaDetalle;
  uso: UsoPlanEmpresa;
  funcionalidades_incluidas: FuncionalidadPlanEmpresa[];
  funcionalidades_no_incluidas: FuncionalidadPlanEmpresa[];
  historial: HistorialMiSuscripcion[];
}

export interface PlanDisponibleEmpresa {
  id_plan: number;
  nombre: string;
  precio_mensual: number | string;
  precio_mensual_bob?: number | string;
  max_sucursales_activas: number;
  max_empleados: number | null;
  funcionalidades: string[];
  es_plan_actual: boolean;
  compatible_con_uso_actual: boolean;
  motivo_incompatibilidad: string | null;
}

export interface IniciarPagoSuscripcionDto {
  id_plan: number;
  meses: number;
  metodo_pago?: string;
}

export interface IntentoPagoSuscripcion {
  referencia: string;
  client_secret: string | null;
  estado_pago: string;
  monto: number | string;
  monto_bob?: number | string;
  moneda: string;
  tipo_cambio_bob?: number | string;
  id_plan: number;
  nombre_plan: string;
  meses: number;
  operacion: 'cambio_plan' | 'renovacion';
  requiere_cobro: boolean;
}

export type EscenarioPruebaStripe = 'exito' | 'rechazado' | 'fondos_insuficientes';

export interface ConfirmarCambioSuscripcionDto {
  id_plan: number;
  meses: number;
  referencia_pago: string;
  escenario_prueba?: EscenarioPruebaStripe;
}

