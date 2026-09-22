# Especificacion Tecnica Permanente: CU30 - Consultar bitacora

**Codigo:** CU30  
**Nombre:** Consultar bitacora  
**Paquete de Dominio:** `seguridad`  
**Directorio Funcional Backend:** `app/modules/seguridad/cu30_bitacora`  
**Directorio Funcional Frontend:** `src/app/modules/seguridad/cu30_bitacora`  
**Directorio Funcional Mobile:** Excluido formalmente (Auditoria y seguridad exclusiva web corporativa)  
**Actores Primarios:** Administrador (Superusuario corporativo de control y gobernanza)  
**Actores Secundarios:** Ninguno (Bloqueo 403 estricto para roles operativos encargados, cajeros o clientes)  
**Metodologia:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Version:** 1.0.0 (Linea Base Permanente - v2.7.0)  
**Estado:** Aprobado y Promovido a Permanente  
**Fuentes de Verdad:**
- Documentacion Funcional: Alcance corporativo de auditoria y gobernanza inmutable.
- Arquitectura de Referencia: FastAPI + SQLAlchemy 2.0 + PostgreSQL Neon (esquema `fashionstore.bitacora`).
- Modelo de Dominio: Entidad `Bitacora`, modelo inmutable de eventos, marcas temporales ISO-8601 UTC y JSON diff estructurado.
- Design System Web: Angular 19+ Standalone, Signals, OnPush, directiva dual de enrutamiento y ChangeDetectorRef defensivo.

---

## 1. Definicion Funcional y Reglas de Negocio

### 1.1 Proposito y Alcance
El caso de uso CU30 establece la infraestructura inmutable de auditoria corporativa y trazabilidad forense para FashionStore. Permite a los superadministradores inspeccionar en tiempo real los eventos de mutacion, inicios de sesion y cambios de estado en toda la plataforma, filtrando por rango temporal, severidad (`INFO`, `WARN`, `ERROR`, `CRITICAL`), operador, modulo o accion, con visualizacion detallada de payloads JSON estructurados (estado previo vs. estado nuevo).

### 1.2 Reglas de Negocio Estrictas

1. **RB-1: Acceso Superadministrador Exclusivo:**
   - El acceso al modulo `/admin/bitacora` y a los endpoints `/api/v1/admin/bitacora` esta estrictamente reservado a usuarios con rol `administrador` o su alias `admin`.
   - Cualquier intento de acceso por roles operativos (`encargado_sucursal`, `cajero`) o `cliente` es denegado con HTTP 403 Forbidden.

2. **RB-2: Inmutabilidad Absoluta de Registros:**
   - Los registros de la tabla `fashionstore.bitacora` son de solo lectura a nivel de API. No existen metodos PUT, PATCH o DELETE expuestos bajo ninguna circunstancia.

3. **RB-3: Auditoria Estructurada y Payloads JSON:**
   - Cada evento almacena la referencia del operador (`id_usuario`, `usuario_nombre`), direccion IP de origen, severidad tipada, accion formal y dos campos JSONB opcionales: `payload_anterior` y `payload_nuevo`.

4. **RB-4: Metricas Consolidadas en Tiempo Real:**
   - Cada consulta paginada retorna simultaneamente el resumen cuantitativo del universo auditado: total de eventos, eventos criticos, alertas/errores y operadores unicos activos.

5. **RB-5: Exclusion Formal e Irrevocable de Ec-mobile:**
   - La auditoria corporativa y visualizacion forense de datos es 100% de uso administrativo web de escritorio. Ec-mobile (Flutter) permanece libre de cualquier modulo de auditoria interna.

---

## 2. Diseno Tecnico y Contratos de Servicio

### 2.1 Backend (FastAPI + PostgreSQL Neon)
- **Tabla:** `fashionstore.bitacora` con indices en `creado_en DESC`, `severidad`, `tabla_modulo`, `id_usuario`.
- **Modelo ORM:** `app/modules/seguridad/cu30_bitacora/modelos.py` (`Bitacora(Base)`).
- **Esquemas Pydantic v2:** `esquemas.py` con `BitacoraFiltros`, `BitacoraEventoResumen`, `BitacoraEventoDetalle`, `BitacoraMetricas`, `BitacoraListadoRespuesta`.
- **Servicio:** `ServicioBitacoraAuditoria` en `servicio.py`.
- **Router REST:** `/api/v1/admin/bitacora` en `router.py`.

### 2.2 Frontend Web (Angular 19+ Standalone)
- **Ruta:** `/admin/bitacora` con `canActivate: [authGuard, roleGuard(['administrador', 'admin'])]`.
- **Tarjeta 12 en AdminDashboard:** Badge "Seguridad y Auditoria", Titulo "Consultar bitacora", boton `#btn-consultar-bitacora` con directiva dual (`routerLink` y `(click)="navegar(...)"`) bajo `@if (esAdmin())`.
- **Componente Principal:** `BitacoraAdminComponent` con 4 KPIs superiores, barra de filtros con debounce de 300 ms, tabla cronologica monoespaciada con badges cromaticos de severidad y modal accesible para JSON diff.

---

## 3. Cobertura y Verificacion de Pruebas
- **Backend Pytest:** `tests/modules/seguridad/test_cu30_bitacora.py` (14 pruebas unitarias de integracion y RBAC, 312 pruebas totales pasando en verde).
- **Frontend Vitest:** `bitacora-admin.service.spec.ts` (4 pruebas), `bitacora-admin.component.spec.ts` (9 pruebas), `admin-dashboard.component.spec.ts` (25 pruebas con despacho de click real en el DOM sobre `#btn-consultar-bitacora`).
- **Total Frontend:** 358 pruebas unitarias en 33 archivos completamente en verde.
- **Compilacion de Produccion:** `npm run build` ejecutada con 0 advertencias y 0 errores.
