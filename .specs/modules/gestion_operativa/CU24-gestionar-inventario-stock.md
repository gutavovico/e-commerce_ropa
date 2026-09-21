# Especificacion Tecnica Permanente: CU24 - Gestionar Inventario, Stock y Existencias por Sucursal

**Codigo:** CU24  
**Nombre:** Gestionar Inventario, Stock y Existencias por Sucursal  
**Paquete de Dominio:** `gestion_operativa`  
**Directorio Funcional Backend:** `app/modules/gestion_operativa/cu24_inventario_stock`  
**Directorio Funcional Frontend:** `src/app/modules/gestion_operativa/cu24_inventario_stock`  
**Directorio Funcional Mobile:** Excluido formalmente (operacion de trastienda y back-office; consumo de solo lectura mediante vitrina publica)  
**Actores Primarios:**
- Administrador (Supervision y control global de existencias multi-sucursal)
- Encargado de Sucursal (Control operativo y recepcion acotado estrictamente a su boutique asignada)  
**Actores Secundarios:**
- Cajero (Consulta de existencias locales para Punto de Venta)
- Cliente (Consulta publica de disponibilidad fisica por sucursal en catalogo web/movil)
- Sistema (Reservas y liberaciones transaccionales en checkout y vestidor virtual)  
**Metodologia:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Version:** 2.0.0 (Linea Base Permanente)  
**Estado:** Aprobado y Promovido a Permanente  
**Fuentes de Verdad:**
- Documento Maestro de Requisitos: `SI2-Parcial1.md` (Seccion 1.2.2 Objetivo 1, Seccion 1.4 Alcance, Seccion 2.1.2 CU26 Lineas 897-915 y Seccion 2.3 Modelo Relacional).
- Arquitectura de Dominio: `.agents/skills/fashionstore-backend-sdd/references/dominio.md` (Integridad transaccional de stock por sede y libro de movimientos Kardex).
- Design System Multiplataforma: `.agents/skills/fashionstore-frontend-sdd/references/fashionstore-tokens.md` (Diseno editorial Atelier, paleta Slate/Camel/Obsidian, tipografia Outfit, ChangeDetectionStrategy.OnPush y Angular Signals).

---

## 1. Definicion Funcional y Reglas de Negocio

### 1.1 Proposito y Alcance
El caso de uso CU24 centraliza la administracion, control fisico y auditoria contable de las existencias de prendas y variantes (SKUs) en cada boutique fisica de la red de FashionStore. Provee mecanismos de recepcion de mercaderia inicial, ajustes manuales por rotura o sobrante, traspasos transaccionales inter-sucursal y una bitacora inmutable (Kardex) que audita cada variacion de saldo.

### 1.2 Declaracion Formal de Exclusion de la Aplicacion Movil (Ec-mobile)
La aplicacion movil de FashionStore (`Ec-mobile`), desarrollada en Flutter 3.x, esta orientada exclusivamente a la experiencia de cara al cliente (catalogo editorial, vestidor de Realidad Aumentada, bolsa y checkout) y consulta de disponibilidad fisica.
Las operaciones de recepcion de mercaderia, ajustes fisicos por mermas, transferencias inter-sucursales y auditoria contable de kardex constituyen tareas operativas de trastienda y back-office corporativo que se ejecutan exclusivamente en el panel web de administracion (`Ec-frontend`).
La aplicacion movil participa en este dominio exclusivamente como consumidor pasivo de solo lectura (`Read-Only`), accediendo al endpoint publico `GET /api/v1/inventario/disponibilidad/{id_variante}`. Por tanto, se ratifica la exclusion de desarrollo de pantallas o controladores mutables en `Ec-mobile`.

### 1.3 Reglas de Negocio Estrictas (RB)

1. **RB-1: Control de Acceso RBAC y Autorizacion:**
   - Todo endpoint administrativo bajo `/api/v1/admin/inventario` exige token JWT valido con rol `administrador` o `encargado_sucursal`.
   - Las peticiones sin autenticacion son rechazadas con HTTP 401 Unauthorized.
   - Peticiones con rol `cajero` o `cliente` son bloqueadas con HTTP 403 Forbidden.

2. **RB-2: Segregacion Territorial Forzada por Sede:**
   - Los usuarios con rol `administrador` poseen visibilidad y capacidad de mutacion global sobre todas las sucursales.
   - Los usuarios con rol `encargado_sucursal` estan forzados a operar exclusivamente sobre su `id_sucursal` asignada en su perfil. Cualquier consulta o mutacion sobre otra sede es bloqueada con HTTP 403 Forbidden (`SUCURSAL_NO_AUTORIZADA`).

