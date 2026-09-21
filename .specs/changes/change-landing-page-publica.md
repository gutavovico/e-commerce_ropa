# Propuesta de Cambio Técnico: Landing Page Pública (Showcase Dashboard)

**ID del Cambio:** `change-landing-page-publica`  
**Módulo:** `public` (Presentación Pública y Transversal)  
**Alcance:** Exclusivamente Frontend Web (`Ec-frontend` - Angular 19+)  
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo (PUDS)  
**Fuente de Verdad Visual:** Prototipo Editorial de Alta Costura Adjunto  
**Estado:** 🟡 En Espera de Aprobación Humana (Gate Estricto de Especificación)  
**Fecha:** 2026-09-20  

---

## 1. Especificación Formal (`spec`)

### 1.1 Propósito y Alcance del Cambio
Diseñar y planificar la pantalla principal pública (Landing Page / Showcase Dashboard) que recibirá a todos los visitantes que ingresen a la aplicación web de **FASHION STORE** antes de autenticarse o registrarse.

La landing page sintetiza visualmente la propuesta de valor omnicanal de la firma:
- Fusión de sastrería tradicional artesanal (Biella y Lyon) con modelado predictivo y visión artificial.
- Simulador interactivo de **Vestidor Virtual con IA · Fitting Room 3D** con análisis de tensión textil y drapeado físico.
- Asistente de estilismo de alta costura **Atelier AI Stylist · Concierge Digital 24/7**.
- Arquitectura de servicios exclusivos: Trazabilidad digital inmutable, entrega guante blanco y percheros inteligentes sincronizados.
- Directorio de **Boutiques Flagship** internacionales (Madrid, París, Milán, Barcelona) con gestión de citas presenciales.

### 1.2 Restricciones de Dominio y No-Afectación
- **Backend (`Ec-backend`)**: CERO cambios. No requiere creación ni modificación de endpoints, esquemas Pydantic ni migraciones de base de datos.
- **Mobile (`Ec-mobile`)**: CERO cambios. La aplicación Flutter conserva su flujo directo a `PantallaLogin`.
- **Frontend (`Ec-frontend`)**: Ubicación arquitectónica desacoplada en `src/app/public/landing/`, fuera de los módulos autenticados (`modules/`).

---

### 1.3 Desglose Anatómico y Visual por Secciones (Fiel a la Imagen)

#### 1.3.1 Barra de Navegación Global Adhesiva (`Header / Navbar`)
- **Posición:** `sticky top-0 z-50 backdrop-blur-md bg-white/90 border-b border-neutral-200`.
- **Identidad de Marca:** Logotipo textual `FASHION STORE` (sans-serif mayúscula con tracking expandido).
- **Enlaces Centrales (Smooth Scroll):**
  - `FUNCIONALIDADES` -> Desplazamiento suave a `#funcionalidades`.
  - `VESTIDOR VIRTUAL IA` -> Desplazamiento suave a `#vestidor-virtual`.
  - `SUCURSALES` -> Desplazamiento suave a `#sucursales`.
- **Accesos de Autenticación (Extremo Derecho):**
  - Enlace de texto: `INICIAR SESIÓN` -> Navegación `routerLink="/login"`.
  - Botón primario: `REGISTRAR` (cápsula/pill negra con texto blanco en negrita) -> Navegación `routerLink="/registro"`.

---

#### 1.3.2 Sección Hero (`#hero`)
- **Cintillo Superior de Metadatos:**
  - Izquierda: `MANIFIESTO DIGITAL — CONFECCIÓN V1.0 · SALAMANCA LA`
  - Centro-Derecha: Icono de ubicación + `Boutique Privada Serrano · Madrid`
  - Derecha: Icono calendario + `Apertura de la Nueva Galería`
- **Tipografía y Título H1:**
  - Texto: `El Futuro de la Alta Costura y la Sastrería Digital`
  - Estilo híbrido de lujo: *"Alta Costura"* en tipografía Serif itálica (`Playfair Display`, `italic font-serif`), el resto en Sans geométrica (`Outfit`).
- **Párrafo Editorial:**
  > *"Fashion Store redefine la experiencia de compra de lujo fusionando la maestría de talleres artesanales de Biella y Lyon con visión artificial predictiva. Calce milimétrico, simulación háptica y un vestidor inteligente al servicio de su armario personal."*
