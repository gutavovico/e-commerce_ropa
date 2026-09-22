# Propuesta de Cambio Técnico: Detalle de Producto, Variantes, Disponibilidad y Reservas

**ID del Cambio:** `CU07-CU08-CU09-CU12-detalle-producto`  
**Módulos Afectados:** `catalogo_productos` / `reservas`  
**Casos de Uso:**
- **CU07** - Consultar Detalle de Producto
- **CU08** - Consultar Tallas, Colores y Características
- **CU09** - Consultar Disponibilidad por Sucursal
- **CU12** - Reservar Varias Prendas (Cita de Prueba Presencial en Boutique)
- **CU10 (Aislado / Preparación Visual)** - Probador Virtual (AR)
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo (PUDS)  
**Fuentes de Verdad Visuales:** `image_2e3062.png` (Mobile), `image_2e2d7e.png` (Web), `image_2e295b.png` (Modal Web de Reserva).  
**Estado:** 🟡 En Espera de Aprobación Humana (Gate Estricto de Especificación)  
**Fecha:** 2026-09-21  

---

## 1. Estructura Documental del Cambio

Esta propuesta de cambio se encuentra desglosada y modularizada en cuatro documentos canónicos dentro de [`.specs/changes/CU07-CU08-CU09-CU12-detalle-producto/`](file:///c:/Users/tonys/OneDrive/Documentos/contenido/SI2/Parcial1-Ecommerce/.specs/changes/CU07-CU08-CU09-CU12-detalle-producto/):

1. **[`spec.md`](file:///c:/Users/tonys/OneDrive/Documentos/contenido/SI2/Parcial1-Ecommerce/.specs/changes/CU07-CU08-CU09-CU12-detalle-producto/spec.md):**
   - Especificación formal e individual de los 4 casos de uso funcionales (CU07, CU08, CU09, CU12) y del aislamiento del probador virtual (CU10).
   - Reglas de negocio inquebrantables: Catálogo 100% de alta costura femenina, integridad relacional con PostgreSQL Neon, trazabilidad en `movimientos_inventario` y criterios de aceptación EARS y Gherkin.
2. **[`plan.md`](file:///c:/Users/tonys/OneDrive/Documentos/contenido/SI2/Parcial1-Ecommerce/.specs/changes/CU07-CU08-CU09-CU12-detalle-producto/plan.md):**
   - Plan de ejecución dividido en 3 bloques secuenciales e independientes:
     - **Bloque 1 (Backend):** Esquemas Pydantic, servicios transaccionales en SQLAlchemy 2.0 y endpoints `/api/v1/productos/{id}`, `/disponibilidad` y `/reservas`.
     - **Bloque 2 (Frontend Web):** Ruta `/productos/:id` fuera del layout global, vista 2 columnas, galería de 4 tomas rotuladas, modal interactivo de citas en boutique (`image_2e295b.png`) y bloque de simulación morfológica (CU10).
     - **Bloque 3 (Mobile Multiplataforma):** Pantalla `PantallaProductoDetalle` a pantalla completa sin `BottomNavigationBar`, galería con botón flotante `"PROBAR EN AR"`, acordeón de disponibilidad con botón directo de reserva por boutique y modal de selección de horario.
3. **[`tasks.md`](file:///c:/Users/tonys/OneDrive/Documentos/contenido/SI2/Parcial1-Ecommerce/.specs/changes/CU07-CU08-CU09-CU12-detalle-producto/tasks.md):**
   - Checklist granular atómico con casillas `[ ]` organizado por Bloque Backend (T-BE-01 a T-BE-10), Bloque Frontend Web (T-FE-01 a T-FE-08) y Bloque Mobile (T-MO-01 a T-MO-07).
4. **[`checkpoint.md`](file:///c:/Users/tonys/OneDrive/Documentos/contenido/SI2/Parcial1-Ecommerce/.specs/changes/CU07-CU08-CU09-CU12-detalle-producto/checkpoint.md):**
   - Matriz de 20 puntos de control de verificación (CP-01 a CP-20) cubriendo transaccionalidad de reservas, retorno dinámico contextual, modal de boutique, análisis estático y reglas de negocio.

---

## 2. Resumen Arquitectónico de Directrices Obligatorias

### 2.1 Patrón Hub-and-Spoke (Pantalla Secundaria / Hoja)
- **Barra de navegación principal (Navbar Web / BottomNavigationBar Mobile):** **ESTRICTAMENTE OCULTA**. La pantalla de Detalle de Producto es una vista secundaria inmersiva.
- **Botón de retorno dinámico (`← VOLVER`):** **ESTRICTAMENTE OBLIGATORIO Y CONTEXTUAL**.
  - En Web: Invoca `Location.back()` del historial nativo de Angular.
  - En Mobile: Invoca `Navigator.pop(context)` de Flutter.
  - Si la clienta accedió desde `/catalogo`, retorna al catálogo conservando su posición de scroll y filtros; si accedió desde `/colecciones` o `/buscar`, retorna limpiamente a su respectivo origen.

### 2.2 Diferenciación de UX entre Web y Mobile (CU09 & CU12)
- **Mobile (`image_2e3062.png`):**
  - La disponibilidad por boutique (CU09) y la reserva de cita (CU12) residen de forma continua en la misma pantalla.
  - Cada tarjeta de boutique con stock (ej. *Flagship Serrano Madrid*, *Boutique Saint-Honoré París*) incluye su propio botón directo `[ 🏢 RESERVAR EN ESTA BOUTIQUE ]`.
- **Frontend Web (`image_2e2d7e.png` y `image_2e295b.png`):**
  - La ficha técnica presenta el botón de acción `[ 📅 CITA DE PRUEBA BOUTIQUE ]`.
  - Al pulsarlo, despliega un modal dedicado (*"RESERVAR CITA DE PRUEBA EN BOUTIQUE"*) donde la clienta visualiza la tarjeta de la prenda seleccionada, elige la boutique insignia mediante radio buttons con badges de existencias, selecciona la fecha/hora en píldoras y confirma la cita.

### 2.3 Aislamiento de CU10 (Probador Virtual AR)
- El botón de probador virtual queda maquetado y posicionado pixel-perfect (*"PROBAR EN AR"* flotante en móvil; bloque morfológico con métricas textiles e *"INICIAR PROBADOR INTERACTIVO"* en web).
- Cero dependencias de renderizado 3D, WebGL pesadas o cámara en este ciclo. Emite una notificación de cortesía informando la disponibilidad en la próxima fase.

---

## 3. Estado de Aprobación
✅ **GATE SUPERADO (2026-09-21):** Autorización concedida. Los bloques de Backend (`T-BE-01…T-BE-10`) y Web (`T-FE-01…T-FE-08`) están implementados y sus checkpoints `CP-01…CP-13` aprobados. El bloque Mobile (`T-MO-01…T-MO-07`, `CP-14…CP-18`) y los checkpoints transversales `CP-19`/`CP-20` continúan pendientes.

> **Nota de reconciliación (2026-09-21):** este apartado declaraba «no se ha generado ni modificado ningún archivo de código fuente» mientras `tasks.md` tenía 18 tareas marcadas `[x]` y `checkpoint.md` 13 checkpoints ✅. El texto del gate había quedado congelado en el momento de la propuesta y contradecía el estado real del repositorio. Se corrige aquí para que la documentación describa lo que efectivamente está implementado.
