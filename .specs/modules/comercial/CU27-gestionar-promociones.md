# Especificacion Tecnica Permanente: CU27 - Gestionar promociones

**Codigo:** CU27  
**Nombre:** Gestionar promociones  
**Paquete de Dominio:** `comercial` / `marketing_descuentos`  
**Directorio Funcional Backend:** `app/modules/comercial/cu27_promociones`  
**Directorio Funcional Frontend:** `src/app/modules/comercial/cu27_promociones`  
**Directorio Funcional Mobile:** Excluido formalmente (gestion y parametrizacion de reglas comerciales reservada exclusivamente al back-office web corporativo)  
**Actores Primarios:**  
- Administrador (Acceso irrestricto: creacion, modificacion, conmutacion de vigencias y baja logica)  
- Encargado de Sucursal (Acceso de consulta informativa de campanas y cupones vigentes)  
**Actores Bloqueados:**  
- Cajero (Bloqueo estricto por politica RBAC - HTTP 403 Forbidden)  
- Cliente (Bloqueo estricto por politica RBAC - HTTP 403 Forbidden)  
**Metodologia:** Spec-Driven Development (SDD) & Sintaxis EARS (Easy Approach to Requirements Syntax)  
**Version:** 2.4.0 (Linea Base Permanente)  
**Estado:** Aprobado y Promovido a Permanente  
**Fuentes de Verdad:**  
- Documento Maestro de Requisitos: `SI2-Parcial1.md` (Modulo de Ventas y Marketing).  
- Arquitectura de Dominio Backend: `.agents/skills/fashionstore-backend-sdd/references/dominio.md`.  
- Design System Multiplataforma: `.agents/skills/fashionstore-frontend-sdd/references/fashionstore-tokens.md` (Diseno editorial Atelier, paleta Slate/Camel/Obsidian, tipografia Outfit, ChangeDetectionStrategy.OnPush y Angular Signals).  

---

## 1. Definicion Funcional y Reglas de Negocio

### 1.1 Proposito y Alcance
El caso de uso CU27 centraliza la definicion, gobierno y trazabilidad de las campanas de incentivo comercial, politicas de descuento y codigos de cupon en la red de tiendas de FashionStore. Concilia el dinamismo publicitario con el estricto control de margenes financieros mediante esquemas de reduccion porcentual y monto fijo, topes maximos de beneficio, vigencias temporales y cupos maximos de redencion.

### 1.2 Declaracion Formal de Exclusion de la Aplicacion Movil (Ec-mobile)
La aplicacion movil de FashionStore (`Ec-mobile`), desarrollada sobre Flutter 3.x, tiene como proposito exclusivo la experiencia de compra B2C orientada al consumidor final (exploracion de prendas, vestidor virtual en Realidad Aumentada, bolsa de compras y checkout digital con Stripe).  
La creacion de campanas comerciales corporativas, la definicion de algoritmos de descuento, el aprovisionamiento de cupones promocionales con topes financieros y la supervision analitica del volumen de canjes son facultades exclusivas de la direccion comercial y back-office corporativo (`Ec-frontend`).  
Por tanto, se ratifica formalmente la exclusion total de `Ec-mobile`: cero modelos, pantallas o servicios en Flutter.

### 1.3 Reglas de Negocio Estrictas (RB)

1. **RB-1: Control de Acceso y Autorizacion RBAC:**
   - Rutas base `/api/v1/admin/promociones` exigen JWT valido (HTTP 401 si ausente). Roles `cajero` o `cliente` son rechazados con HTTP 403 Forbidden. `administrador` posee control irrestricto y `encargado_sucursal` opera en modo de solo lectura.

2. **RB-2: Consistencia Cronologica de Vigencias:**
   - La `fecha_fin` debe ser estrictamente posterior a la `fecha_inicio` (`fecha_fin > fecha_inicio`). Inconsistencias temporales son rechazadas con HTTP 422 Unprocessable Entity en backend y prevenidas sincronamente en frontend.

3. **RB-3: Tipos de Descuento y Parametrizacion Financiera:**
   - Tipo `porcentaje`: `valor_descuento` entre 1.00% y 100.00%. Admite parametrizar opcionalmente `tope_descuento` para mitigar perdidas de margen en compras de alto valor.
   - Tipo `monto_fijo`: `valor_descuento` estrictamente positivo (> 0).