3. **RB-3: Restriccion de No Negatividad e Integridad de Existencias:**
   - La columna `cantidad_disponible` esta protegida por `CheckConstraint('cantidad_disponible >= 0')`. Ninguna operacion puede decrementar el saldo por debajo de cero.
   - Si un decremento o transferencia solicita una cantidad superior al saldo disponible, la transaccion es abortada con HTTP 409 Conflict (`STOCK_INSUFICIENTE`).

4. **RB-4: Calculo Determinista de Semaforo de Stock (Umbrales):**
   - El estado computado de una existencia se calcula de forma automatica:
     * `optimo`: cuando `cantidad_disponible > stock_alerta`.
     * `alerta_baja`: cuando `0 < cantidad_disponible <= stock_alerta`.
     * `agotado`: cuando `cantidad_disponible == 0`.

5. **RB-5: Trazabilidad e Inmutabilidad del Kardex:**
   - Todo incremento, decremento o transferencia de mercaderia genera de forma obligatoria e inmediata un asiento inmutable en la tabla `fashionstore.movimientos_inventario`.
   - Cada movimiento registra: tipo de movimiento, cantidad operada (+/-), saldo anterior, saldo nuevo, motivo justificado, documento de referencia y usuario responsable.

6. **RB-6: Transferencias Inter-Sucursales ACID con Bloqueo Exclusivo:**
   - El traspaso entre dos boutiques se ejecuta dentro de una transaccion atomica con bloqueo de fila `with_for_update()` sobre el registro de origen para prevenir condiciones de carrera.
   - Se reduce el stock disponible en la sucursal de origen y se incrementa en la sucursal de destino (creando el registro si no existia previamente).
   - Se asientan de forma sincronizada los dos movimientos espejo en Kardex: `transferencia_salida` y `transferencia_entrada`.

7. **RB-7: Prohibicion de Auto-Transferencia:**
   - La sucursal de origen y la sucursal de destino deben ser estrictamente diferentes (`id_sucursal_origen != id_sucursal_destino`). Las auto-transferencias son rechazadas con HTTP 422 Unprocessable Entity (`TRANSFERENCIA_MISMA_SUCURSAL`).

8. **RB-8: Justificacion Obligatoria de Auditoria:**
   - Todo ajuste manual fisico exige un motivo explicativo obligatorio con una longitud minima de 5 caracteres no vacios. Motivos inferiores o ausentes son rechazados con HTTP 422 (`MOTIVO_OPERACION_INVALIDO`).

---

## 2. Arquitectura Tecnica del Backend (`Ec-backend`)

### 2.1 Modelos ORM (Esquema `fashionstore`)
- **`InventarioSucursalORM` (`fashionstore.inventario_sucursal`):**
  * `id_inventario`: BigInteger Primary Key autoincremental.
  * `id_sucursal`: Integer FK a `fashionstore.sucursales` (no nulo, indexado).
  * `id_variante`: BigInteger FK a `fashionstore.variantes_producto` (no nulo, indexado).
  * `id_temporada`: Integer FK a `fashionstore.temporadas` (default 1).
  * `cantidad_disponible`: Integer no nulo (default 0, check >= 0).
  * `cantidad_reservada`: Integer no nulo (default 0, check >= 0).
  * `stock_minimo`: Integer no nulo (default 0, check >= 0).
  * `stock_alerta`: Integer no nulo (default 5, check >= 0).
  * `estado`: Enum `estado_prenda_stock` ('disponible', 'reservada', 'agotada', 'proxima_ingreso', 'devuelta').
  * `actualizado_en`: DateTime UTC con `onupdate`.
  * `UniqueConstraint('id_sucursal', 'id_variante', name='uq_inventario_sucursal_variante')`.
- **`MovimientoInventarioORM` (`fashionstore.movimientos_inventario`):**
  * `id_movimiento`: BigInteger Primary Key autoincremental.
  * `id_inventario`: BigInteger FK a `fashionstore.inventario_sucursal` (no nulo, indexado).
  * `tipo_movimiento`: Enum `tipo_movimiento_inv` ('ingreso_proveedor', 'ajuste_positivo', 'ajuste_negativo', 'transferencia_salida', 'transferencia_entrada', 'venta_confirmada', 'cancelacion_pedido', 'reserva', 'liberacion_reserva', 'venta', 'devolucion', 'ajuste').
  * `cantidad`: Integer no nulo (check <> 0).
  * `saldo_anterior`: Integer no nulo (default 0).
  * `saldo_nuevo`: Integer no nulo (default 0).
  * `motivo`: Text no nulo.
  * `id_usuario`: BigInteger FK a `fashionstore.usuarios` (nullable, indexado).
  * `referencia_documento`: String(100) nullable.
  * `creado_en`: DateTime UTC no nulo con valor por defecto now().

