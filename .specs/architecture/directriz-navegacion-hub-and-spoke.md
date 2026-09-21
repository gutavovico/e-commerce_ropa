# Directriz Arquitectónica Global: Jerarquía de Vistas y Navegación (Hub-and-Spoke)

**Versión:** 1.0.0 (Línea Base Arquitectónica del Sistema)  
**Fecha:** 2026-09-21  
**Estado:** 🟢 APROBADA Y VIGENTE  
**Ámbito:** Frontend Web (`Ec-frontend` en Angular 19+) y Mobile Multiplataforma (`Ec-mobile` en Flutter 3.x)  
**Clasificación:** Directriz de Arquitectura Transversal Obligatoria  

---

## 1. Fundamento y Modelo Mental: Patrón Hub-and-Spoke

Toda la navegación y estructura de layouts de la plataforma **FashionStore** se rige de manera estricta y universal bajo el patrón de diseño de interacción **Hub-and-Spoke (Eje y Radios)**.

Bajo este modelo, existen de manera inequívoca exactamente **dos tipos de pantallas**:

```
                       ┌──────────────────────────────────────────────┐
                       │            4 PANTALLAS RAÍZ (HUB)            │
                       │   /inicio, /buscar, /catalogo*, /perfil      │
                       │   * Barra de Navegación: SIEMPRE VISIBLE    │
                       │   * Botón de Regreso (←): PROHIBIDO         │
                       └──────────────────────┬───────────────────────┘
                                              │
                         Navegación / Router  │  Transición / Navigator.push
                                              ▼
                       ┌──────────────────────────────────────────────┐
                       │          PANTALLAS SECUNDARIAS (HOJAS)       │
                       │  Colecciones (CU36), Detalle Prenda (CU07),  │
                       │  Checkout (CU15), Bolsa/Carrito, etc.        │
                       │   * Barra de Navegación: OCULTA / NO DISP.   │
                       │   * Botón de Regreso (←): OBLIGATORIO        │
                       └──────────────────────────────────────────────┘
```

---

## 2. Definición Normativa de Pantallas

### 2.1 Pantallas Principales (Raíz / Hub)
Son **única y exclusivamente las 4 secciones base** accesibles desde la barra de navegación global:

1. **`Inicio`** (`/inicio` o `/home`): Atelier, novedades, bienvenida, colecciones destacadas y recomendaciones IA (CU18).
2. **`Buscar`** (`/buscar`): Motor de búsqueda difusa `pg_trgm`, filtros avanzados y exploración (CU06).
3. **`Catálogo`** (`/catalogo`): Índice canónico de categorías y catálogo general (CU05, *pendiente de implementar*).
4. **`Perfil`** (`/perfil` o `/mi-cuenta`): Gestión de perfil del cliente, citas atelier y pedidos (CU04).

#### Reglas Inviolables para Pantallas Raíz:
* **Barra de Navegación (Navbar / BottomNavigationBar): SIEMPRE VISIBLE.**  
  Solo y únicamente en estas 4 pantallas debe existir y renderizarse el menú principal institucional de navegación.
* **Botón de Regreso (`← Volver`): ESTRICTAMENTE PROHIBIDO.**  
  Al constituir el nivel raíz y origen de la experiencia del usuario, ninguna de estas cuatro pantallas debe incluir flecha, icono ni botón de retroceso hacia rutas previas.

---

### 2.2 Pantallas Secundarias (Hojas, Sub-vistas y Flujos Derivados)
Cualquier otro caso de uso, vista de detalle, proceso transaccional o sub-flujo se desprende jerárquicamente como hijo o pantalla secundaria de alguna de las 4 pantallas principales.

* **Ejemplo activo:** **`Colecciones` (`CU36`)** y su detalle derivan directamente de una acción de exploración originada en `Inicio` (o en `Buscar`).
* **Otros ejemplos:** Detalle de prenda (`CU07`), Checkout digital (`CU15`), Reserva de probador (`CU12`).

#### Reglas Inviolables para Pantallas Secundarias:
* **Barra de Navegación (Navbar / BottomNavigationBar): OCULTA / NO DISPONIBLE.**  
  Ninguna pantalla secundaria debe contener ni renderizar la barra de navegación principal global (ni en Web ni en Mobile). Esto maximiza el área útil de lectura editorial e inmersión en la compra.
* **Botón de Regreso (`← Volver` / `leading: BackButton()`): ESTRICTAMENTE OBLIGATORIO.**  
  Toda pantalla secundaria debe disponer de un botón visible, accesible y semántico de retorno (`← Volver`) en su cabecera que devuelva a la pantalla previa inmediata desde la que se accedió (por ejemplo, retornando hacia `Inicio`).