4. **RB-4: Unicidad Insensible a Mayusculas de Codigo de Cupon:**
   - Si se define `codigo_cupon`, este debe ser unico a nivel global en la base de datos bajo comparacion funcional minuscula (`LOWER(TRIM(codigo_cupon))`). Colisiones se rechazan con HTTP 409 Conflict. Si se omite el cupon, la promocion opera de forma automatica en catalogo.

5. **RB-5: Integridad de Alcance Promocional:**
   - Alcance `global`: Aplica a todo el catalogo sin restricciones de ID.
   - Alcance `categoria`: Exige un `id_categoria` valido y existente (HTTP 422 si nulo o inexistente).
   - Alcance `producto`: Exige un `id_producto` valido y existente (HTTP 422 si nulo o inexistente).

6. **RB-6: Baja Logica y Preservacion Historica:**
   - La desactivacion de promociones conmuta `estado_activo = False`, inhabilitando nuevos canjes pero preservando el historial de ventas, usos acumulados e integridad relacional.

---

## 2. Arquitectura Tecnica del Backend (`Ec-backend`)

### 2.1 Capa de Dominio y Servicios
- **Modulo:** `app/modules/comercial/cu27_promociones`
- **Servicio:** `ServicioGestionPromociones`:
  * `listar_promociones`: Paginacion con filtros multicriterio (`q`, `tipo_descuento`, `estado_activo`, `alcance`, `ordenar_por`) y conteo determinista.
  * `obtener_promocion_por_id`: Recuperacion detallada por identificador unico.
  * `crear_promocion`: Verificacion de unicidad de cupon, consistencia relacional de alcance y persistencia.
  * `actualizar_promocion`: Modificacion integral excluyendo el propio ID en la verificacion de unicidad.
  * `conmutar_estado`: Conmutacion atomica de estado logico (`estado_activo`).
  * `obtener_metricas`: Agregacion cuantitativa (promociones activas, cupones vigentes, descuento promedio, usos totales).
- **Excepciones de Dominio:** `PromocionNoEncontradaError` (404), `CodigoCuponDuplicadoError` (409), `FechasPromocionInvalidasError` (422), `ValorDescuentoInvalidoError` (422) y `AlcancePromocionInvalidoError` (422).

### 2.2 Modelo Persistente ORM y Base de Datos Neon
- `PromocionORM` (`fashionstore.promociones`):
  * Clave primaria: `id_promocion`.
  * Columnas: `nombre`, `descripcion`, `codigo_cupon`, `tipo_descuento`, `valor_descuento`, `fecha_inicio`, `fecha_fin`, `tope_descuento`, `limite_usos`, `usos_actuales`, `alcance`, `id_categoria` (FK), `id_producto` (FK), `estado_activo`, `creado_en`, `actualizado_en`.
  * Restricciones `CHECK`: `chk_promociones_fechas_orden`, `chk_promociones_tipo_descuento`, `chk_promociones_valor_positivo`, `chk_promociones_porcentaje_tope`, `chk_promociones_tope_positivo`, `chk_promociones_usos_no_negativos`, `chk_promociones_limite_positivo`, `chk_promociones_alcance_tipo`.
  * Indice funcional: `uq_promociones_codigo_cupon_lower` sobre `LOWER(TRIM(codigo_cupon))`.

### 2.3 Endpoints REST Expuestos
- `GET /api/v1/admin/promociones`: Listado paginado con filtros multicriterio y metricas de red.
- `POST /api/v1/admin/promociones`: Registro de nueva campana o cupon comercial.
- `GET /api/v1/admin/promociones/{id}`: Detalle de promocion individual.
- `PUT /api/v1/admin/promociones/{id}`: Actualizacion integral de promocion.
- `PATCH /api/v1/admin/promociones/{id}/estado`: Conmutacion atomica de baja logica / reactivacion.

---

## 3. Arquitectura Tecnica del Frontend Web (`Ec-frontend`)

