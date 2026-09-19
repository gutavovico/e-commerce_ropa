import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: 'registro',
    loadComponent: () =>
      import(
        './modules/autenticacion_seguridad/cu01_registrarse/paginas/registro.component'
      ).then((m) => m.RegistroComponent),
  },
  {
    path: '',
    redirectTo: 'registro',
    pathMatch: 'full',
  },
];
