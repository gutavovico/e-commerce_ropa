import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { adminOnlyGuard } from './core/guards/role.guard';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () =>
      import(
        './modules/autenticacion_seguridad/cu02_iniciar_sesion/paginas/login.component'
      ).then((m) => m.LoginComponent),
  },
  {
    path: 'iniciar-sesion',
    redirectTo: 'login',
    pathMatch: 'full',
  },
  {
    path: 'registro',
    loadComponent: () =>
      import(
        './modules/autenticacion_seguridad/cu01_registrarse/paginas/registro.component'
      ).then((m) => m.RegistroComponent),
  },
  {
    path: 'recuperar-password',
    loadComponent: () =>
      import(
        './modules/autenticacion_seguridad/cu33_recuperar_acceso/paginas/recuperar-password.component'
      ).then((m) => m.RecuperarPasswordComponent),
  },
  {
    path: 'recuperar-acceso',
    redirectTo: 'recuperar-password',
    pathMatch: 'full',
  },
  {
    path: 'perfil',
    canActivate: [authGuard],
    loadComponent: () =>
      import(
        './modules/autenticacion_seguridad/cu04_gestionar_perfil/paginas/perfil.component'
      ).then((m) => m.PerfilComponent),
  },
  {
    path: 'mi-cuenta',
    redirectTo: 'perfil',
    pathMatch: 'full',
  },
  {
    path: 'buscar',
    loadComponent: () =>
      import(
        './modules/catalogo/cu06_buscar_filtrar/paginas/buscar-productos.component'
      ).then((m) => m.BuscarProductosComponent),
  },
  {
    path: 'catalogo',
    redirectTo: 'buscar',
    pathMatch: 'full',
  },
  {
    path: 'admin',
    canActivate: [authGuard],
    loadComponent: () =>
      import(
        './modules/admin/dashboard/admin-dashboard.component'
      ).then((m) => m.AdminDashboardComponent),
  },
  {
    path: 'admin/usuarios',
    canActivate: [authGuard, adminOnlyGuard],
    loadComponent: () =>
      import(
        './modules/autenticacion_seguridad/cu20_usuarios_roles/paginas/usuarios-admin.component'
      ).then((m) => m.UsuariosAdminComponent),
  },
  {
    path: 'admin/sucursales',
    canActivate: [authGuard, adminOnlyGuard],
    loadComponent: () =>
      import(
        './modules/gestion_operativa/cu21_sucursales_ciudades/paginas/sucursales-admin.component'
      ).then((m) => m.SucursalesAdminComponent),
  },
  {
    path: 'admin/atributos',
    canActivate: [authGuard],
    loadComponent: () =>
      import(
        './modules/gestion_operativa/cu23_categorias_tallas_colores/paginas/categorias-tallas-colores-admin.component'
      ).then((m) => m.CategoriasTallasColoresAdminComponent),
  },
  {
    path: 'admin/productos',
    canActivate: [authGuard],
    loadComponent: () =>
      import(
        './modules/gestion_operativa/cu22_prendas_productos/paginas/productos-admin.component'
      ).then((m) => m.ProductosAdminComponent),
  },
  {
    path: '',
    redirectTo: 'buscar',
    pathMatch: 'full',
  },
];
