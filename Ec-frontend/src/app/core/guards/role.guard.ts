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
    let usuario = loginService.usuarioActual();

    // Recuperacion defensiva de sesion en caso de sincronizacion diferida
    if (!usuario && typeof window !== 'undefined') {
      try {
        const userJson =
          localStorage.getItem('fashionstore_user') ||
          sessionStorage.getItem('fashionstore_user');
        if (userJson) {
          usuario = JSON.parse(userJson);
        }
      } catch {
        usuario = null;
      }
    }

    if (!usuario) {
      console.warn('[ROLE_GUARD] Acceso denegado: sesion de usuario no encontrada.');
      return router.createUrlTree(['/login']);
    }

    const rolUsuario = String(usuario?.rol || '').toLowerCase().trim();
    const rolesPermitidosNormalizados = rolesPermitidos.map((r) =>
      String(r).toLowerCase().trim()
    );

    const esAdminValido =
      (rolUsuario === 'administrador' || rolUsuario === 'admin') &&
      (rolesPermitidosNormalizados.includes('administrador') ||
        rolesPermitidosNormalizados.includes('admin'));

    if (rolesPermitidosNormalizados.includes(rolUsuario) || esAdminValido) {
      return true;
    }

    console.warn(
      '[ROLE_GUARD] Acceso denegado. Rol usuario:',
      rolUsuario,
      'Roles requeridos:',
      rolesPermitidos
    );
    return router.createUrlTree(['/admin']);
  };
};

export const adminOnlyGuard: CanActivateFn = () => {
  const loginService = inject(LoginService);
  const router = inject(Router);
  let usuario = loginService.usuarioActual();

  // Recuperacion defensiva de sesion
  if (!usuario && typeof window !== 'undefined') {
    try {
      const userJson =
        localStorage.getItem('fashionstore_user') ||
        sessionStorage.getItem('fashionstore_user');
      if (userJson) {
        usuario = JSON.parse(userJson);
      }
    } catch {
      usuario = null;
    }
  }

  if (!usuario) {
    console.warn('[ROLE_GUARD] Acceso denegado a adminOnlyGuard: sesion no encontrada.');
    return router.createUrlTree(['/login']);
  }

  const rolUsuario = String(usuario?.rol || '').toLowerCase().trim();
  if (rolUsuario === 'administrador' || rolUsuario === 'admin') {
    return true;
  }

  console.warn(
    '[ROLE_GUARD] Acceso denegado a adminOnlyGuard. Rol usuario:',
    rolUsuario
  );
  return router.createUrlTree(['/admin']);
};

