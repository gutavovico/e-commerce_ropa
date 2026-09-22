import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { MainLayoutComponent } from './core/layouts/main-layout/main-layout.component';

export const routes: Routes = [
  // =========================================================================
  // 0. LANDING PAGE INSTITUCIONAL PÚBLICA
  // Debe declararse ANTES del bloque de MainLayoutComponent: ambos usan `path: ''`
  // y Angular resuelve las rutas en orden. Con el layout por delante, la URL raíz
  // entraba en él y, al no existir ningún hijo con `path: ''`, la landing quedaba
  // inalcanzable. Su `pathMatch: 'full'` garantiza que solo capture la URL vacía
  // exacta, sin interferir con /inicio, /catalogo ni el resto de secciones.
  // =========================================================================
  {
    path: '',
    loadComponent: () =>
      import('./public/landing/landing.component').then(
        (m) => m.LandingPageComponent
      ),
    pathMatch: 'full',
    title: 'FASHION STORE | Alta Costura y Sastrería Digital',
  },

  // =========================================================================
  // 1. PANTALLAS RAÍZ (HUB) BAJO MAIN LAYOUT CON NAVBAR PERSISTENTE
  // Únicamente estas 4 secciones tienen la barra de navegación institucional
  // y carecen estrictamente de botón volver (←).
  // =========================================================================
  {
    path: '',
    component: MainLayoutComponent,
    children: [
      {
        path: 'inicio',
        loadComponent: () =>
          import('./modules/inicio/paginas/inicio.component').then(
            (m) => m.InicioComponent
          ),
        title: 'FASHION STORE | Inicio & Atelier Exclusivo',
      },
      {
        path: 'home',
        redirectTo: 'inicio',
        pathMatch: 'full',
      },
      {
        path: 'buscar',
        loadComponent: () =>
          import(
            './modules/catalogo/cu06_buscar_filtrar/paginas/buscar-productos.component'
          ).then((m) => m.BuscarProductosComponent),
        title: 'FASHION STORE | Búsqueda & Catálogo Atelier',
      },
      {
        path: 'catalogo',
        loadComponent: () =>
          import(
            './modules/catalogo/cu05_consultar_catalogo/paginas/catalogo.component'
          ).then((m) => m.CatalogoComponent),
        title: 'FASHION STORE | Catálogo & Exploración Atelier',
      },
      {
        path: 'perfil',
        canActivate: [authGuard],
        loadComponent: () =>
          import(
            './modules/autenticacion_seguridad/cu04_gestionar_perfil/paginas/perfil.component'
          ).then((m) => m.PerfilComponent),
        title: 'FASHION STORE | Perfil de Cliente Atelier',
      },
      {
        path: 'mi-cuenta',
        redirectTo: 'perfil',
        pathMatch: 'full',
      },
    ],
  },

  // =========================================================================
  // 2. PANTALLAS SECUNDARIAS (HOJAS / SPOKE) FUERA DEL MAIN LAYOUT
  // Barra de navegación global oculta / no disponible.
  // Botón funcional de regreso (← Volver) estrictamente obligatorio.
  // =========================================================================
  {
    path: 'colecciones',
    loadComponent: () =>
      import(
        './modules/colecciones/paginas/colecciones/colecciones.component'
      ).then((m) => m.ColeccionesComponent),
    title: 'FASHION STORE | Colecciones & Archivo de Sastrería',
  },
  {
    path: 'colecciones/:id',
    loadComponent: () =>
      import(
        './modules/colecciones/paginas/coleccion-detalle/coleccion-detalle.component'
      ).then((m) => m.ColeccionDetalleComponent),
    title: 'FASHION STORE | Detalle de Colección',
  },
  {
    path: 'productos/:id',
    loadComponent: () =>
      import(
        './modules/catalogo/cu07_detalle_producto/paginas/producto-detalle.component'
      ).then((m) => m.ProductoDetalleComponent),
    title: 'FASHION STORE | Detalle de Prenda de Alta Costura',
  },

  // =========================================================================
  // 3. FLUJOS DE AUTENTICACIÓN Y SEGURIDAD
  // =========================================================================
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

  // =========================================================================
  // 4. RUTA COMODÍN (404)
  // `vercel.json` reescribe cualquier URL a index.html, así que sin este comodín
  // un enlace obsoleto provocaba un NG04002 y una pantalla en blanco.
  // =========================================================================
  {
    path: '**',
    redirectTo: '',
  },
];
