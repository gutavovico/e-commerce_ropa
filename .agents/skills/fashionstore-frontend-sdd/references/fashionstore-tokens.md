# FASHION STORE — Design System Tokens & Mathematical Core System
**Versión:** 1.0.0 Production  
**Tipo:** Sistema de Tokens Normativos Multiplataforma (Web Tailwind + Mobile Flutter)  
**Tipografía Raíz:** Outfit (Google Fonts)  
**Regla de Oro:** Sustitución global de la nomenclatura previa "AURA STUDIO" por **FASHION STORE**.

---

## 1. Principios Rectores del Sistema de Diseño

El diseño de **FASHION STORE** no es meramente decorativo; es una estructura matemática y arquitectónica concebida para resaltar el textil, la silueta y la experiencia omnicanal de alta costura.

1. **Minimal:** Claridad sin ornamentos superfluos. El fondo blanco de galería y los contornos finos ceden todo el protagonismo a la fotografía editorial, el drapeado textil y los acabados artesanales.
2. **Premium:** Resonancia táctil en cada interacción digital. Las microanimaciones emulan el peso del metal pulido, el chasquido del herraje de latón y el deslizamiento de la seda pura.
3. **Consistent:** Integridad geométrica matemática. La escala de espaciado en potencias de 2 gobierna todo el layout sin excepción ni desviaciones arbitrarias.
4. **Accessible:** Utilidad sin fricción. Contraste WCAG 2.1 AAA en tipografía de lectura, soporte de lectores de pantalla y accesibilidad táctil estricta.
5. **Responsive:** Refinamiento adaptativo fluido entre monitores de escritorio (1440px+), tabletas y compras móviles en mano sin pérdida estética.
6. **Reusable:** Primitivas atómicas desacopladas que separan la presentación del estado de negocio, acelerando el desarrollo de casos de uso.
7. **Content-Focused:** La interfaz funciona como el marco neutro de una galería de arte contemporáneo: soporte limpio para la exhibición de prendas y experiencias inmersivas (Vestidor AR).

---

## 2. Paleta Cromática y Distribución Tonal

### 2.1 Tokens Semánticos de Superficie y Marca (Material 3 / Tailored)

| Token Name | HEX | Uso Normativo en FASHION STORE |
|---|---|---|
| `primary` | `#000000` | Botones de acción principal, tipografía de cabeceras, anclas arquitectónicas |
| `on-primary` | `#FFFFFF` | Texto y glifos sobre superficies primarias oscuras |
| `primary-container` | `#1B1C1D` | Paneles de acento sobrio, tarjetas oscuras destacadas |
| `on-primary-container` | `#848485` | Subtítulos y metadatos dentro de contenedores primarios |
| `primary-fixed` | `#E3E2E3` | Fondos de interacción fija, botones secundarios |
| `primary-fixed-dim` | `#C7C6C7` | Estados hover de elementos fijos |
| `secondary` | `#675D4E` | Tonalidad camel/cashmere para acentos textiles y etiquetas de lujo |
| `on-secondary` | `#FFFFFF` | Texto sobre elementos camel oscuro |
| `secondary-container` | `#ECDECB` | Badges de colección cápsula, píldoras de edición limitada |
| `on-secondary-container` | `#6B6152` | Tipografía de alta legibilidad sobre contenedores camel claros |
| `secondary-fixed` | `#EFE0CE` | Fondos destacados de materialidad textil |
| `secondary-fixed-dim` | `#D2C4B3` | Bordes activos de selección de colección |
| `tertiary` | `#000000` | Acentos complementarios de contraste |
| `tertiary-container` | `#161C21` | Contenedores de interfaz editorial profunda |
| `on-tertiary-container` | `#7E848B` | Textos secundarios en contenedores terciarios |
| `background` | `#F9F9FB` | Fondo general de la aplicación web y móvil |
| `on-background` | `#1A1C1D` | Color de texto principal sobre fondo general |
| `surface` | `#F9F9FB` | Superficie base de lectura |
| `on-surface` | `#1A1C1D` | Texto general de lectura, etiquetas de formulario |
| `surface-variant` | `#E2E2E4` | Separadores de sección, campos de entrada deshabilitados |
| `on-surface-variant` | `#45474A` | Texto secundario, descripciones de producto, breadcrumbs |
| `surface-dim` | `#D9DADC` | Fondos tenues para estados inactivos |
| `surface-bright` | `#F9F9FB` | Fondos elevados iluminados |
| `surface-container-lowest` | `#FFFFFF` | Tarjetas de producto, modales, menú flyout, drawer de carrito |
| `surface-container-low` | `#F3F3F5` | Fondos de tablas, selectores de talla |
| `surface-container` | `#EDEEF0` | Píldoras de filtro en reposo, insignias de estado |
| `surface-container-high` | `#E8E8EA` | Fondos de preview en hover |
| `surface-container-highest` | `#E2E2E4` | Bordes de tarjetas en reposo, divisores sutiles |
| `outline` | `#75777A` | Bordes estándar, iconos secundarios |
| `outline-variant` | `#C5C6C9` | Líneas de división de tabla, bordes ultra-finos |
| `error` | `#BA1A1A` | Notificación de error crítico, alerta de stock agotado |
| `on-error` | `#FFFFFF` | Texto sobre badges de error |
| `error-container` | `#FFDAD6` | Fondos de alertas de fallo de validación o pasarela |
| `on-error-container` | `#93000A` | Texto enfático de error |

