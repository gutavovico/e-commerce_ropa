import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { LoginService } from '../../modules/autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import { TenantService } from '../tenant/tenant.service';

/**
 * Interceptor HTTP de Autenticación y Seguridad (CU02/CU03).
 * 1. Inyecta el header Authorization: Bearer <token> en peticiones salientes cuando existe sesión activa.
 * 2. Captura errores 401 Unauthorized (token expirado o revocado), purga la sesión local
 *    y redirige automáticamente al usuario a la pantalla de /login.
 * 3. P2-CU02: dentro del portal de una tienda añade `X-Tenant: <codigo>` a las peticiones de la API;
 *    un 403 CLIENTE_NO_REGISTRADO abre «Registrarme en esta tienda».
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const loginService = inject(LoginService);
  const tenantService = inject(TenantService);
  const token = loginService.obtenerToken();

  const cabeceras: Record<string, string> = {};
  if (token && !req.headers.has('Authorization')) {
    cabeceras['Authorization'] = `Bearer ${token}`;
  }
  const tienda = tenantService.tenantActual();
  if (tienda && req.url.startsWith('/api/') && !req.headers.has('X-Tenant')) {
    cabeceras['X-Tenant'] = tienda.codigo;
  }
  const reqClonada = Object.keys(cabeceras).length ? req.clone({ setHeaders: cabeceras }) : req;

  return next(reqClonada).pipe(
    catchError((error: HttpErrorResponse) => {
      // Si el backend responde 401 y no es la petición de login en sí (credenciales inválidas)
      if (error.status === 401 && !req.url.includes('/autenticacion/login')) {
        loginService.purgarSesionLocal(true);
      }
      if (error.status === 403 && error.error?.code === 'CLIENTE_NO_REGISTRADO') {
        tenantService.registroSolicitado.set(true);
      }
      return throwError(() => error);
    })
  );
};