### 2.2 Migracion de Base de Datos
- **Alembic Revision:** `0005_cu24_inventario_kardex.py` ejecutada exitosamente en PostgreSQL Neon.

### 2.3 Endpoints REST Expuestos
| Metodo | Ruta | Rol Permitido | Descripcion |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/admin/inventario` | `administrador`, `encargado_sucursal` | Consulta paginada con filtros combinados (sede, categoria, estado, q). |
| `POST` | `/api/v1/admin/inventario` | `administrador`, `encargado_sucursal` | Alta inicial de existencias y primer asiento en Kardex (HTTP 201). |
| `POST` | `/api/v1/admin/inventario/{id}/ajuste` | `administrador`, `encargado_sucursal` | Ajuste manual fisico (incremento/decremento) con validacion y auditoria. |
| `POST` | `/api/v1/admin/inventario/transferencia` | `administrador`, `encargado_sucursal` | Traspaso transaccional inter-sucursal con doble asiento en Kardex. |
| `GET` | `/api/v1/admin/inventario/{id}/kardex` | `administrador`, `encargado_sucursal` | Historial cronologico descendente de movimientos de una existencia. |
| `GET` | `/api/v1/inventario/disponibilidad/{id_variante}` | Publico | Consulta de tiendas fisicas con existencias para una variante. |

---

## 3. Arquitectura Tecnica del Frontend Web (`Ec-frontend`)

### 3.1 Componentes y Vistas
- **`AdminDashboardComponent` (`/admin`):**
  * Incorporacion de la 5ta tarjeta boutique: "Inventario y Existencias" bajo la categoria "Gestion Operativa".
  * Badge: "Control de Stock".
  * Boton: "Gestionar Inventario", `id="btn-gestionar-inventario"`, enlazado a `/admin/inventario`.
  * Visibilidad RBAC: visible tanto para `administrador` como para `encargado_sucursal`. Oculta para clientes y cajeros.
- **`InventarioAdminComponent` (`/admin/inventario`):**
  * Componente Standalone con `ChangeDetectionStrategy.OnPush` y layout editorial Atelier (`max-w-[1440px] px-6 py-8 mx-auto`).
  * Enlace superior de retorno: "<- Volver al Panel Principal" hacia `/admin`.
  * Barra reactiva de filtrado:
    - Selector de sucursal: fijado y deshabilitado para `encargado_sucursal` en su sede asignada; selector libre con "Todas las Sedes" para `administrador`.
    - Selector de categoria alimentado por `AtributosAdminService`.
    - Selector de estado: `todos`, `optimo`, `alerta_baja`, `agotado`.
    - Busqueda en vivo con debounce de 300ms por modelo o SKU.
  * Tabla maestra editorial:
    - Miniatura de prenda cuadrada con fallback SVG sobrio.
    - Prenda, SKU corporativo, talla y swatch de color `#HEX`.
    - Sede asociada y desglose de cantidad disponible (destacada) y reservada.
    - Badges cromados de estado (`Optimo`, `Alerta de Reposicion`, `Agotado`).
    - Acciones contextuales: "Ajustar", "Transferir" (deshabilitado si disponible == 0) y "Kardex".
  * Modales reactivos con `NonNullableFormBuilder`:
    - Modal de Alta Inicial (Recepcion de mercaderia).
    - Modal de Ajuste Fisico (merma/sobrante con justificacion minima de 5 caracteres y control de saldo disponible).
    - Modal de Transferencia Inter-Sedes (exclusion de sede origen y tope en disponible).
    - Drawer/Modal de Kardex (listado cronologico con variacion +/- y saldos).
  * Luxury Banners: captura contextual de errores HTTP 409 y 422 preservando los formularios intactos.

### 3.2 Seguridad y Enrutamiento
- Ruta `/admin/inventario` custodiada por `[authGuard, roleGuard(['administrador', 'encargado_sucursal'])]`.

---

## 4. Matriz de Cobertura y Verificacion Automatizada

| Suite | Comando | Metricas de Exito | Estado |
| :--- | :--- | :--- | :--- |
| **Backend (Ec-backend)** | `pytest tests/modules/gestion_operativa/test_cu24_inventario_stock.py` | 17/17 tests unitarios e integracion | 100% Verde |
| **Backend Suite Completa** | `pytest` | 208/208 tests pasando limpiamente | 100% Verde |
| **Frontend (Ec-frontend)** | `ng test --watch=false` | 19/19 suites, 168/168 tests pasando | 100% Verde |
| **Compilacion AOT** | `ng build` | 0 errores de tipo, bundles optimizados | 100% Verde |
| **Auditoria Lexica** | `audit_emojis.py` | 0 emojis detectados en todo el repositorio | Cumplimiento 100% |
