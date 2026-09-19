# FASHION STORE — Catálogo y Especificación de Componentes UI
**Versión:** 1.0.0 Production  
**Metodología:** Spec-Driven Development (SDD) & Atomic Design Hierarchy  
**Plataformas:** Angular 19+ (Standalone + Tailwind CSS) & Flutter 3.x (Stateless/Stateful + AppTheme)  
**Rejilla Espacial:** Escala Base-2 (2, 4, 8, 16, 32, 64, 128px)  
**Tipografía:** Outfit (300, 400, 500, 600, 700)  
**Regla de Naming:** Sustitución estricta y global de la denominación previa "AURA STUDIO" por **FASHION STORE**.

---

## Índice General

1. [PARTE 1: COMPONENTES ATÓMICOS (Prioridad Ciclo #1: Auth & Admin)](#parte-1-componentes-atómicos)
   - [1.1 Matriz de Botones (6 Tipos × 6 Estados)](#11-matriz-de-botones)
   - [1.2 Inputs y Campos de Formulario (Form Atoms)](#12-inputs-y-campos-de-formulario)
   - [1.3 Controles de Selección y Micro-Formularios](#13-controles-de-selección-y-micro-formularios)
   - [1.4 Indicadores de Feedback, Badges y Navegación Menor](#14-indicadores-de-feedback-badges-y-navegación-menor)
   - [1.5 Matriz Unificada de 9 Estados de Componente](#15-matriz-unificada-de-9-estados)
2. [PARTE 2: VOCABULARIO DE ICONOGRAFÍA (38 Glifos Normativos)](#parte-2-vocabulario-de-iconografía)
3. [PARTE 3: COMPONENTES COMPUESTOS Y ENSAMBLADOS (Planificados Ciclo #2 en adelante)](#parte-3-componentes-compuestos-y-ensamblados)
   - [3.1 Sistema de Barra de Búsqueda (5 Estados)](#31-sistema-de-barra-de-búsqueda)
   - [3.2 Tarjetas de Producto (4 Variantes & Formato Fila)](#32-tarjetas-de-producto)
   - [3.3 Panel de Filtros y Selector de Ordenamiento](#33-panel-de-filtros-y-selector-de-ordenamiento)
   - [3.4 Atelier Calendar (Reserva de Probador CU12)](#34-atelier-calendar)
   - [3.5 Ensamblado de Formulario de Checkout (CU15/16)](#35-ensamblado-de-formulario-de-checkout)
   - [3.6 Drawer Deslizante de Bolsa de Compras (CU11)](#36-drawer-deslizante-de-bolsa-de-compras)
   - [3.7 Menú Desplegable de Usuario y Centro de Notificaciones](#37-menú-desplegable-de-usuario-y-centro-de-notificaciones)
4. [PARTE 4: GUÍA DE IMPLEMENTACIÓN DE CÓDIGO LISTA PARA PRODUCCIÓN](#parte-4-guía-de-implementación-de-código)
   - [4.1 Implementaciones en Angular 19+ (Standalone + Signals + Tailwind)](#41-implementaciones-en-angular-19)
   - [4.2 Implementaciones en Flutter 3.x (Widgets Tipados + AppTheme)](#42-implementaciones-en-flutter-3x)

---

# PARTE 1: COMPONENTES ATÓMICOS

## 1.1 Matriz de Botones

Los botones de **FASHION STORE** siguen una anatomía fija con una altura óptica de **48px (`h-12`)**, relleno horizontal de **32px (`px-space-5`)** y radio de curvatura de **4px (`rounded-sm` / `AppRadius.sm`)**. El texto se compone en tipografía `Outfit`, peso SemiBold 600 (`font-label-caps text-label-caps`), transformación en mayúsculas y `letter-spacing` expandido (0.12em).

### Tipos y Comportamiento de Color

| Tipo | Fondo Base | Texto / Glifo | Borde / Sombra | Rol en la Experiencia |
|---|---|---|---|---|
| **Primary** | `#000000` (`primary`) | `#FFFFFF` (`on-primary`) | Ninguno (Sólido) | Acción principal (Añadir a bolsa, Pagar, Registrar) |
| **Secondary** | `#E8E8EA` (`surface-container-high`) | `#000000` (`primary`) | Ninguno | Exploración secundaria, filtros, acciones alternativas |
| **Tertiary Sand** | `#ECDECB` (`secondary-container`) | `#221A0F` (`on-secondary-fixed`) | Ninguno | Acciones vinculadas a colecciones cápsula y lookbook |
| **Ghost** | `transparent` | `#000000` (`primary`) | Ninguno | Enlaces contextuales, detalles, botones de cancelación |
| **Destructive** | `#BA1A1A` (`error`) | `#FFFFFF` (`on-error`) | Ninguno | Eliminar ítems, anular reservas, revocar acceso |
| **Icon Button** | `#EDEEF0` (`surface-container`) | `#000000` (`primary`) | Bounding box 48×48px | Acciones rápidas (Wishlist, Cerrar, Carrito) |

### Matriz de Estados (6 Tipos × 6 Estados)

| Tipo | 1. Default | 2. Hover | 3. Focus (Anillo Doble) | 4. Active (Presionado) | 5. Disabled | 6. Loading (Spinner) |
|---|---|---|---|---|---|---|
| **Primary** | `bg-primary text-on-primary` | `bg-primary-container shadow-sm` | `shadow-[0_0_0_2px_#ffffff,0_0_0_4px_#000000]` | `bg-on-surface-variant translate-y-[1px]` | `bg-surface-container-highest text-outline cursor-not-allowed` | Spinner `progress_activity` animado + texto "Wait" |
| **Secondary** | `bg-surface-container-high text-primary` | `bg-surface-container-highest shadow-sm` | `shadow-[0_0_0_2px_#ffffff,0_0_0_4px_#000000]` | `bg-surface-dim translate-y-[1px]` | `bg-surface-container-low text-outline cursor-not-allowed` | Spinner `progress_activity` + texto "Sync" |
| **Tertiary Sand** | `bg-secondary-container text-on-secondary-fixed` | `bg-secondary-fixed shadow-sm` | `shadow-[0_0_0_2px_#ffffff,0_0_0_4px_#675d4e]` | `bg-secondary-fixed-dim translate-y-[1px]` | `bg-surface-container text-outline cursor-not-allowed` | Spinner `progress_activity` + texto "Load" |
| **Ghost** | `bg-transparent text-primary` | `bg-surface-container text-primary` | `shadow-[0_0_0_2px_#ffffff,0_0_0_4px_#000000]` | `bg-surface-container-high translate-y-[1px]` | `text-outline cursor-not-allowed` | Spinner `progress_activity` + texto "Fetch" |
| **Destructive** | `bg-error text-on-error` | `bg-error/90 shadow-sm` | `shadow-[0_0_0_2px_#ffffff,0_0_0_4px_#ba1a1a]` | `bg-error-container text-on-error-container translate-y-[1px]` | `bg-surface-container text-outline cursor-not-allowed` | Spinner `progress_activity` + texto "Purge" |
| **Icon Button** | `w-12 h-12 bg-surface-container` | `bg-surface-container-high shadow-sm` | `shadow-[0_0_0_2px_#ffffff,0_0_0_4px_#000000]` | `bg-primary text-on-primary` | `opacity-40 cursor-not-allowed` | Spinner central de 18px |

---

## 1.2 Inputs y Campos de Formulario (Form Atoms)

Los campos de entrada están diseñados para una captura sobria y legible de datos de clientes, login, tarjetas y registros de inventario.

* **Dimensiones Base:** Altura 48px (`h-12`), relleno horizontal 16px (`px-space-4`), radio de curvatura 4px (`rounded`).
* **Tipografía del Valor:** Outfit Regular 400, 14px (`font-body-md text-body-md`), interlineado 22px.
* **Tipografía de Etiqueta (Label):** Outfit SemiBold 600, 11px (`font-label-caps text-label-caps`), mayúsculas y tracking expandido.

### Estados Operativos de Input

1. **Default (Reposo):**
   * Contenedor: `bg-surface-container-low` (`#F3F3F5`).
   * Placeholder: `text-outline` (`#75777A`), icono descriptivo derecho (18px).
2. **Focused (Enfocado / Activo):**
   * Contenedor: `bg-surface-container-lowest` (`#FFFFFF`).
   * Borde / Anillo: `shadow-[0_0_0_2px_#000000]`.
   * Etiqueta: `text-primary` (`#000000`).
3. **Filled (Con Valor):**
   * Contenedor: `bg-surface-container-low`, texto de alto contraste `text-on-surface` (`#1A1C1D`).
4. **Password / Filled con Toggle:**
   * Campo protegido con botón terminal interactivo para conmutar `visibility` / `visibility_off`.
5. **Error (Validación Fallida):**
   * Contenedor: `bg-error-container/40` (`rgba(255,218,214,0.4)`).
   * Anillo: `shadow-[0_0_0_2px_#BA1A1A]`.
   * Mensaje explicativo inferior en tipografía `font-body-sm text-body-sm text-error` (`#BA1A1A`).
6. **Disabled (Bloqueado):**
   * Contenedor: `bg-surface-container-high` (`#E8E8EA`), cursor `cursor-not-allowed`, icono `lock` de 18px.

### Variantes Especiales
* **Select Dropdown:** Altura 48px, fondo `surface-container-low`, selector de opciones con icono de apertura `expand_more` (18px).
* **Textarea (Notas de Taller / Modista):** Altura mínima de 96px (`h-24`), padding interno de 16px (`p-space-4`), fondo `surface-container-low` para instrucciones de entrega o reservas especiales.

---

## 1.3 Controles de Selección y Micro-Formularios

### Checkboxes (16×16px, `rounded-sm`)
* **Unselected:** Fondo `surface-container-highest` (`#E2E2E4`).
* **Checked:** Fondo `primary` (`#000000`), icono central `check` (14px) en color `on-primary` (`#FFFFFF`).
* **Indeterminate:** Fondo `primary`, icono central `remove` (14px) en blanco.
* **Disabled:** Fondo `surface-dim` (`#D9DADC`), opacidad al 40%, cursor bloqueado.

### Radio Buttons (16×16px, `rounded-full`)
* **Unselected:** Fondo circular `surface-container-highest`.
* **Selected:** Fondo `primary` con punto central blanco concéntrico de 6×6px (`w-1.5 h-1.5 rounded-full bg-on-primary`).
* **Disabled:** Fondo `surface-dim` con opacidad al 40%.

### Switches Táctiles (40×24px, `w-10 h-6 rounded-full`)
* **Off:** Fondo `surface-container-highest`, botón deslizante interior de 20×20px en `surface-container-lowest` alineado a la izquierda.
* **On:** Fondo `primary`, botón deslizante interior blanco alineado a la derecha.
* **Disabled:** Fondo `surface-dim` con botón inactivo atenuado.

### Selector de Cantidad (Quantity Selector Atom)
* **Contenedor:** Altura 36px (`h-9`), fondo blanco `surface-container-lowest` con elevación `shadow-sm`.
* **Botones [-] y [+]:** Ancho 32px (`w-8`), icono de 16px (`remove`, `add`).
* **Display Central:** Ancho 32px (`w-8`), texto centrado en `font-label-caps text-label-caps text-primary` con formato numérico a 2 dígitos (`01`, `02`, `03`).

### Selector de Fecha Rápido (Date Picker Atom)
* **Estructura:** Contenedor de 36px de altura, fondo blanco, texto en `font-body-sm`, emparejado con icono `calendar_today` (16px) en color `outline`. Diseñado para selección ágil en agendamiento de probador (`CU12`).

---

## 1.4 Indicadores de Feedback, Badges y Navegación Menor

### Badges Editoriales de Producto
* `NEW`: Fondo `primary` (`#000000`), texto `on-primary` (`#FFFFFF`), tipografía `label-caps`.
* `SALE -30%`: Fondo `secondary-container` (`#ECDECB`), texto `on-secondary-fixed` (`#221A0F`).
* `LIMITED EDITION`: Fondo `surface-container-highest` (`#E2E2E4`), texto `on-surface` (`#1A1C1D`).
* `LOW STOCK`: Fondo `error` (`#BA1A1A`), texto `on-error` (`#FFFFFF`).

### Chips Interactivos y Tags de Filtro
* **Píldora Inactiva:** `px-space-4 py-space-2 rounded-full bg-surface-container text-on-surface-variant`.
* **Píldora en Hover:** Fondo `surface-container-high` con texto `primary`.
* **Píldora Activa (Seleccionada):** Fondo `primary`, texto blanco `on-primary`, incluye botón de deselección con glifo `close` de 14px.
* **Wishlist Tooltip Trigger:** Botón circular de 32×32px con icono `bookmark_border` (18px) y tooltip flotante con sombra suave.

### Alertas Semánticas de 4 Niveles
1. **Success:** Fondo `surface-container`, icono `check_circle` (20px), texto *"Garment reserved for 30m"*.
2. **Information:** Fondo `surface-container`, icono `info` (20px), texto *"Atelier holiday schedule"*.
3. **Advisory (Advertencia de Stock):** Fondo `secondary-container/60`, icono `warning` (20px) en camel oscuro, texto *"Only 2 pieces remaining"*.
4. **Error (Fallo de Transacción):** Fondo `error-container/40`, icono `report` (20px) en rojo vino, texto *"Card Declined: Verify billing address"*.

### Toast Banner Flotante
* Fondo `primary` (`#000000`), texto `on-primary`, borde redondeado con sombra `shadow-xl`.
* Incorpora miniatura editorial del producto de 40×48px (`w-10 h-12 rounded object-cover`).
* Muestra título en `label-caps text-surface-dim` (*"SHOPPING BAG UPDATED"*), nombre de la prenda y enlace de acción subrayado *"VIEW BAG"*.

### Barra de Progreso (Order Pipeline)
* Altura 6px (`h-1.5`), fondo `surface-container-highest`, barra activa `primary` con terminación circular (`rounded-full`).

### Migas de Pan (Breadcrumbs) y Pestañas (Tabs)
* **Breadcrumbs:** Enlaces en `font-label-caps`, separados por `/` en color `outline-variant`, con la página actual en negrita.
* **Tabs:** Texto en mayúsculas `label-caps`. La pestaña activa proyecta un subrayado físico de 2px mediante `shadow-[0_2px_0_0_#000000]`.

---

## 1.5 Matriz Unificada de 9 Estados

Alineación de comportamiento técnico y visual para auditoría y QA:

| Estado | Botón de Acción | Campo de Texto (Input) | Píldora de Selección | Checkbox / Radio |
|---|---|---|---|---|
| **1. Default** | `bg-primary text-on-primary` | `bg-surface-container-low` | `bg-surface-container` | Borde/fondo `surface-container-highest` |
| **2. Hover** | `bg-primary-container shadow-sm` | `bg-surface-container shadow-sm` | `bg-surface-container-high` | Halo de hover sutil |
| **3. Focus** | `shadow-[0_0_0_2px_#fff,0_0_0_4px_#000]` | `shadow-[0_0_0_2px_#000000]` | `shadow-[0_0_0_2px_#000000]` | Anillo exterior de 2px |
| **4. Active** | `translate-y-[1px]` | Valor activo enfocado | `bg-primary text-on-primary` | Icono o punto visible activo |
| **5. Disabled** | `bg-surface-container-highest text-outline` | `bg-surface-container-high cursor-not-allowed` | `opacity-40 cursor-not-allowed` | Fondo atenudado al 40% |
| **6. Error** | `bg-error text-on-error` | `bg-error-container/40 shadow-[0_0_0_2px_#ba1a1a]` | Borde/alerta en tono error | Borde de fallo en rojo |
| **7. Loading** | Spinner animado `progress_activity` | Indicador de validación rotando | Glifo rotando de sincronización | Estado bloqueado transicional |
| **8. Success** | Glifo `check` + texto "Done" | Icono `check_circle` verde | Selección confirmada fija | Marcado afirmativo |
| **9. Selected** | Fondo de selección fijo | Texto persistido en base de datos | Píldora negra con glifo `close` | Marcado permanente |

---

# PARTE 2: VOCABULARIO DE ICONOGRAFÍA (38 GLIFOS)

Los iconos del sistema corresponden a **Material Symbols Outlined** con un bounding box normativo de **24×24px** y un grosor de trazo óptico unificado de **1.5px** (`font-variation-settings: 'opsz' 24, 'wght' 400, 'FILL' 0`).

| N° | Identificador Material | Glifo Visual | Semántica y Uso en FASHION STORE |
|:---:|---|:---:|---|
| **01** | `search` | 🔍 | Búsqueda difusa de prendas en catálogo por texto (`CU06`) |
| **02** | `shopping_bag` | 🛍️ | Bolsa de compras digital, drawer lateral flotante (`CU11`) |
| **03** | `shopping_cart` | 🛒 | Resumen de carrito omnicanal y pedidos consolidados |
| **04** | `favorite` | 🤍/🖤 | Guardar en lista de deseos (Fill 0 en reposo, Fill 1 al seleccionar) |
| **05** | `person` | 👤 | Acceso a sesión de usuario y navegación personal |
| **06** | `account_circle` | 🪪 | Perfil detallado del cliente, medidas y direcciones (`CU04`) |
| **07** | `menu` | ☰ | Menú hamburguesa responsivo para vista móvil (360px) |
| **08** | `close` | ✕ | Cerrar modales, drawers laterales y descartar chips de filtro |
| **09** | `tune` | 🎚️ | Apertura del panel de filtros avanzados (tallas, colores, precios) |
| **10** | `swap_vert` | ⇅ | Menú de ordenamiento de catálogo (precio, novedades, valoración) |
| **11** | `chevron_left` | ‹ | Navegación previa en paginación o carrusel de fotos |
| **12** | `chevron_right` | › | Navegación siguiente en paginación y enlaces de acordeón |
| **13** | `expand_less` | ∧ | Colapsar acordeón o cerrar menú desplegable |
| **14** | `expand_more` | ∨ | Desplegar selector de opciones o filtros |
| **15** | `arrow_back` | ← | Regresar a la vista previa del catálogo desde el detalle (PDP) |
| **16** | `arrow_forward` | → | Avanzar al siguiente paso en el pipeline de checkout (`CU15`) |
| **17** | `add` | + | Incrementar cantidad de prendas en bolsa o abrir subcategorías |
| **18** | `remove` | − | Decrementar cantidad de prendas o estado indeterminado |
| **19** | `delete` | 🗑️ | Eliminar variante de la bolsa o descartar borrador |
| **20** | `edit` | ✏️ | Modificar dirección de envío o parámetros de inventario |
| **21** | `share` | 🔗 | Compartir lookbook editorial o prenda en canales sociales |
| **22** | `star` | ⭐ | Valoración completa de prenda (estrellas 1 a 5) |
| **23** | `star_half` | ✬ | Valoración intermedia decimal |
| **24** | `check` | ✓ | Confirmación afirmativa, elemento seleccionado en lista |
| **25** | `cancel` | ⓧ | Limpiar campo de búsqueda activo o rechazar acción |
| **26** | `visibility` | 👁️ | Mostrar contraseña en formulario o previsualizar asset |
| **27** | `visibility_off` | 🙈 | Ocultar contraseña segura |
| **28** | `home` | 🏠 | Enlace a la página principal y editorial de la marca |
| **29** | `inventory_2` | 📦 | Gestión de inventario por sucursal (`CU24`) y archivo de órdenes |
| **30** | `local_shipping` | 🚚 | Estado de despacho a domicilio con courier neutral en carbono |
| **31** | `location_on` | 📍 | Selección de sucursal física para retiro o reserva (`CU12`, `CU21`) |
| **32** | `credit_card` | 💳 | Pago electrónico cifrado con tarjeta vía Stripe (`CU16`) |
| **33** | `calendar_month` | 📅 | Atelier Calendar para agendamiento de citas de probador (`CU12`) |
| **34** | `schedule` | 🕒 | Horario de apertura/cierre de sucursales físicas |
| **35** | `notifications` | 🔔 | Centro de notificaciones, alertas de stock y pedidos despachados |
| **36** | `settings` | ⚙️ | Configuración de cuenta, moneda e idioma |
| **37** | `logout` | 🚪 | Cierre seguro de sesión con invalidación de token JWT (`CU03`) |
| **38** | `login` | 🔑 | Inicio de sesión en plataforma (`CU02`) |

---

# PARTE 3: COMPONENTES COMPUESTOS Y ENSAMBLADOS

## 3.1 Sistema de Barra de Búsqueda
Módulo de cabecera para búsqueda interactiva con 5 estados:
1. **Default:** Altura 48px, fondo blanco, icono `search` izquierdo, texto placeholder tenue y atajo de teclado en badge `⌘K`.
2. **Focused:** Elevación perimetral `shadow-[0_0_0_2px_#000000]`, icono `cancel` para limpiar texto rápidamente.
3. **Filled:** Muestra el término ingresado con tipografía de alto contraste.
4. **Loading:** Icono derecho sustituido por spinner animado `progress_activity` mientras se consulta `/api/v1/catalogo/buscar`.
5. **Zero Results Preview:** Desplegable flotante en `surface-container-lowest` que indica con delicadeza: *"No matching garments found in A/W 25 catalog."*

---

## 3.2 Tarjetas de Producto

Las tarjetas de producto poseen una proporción vertical fija de **aspect ratio 3:4** para fotografía de alta costura sobre fondos neutros de galería.

### Variantes de Tarjeta
1. **Card Default:** Imagen con bordes redondeados (`rounded`), etiqueta flotante `PRE-ORDER` en la esquina superior izquierda con efecto `backdrop-blur`, y botón circular de wishlist en la esquina superior derecha. En la base: nombre de la prenda, precio ($890.00), valoración (4.9 ⭐) y muestrario de colores (swatches circulares con halo de selección).
2. **Card Hover con Quick Add:** Al pasar el cursor, la imagen experimenta un sutil zoom (`scale-105 duration-500`) y emerge un gradiente oscuro inferior (`bg-gradient-to-t from-black/60 to-transparent`) que expone el selector de tallas rápidas (36, 38, 40 disponibles, 42 agotada/deshabilitada).
3. **Card Favorited:** Botón de wishlist con corazón en color primario sólido (`font-variation-settings: 'FILL' 1;`) y badge `FAVORITED`.
4. **Card Sale:** Badge superior en tono camel cálido `SALE -30%`, precio actual en negrita y precio original tachado (`line-through text-outline`).
5. **Product List Row (Vista Horizontal):** Disposición de lista para carritos y resultados compactos: miniatura de 80×96px (`w-20 h-24`), referencia (`REF. AU-4920`), composición textil, disponibilidad en sucursal (*"IN STOCK AT STOCKHOLM ATELIER"*), precio y botón de acción directa *"Add to Bag"*.

---

## 3.3 Panel de Filtros y Selector de Ordenamiento

### Panel Lateral de Filtros (Filter Panel)
* **Selector de Tallas (EU):** Cuadrícula de 5 columnas con botones de talla (XS, S, M, L, XL). La talla M seleccionada viste de negro primario; la talla XL agotada aparece tachada con línea oblicua y cursor bloqueado.
* **Paleta de Colores (Color Palette):** Conjunto de botones circulares (28×28px) que presentan negro obsidiana (con anillo de selección de 2px blanco + 3px negro), champagne crudo, camel y pizarra.
* **Control Deslizante de Rango de Precio:** Barra de 6px de altura con dos tiradores circulares de 16px con sombra flotante que delimitan el intervalo ($300 — $1,800).
* **Filtro de Disponibilidad Inmediata:** Switch interactivo rotulado *"In Stock Pieces Only"*.

### Selector de Ordenamiento (Sort Architecture)
Dropdown de 48px de altura con apertura de menú flotante en `surface-container`:
* *Recommended Curations* (con icono de check activo)
* *Newest Arrivals*
* *Price: High to Low*
* *Price: Low to High*
* *Client Rating (4.5+)*

---

## 3.4 Atelier Calendar (Reserva de Probador CU12)

Cuadrícula de 7 columnas concebida para la programación de citas en tienda física:
* **Cabecera:** Navegación por meses con botones de flecha, indicando el mes corriente (*"October 2025"*) y la sucursal asignada (*"Stockholm Flagship"*).
* **Nombres de Días:** `Mo`, `Tu`, `We`, `Th`, `Fr`, `Sa`, `Su` en `font-label-caps text-outline`.
* **Estados de Celda de Día:**
  * *Días Pasados:* Tipografía atenuada al 30% (`text-outline/30`).
  * *Días Sin Disponibilidad:* Número tachado (`line-through text-outline`).
  * *Días Disponibles:* Hover interactivo con fondo `surface-container`.
  * *Día Seleccionado:* Celda destacada con fondo `primary` (`#000000`), texto blanco `on-primary` y sombra sutil.

---

## 3.5 Ensamblado de Formulario de Checkout (CU15/16)

Formulario estructurado en dos secciones con distintivo superior *"ENCRYPTED 256-BIT"*:
1. **Datos de Despacho (Patron Dispatch):**
   * Fila 1: First Name (Eleanor) y Last Name (Vance) en campos de 48px.
   * Fila 2: Street Address completo.
   * Fila 3: Ciudad (Stockholm), País (Dropdown de selección) y Código Postal (114 34).
2. **Instrumento de Pago (Payment Capture):**
   * Selector tipo Radio marcado *"Credit Card (Vault Encrypted)"* acompañado de los distintivos de red (VISA, MC, AMEX).
   * Campo de número de tarjeta enmascarado (`•••• •••• •••• 8842`) con fecha de expiración alineada a la derecha (`12/28`).

---

## 3.6 Drawer Deslizante de Bolsa de Compras (CU11)

Panel lateral con animación de entrada deslizante para el carrito omnicanal:
* **Encabezado:** Contador de artículos (*"02 ITEMS"*) y botón de cierre (`close`).
* **Lista de Artículos:** Cada elemento incorpora imagen de 64×80px, nombre del artículo, talla, color, precio unitario, control de cantidad [- 1 +] y botón de remoción rápida (`delete`).
* **Cupón de Privilegio:** Campo de texto de 40px con botón lateral *"Apply"*.
* **Resumen Financiero:**
  * Subtotal ($1,280.00)
  * Express Carbon-Neutral Shipping (*Complimentary*)
  * Taxes & Duties Included ($0.00)
  * **Total Definitivo:** En tipografía `font-title-lg text-title-lg font-semibold`.
* **Botón de Checkout:** Botón de 48px de ancho completo en negro primario rotulado *"Proceed to Checkout"*.

---

## 3.7 Menú Desplegable de Usuario y Centro de Notificaciones

### Menú de Usuario (User Profile Dropdown)
* **Encabezado:** Avatar circular de 48×48px con las iniciales del cliente ("EV"), nombre completo y correo electrónico.
* **Opciones de Cuenta:**
  * *Account Details & Addresses* (icono `account_circle`)
  * *Orders Archive* con badge de estado `3 ACTIVE` (icono `inventory_2`)
  * *Curated Wishlist* indicando "12 Items" (icono `favorite`)
  * *Security & Preferences* (icono `settings`)
* **Pie:** Enlace destructivo destacado en rojo vino *"Sign Out from Atelier"* con icono `logout`.

### Centro de Notificaciones (Notification Center)
Bandeja de avisos con indicador de mensajes no leídos ("2") y botón *"Mark All Read"*:
* **Notificación Crítica / Envío (No leída):** Barra vertical izquierda negra de 4px, icono `local_shipping`, asunto *"Your order #AU-8921 has dispatched"*, detalle de courier y marca de tiempo *"10M AGO"*.
* **Notificación de Promoción (No leída):** Barra vertical camel de 4px, icono `sell`, aviso de baja de precio en prenda guardada en wishlist (*"2H AGO"*).
* **Notificación Leída:** Opacidad al 60%, icono `verified`, confirmación de reserva en probador (*"1D AGO"*).

---

# PARTE 4: GUÍA DE IMPLEMENTACIÓN DE CÓDIGO

## 4.1 Implementaciones en Angular 19+

### Componente de Botón Primario y Variantes (`luxury-button.component.ts`)

```typescript
import { Component, ChangeDetectionStrategy, input, output } from '@angular/core';
import { CommonModule } from '@angular/common';

export type ButtonVariant = 'primary' | 'secondary' | 'tertiary' | 'ghost' | 'destructive';

@Component({
  selector: 'app-luxury-button',
  standalone: true,
  imports: [CommonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <button
      [type]="type()"
      [disabled]="disabled() || loading()"
      (click)="onClick.emit($event)"
      [class]="buttonClasses()"
    >
      @if (loading()) {
        <span class="material-symbols-outlined animate-spin text-[16px]">progress_activity</span>
        <span>{{ loadingText() }}</span>
      } @else {
        <ng-content />
      }
    </button>
  `
})
export class LuxuryButtonComponent {
  readonly variant = input<ButtonVariant>('primary');
  readonly type = input<'button' | 'submit' | 'reset'>('button');
  readonly disabled = input<boolean>(false);
  readonly loading = input<boolean>(false);
  readonly loadingText = input<string>('Wait');
  readonly fullWidth = input<boolean>(false);

  readonly onClick = output<MouseEvent>();

  protected buttonClasses(): string {
    const base = 'h-12 px-space-5 rounded-sm font-label-caps text-label-caps uppercase transition-all duration-150 flex items-center justify-center gap-space-2 outline-none';
    const width = this.fullWidth() ? 'w-full' : 'w-auto';

    if (this.disabled()) {
      return `${base} ${width} bg-surface-container-highest text-outline cursor-not-allowed opacity-60`;
    }

    switch (this.variant()) {
      case 'primary':
        return `${base} ${width} bg-primary text-on-primary hover:bg-primary-container focus:shadow-[0_0_0_2px_#ffffff,0_0_0_4px_#000000] active:translate-y-[1px] shadow-sm`;
      case 'secondary':
        return `${base} ${width} bg-surface-container-high text-primary hover:bg-surface-container-highest focus:shadow-[0_0_0_2px_#ffffff,0_0_0_4px_#000000] active:translate-y-[1px]`;
      case 'tertiary':
        return `${base} ${width} bg-secondary-container text-on-secondary-fixed hover:bg-secondary-fixed focus:shadow-[0_0_0_2px_#ffffff,0_0_0_4px_#675d4e] active:translate-y-[1px]`;
      case 'ghost':
        return `${base} ${width} bg-transparent text-primary hover:bg-surface-container focus:shadow-[0_0_0_2px_#ffffff,0_0_0_4px_#000000] active:translate-y-[1px]`;
      case 'destructive':
        return `${base} ${width} bg-error text-on-error hover:bg-error/90 focus:shadow-[0_0_0_2px_#ffffff,0_0_0_4px_#ba1a1a] active:translate-y-[1px]`;
    }
  }
}
```

---

### Componente de Input de Texto (`luxury-text-field.component.ts`)

```typescript
import { Component, ChangeDetectionStrategy, input, forwardRef, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ControlValueAccessor, NG_VALUE_ACCESSOR, ReactiveFormsModule } from '@angular/forms';

@Component({
  selector: 'app-luxury-text-field',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => LuxuryTextFieldComponent),
      multi: true
    }
  ],
  template: `
    <div class="flex flex-col gap-space-1 w-full">
      @if (label()) {
        <label class="font-label-caps text-label-caps uppercase" [class.text-error]="errorMessage()" [class.text-on-surface-variant]="!errorMessage()">
          {{ label() }}
        </label>
      }
      <div [class]="containerClasses()">
        <input
          [type]="currentType()"
          [placeholder]="placeholder()"
          [disabled]="disabled()"
          [value]="value()"
          (input)="handleInput($event)"
          (blur)="onTouched()"
          class="bg-transparent w-full text-on-surface placeholder:text-outline focus:outline-none font-body-md text-body-md"
        />
        @if (isPassword()) {
          <button type="button" (click)="togglePasswordVisibility()" class="text-on-surface-variant hover:text-primary">
            <span class="material-symbols-outlined text-[18px]">
              {{ showPassword() ? 'visibility' : 'visibility_off' }}
            </span>
          </button>
        } @else if (icon()) {
          <span class="material-symbols-outlined text-[18px]" [class.text-error]="errorMessage()" [class.text-outline]="!errorMessage()">
            {{ icon() }}
          </span>
        }
      </div>
      @if (errorMessage()) {
        <span class="font-body-sm text-body-sm text-error mt-0.5">{{ errorMessage() }}</span>
      }
    </div>
  `
})
export class LuxuryTextFieldComponent implements ControlValueAccessor {
  readonly label = input<string>('');
  readonly placeholder = input<string>('');
  readonly type = input<string>('text');
  readonly icon = input<string>('');
  readonly disabled = input<boolean>(false);
  readonly errorMessage = input<string>('');

  protected readonly value = signal<string>('');
  protected readonly showPassword = signal<boolean>(false);

  protected isPassword(): boolean {
    return this.type() === 'password';
  }

  protected currentType(): string {
    if (this.isPassword()) {
      return this.showPassword() ? 'text' : 'password';
    }
    return this.type();
  }

  protected togglePasswordVisibility(): void {
    this.showPassword.update(prev => !prev);
  }

  protected containerClasses(): string {
    const base = 'h-12 px-space-4 rounded flex items-center justify-between transition-all';
    if (this.disabled()) {
      return `${base} bg-surface-container-high cursor-not-allowed opacity-60`;
    }
    if (this.errorMessage()) {
      return `${base} bg-error-container/40 shadow-[0_0_0_2px_#ba1a1a]`;
    }
    return `${base} bg-surface-container-low focus-within:bg-surface-container-lowest focus-within:shadow-[0_0_0_2px_#000000]`;
  }

  protected onChange: (val: string) => void = () => {};
  protected onTouched: () => void = () => {};

  handleInput(event: Event): void {
    const target = event.target as HTMLInputElement;
    this.value.set(target.value);
    this.onChange(target.value);
  }

  writeValue(val: string): void {
    this.value.set(val || '');
  }

  registerOnChange(fn: (val: string) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }
}
```

---

## 4.2 Implementaciones en Flutter 3.x

### Widget de Botón de Lujo (`luxury_button.dart`)

```dart
import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';
import '../../theme/app_spacing.dart';
import '../../theme/app_radius.dart';
import '../../theme/app_typography.dart';

enum LuxuryButtonVariant { primary, secondary, tertiary, ghost, destructive }

class LuxuryButton extends StatelessWidget {
  final String text;
  final VoidCallback? onPressed;
  final LuxuryButtonVariant variant;
  final bool isLoading;
  final bool isFullWidth;
  final IconData? icon;

  const LuxuryButton({
    super.key,
    required this.text,
    this.onPressed,
    this.variant = LuxuryButtonVariant.primary,
    this.isLoading = false,
    this.isFullWidth = false,
    this.icon,
  });

  @override
  Widget build(BuildContext context) {
    final bool isEnabled = onPressed != null && !isLoading;

    Color backgroundColor;
    Color textColor;
    BorderSide borderSide = BorderSide.none;

    switch (variant) {
      case LuxuryButtonVariant.primary:
        backgroundColor = isEnabled ? AppColors.primary : AppColors.surfaceContainerHighest;
        textColor = isEnabled ? AppColors.onPrimary : AppColors.outline;
        break;
      case LuxuryButtonVariant.secondary:
        backgroundColor = isEnabled ? AppColors.surfaceContainerHigh : AppColors.surfaceContainerLow;
        textColor = isEnabled ? AppColors.primary : AppColors.outline;
        break;
      case LuxuryButtonVariant.tertiary:
        backgroundColor = isEnabled ? AppColors.secondaryContainer : AppColors.surfaceContainer;
        textColor = isEnabled ? AppColors.onSecondaryContainer : AppColors.outline;
        break;
      case LuxuryButtonVariant.ghost:
        backgroundColor = Colors.transparent;
        textColor = isEnabled ? AppColors.primary : AppColors.outline;
        break;
      case LuxuryButtonVariant.destructive:
        backgroundColor = isEnabled ? AppColors.error : AppColors.surfaceContainer;
        textColor = isEnabled ? AppColors.onError : AppColors.outline;
        break;
    }

    final Widget content = isLoading
        ? const SizedBox(
            width: 18.0,
            height: 18.0,
            child: CircularProgressIndicator(
              strokeWidth: 1.5,
              valueColor: AlwaysStoppedAnimation<Color>(AppColors.onPrimary),
            ),
          )
        : Row(
            mainAxisSize: MainAxisSize.min,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (icon != null) ...[
                Icon(icon, size: 18.0, color: textColor),
                const SizedBox(width: AppSpacing.space3),
              ],
              Text(
                text.toUpperCase(),
                style: AppTypography.labelCaps.copyWith(color: textColor),
              ),
            ],
          );

    return SizedBox(
      height: 48.0,
      width: isFullWidth ? double.infinity : null,
      child: Material(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(AppRadius.sm),
        child: InkWell(
          onTap: isEnabled ? onPressed : null,
          borderRadius: BorderRadius.circular(AppRadius.sm),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: AppSpacing.space5),
            child: Center(child: content),
          ),
        ),
      ),
    );
  }
}
```

---

### Widget de Selector de Talla (`size_pill_widget.dart`)

```dart
import 'package:flutter/material.dart';
import '../../theme/app_colors.dart';
import '../../theme/app_spacing.dart';
import '../../theme/app_radius.dart';
import '../../theme/app_typography.dart';

class SizePillWidget extends StatelessWidget {
  final String sizeLabel;
  final bool isSelected;
  final bool isAvailable;
  final VoidCallback? onSelected;

  const SizePillWidget({
    super.key,
    required this.sizeLabel,
    required this.isSelected,
    this.isAvailable = true,
    this.onSelected,
  });

  @override
  Widget build(BuildContext context) {
    if (!isAvailable) {
      return Container(
        height: 40.0,
        decoration: BoxDecoration(
          color: AppColors.surfaceContainerLow,
          borderRadius: BorderRadius.circular(AppRadius.sm),
        ),
        child: Center(
          child: Text(
            sizeLabel,
            style: AppTypography.labelCaps.copyWith(
              color: AppColors.outline,
              decoration: TextDecoration.lineThrough,
            ),
          ),
        ),
      );
    }

    final Color bgColor = isSelected ? AppColors.primary : AppColors.surfaceContainerLow;
    final Color textColor = isSelected ? AppColors.onPrimary : AppColors.onSurface;

    return Material(
      color: bgColor,
      borderRadius: BorderRadius.circular(AppRadius.sm),
      child: InkWell(
        onTap: onSelected,
        borderRadius: BorderRadius.circular(AppRadius.sm),
        child: SizedBox(
          height: 40.0,
          child: Center(
            child: Text(
              sizeLabel,
              style: AppTypography.labelCaps.copyWith(color: textColor),
            ),
          ),
        ),
      ),
    );
  }
}
```
