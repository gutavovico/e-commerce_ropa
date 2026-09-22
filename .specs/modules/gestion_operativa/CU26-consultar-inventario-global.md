# Especificacion Tecnica Permanente: CU26 - Consultar inventario global

**Codigo:** CU26  
**Nombre:** Consultar inventario global  
**Paquete de Dominio:** `gestion_operativa` / `inventario`  
**Directorio Funcional Backend:** `app/modules/gestion_operativa/cu26_inventario_global`  
**Directorio Funcional Frontend:** `src/app/modules/gestion_operativa/cu26_inventario_global`  
**Directorio Funcional Mobile:** Excluido formalmente (auditoria corporativa analitica y balance consolidado multi-sede; exclusivo del panel web de administracion)  
**Actores Primarios:**  
- Administrador (Control e inspeccion panoramica de existencias en la totalidad de la red comercial, evaluacion de alertas y balances multi-sede)  
- Encargado de Sucursal (Consulta multi-sede orientada a derivacion inter-tiendas y consulta de existencias en boutiques hermanas)  
**Actores Bloqueados:**  
- Cajero (Bloqueo estricto por politica RBAC - HTTP 403 Forbidden)  
- Cliente (Bloqueo estricto por politica RBAC - HTTP 403 Forbidden)  
**Metodologia:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Version:** 2.2.0 (Linea Base Permanente)  
**Estado:** Aprobado y Promovido a Permanente  
**Fuentes de Verdad:**  
- Documento Maestro de Requisitos: `SI2-Parcial1.md` (Seccion 1.4 Modulo de Inventarios y Gestion Multi-Sucursal, Seccion 2.3 Esquema Relacional de Base de Datos).  
- Arquitectura de Dominio Backend: `.agents/skills/fashionstore-backend-sdd/references/dominio.md`.  
- Design System Multiplataforma: `.agents/skills/fashionstore-frontend-sdd/references/fashionstore-tokens.md` (Diseno editorial Atelier, paleta Slate/Camel/Obsidian, tipografia Outfit, ChangeDetectionStrategy.OnPush y Angular Signals).  

---

## 1. Definicion Funcional y Reglas de Negocio

### 1.1 Proposito y Alcance
El caso de uso CU26 provee una vision analitica consolidada y en tiempo real de las existencias fisicas y disponibles de todas las prendas y variantes (talla/color) en la totalidad de sucursales activas de la cadena FashionStore. Centraliza los balances comerciales, calcula indicadores globales de red, clasifica el estado semaforico de stock y provee un directorio logistico de coordinacion inter-tiendas para derivaciones de clientes.

### 1.2 Declaracion Formal de Exclusion de la Aplicacion Movil (Ec-mobile)
La aplicacion movil de FashionStore (`Ec-mobile`), desarrollada en Flutter 3.x, se focaliza con exclusividad en la experiencia B2C del cliente final (navegacion por catalogo, bolsa de compras, vestidor en Realidad Aumentada y pasarela de pagos).  
La auditoria de balances multi-sede, la gestion de roturas de stock en la red de boutiques y la coordinacion logistica corporativa constituyen funciones reservadas a la trastienda operativa y gerencial ejecutada en el panel de administracion web de escritorio (`Ec-frontend`).  
Por tanto, se ratifica la exclusion formal y justificada de `Ec-mobile` para este caso de uso: cero pantallas, modelos Dart o servicios HTTP asociados en Flutter.

### 1.3 Reglas de Negocio Estrictas (RB)

1. **RB-1: Control de Acceso y Autorizacion RBAC:**
   - El endpoint `GET /api/v1/admin/inventario/global` requiere autenticacion obligatoria con JWT y pertenencia a los roles `administrador` o `encargado_sucursal`. Peticiones no autenticadas devuelven HTTP 401 Unauthorized; roles `cajero` o `cliente` devuelven HTTP 403 Forbidden.

2. **RB-2: Agregacion Relacional y Exclusion de Sedes Inactivas:**
   - Las existencias deben sumar exclusivamente las cantidades de sucursales activas (`SucursalORM.activa.is_(True)`). Tiendas cerradas o en mantenimiento no computan en el disponible consolidado ni en las metricas de red.

3. **RB-3: Resiliencia contra Nulos y Catalogo Completo:**
   - Variantes registradas en el catalogo maestro que no cuenten con filas en la tabla `inventario_sucursal` deben computar con 0 unidades (`COALESCE(SUM(...), 0)`), sin romper la consulta analitica ni ser omitidas del reporte.

4. **RB-4: Semaforizacion Estandarizada:**
   - El estado de stock por variante en red se clasifica como:
     * `agotado`: `total_disponible <= 0`.
     * `alerta_baja`: `0 < total_disponible <= 5`.
     * `optimo`: `total_disponible > 5`.

5. **RB-5: Integracion Logistica Directa:**
   - Cada registro del desglose por boutique debe incorporar la direccion fisica y el telefono directo de la tienda para facilitar la comunicacion inmediata inter-sucursales.

---

## 2. Arquitectura Tecnica del Backend (`Ec-backend`)

### 2.1 Capa de Dominio y Servicios
- **Modulo:** `app/modules/gestion_operativa/cu26_inventario_global`
- **Servicio:** `ServicioInventarioGlobal` (`servicio.py`)
  * Agregacion relacional optimizada uniendo `VarianteProductoORM`, `ProductoORM`, `CategoriaORM`, `TallaORM`, `ColorORM`, con `LEFT OUTER JOIN` hacia `InventarioSucursalORM` y `SucursalORM`.
  * Filtros multicriterio: `q` (insensible a mayusculas/minusculas sobre prenda y SKU), `id_categoria`, `id_sucursal`, `estado_stock` (evaluado en clausula `HAVING`) y ordenacion dinamica.
  * Paginacion determinista y conteo total mediante subconsulta aliada.
  * Ingestion matricial en memoria de las existencias por boutique activa (`ExistenciaSucursalItemOut`).
  * Computo de metricas globales de red (`total_unidades_red`, `variantes_monitoreadas`, `alertas_stock_bajo`, `sedes_activas`).

