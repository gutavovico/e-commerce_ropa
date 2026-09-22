import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { adminOnlyGuard, roleGuard } from './core/guards/role.guard';
import { MainLayoutComponent } from './core/layouts/main-layout/main-layout.component';

export const routes: Routes = [
  // =========================================================================
  // 0. LANDING PAGE INSTITUCIONAL PÚBLICA
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
  // 4. PANEL DE CONTROL Y MÓDULOS ADMINISTRATIVOS CORPORATIVOS
  // =========================================================================
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
    path: 'admin/inventario',
    canActivate: [authGuard, roleGuard(['administrador', 'admin', 'encargado_sucursal'])],
    loadComponent: () =>
      import(
        './modules/gestion_operativa/cu24_inventario_stock/paginas/inventario-admin.component'
      ).then((m) => m.InventarioAdminComponent),
  },
  {
    path: 'admin/proveedores',
    canActivate: [authGuard, roleGuard(['administrador', 'admin', 'encargado_sucursal'])],
    loadComponent: () =>
      import(
        './modules/gestion_operativa/cu25_proveedores/paginas/proveedores-admin.component'
      ).then((m) => m.ProveedoresAdminComponent),
  },
  {
    path: 'admin/inventario-global',
    canActivate: [authGuard, roleGuard(['administrador', 'admin', 'encargado_sucursal'])],
    loadComponent: () =>
      import(
        './modules/gestion_operativa/cu26_inventario_global/paginas/inventario-global-admin.component'
      ).then((m) => m.InventarioGlobalAdminComponent),
  },
  {
    path: 'admin/temporadas-colecciones',
    canActivate: [authGuard, roleGuard(['administrador', 'admin', 'encargado_sucursal'])],
    loadComponent: () =>
      import(
        './modules/catalogo/cu24_temporadas_colecciones/paginas/temporadas-colecciones-admin.component'
      ).then((m) => m.TemporadasColeccionesAdminComponent),
  },
  {
    path: 'admin/promociones',
    canActivate: [authGuard, roleGuard(['administrador', 'admin', 'encargado_sucursal'])],
    loadComponent: () =>
      import(
        './modules/comercial/cu27_promociones/paginas/promociones-admin.component'
      ).then((m) => m.PromocionesAdminComponent),
  },
  {
    path: 'admin/ventas-reservas',
    canActivate: [authGuard, roleGuard(['administrador', 'admin', 'encargado_sucursal'])],
    loadComponent: () =>
      import(
        './modules/comercial/cu28_ventas_reservas/paginas/ventas-reservas-admin.component'
      ).then((m) => m.VentasReservasAdminComponent),
  },
  {
    path: 'admin/indicadores',
    canActivate: [authGuard, roleGuard(['administrador', 'admin', 'encargado_sucursal'])],
    loadComponent: () =>
      import(
        './modules/comercial/cu29_indicadores/paginas/indicadores-admin.component'
      ).then((m) => m.IndicadoresAdminComponent),
  },
  {
    path: 'admin/bitacora',
    canActivate: [authGuard, roleGuard(['administrador', 'admin'])],
    loadComponent: () =>
      import(
        './modules/seguridad/cu30_bitacora/paginas/bitacora-admin.component'
      ).then((m) => m.BitacoraAdminComponent),
  },
  {
    path: 'admin/perfil',
    canActivate: [authGuard, roleGuard(['administrador', 'admin', 'encargado_sucursal'])],
    loadComponent: () =>
      import(
        './modules/autenticacion_seguridad/cu04_gestionar_perfil/paginas/perfil.component'
      ).then((m) => m.PerfilComponent),
    title: 'FASHION STORE | Perfil Institucional Administrador',
  },

  // =========================================================================
  // 5. RUTA COMODÍN (404)
  // =========================================================================
  {
    path: '**',
    redirectTo: '',
  },
];
