/**
 * P2-CU02 · Acceso por empresa. Contratos copiados del backend
 * (`modules/plataforma/cu02_acceso_empresa/esquemas.py`).
 */

/** Datos públicos de una empresa (tienda). */
export interface EmpresaPublica {
  codigo: string;
  nombre: string;
}

/** Respuesta de `POST /api/v1/mis-empresas` («Registrarme en esta tienda»). */
export interface RegistroEnTiendaRespuesta {
  empresa: EmpresaPublica;
  registrado_ahora: boolean;
}

/** Nombre de la plataforma, fuera del portal de una tienda (directorio, login general). */
export const NOMBRE_PLATAFORMA = 'FashionStore';

/**
 * Primeros segmentos de URL que no son el código de una tienda. Debe coincidir con el CHECK
 * `chk_tenants_codigo_reservado` de la migración 0015 (decisión A13) más las rutas antiguas del
 * cliente que redirigen al directorio (A14).
 */
export const SEGMENTOS_RESERVADOS = new Set([
  '', 'admin', 'login', 'registro', 'recuperar-acceso', 'recuperar-password', 'iniciar-sesion',
  'api', 'ar', 'static', 'assets', 'mis-tiendas', 'pago', 'plataforma',
]);