- **Botones de Conversión:**
  - Botón Primario: `ARMAR OUTFIT ↗` (negro sólido, píldora con flecha oblicua, enlaza a `/catalogo`).
  - Botón Secundario: `AGENDAR SESIÓN` (blanco con borde fino neutro, scroll a `#sucursales`).
  - Enlace Terciario: `CATÁLOGO A MEDIDA` (con icono de percha/compás).
- **Métricas de Precisión Técnica (Grid 3 columnas):**
  - **`0.8 mm`** | `PRECISIÓN BIOMÉTRICA`
  - **`50 piezas`** | `EDICIÓN CÁPSULA LIMITADA`
  - **`100%`** | `TRAZABILIDAD EN BLOCKCHAIN`
- **Tarjeta Visual Editorial (Flagship Madrid):**
  - Fotografía vertical de la boutique de Serrano (iluminación cálida, lámpara escultural, perchero de prendas atelier, mostrador con atención personalizada).
  - Tarjeta superpuesta inferior:
    - Rótulo: `ATELIER SALAMANCA`
    - Título: `Boutique Privada Serrano · Madrid`
    - Subtítulo: `Prueba presencial con validación digital 3D`
    - Icono de calendario interactivo para reserva de cita.

---

#### 1.3.3 Sección Vestidor Virtual con IA (`#vestidor-virtual`)
- **Eyebrow:** `✦ PROBADOR BIOMÉTRICO 3D Y HÁPTICO`
- **Título de Sección:** `Vestidor Virtual con IA · Fitting Room 3D` (*"Fitting Room 3D"* en serif itálica).
- **Descripción:** Explicación del motor de renderizado físico para lanas Super 150s y seda 22 momme con elongación háptica.
- **Espacio de Trabajo / Showcase Interactivo:**
  - **Columna Izquierda (Panel de Control y Métricas de Tensión):**
    - `PASO 1: SELECCIONE UNA PRENDA DE DEMOSTRACIÓN`
    - Selector interactivo de 3 prendas demo (gestionado con Signals de Angular):
      1. *SASTRERÍA* | **Blazer Lana Camel** | *Lana Super 150s* (Seleccionado / Borde activo)
      2. *NOCHE* | **Vestido Plisado** | *Seda de Morera*
      3. *ATELIER* | **Pantalón Palazzo** | *Cashmere Puro*
    - Bloque **Mapa de Tensión Textil** con badge `Ajuste Óptimo 98.4%`:
      - Barra 1: *Hombros & Espalda* -> `Holgura exacta (0.5 cm)`
      - Barra 2: *Pretina & Cadera* -> `Caída fluida natural`
    - Caja de garantía artesanal:
      > *"Algoritmo entrenado con 120.000 biotipos femeninos; validado por maestros sastres en París y Biella."*
    - Botón de Conversión: `INICIAR SESIÓN Y PROBAR MI PRENDA` (negro sólido, lleva a `/login`).
    - Pie técnico: *"La versión completa permite calibración por escaneo lidar personal o medidas antropométricas ISO 8559."*
  - **Columna Derecha (Visor de Taller 3D Simulado):**
    - Escena de taller atelier con maniquí sastre, drapeado de prenda y herramientas artesanales.
    - Bocadillo / Tooltip de diagnóstico en tiempo real:
      `"Conformidad de busto: exacto · Pliegue según torsión"`
    - Barra inferior de controles hápticos:
      - Botones: `VISTA DORSAL`, `ROTACIÓN 360°` (activo con píldora oscura), `COLISIÓN 4D`, `EN VIVO 60 FPS`.
      - Métrica lateral: `Tensión de fijación: 0.12 N/mm`.

---

#### 1.3.4 Sección Asesoría de Estilismo IA (`#concierge-ia`)
- **Eyebrow:** `ASESORÍA EDITORIAL EN TIEMPO REAL`
- **Columna Izquierda (Propuesta Editorial):**
  - Título: `Atelier AI Stylist · Concierge Digital 24/7` (*"Concierge Digital 24/7"* en serif itálica).
  - Texto descriptivo: Asesoría de protocolo para eventos internacionales y sincronización con estilistas en tienda física.
  - Lista de beneficios con iconos circulares:
    1. **Coherencia Predictiva:** Análisis de climatología y protocolo según la geolocalización de cada evento.
    2. **Conexión con Percheros Físicos:** Apartado directo y prueba humana en tienda en < 4 horas en Madrid.
  - Enlace: `INICIAR CONVERSACIÓN DE PRUEBA ↗`
