import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { LoginService } from '../../modules/autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';

/**
 * Interceptor HTTP de Autenticación y Seguridad (CU02/CU03).
 * 1. Inyecta el header Authorization: Bearer <token> en peticiones salientes cuando existe sesión activa.
 * 2. Captura errores 401 Unauthorized (token expirado o revocado), purga la sesión local
 *    y redirige automáticamente al usuario a la pantalla de /login.
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const loginService = inject(LoginService);
  const token = loginService.obtenerToken();

  let reqClonada = req;
  if (token && !req.headers.has('Authorization')) {
    reqClonada = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`,
      },
    });
  }

  return next(reqClonada).pipe(
    catchError((error: HttpErrorResponse) => {
      // Si el backend responde 401 y no es la petición de login en sí (credenciales inválidas)
      if (error.status === 401 && !req.url.includes('/autenticacion/login')) {
        loginService.purgarSesionLocal(true);
      }
      return throwError(() => error);
    })
  );
};
