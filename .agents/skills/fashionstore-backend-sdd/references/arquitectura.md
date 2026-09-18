# Arquitectura del backend de FashionStore

## Contenido
1. Clasificación arquitectónica
2. Capas y reglas de dependencia
3. Estructura de carpetas de referencia
4. Catálogo de módulos por paquete (CU → Router → Service → ORM/Model)
5. Despliegue y entorno

---

## 1. Clasificación arquitectónica

Derivada de los diagramas de diseño físico (2.3.1.1), paquetes por capas (2.3.1.2) e implementación (2.4.2–2.4.3) del documento del proyecto. El documento no la nombra con una sola etiqueta; esta es la clasificación que mejor la describe:

- **Estilo general**: cliente-servidor en tres niveles (clientes → API → base de datos), con integraciones externas.
- **Backend**: **monolito modular en capas** (arquitectura *layered*): un solo servicio FastAPI desplegable, organizado en seis paquetes de dominio y, dentro de cada uno, en capas `Router → Service → ORM/Model`.
- **Interfaz**: **API RESTful** sin estado, versionada (`/api/v1`), consumida por dos clientes (Angular SPA y Flutter).
- **Organización**: **guiada por casos de uso** (PUDS): cada CU atraviesa verticalmente Interfaz → Vista → Componente → Servicio front → Router → Service → ORM → Model.
- **Despliegue**: nube con servicios gestionados (Vercel para el front web, Render para FastAPI, Neon para PostgreSQL) y servicios externos (Stripe en sandbox, servicio de IA vía API).

Lo que **no** es (y no debe volverse sin decisión explícita): microservicios, event-driven, ni arquitectura hexagonal formal. Sí conviene aplicar *de forma ligera* la idea de puertos/adaptadores para Stripe e IA (ver `integrations/`).

## 2. Capas y reglas de dependencia

```
Cliente (Angular / Flutter)
        │  HTTPS · JSON · /api/v1
        ▼
┌───────────────────────────────┐
│ Router   (HTTP, auth, schemas)│  ← traduce excepciones de dominio a HTTP
├───────────────────────────────┤
│ Service  (negocio, transacción)│ ← reglas, orquestación, llama a integraciones
├───────────────────────────────┤
│ ORM / Model (persistencia)    │
└──────────────┬────────────────┘
               ▼
        PostgreSQL (Neon)        Stripe · Servicio IA (vía integrations/)
```

Settings (configuración) es transversal: lo leen todas las capas, no depende de ninguna.

| Capa | Puede importar | No puede importar | Responsabilidad |
|---|---|---|---|
| Router | Service, schemas, deps de auth | ORM/Models directamente, integraciones | HTTP, validación de entrada, códigos de respuesta |
| Service | ORM/Models, integraciones, excepciones de dominio | `fastapi` (Request, HTTPException, Depends) | Reglas de negocio, transacciones, autorización por alcance |
| ORM/Model | SQLAlchemy y tipos | Services, Routers | Mapeo a tablas |
| Integrations | SDK/HTTP del proveedor | Routers | Adaptador de Stripe / IA con timeouts y errores propios |

**Dependencias entre paquetes.** Un paquete puede *usar el service* de otro (p. ej. Compras y Pagos llama al service de inventario), nunca sus modelos ORM ni sus tablas directamente. Así el stock tiene un único guardián.

## 3. Estructura de carpetas de referencia

Usa esta estructura solo si el repo aún no tiene una; si ya existe, respétala.

```
backend/
├── app/
│   ├── main.py                    # crea FastAPI, monta routers bajo /api/v1, handlers de error
│   ├── core/
│   │   ├── config.py              # Settings (variables de entorno)
│   │   ├── database.py            # engine, sesión, get_db
│   │   ├── security.py            # hash de contraseñas, emisión/validación de JWT
│   │   ├── deps.py                # get_current_user, require_roles, alcance por sucursal
│   │   └── errors.py              # excepciones de dominio base
│   ├── modules/
│   │   ├── autenticacion/         # router.py · service.py · models.py · schemas.py
│   │   ├── catalogo/
│   │   ├── gestion_operativa/
│   │   ├── reservas/
│   │   ├── compras_pagos/
│   │   └── funciones_avanzadas/   # vestidor, ia, reportes, bitácora
│   └── integrations/
│       ├── stripe_client.py
│       └── ia_client.py
├── migrations/                    # Alembic
├── tests/                         # espejo de modules/, más tests/integration
└── specs/                         # <CU>-<slug>/requirements.md · design.md · tasks.md
```

Si un paquete crece, separa `service.py` en un paquete `services/` con un archivo por caso de uso, manteniendo los nombres del catálogo de la sección 4.

## 4. Catálogo de módulos por paquete

Nombres tomados de los diagramas 2.4.3 del documento (en el código, pásalos a `snake_case`). Úsalos como punto de partida al diseñar; si un CU no aparece, decide su lugar en el diseño y preséntalo en la puerta 2.

### Autenticación y Seguridad
| CU | Router | Service | ORM / Model |
|---|---|---|---|
| CU01 Registrarse | RouterAuth | ServicioRegistroUsuario | UsuarioORM / Usuario |
| CU02 Iniciar sesión | RouterAuth | ServicioAutenticarLogin | UsuarioORM / Usuario |
| CU03 Cerrar sesión | RouterAuth | ServicioRevocarToken | TokenSesionORM / TokenSesion |
| CU04 Gestionar perfil | RouterPerfil | ServicioGestionPerfil | UsuarioORM / Usuario |
| CU20 Usuarios y roles | RouterUsuarios | ServicioUsuariosRoles | UsuarioORM, RolORM / Usuario, Rol |
| CU33 Recuperar acceso | RouterAuth | ServicioRecuperarPass | UsuarioORM / Usuario |