- **Columna Derecha (Simulación de Chat en Vivo):**
  - Encabezado: Avatar `FS`, `Atelier Concierge AI`, `Conectado con Suite Privada Madrid`, badge `ATELIER EN VIVO`.
  - Burbuja Usuario (Fondo negro):
    > *"¿Qué prendas combinan mejor con mi blazer camel de doble botonadura para una gala de noche en el Palacio Real de la Almudaina?"*
  - Burbuja Concierge AI (Fondo gris neutro claro):
    > *"Para el clima de noviembre en Palma (temp. estimada 17°C), la sobriedad formal sugiere atenuar la energía con una seda de contraste en tonos oscuros o brillo sutil. Le sugiero:"*
    - Mini-card 1: Thumbnail + `VESTIDO DE GALA NOCHE` + `Vestido de Seda Lurex con Cortes Asimétricos` + `875 €` + botón `Ver en vestidor`.
    - Mini-card 2: Thumbnail + `COMPLEMENTO DE ALTA COSTURA` + `Pantalón Palazzo Lana Super 150s` + `550 €` + botón `Disponible en boutique`.
  - Barra de entrada de texto simulada:
    `"¿Tienen disponibilidad de la talla 38 para prueba en Madrid este viernes?"` + botón de enviar con flecha.

---

#### 1.3.5 Sección Privilegios del Miembro Atelier (`#funcionalidades`)
- **Eyebrow:** `ARQUITECTURA DE SERVICIO`
- **Encabezado:** `Privilegios del Miembro Atelier` (*"del Miembro Atelier"* en serif itálica).
- **Subtexto:** Compromiso de infraestructura física de excelencia, taller propio en Madrid y boutiques insignia.
- **Grilla de 3 Tarjetas de Servicio:**
  1. **Tarjeta 1:**
     - Icono: Chip / Pasaporte digital.
     - Categoría: `PASAPORTE DIGITAL`
     - Título: `Trazabilidad Digital Inmutable`
     - Detalle: Certificación de procedencia de cada hilatura de Biella hasta la costura final con registro blockchain.
     - Enlace: `VER CERTIFICACIÓN OFICIAL →`
  2. **Tarjeta 2:**
     - Icono: Transporte guante blanco.
     - Categoría: `SERVICIO DE GUANTE`
     - Título: `Citas & Entrega Guante Blanco`
     - Detalle: Entrega en mano de prendas planchadas e indeformables en Madrid, Barcelona, París y Milán con sastre a domicilio.
     - Enlace: `RED DE CIUDADES →`
  3. **Tarjeta 3:**
     - Icono: Tienda física de lujo.
     - Categoría: `EXPERIENCIA 360°`
     - Título: `Sincronización Omnicanal`
     - Detalle: Prendas guardadas en el vestidor digital listas físicamente en el perchero de la boutique antes de su llegada.
     - Enlace: `AGENDAR LA GALERÍA →`

---

#### 1.3.6 Sección Nuestras Sucursales (`#sucursales`)
- **Eyebrow:** `PRESENCIA FÍSICA GLOBAL`
- **Encabezado:** `Nuestras Sucursales · Boutiques Flagship` (*"Boutiques Flagship"* en serif itálica).
- **Subtexto:** Espacios de experimentación sensorial donde los probadores biométricos conviven con los consultores de moda.
- **Grilla de 4 Boutiques Flagship:**
  1. **Madrid · Serrano** (Flagship Principal):
     - Rótulo: `FLAGSHIP PRINCIPAL` | Badge verde: `ABIERTO`
     - Dirección: `Calle de Serrano 48, Salamanca`
     - Horario: `Lun - Sáb: 10:00 - 20:30`
     - Especialidad: `Vestidor 3D Háptico · Sastrería Bespoke · Salón Privado VIP`
     - Botón negro: `AGENDAR CITA`
  2. **París · Saint-Honoré**:
     - Rótulo: `HAUTE COUTURE` | Badge verde: `ABIERTO`
     - Dirección: `22 Rue du Faubourg Saint-Honoré`
     - Horario: `Mar - Sáb: 10:30 - 19:30`
     - Especialidad: `Atelier de Alta Costura de Lyon · Archivo y Cursos Históricos`
     - Botón outline: `AGENDAR CITA`
  3. **Milán · Montenapoleone**:
     - Rótulo: `SASTRERÍA A MEDIDA` | Badge verde: `ABIERTO`
     - Dirección: `Via Montenapoleone 8b, Quadrilatero`
     - Horario: `Lun - Sáb: 10:00 - 19:30`
     - Especialidad: `Selección Biella Lanificio · Confección 2D/3D Express`
     - Botón outline: `AGENDAR CITA`
  4. **Barcelona · Gràcia**:
     - Rótulo: `ATELIER MEDITERRÁNEO` | Badge verde: `ABIERTO`
     - Dirección: `Passeig de Gràcia 74, Eixample`
     - Horario: `Lun - Sáb: 10:30 - 20:00`
     - Especialidad: `Consulado de Calzado a Medida · Terrazas Experienciales`
     - Botón outline: `AGENDAR CITA`

