# Especificación Técnica: Empresa de prueba Menshopping (P2-RF15)

**ID del cambio:** `P2-RF15-menshopping`
**Fuente:** `SI2-Parcial2.md` RF15 y las respuestas del usuario del 2026-11-09:
- precios Bs 120 / 280 / 350 / 480;
- variantes M y L en un color;
- el usuario aporta los PNG del vestidor;
- administrador más un encargado y un cajero por sucursal.

**Depende de:** `P2-CU11-fix-moneda-zona-bolivia` (en producción, Alembic `0016`).
**Nivel SDD:** **2 (riesgo medio)**: escritura de datos en producción con el dueño de la base. No hay migración ni código de aplicación nuevo.
**Bloques:** Script y datos → ensayo en la rama de pruebas → carga en producción (la hace el usuario).
**Responsable:** Gustavo (`reparticion.md`).
**Estado:** 🟢 Aprobada (2026-11-09). En implementación.
**Fecha:** 2026-11-09

---

## 0. Hallazgos (rama de pruebas, al 2026-11-09)

| Necesita | Hoy |
| :--- | :--- |
| Ciudad de **Beni** | `ciudades` tiene Santa Cruz de la Sierra, La Paz, Cochabamba y Tarija; **no hay ninguna de Beni**. |
| Tallas M y L, colores negro, azul marino y blanco | Existen (`tallas` 3 y 4; `colores` Negro, Azul Marino, Blanco). Son catálogos globales y se reutilizan. |
| Plan | Básico permite 2 sucursales activas, justo las de Menshopping. |
| Imágenes del vestidor | `modelo_ar_url` apunta a un PNG de `Ec-frontend/public/ar/` con la prenda sola. No hay ninguno de prendas masculinas. |
| Inventario | `inventario_sucursal.id_temporada` es obligatorio: hace falta una temporada de Menshopping. Toda variación de stock se registra en `movimientos_inventario`. |
| Empleados | Cada empleado necesita su ficha en `empleados` (D3 de CU31-CU32) y sus filas en `empleado_sucursal` (RN07). |

---

## 1. Qué se carga

| Elemento | Valor |
| :--- | :--- |
| **Empresa** | Código `menshopping`, nombre «Menshopping», estado `activa`. |
| **Suscripción** | Plan **Básico**, `activa`, desde el día de la carga hasta un año después; historial `alta`. |
| **Configuración** | Valores por defecto: BOB, `America/La_Paz`, 24 h, 15 días, operación sin conexión activada, 7 días. |
| **Ciudad global nueva** | **Trinidad** (capital de Beni), Bolivia. Solo se crea si no existe. |
| **Sucursales** | «Menshopping Santa Cruz» (Santa Cruz de la Sierra) y «Menshopping Beni» (Trinidad), de 09:00 a 20:00. La dirección y el teléfono salen del archivo de datos (§2). |
| **Categorías** | Camisetas, Pantalones, Camisas formales, Pantalones de gala. |
| **Temporada** | «Colección 2026-2027», tipo `nueva_coleccion`, del día de la carga a un año después. |
| **Prendas** (una por categoría) | Camiseta básica **negra**, Bs 120 · Pantalón chino **azul marino**, Bs 280 · Camisa formal **blanca**, Bs 350 · Pantalón de gala **negro**, Bs 480. |
| **Variantes** | Tallas **M** y **L** de cada prenda (8 en total), sin recargo. SKU `MSH-<PRENDA>-<TALLA>`. |
| **Stock** | Santa Cruz: 10 por prenda, **5 + 5**. Beni: 5 por prenda, 5 ÷ 2 con división entera = **2 + 2** (RF15). Cada fila de inventario con su movimiento `ingreso_proveedor`, responsable el administrador. |
| **Usuarios** | `admin@menshopping.com` (administrador). Por sucursal: `encargado.santacruz@` / `cajero.santacruz@` y `encargado.beni@` / `cajero.beni@` (`@menshopping.com`). Cada uno con su ficha de empleado y su sucursal autorizada, que es también la principal. |
| **Ventas** | **No se cargan.** Inventar ventas contradice «cero datos inventados». RF15 se cumple haciendo ventas reales en la caja de Menshopping después de la carga (T-PR-03). |