---

### 2.2 Escala Primaria — Deep Obsidian & Slate (10 Pasos)

| Paso | Token HEX | Luminancia | Uso Específico |
|---|---|---|---|
| `primary-50` | `#F6F7F9` | Ultra-claro | Fondos de muestras, hover de celdas |
| `primary-100` | `#ECEEF2` | Muy claro | Bordes tenues de elementos interactivos |
| `primary-200` | `#D5D8E1` | Claro | Líneas de estructura secundaria |
| `primary-300` | `#B0B6C5` | Medio-bajo | Iconografía inactiva |
| `primary-400` | `#848DA3` | Medio | Metadatos editoriales |
| `primary-500` | `#626C84` | Base fría | Iconos de acción secundaria |
| `primary-600` | `#4B5368` | Intenso | Texto secundario con alto contraste |
| `primary-700` | `#383E4F` | Oscuro | Botones secundarios con texto blanco |
| `primary-800` | `#242833` | Muy oscuro | Encabezados de tablas |
| `primary-900` | `#0F1116` | Obsidian | Negro de máxima pureza, tipografía H1-H6 |

---

### 2.3 Escala Secundaria — Champagne & Camel (10 Pasos)

Evoca la paleta cromática de lanas crudas, vicuña, seda silvestre y cuero curtido:

| Paso | Token HEX | Uso Específico |
|---|---|---|
| `secondary-50` | `#FBF9F5` | Fondo cálido de cápsulas editoriales |
| `secondary-100` | `#F5EFE6` | Tarjetas de recomendación IA y probador virtual |
| `secondary-200` | `#E9DCCB` | Borde de tarjetas seleccionadas |
| `secondary-300` | `#D8C3A7` | Acentos de color en selectores de muestra |
| `secondary-400` | `#C5A782` | Píldoras de temporada y lookbook |
| `secondary-500` | `#AD8C63` | Tono insignia Camel FashionStore |
| `secondary-600` | `#8E714C` | Texto camel en fondos claros |
| `secondary-700` | `#6F5739` | Encabezados de colección otoño/invierno |
| `secondary-800` | `#503E28` | Acentos oscuros sobre superficies champagne |
| `secondary-900` | `#332719` | Tipografía de lujo para marcas de agua y monogramas |

---

### 2.4 Escala de Neutros Arquitectónicos (12 Pasos)

| Paso | Token HEX | Aplicación en Layout |
|---|---|---|
| `neutral-0` | `#FFFFFF` | Lienzo blanco museo, tarjeta de producto en reposo |
| `neutral-50` | `#FAFAFA` | Fondo alterno de listas |
| `neutral-100` | `#F4F4F5` | Fondos de inputs de texto deshabilitados |
| `neutral-200` | `#E4E4E7` | **Línea Hairline estándar** (divisores de 1px) |
| `neutral-300` | `#D4D4D8` | **Borde en Hover** de tarjetas e inputs |
| `neutral-400` | `#A1A1AA` | Placeholder de inputs |
| `neutral-500` | `#71717A` | Texto de pie de foto y leyendas legales |
| `neutral-600` | `#52525B` | Cuerpo de texto descriptivo |
| `neutral-700` | `#3F3F46` | Etiquetas de formulario en reposo |
| `neutral-800` | `#27272A` | Títulos secundarios |
| `neutral-900` | `#18181B` | **Borde Activo / Focus** de inputs y selecciones |
| `neutral-950` | `#09090B` | Contraste máximo de texto |