---

#### 1.3.7 Pie de Página Corporativo (`Footer`)
- **Fondo:** Gris ultra-claro / neutro museo (`bg-[#F9F9FB] border-t border-neutral-200`).
- **Columna 1:** Logotipo `FASHION STORE`, declaración de misión textil y sostenibilidad con IA, dirección de Sede Central (Calle de Serrano 48, Salamanca, Madrid).
- **Columna 2 (Manifiesto & Origen):** Enlaces a Código de Ética, Taller Artesanal en Biella, Seda de Morera de Lyon, Visión Artificial de Tejidos 2026, Guía de Cuidado.
- **Columna 3 (Soporte VIP):** Concierge, Guía de Medidas y Tallas, Cuidado de Tejidos Nobles, Envío en Embalaje Seguro, Cancelación de Reservas.
- **Barra Legal Inferior:** Copyright `© 2026 Fashion Store Flagship Digital. Todos los derechos reservados.` y enlaces a `Privacidad`, `Términos del Atelier`, `Directiva Transparente`.

---

### 1.4 Política de Navegación Interna (Desacoplamiento del botón 'INICIO' respecto a la Landing Page)
- **Problema Detectado:** Al asignarse `path: ''` a la `LandingPageComponent`, las cabeceras de navegación de las vistas internas y autenticadas (`/perfil`, `/buscar`, `/catalogo`) que contenían enlaces `routerLink="/"` provocaban que al pulsar `INICIO` o el logotipo `FASHION STORE`, el usuario fuera expulsado de su sesión activa y redirigido a la Landing Page pública de bienvenida.
- **Decisión Arquitectónica:**
  1. El botón `INICIO` y el logotipo dentro del ecosistema de navegación interno se desvinculan de la ruta raíz pública (`/`) y se enrutan a `/inicio`.
  2. En [app.routes.ts](file:///c:/Users/tonys/OneDrive/Documentos/contenido/SI2/Parcial1-Ecommerce/Ec-frontend/src/app/app.routes.ts), se define `{ path: 'inicio', redirectTo: 'catalogo', pathMatch: 'full' }`.
  3. Esto mantiene al usuario dentro de la galería de compra interna mientras se planifica y desarrolla el panel / dashboard de inicio autenticado ("función a implementar más adelante").
  4. Los hipervínculos de retorno contextual (como el botón "EXPLORAR PIEZAS" en el perfil de cliente) apuntan explícitamente a `/catalogo`.

---

## 2. Plan de Ejecución Secuencial (`plan`)

Una vez aprobada esta especificación, la ejecución se llevará a cabo en las siguientes fases ordenadas:

### Fase 1: Enrutamiento y Creación de Componente Base
- Crear el componente standalone `LandingPageComponent` en `Ec-frontend/src/app/public/landing/`.
- Reconfigurar la ruta vacía `path: ''` en [app.routes.ts](file:///c:/Users/tonys/OneDrive/Documentos/contenido/SI2/Parcial1-Ecommerce/Ec-frontend/src/app/app.routes.ts) para cargar perezosamente este componente con título de alta costura.

### Fase 2: Layout Base, Header Adhesivo y Footer
- Maquetar el Navbar sticky con efecto `backdrop-blur-md` y navegación por anclas.
- Maquetar el Footer completo con enlaces informativos y estructura multiciudad.

### Fase 3: Hero Section & Showcase de Boutique
- Maquetar la cabecera con el H1 estilizado (Serif + Sans), los botones de acción, las métricas técnicas de 0.8mm y la tarjeta visual del Atelier Madrid.

### Fase 4: Secciones de Interactividad (Vestidor 3D, Concierge AI, Privilegios, Sucursales)
- Desarrollar la sección del Vestidor 3D con selector reactivo de prendas basado en Signals (`selectedGarment`), mapa de tensión textil y canvas de previsualización.
- Maquetar la simulación de chat con Atelier Concierge AI con burbujas de usuario y sugerencias de producto.
- Desarrollar las tarjetas de arquitectura de servicio (Privilegios).
- Construir la cuadrícula de las 4 sucursales flagship con sus badges de estado y botones de cita.

### Fase 5: Smooth Scrolling, Verificación y Pruebas Unitarias
- Implementar la lógica de desplazamiento suave `scrollToSection(id: string)` con `ViewportScroller` / API nativa del DOM.
- Desarrollar la suite de pruebas unitarias en `landing.component.spec.ts`.
- Ejecutar compilación de producción con `npm run build` para asegurar cero advertencias y cumplimiento de budgets.

---

## 3. Lista de Tareas Atómicas (`tasks`)

- [x] **T1. Enrutamiento:** Reemplazar redirección en `path: ''` de `Ec-frontend/src/app/app.routes.ts` para renderizar `LandingPageComponent`.
- [x] **T2. Andamiaje del Componente:** Crear `landing.component.ts`, `landing.component.html` y `landing.component.scss` bajo `Ec-frontend/src/app/public/landing/`.
- [x] **T3. Header Navbar:** Maquetar barra de navegación fija con logo `FASHION STORE`, anclas `#funcionalidades`, `#vestidor-virtual`, `#sucursales`, y enlaces a `/login` y `/registro`.
- [x] **T4. Hero Section:** Maquetar título híbrido Serif/Sans, botones `ARMAR OUTFIT`, métricas `0.8mm` / `50 piezas` / `100%` y card de Boutique Serrano.
- [x] **T5. Sección Vestidor 3D:** Construir selector de prendas demo reactivo con Signals, barras de tensión textil (98.4%) y controles 3D simulados.
- [x] **T6. Sección Concierge AI:** Construir diálogo interactivo simulado con sugerencias de vestidos/pantalones y barra de consulta.
- [x] **T7. Sección Privilegios:** Construir tarjetas de Trazabilidad Digital, Entrega Guante Blanco y Sincronización Omnicanal.
- [x] **T8. Sección Sucursales:** Maquetar tarjetas de Madrid, París, Milán y Barcelona con badges de estado y botones de cita.
- [x] **T9. Footer Corporativo:** Maquetar pie de página con manifiesto, sedes, enlaces legales y copyright.
- [x] **T10. Smooth Scroll:** Implementar y vincular `scrollToSection()` para navegación fluida intra-página.
- [x] **T11. Pruebas Unitarias:** Crear `landing.component.spec.ts` verificando renderizado, routing y eventos de clic.
- [x] **T12. Build & Calidad:** Ejecutar `npm run build` en `Ec-frontend` y verificar ausencia de errores de TypeScript o CSS.
- [x] **T13. Desacoplamiento de Navegación Interna:** Modificar `INICIO` y el logotipo en las cabeceras internas (`buscar-productos.component.html`, `perfil.component.html`) hacia `/inicio` (redirigido a `/catalogo`), impidiendo que los usuarios autenticados sean expulsados a la landing page pública.

---

## 4. Puntos de Control y Verificación (`checkpoints`)

| ID | Criterio de Verificación | Método de Validación | Resultado Esperado |
|---|---|---|---|
| **CP-01** | Correspondencia Visual Exacta | Inspección visual en navegador (`localhost:4200`) | Fidelidad absoluta con la imagen: tipografía serif itálica en títulos destacados, paleta blanco/negro/camel y proporciones exactas. |
| **CP-02** | Navegación por Anclas Fluida | Clic en `FUNCIONALIDADES`, `VESTIDOR VIRTUAL IA` y `SUCURSALES` | Desplazamiento animado suave (*smooth scroll*) al elemento objetivo sin salto instantáneo ni recarga. |
| **CP-03** | Redirección a Autenticación | Clic en `INICIAR SESIÓN` y `REGISTRAR` | Navegación correcta a `/login` y `/registro` mediante el Angular Router. |
| **CP-04** | Aislamiento Multiplataforma | `git status` en terminal | Cero archivos modificados en `Ec-backend/` ni en `Ec-mobile/`. |
| **CP-05** | Integridad de Compilación | `npm run build` | Compilación exitosa de Angular en `dist/Ec-frontend/browser` dentro de los presupuestos definidos. |

---

> ⛔ **GATE DE APROBACIÓN OBLIGATORIO (STRICT STOP)**: La especificación técnica y el plan de trabajo están completamente definidos. No se modificará ni generará código en `Ec-frontend` hasta contar con la autorización explícita del usuario.