---

## 3. Impacto Técnico en Frontend Web (`Ec-frontend` — Angular 19+)

### 3.1 Estructura de Rutas y Layouts
1. **Layout Principal (`MainLayoutComponent`):**
   - Contiene la barra superior persistente institucional (`<header>`) con los enlaces exclusivos a `/inicio`, `/buscar`, `/catalogo` y `/perfil`, utilidades (notificaciones, cesta, avatar) y el `<router-outlet></router-outlet>` principal para las rutas hijas.
   - Las 4 rutas hijas exclusivas son:
     ```typescript
     {
       path: '',
       component: MainLayoutComponent,
       children: [
         { path: 'inicio', loadComponent: () => import('./modules/inicio/paginas/inicio.component').then(m => m.InicioComponent) },
         { path: 'buscar', loadComponent: () => import('./modules/catalogo/cu06_buscar_filtrar/paginas/buscar-productos.component').then(m => m.BuscarProductosComponent) },
         { path: 'catalogo', ... }, // Pendiente CU05
         { path: 'perfil', canActivate: [authGuard], loadComponent: () => import('./modules/autenticacion_seguridad/cu04_gestionar_perfil/paginas/perfil.component').then(m => m.PerfilComponent) },
       ]
     }
     ```
2. **Rutas Secundarias Fuera del Layout Principal:**
   - Rutas como `/colecciones` y `/colecciones/:id` se declaran al nivel raíz de enrutamiento (fuera de `MainLayoutComponent`) o con un layout secundario sin navbar global.
   - Cada componente secundario incluye en su propia cabecera el botón `← Volver` con redirección hacia la vista de origen (ej. `/inicio`).
3. **Manejo de `Catálogo` (CU05):**
   - Al no estar implementado `CU05`, la ruta `/catalogo` no debe redirigir a vistas secundarias ni inventadas.

---

## 4. Impacto Técnico en Mobile Multiplataforma (`Ec-mobile` — Flutter 3.x)

### 4.1 Scaffolding y Transiciones
1. **Contenedor Raíz (Tabs Hub):**
   - La propiedad `bottomNavigationBar` con el `BottomNavigationBar` de 4 ítems (`Inicio`, `Buscar`, `Catálogo`, `Perfil`) pertenece **exclusivamente al Scaffold raíz** del contenedor de pestañas.
   - Las 4 pantallas raíz configuran `automaticallyImplyLeading: false` en su `AppBar`, prohibiendo cualquier botón de retroceso.
2. **Navegación a Vistas Hijas (`Navigator.push`):**
   - Al transicionar a `ColeccionesScreen` (CU36), `DetalleColeccionScreen` o cualquier pantalla hoja, se realiza mediante `Navigator.of(context).push(...)`.
   - El Scaffold de la pantalla secundaria **no declara `bottomNavigationBar`** (queda completamente oculta).
   - Su `AppBar` incluye obligatoriamente `leading: IconButton(icon: Icon(Icons.arrow_back), onPressed: () => Navigator.of(context).pop())`.
3. **Alineación de Catálogo (CU05):**
   - El botón/ítem de Catálogo en el menú no debe realizar transiciones a pantallas ajenas como Colecciones mientras CU05 se encuentre en estado pendiente de especificación.

---

## 5. Auditoría de Cumplimiento en Casos de Uso Existentes

| Caso de Uso | Tipo de Pantalla | Barra de Navegación | Botón Volver (←) | Estado de Cumplimiento |
| :--- | :--- | :--- | :--- | :--- |
| **Inicio** | Principal (Hub) | Visible (Siempre) | Prohibido | ✅ Conforme |
| **Buscar (CU06)** | Principal (Hub) | Visible (Siempre) | Prohibido | ✅ Conforme (`automaticallyImplyLeading: false`) |
| **Catálogo (CU05)** | Principal (Hub) | Visible (Siempre) | Prohibido | ⏳ Pendiente de implementar |
| **Perfil (CU04)** | Principal (Hub) | Visible (Siempre) | Prohibido | ✅ Conforme |
| **Colecciones (CU36)** | Secundaria (Hoja) | Oculta / No disponible | Obligatorio hacia `/inicio` | ✅ Conforme en Mobile / En migración de Layout en Web |
| **Detalle Colección (CU36)** | Secundaria (Hoja) | Oculta / No disponible | Obligatorio hacia `/colecciones` | ✅ Conforme |