---

### 2.5 Estados Cromáticos Semánticos

Diseñados con discreción para alertar sin romper la atmósfera de sofisticación:

| Semántica | Nivel | HEX | Rol |
|---|---|---|---|
| **Success** | `bg` | `#F0FDF4` | Fondo de notificación de compra completada / reserva confirmada |
| | `light` | `#86EFAC` | Borde de confirmación suave |
| | `default` | `#16A34A` | Icono de stock disponible y éxito |
| | `dark` | `#14532D` | Texto de confirmación |
| **Warning** | `bg` | `#FFFBEB` | Alerta de "Últimas unidades en sucursal" |
| | `light` | `#FCD34D` | Borde de aviso |
| | `default` | `#D97706` | Píldora de stock bajo |
| | `dark` | `#78350F` | Texto de advertencia |
| **Error** | `bg` | `#FEF2F2` | Error en pago Stripe / Prenda agotada |
| | `light` | `#FCA5A5` | Borde de input inválido |
| | `default` | `#DC2626` | Icono de error crítico |
| | `dark` | `#7F1D1D` | Mensaje de error de validación |
| **Info** | `bg` | `#F0F9FF` | Banner de envío gratuito o probador AR activo |
| | `light` | `#7DD3FC` | Borde de llamada informativa |
| | `default` | `#0284C7` | Icono de información y guía de tallas |
| | `dark` | `#0C4A6E` | Texto informativo |

---

## 3. Sistema Tipográfico Arquitectónico (Outfit)

La tipografía oficial de FASHION STORE es **Outfit** (Sans-Serif Geométrica Moderna), configurada con kerning óptico y tracking ajustado matemáticamente.

| Token Name | Weight | Size (px / rem) | Line Height | Letter Spacing | Caso de Uso en FASHION STORE |
|---|---|---|---|---|---|
| `display-hero` | Light 300 | 72px / 4.5rem | 80px / 5.0rem | `-0.03em` | Hero de campañas y portadas de lookbook |
| `display-hero-mobile`| Light 300 | 40px / 2.5rem | 48px / 3.0rem | `-0.02em` | Hero editorial en pantallas móviles |
| `display-xl` | Bold 700 | 64px / 4.0rem | 72px / 4.5rem | `-0.02em` | Título mayor de pasarela o cápsula |
| `display-l` | Bold 700 | 48px / 3.0rem | 56px / 3.5rem | `-0.02em` | Encabezados de colección de temporada |
| `headline-lg` | Light 300 | 48px / 3.0rem | 56px / 3.5rem | `-0.02em` | Títulos principales de páginas |
| `headline-lg-mobile`| Regular 400 | 32px / 2.0rem | 40px / 2.5rem | `-0.01em` | Títulos de página en aplicación móvil |
| `display-m` | SemiBold 600| 40px / 2.5rem | 48px / 3.0rem | `-0.01em` | Destacados de líneas exclusivas |
| `headline-md` (H1) | Regular/Med 500| 32px / 2.0rem | 40px / 2.5rem | `-0.01em` | Nombre de producto en PDP, títulos de sección |
| `headline-h2` (H2) | Medium 500 | 28px / 1.75rem | 36px / 2.25rem | `-0.01em` | Título de modales, resumen de checkout |
| `headline-sm` (H3) | Medium 500 | 24px / 1.5rem | 32px / 2.0rem | `-0.005em` | Título de tarjetas destacadas, sucursales |
| `title-lg` (H4) | Medium 500 | 20px / 1.25rem | 28px / 1.75rem | `0em` | Subtítulos de módulo, precio destacado |
| `title-md` (H5/H6) | Medium 500 | 16px / 1.0rem | 24px / 1.5rem | `0.01em` | Títulos de campos, pestañas de navegación |
| `body-lg` | Light/Reg 400 | 18px / 1.125rem| 28px / 1.75rem | `0em` | Párrafo introductorio de producto |
| `body-md` | Regular 400 | 14px / 0.875rem| 22px / 1.375rem| `0.01em` | Cuerpo de texto general, especificaciones |
| `body-sm` | Regular 400 | 12px / 0.75rem | 18px / 1.125rem| `0.01em` | Instrucciones de cuidado, texto secundario |
| `label-large` | Medium 500 | 14px / 0.875rem| 20px / 1.25rem | `0.02em` | Texto de botones primarios ("AÑADIR A BOLSA") |
| `label-sm` | Medium 500 | 12px / 0.75rem | 16px / 1.0rem | `0.02em` | Píldoras de talla (XS, S, M, L, XL) |
| `label-caps` | SemiBold 600| 11px / 0.6875rem| 16px / 1.0rem | `0.12em` | Badges en mayúsculas, tracking ultra-expandido |
| `caption-lg` | Regular 400 | 12px / 0.75rem | 16px / 1.0rem | `0em` | Datos de modelo ("Modelo mide 181cm...") |
| `caption-sm` | Regular 400 | 10px / 0.625rem| 14px / 0.875rem| `0em` | Leyendas de pie legal, IVA incluido |