---

## 2. Decisiones

| ID | Decisión |
| :--- | :--- |
| **R1** | **Datos en un archivo versionado** (`Ec-backend/scripts/datos/menshopping.json`): empresa, sucursales (con dirección y teléfono), categorías, prendas, precios, variantes, stock e imágenes. Sin contraseñas. Las direcciones van como «Dirección por confirmar» hasta que me las des; el administrador las puede corregir desde «Sucursales». |
| **R2** | **Contraseña inicial:** el script la lee de la variable de entorno `MENSHOPPING_CLAVE_INICIAL` o, si no existe, la pide sin mostrarla. Exige la misma complejidad que CU20 y nunca la imprime ni la guarda. Es la misma para las 5 cuentas, que se cambian al primer uso desde Perfil. |
| **R3** | **Imágenes:** los 4 PNG que me pasas se copian a `Ec-frontend/public/ar/` como `menshopping_camiseta.png`, `menshopping_pantalon.png`, `menshopping_camisa.png` y `menshopping_pantalon_gala.png`. `modelo_ar_url` e `imagen_url` apuntan a ellos (`/ar/...`), salvo que aportes también fotos de catálogo. **El script no carga nada si falta alguno.** |
| **R4** | **Una transacción, todo o nada.** Se conecta como dueño de la base (`DATABASE_URL_MIGRACIONES`, o `DATABASE_URL_PRUEBAS` con `--db pruebas`) y fija el contexto de Menshopping en cada inserción, para que valgan las FK compuestas y el `id_tenant` por defecto. |
| **R5** | **Sin `--aplicar` solo muestra lo que haría**, como `regularizar_fichas_empleado.py`. Si `menshopping` ya existe, se detiene sin tocar nada: no es una carga repetible. |
| **R6** | **Aislamiento verificable:** prueba de integración que ejecuta la carga dentro de la transacción de la rama de pruebas y la deshace al final. Comprueba que FASHION STORE no ve nada de Menshopping, y al revés, en catálogo, sucursales, usuarios e inventario. |
| **R7** | **Ensayo en `pruebas-multitenant`** con `--aplicar` antes de producción. La carga en producción la ejecutas tú, después del ensayo. |

## 3. Uso
```powershell
cd Ec-backend
.\.venv\Scripts\python.exe scripts\cargar_menshopping.py --db pruebas            # ver qué haría
.\.venv\Scripts\python.exe scripts\cargar_menshopping.py --db pruebas --aplicar  # ensayo
.\.venv\Scripts\python.exe scripts\cargar_menshopping.py --aplicar               # producción
```
Con `--aplicar`, si `MENSHOPPING_CLAVE_INICIAL` no está definida, el script pide la contraseña sin
mostrarla (`getpass`).

## 4. Pruebas
- **Unitarias:**
  - el reparto del stock (10 → 5 + 5; 5 → 2 + 2);
  - la validación del archivo de datos y de la contraseña;
  - que falte un PNG detiene la carga.
- **Integración (rama de pruebas, con rollback):**
  - la carga completa: 1 empresa, 2 sucursales, 4 categorías, 4 prendas, 8 variantes, 16 filas de inventario con su movimiento y 5 usuarios con sus fichas;
  - el aislamiento con FASHION STORE (R6);
  - el login de `admin@menshopping.com` devuelve `tenant = menshopping` y `moneda = BOB`;
  - el directorio lista Menshopping.

## 5. Fuera de alcance
- Portada (landing) propia de Menshopping: la del portal sigue siendo la de FASHION STORE (limitación conocida de P2-CU02). Queda para cuando se defina el contenido por empresa.
- Ventas de ejemplo (§1).
