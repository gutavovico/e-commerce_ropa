import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { adminOnlyGuard, cajeroACajaGuard, roleGuard } from './core/guards/role.guard';
import { MainLayoutComponent } from './core/layouts/main-layout/main-layout.component';
import { PortalComponent } from './core/layouts/portal/portal.component';
import { tenantGuard } from './core/guards/tenant.guard';

export const routes: Routes = [
  // =========================================================================
  // 0. DIRECTORIO DE TIENDAS (P2-CU02, decisión A4)
  // =========================================================================
  {
    path: '',
    loadComponent: () =>
      import('./modules/plataforma/directorio/paginas/directorio.component').then(
        (m) => m.DirectorioComponent
      ),
    pathMatch: 'full',
    title: 'Tiendas',
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
    canActivate: [authGuard, cajeroACajaGuard],
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
    canActivate: [authGuard, cajeroACajaGuard],
    loadComponent: () =>
      import(
        './modules/gestion_operativa/cu23_categorias_tallas_colores/paginas/categorias-tallas-colores-admin.component'
      ).then((m) => m.CategoriasTallasColoresAdminComponent),
  },
  {
    path: 'admin/productos',
    canActivate: [authGuard, cajeroACajaGuard],
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
    path: 'admin/pos',
    canActivate: [authGuard, roleGuard(['administrador', 'admin', 'encargado_sucursal', 'cajero'])],
    loadComponent: () =>
      import(
        './modules/compras_pagos/cu31_cu32_punto_venta/paginas/punto-venta.component'
      ).then((m) => m.PuntoVentaComponent),
    title: 'FASHION STORE | Punto de venta',
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
    // P2-CU11: parámetros de la empresa (solo el administrador)
    path: 'admin/configuracion',
    canActivate: [authGuard, roleGuard(['administrador', 'admin'])],
    loadComponent: () =>
      import(
        './modules/plataforma/cu11_parametros_empresa/paginas/parametros-empresa.component'
      ).then((m) => m.ParametrosEmpresaComponent),
    title: 'Configuración',
  },
  {
    path: 'admin/reportes',
    canActivate: [authGuard, roleGuard(['administrador', 'admin', 'encargado_sucursal'])],
    loadComponent: () =>
      import(
        './modules/comercial/cu31_reportes_voz/paginas/reportes-admin.component'
      ).then((m) => m.ReportesAdminComponent),
    title: 'FASHION STORE | Generar reportes ejecutivos y consultas por voz',
  },
  {
    // «Mi perfil» del empleado; el perfil del cliente solo admite clientes (GET /perfil → 403)
    path: 'admin/perfil',
    canActivate: [authGuard, roleGuard(['administrador', 'admin', 'encargado_sucursal', 'cajero'])],
    loadComponent: () =>
      import(
        './modules/autenticacion_seguridad/cu04_perfil_empleado/paginas/perfil-empleado.component'
      ).then((m) => m.PerfilEmpleadoComponent),
    title: 'Mi perfil',
  },
  {
    path: 'admin/plataforma',
    canActivate: [authGuard, roleGuard(['super_administrador'])],
    loadComponent: () =>
      import(
        './modules/plataforma/superadmin/paginas/superadmin-panel.component'
      ).then((m) => m.SuperadminPanelComponent),
    title: 'FASHION STORE | Panel del Super Administrador SaaS',
  },
  {
    path: 'admin/suscripcion',
    canActivate: [authGuard, roleGuard(['administrador', 'admin'])],
    loadComponent: () =>
      import(
        './modules/plataforma/mi_suscripcion/paginas/mi-suscripcion-admin.component'
      ).then((m) => m.MiSuscripcionAdminComponent),
    title: 'FASHION STORE | Mi Suscripción y Renovación con Stripe',
  },
  {
    path: 'admin/reportes-ia',
    canActivate: [authGuard, roleGuard(['administrador', 'admin'])],
    loadComponent: () =>
      import(
        './modules/comercial/cu21_reportes_ia/paginas/reportes-ia-admin.component'
      ).then((m) => m.ReportesIaAdminComponent),
    title: 'FASHION STORE | Asistente de Reportes con IA en Bolivianos (CU21)',
  },
  {
    path: 'admin/aprendizaje-ml',
    canActivate: [authGuard, roleGuard(['administrador', 'admin'])],
    loadComponent: () =>
      import(
        './modules/comercial/cu23_cu25_aprendizaje_ml/paginas/aprendizaje-ml-admin.component'
      ).then((m) => m.AprendizajeMlAdminComponent),
    title: 'FASHION STORE | Aprendizaje Automático y Segmentación ML (CU23–CU25)',
  },

  // =========================================================================
  // 5. RUTAS ANTIGUAS DEL CLIENTE → DIRECTORIO (P2-CU02, decisión A14)
  // =========================================================================
  { path: 'inicio', redirectTo: '', pathMatch: 'full' },
  { path: 'home', redirectTo: '', pathMatch: 'full' },
  { path: 'buscar', redirectTo: '', pathMatch: 'full' },
  { path: 'catalogo', redirectTo: '', pathMatch: 'full' },
  { path: 'perfil', redirectTo: '', pathMatch: 'full' },
  { path: 'mi-cuenta', redirectTo: '', pathMatch: 'full' },
  { path: 'colecciones', redirectTo: '', pathMatch: 'full' },
  { path: 'colecciones/:id', redirectTo: '', pathMatch: 'full' },
  { path: 'bolsa', redirectTo: '', pathMatch: 'full' },
  { path: 'pago/:idVenta', redirectTo: '', pathMatch: 'full' },
  { path: 'reservas', redirectTo: '', pathMatch: 'full' },
  { path: 'productos/:id', redirectTo: '', pathMatch: 'full' },
  { path: 'catalogo/:id', redirectTo: '', pathMatch: 'full' },
  { path: 'registro', redirectTo: '', pathMatch: 'full' },

  // =========================================================================
  // 6. PORTAL DE CADA TIENDA: /{codigo}/... (P2-CU02, decisión A3)
  //    Va después de todas las rutas fijas: ':codigo' captura cualquier primer segmento.
  // =========================================================================
  {
    path: ':codigo',
    component: PortalComponent,
    canActivate: [tenantGuard],
    children: [
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
        path: 'bolsa',
        canActivate: [authGuard],
        loadComponent: () =>
          import(
            './modules/compras_pagos/cu11_gestionar_carrito/paginas/bolsa-compra.component'
          ).then((m) => m.BolsaCompraComponent),
        title: 'FASHION STORE | Bolsa de Compra & Checkout',
      },
      {
        path: 'pago/:idVenta',
        canActivate: [authGuard],
        loadComponent: () =>
          import(
            './modules/compras_pagos/cu16_realizar_pago/paginas/checkout-pago.component'
          ).then((m) => m.CheckoutPagoComponent),
        title: 'FASHION STORE | Pago Seguro & Pasarela Atelier',
      },
      {
        path: 'reservas',
        canActivate: [authGuard],
        loadComponent: () =>
          import(
            './modules/reservas/cu13_consultar_cancelar_reservas/paginas/mis-reservas.component'
          ).then((m) => m.MisReservasComponent),
        title: 'FASHION STORE | Mis Reservas de Probador',
      },
      {
        path: 'productos/:id',
        loadComponent: () =>
          import(
            './modules/catalogo/cu07_detalle_producto/paginas/producto-detalle.component'
          ).then((m) => m.ProductoDetalleComponent),
        title: 'FASHION STORE | Detalle de Prenda de Alta Costura',
      },
      {
        path: 'catalogo/:id',
        redirectTo: 'productos/:id',
        pathMatch: 'full',
      },

      // Acceso desde el portal (P2-CU02 §B.3)
      {
        path: 'login',
        loadComponent: () =>
          import(
            './modules/autenticacion_seguridad/cu02_iniciar_sesion/paginas/login.component'
          ).then((m) => m.LoginComponent),
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
    ],
  },

  // =========================================================================
  // 7. RUTA COMODÍN (404)
  // =========================================================================
  {
    path: '**',
    redirectTo: '',
  },
];