---

## 4. Cadencia de Espaciado Estricto (Base-2 Power Grid)

FASHION STORE elimina totalmente los valores de margen y relleno aleatorios. Todo espaciado responde a **potencias de 2**.

| Token Name | Token Alias | Valor (px) | Valor (rem) | Caso de Uso Normativo en FASHION STORE |
|---|---|---|---|---|
| `space-1` | `space-2px` | 2px | 0.125rem | Hairline borders, microanillos de selector de color, gaps mínimos |
| `space-2` | `space-4px` | 4px | 0.25rem | Padding vertical de píldoras compactas, separación icono-texto |
| `space-3` | `space-8px` | 8px | 0.5rem | Padding vertical de botones, separación entre título y precio |
| `space-4` | `space-16px`| 16px | 1.0rem | Padding interno de tarjetas, separación entre píldoras, margen móvil |
| `space-5` | `space-32px`| 32px | 2.0rem | Separación entre bloques, gutter de cuadrícula desktop, pad de botón |
| `space-6` | `space-64px`| 64px | 4.0rem | División rítmica de secciones, margen de viewport desktop |
| `space-7` | `space-128px`| 128px | 8.0rem | Espacio de respiración para separadores editoriales y lookbooks |

### Restricción Dura (Hard Constraint): Prohibición de Valores Arbitrarios
Queda terminantemente prohibido el uso de clases o valores arbitrarios no binarios.
> **Valores Prohibidos:** `3px, 5px, 6px, 10px, 12px, 20px, 24px, 28px, 40px, 48px, 56px`.  
> Todo componente o layout que introduzca `p-[10px]` o `EdgeInsets.all(12)` viola la especificación del sistema.

---

## 5. Cadencia Vertical de Layout (4-Part Vertical Reference Cadence)

Referencia exclusiva para el ritmo y secuencia vertical de las páginas principales (no es una cuadrícula de columnas horizontal). Divide el alto del viewport en 4 zonas simétricas con ratio **1 : 1 : 1 : 1 (25% cada zona)**:

