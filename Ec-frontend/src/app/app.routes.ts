import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

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
    path: 'inicio',
    redirectTo: 'catalogo',
    pathMatch: 'full',
  },
  {
    path: '',
    loadComponent: () =>
      import('./public/landing/landing.component').then(
        (m) => m.LandingPageComponent
      ),
    pathMatch: 'full',
    title: 'FASHION STORE | Alta Costura y Sastrería Digital',
  },
];