### 2.2 Esquemas Pydantic v2
- **Archivo:** `esquemas.py`
  * `ExistenciaSucursalItemOut`: DTO de detalle logistico por sede.
  * `InventarioGlobalItemOut`: DTO consolidado por variante con desglose.
  * `MetricasInventarioGlobalOut`: Indicadores cuantitativos de red comercial.
  * `InventarioGlobalFiltrosIn`: Validacion de parametros de consulta y paginacion.
  * `RespuestaInventarioGlobalOut`: Envoltura de respuesta de endpoint.

### 2.3 Router REST
- **Ruta:** `GET /api/v1/admin/inventario/global`
- **Seguridad:** `require_roles(["administrador", "encargado_sucursal"])`
- **Codigos HTTP:** 200 OK, 401 Unauthorized, 403 Forbidden, 422 Unprocessable Entity.

---

## 3. Arquitectura Tecnica del Frontend Web (`Ec-frontend`)

### 3.1 Integracion en Dashboard Corporativo
- **Componente:** `AdminDashboardComponent` (`/admin`)
  * Septima tarjeta boutique bajo la seccion "Gestion Operativa".
  * Titulo oficial: "Consultar inventario global".
  * Badge: "Consolidado Multi-Sede".
  * Boton: `id="btn-consultar-inventario-global"` con `routerLink="/admin/inventario-global"`.
  * Visibilidad RBAC: `@if (esAdmin() || esEncargado())`. Total modulos activos: 7 (admin), 5 (encargado).

### 3.2 Vista Administrativa Principal
- **Ruta:** `/admin/inventario-global`
- **Proteccion:** `canActivate: [authGuard, roleGuard(['administrador', 'encargado_sucursal'])]`
- **Componente:** `InventarioGlobalAdminComponent`
  * Standalone Component con `ChangeDetectionStrategy.OnPush`.
  * Layout editorial centrado `max-w-[1440px] px-6 py-8 mx-auto`.
  * H1 principal exacto: "Consultar inventario global".
  * Miga de pan: "CONSULTAR INVENTARIO GLOBAL".
  * Enlace superior: "Volver al Panel Principal" (`/admin`).
  * 4 Tarjetas de metricas superiores sincronizadas con Signals:
    1. Unidades en Red.
    2. Variantes Monitoreadas.
    3. Alertas de Stock Bajo.
    4. Sedes Activas.
  * Barra de herramientas reactiva con retardo (`debounceTime(300)`), selectores de categoria, sucursal, estado de stock y ordenamiento.
  * Tabla maestra consolidada: miniatura, SKU monospace, talla, swatches `#HEX`, chips de disponibilidad por boutique, totales de red y badges cromados.
  * Modal accesible de detalle logistico y derivacion inter-tiendas con enlace directo `tel:`.
  * Luxury Banners contextuales para gestion no destructiva de errores de red.

---

## 4. Matriz de Trazabilidad de Requisitos

| Criterio EARS | Capa | Componente / Archivo | Codigo HTTP Esperado | Estado de Verificacion |
| :--- | :--- | :--- | :--- | :--- |
| **# AC-1** | Backend | `cu26_inventario_global/router.py` | 401 / 403 | Verificado (pytest) |
| **# AC-2** | Backend | `cu26_inventario_global/servicio.py` | 200 OK | Verificado (pytest) |
| **# AC-3** | Backend | `cu26_inventario_global/router.py` | 200 OK | Verificado (pytest) |
| **# AC-4** | Backend | `cu26_inventario_global/servicio.py` | 200 OK | Verificado (pytest) |
| **# AC-5** | Backend | `cu26_inventario_global/servicio.py` | 200 OK | Verificado (pytest) |
| **# AC-6** | Backend | `cu26_inventario_global/esquemas.py` | 422 Unprocessable | Verificado (pytest) |
| **# AC-7** | Backend | `cu26_inventario_global/servicio.py` | 200 OK | Verificado (pytest) |
| **# AC-8** | Frontend | `admin-dashboard.component.html` | N/A | Verificado (vitest) |
| **# AC-9** | Frontend | `inventario-global-admin.component.ts` | N/A | Verificado (vitest) |
| **# AC-10** | Frontend | `inventario-global-admin.component.html` | N/A | Verificado (vitest) |
| **# AC-11** | Frontend | `inventario-global-admin.component.ts` | N/A | Verificado (vitest) |
| **# AC-12** | Frontend | `inventario-global-admin.component.html` | N/A | Verificado (vitest) |
| **# AC-13** | Frontend | `inventario-global-admin.component.ts` | N/A | Verificado (vitest) |
| **# AC-14** | Frontend | `inventario-global-admin.component.html` | N/A | Verificado (vitest) |
| **# AC-15** | Frontend | `inventario-global-admin.component.html` | N/A | Verificado (vitest) |

---

## 5. Criterios de Calidad y Definicion de Terminado (DoD)
1. Suites automatizadas: 234/234 tests de backend pasando en verde; 222/222 tests de frontend pasando en verde.
2. Compilacion AOT: `ng build` en `Ec-frontend` ejecutada con 0 errores y 0 advertencias de compilacion.
3. Auditoria lexica: CERO emojis en plantillas HTML, codigo TypeScript, hojas SCSS, modelos Python o documentacion markdown.
4. Gobernanza: Exclusion justificada de `Ec-mobile` ratificada formalmente.