```
┌─────────────────────────────────────────────────────────────┐
│  Zona 01 (25%) — Header & Hero                              │
│  Declaración de marca, barra global fija, campaña principal │
├─────────────────────────────────────────────────────────────┤
│  Zona 02 (25%) — Colecciones & Catálogo                     │
│  Navegación de categorías, filtros textiles, prendas clave  │
├─────────────────────────────────────────────────────────────┤
│  Zona 03 (25%) — Lookbook & Experiencia Editorial           │
│  Inmersión en artesanía, historias de taller, probador AR   │
├─────────────────────────────────────────────────────────────┤
│  Zona 04 (25%) — Confianza, Asistencia & Footer             │
│  Certificaciones, citas de probador, atención, marco legal  │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Geometría: Radios de Borde (Border Radii)

| Token Name | Valor | Tailwind Class | Flutter Equivalent | Casos de Uso |
|---|---|---|---|---|
| `radius-xs` | 2px | `rounded-[2px]` | `BorderRadius.circular(2)` | Checkboxes, tags micro |
| `radius-sm` | 4px | `rounded` / `rounded-sm` | `BorderRadius.circular(4)` | Botones, inputs de texto, píldoras |
| `radius-md` | 8px | `rounded-lg` (8px) | `BorderRadius.circular(8)` | Tarjetas de producto, dropdowns |
| `radius-lg` | 16px | `rounded-xl` (16px) | `BorderRadius.circular(16)` | Contenedores grandes, vistas lookbook |
| `radius-xl` | 32px | `rounded-2xl` (32px)| `BorderRadius.circular(32)` | Drawers de carrito, modales |
| `radius-full`| 9999px| `rounded-full` | `BorderRadius.circular(9999)`| Píldoras de talla, badges circulares |

---

## 7. Elevación y Profundidad Óptica (Elevation Matrix)

FASHION STORE rechaza las sombras pesadas y artificiales. Se utiliza tensión superficial luminosa y difusión suave:

| Nivel | Box Shadow CSS | Opacidad Difusa | Caso de Uso |
|---|---|---|---|
| `elevation-0` | `none` | 0% | Superficies base, secciones delimitadas por líneas hairline |
| `elevation-1` | `0 1px 2px rgba(0,0,0,0.04)` | 4% | Tarjetas de producto en reposo, botones sobrios, muestras |
| `elevation-2` | `0 4px 8px -2px rgba(0,0,0,0.06), 0 2px 4px -2px rgba(0,0,0,0.04)` | 6% | Estado hover de tarjetas, barra de búsqueda enfocada |
| `elevation-3` | `0 12px 24px -4px rgba(0,0,0,0.08)` | 8% | Menús desplegables, vista rápida (Quick-view), preview flotante |
| `elevation-4` | `0 24px 48px -12px rgba(0,0,0,0.12)` | 12% | Drawer deslizante de bolsa de compras, modal de vestidor AR |

---

## 8. Arquitectura de Bordes y Trazo Lineal

### 8.1 Grosores de Borde
* **1px Hairline (`border`):** Divisor estándar de secciones, contorno de tarjetas en reposo y celdas de tabla.
* **2px Emphasis (`border-2`):** Pestaña de navegación activa, indicador de foco accesible, selector de talla seleccionado.
* **4px Accent Marker (`border-4`):** Marcador editorial vertical, bloque destacado de lookbook.

### 8.2 Estilos de Trazo
* **Solid Primary:** Estructura general, botones, tarjetas, inputs.
* **Dashed Secondary:** Guía de medidas corporales para vestidor AR, zona de drag & drop de imágenes en administración.

### 8.3 Estados Tonales del Trazo
* **Reposado:** `neutral-200` (`#E4E4E7`)
* **Hover:** `neutral-300` (`#D4D4D8`)
* **Activo / Foco:** `neutral-900` (`#18181B`)

---

