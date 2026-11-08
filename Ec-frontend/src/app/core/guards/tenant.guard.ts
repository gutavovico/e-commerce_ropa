import { inject } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { CanActivateFn, Router } from '@angular/router';
import { catchError, map, of } from 'rxjs';
import { TenantService } from '../tenant/tenant.service';
import { LoginService } from '../../modules/autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';

/** Destino del panel según el rol del empleado (mismo criterio que el login). */
export function destinoEmpleado(rol: string): string {
  return String(rol).toLowerCase().trim() === 'cajero' ? '/admin/pos' : '/admin';
}

export function esRolEmpleado(rol: string | undefined | null): boolean {
  return ['administrador', 'admin', 'encargado_sucursal', 'cajero'].includes(String(rol ?? '').toLowerCase().trim());
}

/**
 * P2-CU02 · Entrada al portal `/{codigo}`.
 *
 * - Tienda inexistente o no disponible → directorio `/` con el aviso correspondiente.
 * - Empleado con sesión que abre el portal de otra empresa → su panel (decisión A5).
 * - Cliente con sesión → carga sus tiendas para saber si está registrado en esta.
 */
export const tenantGuard: CanActivateFn = (route) => {
  const tenant = inject(TenantService);
  const login = inject(LoginService);
  const router = inject(Router);
  const codigo = String(route.paramMap.get('codigo') ?? '').toLowerCase();
  const usuario = login.usuarioActual();

  if (usuario && esRolEmpleado(usuario.rol) && usuario.tenant && usuario.tenant.codigo !== codigo) {
    return router.createUrlTree([destinoEmpleado(usuario.rol)]);
  }

  if (usuario?.rol === 'cliente' && tenant.misEmpresas() === null) {
    tenant.cargarMisEmpresas().subscribe({ error: () => tenant.misEmpresas.set(null) });
  }

  if (tenant.tenantActual()?.codigo === codigo) {
    return true;
  }
  return tenant.cargar(codigo).pipe(
    map(() => true),
    catchError((error: HttpErrorResponse) =>
      of(
        router.createUrlTree(['/'], {
          queryParams: { aviso: error.status === 404 ? 'tienda-inexistente' : 'tienda-no-disponible' },
        })
      )
    )
  );
};