### Catálogo y Exploración
| CU | Router | Service | ORM / Model |
|---|---|---|---|
| CU05 Consultar catálogo | RouterCatalogo | ServicioConsultarCatalogo | ProductoORM / Producto, Categoria |
| CU06 Buscar y filtrar | RouterBusqueda | ServicioBuscarFiltro | ProductoORM (pg_trgm) / Producto |
| CU07 Detalle de producto | RouterProducto | ServicioObtenerDetalle | ProductoORM / Producto |
| CU08 Tallas, colores, características | RouterVariantes | ServicioConsultarVariantes | VariantesProductoORM / VarianteProducto, Talla |
| CU09 Disponibilidad por sucursal | RouterInventario | ServicioConsultarStock | InventarioSucursalORM / InventarioSucursal, Sucursal |

### Gestión Operativa
| CU | Router | Service | ORM / Model |
|---|---|---|---|
| CU21 Sucursales y ciudades | RouterSucursal | ServicioGestionSucursal | SucursalORM, CiudadORM / Sucursal, Ciudad |
| CU22 Productos | RouterProductoAdmin | ServicioGestionProducto | ProductoORM / Producto, VarianteProd |
| CU23 Categorías, tallas, colores | RouterAtributos | ServicioGestionAtributos | Cat/Talla/Color ORM / Categoria, Talla, Color |
| CU24 Temporadas y colecciones | RouterTemporada | ServicioGestionTemporada | Temporada/Coleccion ORM / Temporada, Coleccion |
| CU25 Proveedores | RouterProveedor | ServicioGestionProveedor | ProveedorORM / Proveedor |
| CU27 Promociones | RouterPromocion | ServicioGestionPromocion | PromocionORM / Promocion, PromocionProducto |

### Reservas
| CU | Router | Service | ORM / Model |
|---|---|---|---|
| CU12 Reservar prendas | RouterReserva | ServicioCrearReserva | ReservaORM, DetalleORM / Reserva, ReservaDetalle |
| CU13 Consultar y cancelar | RouterReserva | ServicioGestionarReserva | ReservaORM, InventarioORM / Reserva, Inventario |
| CU14 Consultar estado | RouterReserva | ServicioConsultarEstado | ReservaORM / Reserva |

### Compras y Pagos
| CU | Router | Service | ORM / Model |
|---|---|---|---|
| CU11 Carrito | RouterCarrito | ServicioGestionCarrito | CarritoORM, DetalleORM / Carrito, CarritoDetalle |
| CU15 Comprar (checkout) | RouterCheckout | ServicioProcesarCompra | VentaORM, VentaDetalleORM / Venta, VentaDetalle |
| CU16 Pago electrónico | RouterPagos | ServicioProcesarPago | PagoORM / Pago |
| CU17 Historial de compras | RouterHistorial | ServicioConsultarCompras | VentaORM / Venta |
| CU31 Venta presencial | RouterPOS | ServicioRegistrarPOS | VentaORM, InventarioORM / Venta, InventarioSucursal |
| CU32 Cobro y comprobante | RouterCobroPOS | ServicioEmitirComprobante | VentaORM, PagoORM / Venta, Pago |

### Funciones Avanzadas
| CU | Router | Service | ORM / Model |
|---|---|---|---|
| CU10 Vestidor virtual | RouterVestidor | ServicioProcesarAR | SesionVestidorORM / SesionesVestidorVirtual |
| CU18 Recomendaciones | RouterRecomendaciones | ServicioSugerenciasIA | RecomendacionIAORM / RecomendacionIA |
| CU19 Asistente inteligente | RouterChatbot | ServicioProcesarChat | InteraccionChatbotORM / InteraccionesChatbot |
| CU26 Inventario global | RouterReportes | ServicioInventarioGlobal | VwInventarioORM / vw_inventario_consolidado |
| CU28 Ventas y reservas | RouterAdminTransacciones | ServicioVentasReservas | Vistas ORM / vw_ventas…, vw_reservas… |
| CU29 Indicadores (KPI) | RouterDashboard | ServicioGenerarKPIs | SolicitudReporteORM / SolicitudesReporteIA |
| CU30/33 Bitácora | RouterBitacora | ServicioConsultarAuditoria | MovimientoInventarioORM / MovimientoInventario |

## 5. Despliegue y entorno

- **Render** ejecuta FastAPI (ASGI); **Neon** aloja PostgreSQL; **Vercel** sirve el frontend web. El móvil consume la misma API por HTTPS.
- Habilita CORS solo para los orígenes del front web; el móvil no lo necesita.
- Neon suspende cómputo por inactividad y Render (plan gratuito) también puede dormir el servicio: contempla reintento de conexión y `pool_pre_ping` en el engine, y no asumas conexiones persistentes.
- Variables de entorno esperadas (nombres sugeridos): `DATABASE_URL`, `JWT_SECRET`, `JWT_EXPIRE_MINUTES`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `IA_API_KEY`, `CORS_ORIGINS`.
- Extensiones PostgreSQL requeridas por el esquema: `pgcrypto`, `citext`, `pg_trgm`. Esquema `fashionstore` con `search_path` configurado.
