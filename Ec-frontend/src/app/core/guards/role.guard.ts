import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { LoginService } from '../../modules/autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';

/**
 * Fabrica de guards para autorizacion RBAC basada en roles.
 * Si el usuario carece del rol necesario, redirige a /admin.
 */
export const roleGuard = (rolesPermitidos: string[]): CanActivateFn => {
  return () => {
    const loginService = inject(LoginService);
    const router = inject(Router);
    const usuario = loginService.usuarioActual();

    if (!usuario) {
      return router.createUrlTree(['/login']);
    }

    const rolNormalizado = String(usuario?.rol || '').toLowerCase().trim();
    const rolesPermitidosNormalizados = rolesPermitidos.map((r) =>
      String(r).toLowerCase().trim()
    );

    if (rolesPermitidosNormalizados.includes(rolNormalizado)) {
      return true;
    }

    return router.createUrlTree(['/admin']);
  };
};

export const adminOnlyGuard: CanActivateFn = () => {
  const loginService = inject(LoginService);
  const router = inject(Router);
  const usuario = loginService.usuarioActual();

  if (!usuario) {
    return router.createUrlTree(['/login']);
  }

  const rolNormalizado = String(usuario?.rol || '').toLowerCase().trim();
  if (rolNormalizado === 'administrador') {
    return true;
  }

  return router.createUrlTree(['/admin']);
};
