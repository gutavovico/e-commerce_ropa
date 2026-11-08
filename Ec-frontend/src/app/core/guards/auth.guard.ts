import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { LoginService } from '../../modules/autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import { TenantService } from '../tenant/tenant.service';

export const authGuard: CanActivateFn = () => {
  const router = inject(Router);
  const loginService = inject(LoginService);

  const token = loginService.obtenerToken();
  if (token && !loginService.esTokenExpirado(token)) {
    return true;
  }

  loginService.purgarSesionLocal(false);
  // P2-CU02: dentro de una tienda, a su login (tenantGuard del portal ya fijó la tienda)
  return router.createUrlTree(inject(TenantService).ruta(['/login']));
};
