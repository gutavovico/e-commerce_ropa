import { Routes } from '@angular/router';

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
    path: '',
    redirectTo: 'login',
    pathMatch: 'full',
  },
];
