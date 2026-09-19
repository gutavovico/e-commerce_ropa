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
    path: '',
    redirectTo: 'login',
    pathMatch: 'full',
  },
];