### 3.1 Componentes y Rutas
- **Ruta:** `/admin/promociones` custodiada por `[authGuard, roleGuard(['administrador', 'encargado_sucursal'])]`.
- **Componente:** `PromocionesAdminComponent` (Standalone, `ChangeDetectionStrategy.OnPush`, Angular Signals).
- **Servicio:** `PromocionesAdminService` (estado reactivo centralizado con Signals y cliente HTTP tipado).

### 3.2 Interfaz de Usuario y Fidelidad Editorial
- Layout editorial `max-w-[1440px] px-6 py-8 mx-auto`, fondo Slate 50, tipografia Outfit, acentos Camel (`#AD8C63`) y Obsidian (`#0F172A`).
- Novena tarjeta corporativa en `AdminDashboardComponent` bajo la categoria "Gestion Comercial" con badge "Marketing y Descuentos" y doble enlace de navegacion.
- Rejilla superior de 4 KPIs cuantitativos (Promociones Activas, Cupones Vigentes, Descuento Promedio, Usos Acumulados).
- Barra de herramientas reactiva con busqueda con debounce de 300 ms, selector de tipo, selector de estado, selector de alcance y boton de reinicio.
- Tabla maestra con badges cromaticos de vigencia (`Vigente`, `Proxima`, `Expirada`), chip monoespaciado de cupon y fraccion de usos.
- Modales reactivos con `NonNullableFormBuilder`, validacion sincronica inline de fechas y Luxury Banners no destructivos ante errores HTTP 409 y 422.

---

## 4. Matriz de Trazabilidad y Verificacion

| Criterio EARS | Descripcion Sintetica | Capa | Estado de Verificacion |
| :--- | :--- | :--- | :--- |
| **# AC-1** | Autenticacion Obligatoria JWT (401) | Backend | Verificado con Pytest (100% verde) |
| **# AC-2** | Control de Acceso RBAC por Rol (403) | Backend | Verificado con Pytest (100% verde) |
| **# AC-3** | Segregacion Funcional de Operacion | Backend | Verificado con Pytest (100% verde) |
| **# AC-4** | Estructura de Entidad Promocion | Backend | Verificado con Pytest y Alembic |
| **# AC-5** | Validacion Cronologica de Fechas (422) | Backend | Verificado con Pytest (100% verde) |
| **# AC-6** | Validacion de Rango de Descuento (422) | Backend | Verificado con Pytest (100% verde) |
| **# AC-7** | Validacion de Unicidad de Codigo Cupon (409) | Backend | Verificado con Pytest (100% verde) |
| **# AC-8** | Integridad de Alcance Promocional (422) | Backend | Verificado con Pytest (100% verde) |
| **# AC-9** | Listado Paginado con Filtros Multicriterio (200) | Backend | Verificado con Pytest (100% verde) |
| **# AC-10** | Detalle Individual de Promocion (200 / 404) | Backend | Verificado con Pytest (100% verde) |
| **# AC-11** | Alta de Promocion Comercial (201) | Backend | Verificado con Pytest (100% verde) |
| **# AC-12** | Modificacion de Promocion (200) | Backend | Verificado con Pytest (100% verde) |
| **# AC-13** | Baja Logica y Conmutacion de Estado (PATCH 200) | Backend | Verificado con Pytest (100% verde) |
| **# AC-14** | Tarjeta Corporativa en AdminDashboardComponent | Frontend | Verificado con Vitest (100% verde) |
| **# AC-15** | Layout Editorial y Cabecera de la Vista | Frontend | Verificado con Vitest (100% verde) |
| **# AC-16** | Tarjetas de KPIs Comerciales de Red | Frontend | Verificado con Vitest (100% verde) |
| **# AC-17** | Barra de Filtros con Debounce (300 ms) | Frontend | Verificado con Vitest (100% verde) |
| **# AC-18** | Tabla Maestra con Badges Cromaticos | Frontend | Verificado con Vitest (100% verde) |
| **# AC-19** | Modal Reactivo con Validacion Sincronica | Frontend | Verificado con Vitest (100% verde) |
| **# AC-20** | Modal de Confirmacion de Baja Logica | Frontend | Verificado con Vitest (100% verde) |
| **# AC-21** | Luxury Banners No Destructivos | Frontend | Verificado con Vitest (100% verde) |
| **# AC-22** | Estados de Carga y Vacio | Frontend | Verificado con Vitest (100% verde) |