## 9. Configuración Exportable para Tailwind CSS (`tailwind.config.js`)

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "primary": "#000000",
        "on-primary": "#ffffff",
        "primary-container": "#1b1c1d",
        "on-primary-container": "#848485",
        "primary-fixed": "#e3e2e3",
        "primary-fixed-dim": "#c7c6c7",
        "on-primary-fixed": "#1b1c1d",
        "on-primary-fixed-variant": "#464748",
        
        "secondary": "#675d4e",
        "on-secondary": "#ffffff",
        "secondary-container": "#ecdecb",
        "on-secondary-container": "#6b6152",
        "secondary-fixed": "#efe0ce",
        "secondary-fixed-dim": "#d2c4b3",
        "on-secondary-fixed": "#221a0f",
        "on-secondary-fixed-variant": "#4f4538",

        "tertiary": "#000000",
        "on-tertiary": "#ffffff",
        "tertiary-container": "#161c21",
        "on-tertiary-container": "#7e848b",
        "tertiary-fixed": "#dde3ea",
        "tertiary-fixed-dim": "#c1c7ce",
        "on-tertiary-fixed": "#161c21",
        "on-tertiary-fixed-variant": "#41474d",

        "background": "#f9f9fb",
        "on-background": "#1a1c1d",
        "surface": "#f9f9fb",
        "on-surface": "#1a1c1d",
        "surface-variant": "#e2e2e4",
        "on-surface-variant": "#45474a",
        "surface-dim": "#d9dadc",
        "surface-bright": "#f9f9fb",
        "surface-container-lowest": "#ffffff",
        "surface-container-low": "#f3f3f5",
        "surface-container": "#edeef0",
        "surface-container-high": "#e8e8ea",
        "surface-container-highest": "#e2e2e4",
        "surface-tint": "#5e5e5f",
        "inverse-surface": "#2f3132",
        "inverse-on-surface": "#f0f0f2",
        "inverse-primary": "#c7c6c7",

        "outline": "#75777a",
        "outline-variant": "#c5c6c9",

        "error": "#ba1a1a",
        "on-error": "#ffffff",
        "error-container": "#ffdad6",
        "on-error-container": "#93000a",

        // Escalas específicas de FASHION STORE
        slate: {
          50: "#F6F7F9",
          100: "#ECEEF2",
          200: "#D5D8E1",
          300: "#B0B6C5",
          400: "#848DA3",
          500: "#626C84",
          600: "#4B5368",
          700: "#383E4F",
          800: "#242833",
          900: "#0F1116",
        },
        camel: {
          50: "#FBF9F5",
          100: "#F5EFE6",
          200: "#E9DCCB",
          300: "#D8C3A7",
          400: "#C5A782",
          500: "#AD8C63",
          600: "#8E714C",
          700: "#6F5739",
          800: "#503E28",
          900: "#332719",
        },
        neutral: {
          0: "#FFFFFF",
          50: "#FAFAFA",
          100: "#F4F4F5",
          200: "#E4E4E7",
          300: "#D4D4D8",
          400: "#A1A1AA",
          500: "#71717A",
          600: "#52525B",
          700: "#3F3F46",
          800: "#27272A",
          900: "#18181B",
          950: "#09090B",
        }
      },
      spacing: {
        "space-1": "2px",
        "space-2": "4px",
        "space-3": "8px",
        "space-4": "16px",
        "space-5": "32px",
        "space-6": "64px",
        "space-7": "128px",
      },
      borderRadius: {
        "xs": "2px",
        "sm": "4px",
        "DEFAULT": "4px",
        "md": "8px",
        "lg": "16px",
        "xl": "32px",
        "full": "9999px",
      },
      boxShadow: {
        "elevation-0": "none",
        "elevation-1": "0 1px 2px rgba(0,0,0,0.04)",
        "elevation-2": "0 4px 8px -2px rgba(0,0,0,0.06), 0 2px 4px -2px rgba(0,0,0,0.04)",
        "elevation-3": "0 12px 24px -4px rgba(0,0,0,0.08)",
        "elevation-4": "0 24px 48px -12px rgba(0,0,0,0.12)",
      },
      fontFamily: {
        sans: ["Outfit", "sans-serif"],
        outfit: ["Outfit", "sans-serif"],
      },
      fontSize: {
        "display-hero": ["72px", { lineHeight: "80px", letterSpacing: "-0.03em", fontWeight: "300" }],
        "display-hero-mobile": ["40px", { lineHeight: "48px", letterSpacing: "-0.02em", fontWeight: "300" }],
        "display-xl": ["64px", { lineHeight: "72px", letterSpacing: "-0.02em", fontWeight: "700" }],
        "display-l": ["48px", { lineHeight: "56px", letterSpacing: "-0.02em", fontWeight: "700" }],
        "display-m": ["40px", { lineHeight: "48px", letterSpacing: "-0.01em", fontWeight: "600" }],
        "headline-lg": ["48px", { lineHeight: "56px", letterSpacing: "-0.02em", fontWeight: "300" }],
        "headline-lg-mobile": ["32px", { lineHeight: "40px", letterSpacing: "-0.01em", fontWeight: "400" }],
        "headline-md": ["32px", { lineHeight: "40px", letterSpacing: "-0.01em", fontWeight: "400" }],
        "headline-sm": ["24px", { lineHeight: "32px", letterSpacing: "-0.005em", fontWeight: "500" }],
        "title-lg": ["20px", { lineHeight: "28px", letterSpacing: "0em", fontWeight: "500" }],
        "title-md": ["16px", { lineHeight: "24px", letterSpacing: "0.01em", fontWeight: "500" }],
        "body-lg": ["18px", { lineHeight: "28px", letterSpacing: "0em", fontWeight: "300" }],
        "body-md": ["14px", { lineHeight: "22px", letterSpacing: "0.01em", fontWeight: "400" }],
        "body-sm": ["12px", { lineHeight: "18px", letterSpacing: "0.01em", fontWeight: "400" }],
        "label-caps": ["11px", { lineHeight: "16px", letterSpacing: "0.12em", fontWeight: "600" }],
        "label-sm": ["12px", { lineHeight: "16px", letterSpacing: "0.02em", fontWeight: "500" }],
      }
    }
  }
};
```
