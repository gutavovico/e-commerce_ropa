# Especificación Técnica Permanente: Empresa de prueba Menshopping — P2-RF15

**Fuente:** `SI2-Parcial2.md` (RF15) y las decisiones del usuario del 2026-11-09
**Paquete de Dominio:** `plataforma` (datos de una empresa; sin código de aplicación nuevo)
**Backend:** sin migración · `Ec-backend/scripts/cargar_menshopping.py` + `Ec-backend/scripts/datos/menshopping.json`
**Frontend:** 4 PNG en `Ec-frontend/public/ar/menshopping_{camiseta,pantalon,camisa,pantalon_gala}.png`
**Mobile:** sin cambios
**Depende de:** `P2-CU13-CU12-fundacion-multitenant.md`, `P2-CU11-parametros-empresa.md` (moneda BOB, Alembic `0016`)
**Estado:** Cerrado (2026-11-09). Cargado en producción.
**Historial del cambio:** `.specs/finalized/P2-RF15-menshopping/`

---

## 1. Qué hay en producción

| Elemento | Valor |
| :--- | :--- |
| Empresa | Código `menshopping`, «Menshopping», `activa`, moda **masculina**. Plan Básico por un año desde la carga. Moneda BOB, `America/La_Paz`. |
| Ciudad global | Trinidad (Beni), creada por la carga. |
| Sucursales | «Menshopping Santa Cruz» (Santa Cruz de la Sierra) y «Menshopping Beni» (Trinidad), con «Dirección por confirmar» hasta que el administrador la corrija. |
| Catálogo | Camiseta básica negra Bs 120 · Pantalón chino azul marino Bs 280 · Camisa formal blanca Bs 350 · Pantalón de gala negro Bs 480. Tallas M y L (8 variantes, SKU `MSH-<PRENDA>-<TALLA>`). Temporada «Colección 2026-2027». |
| Stock inicial | Santa Cruz 5 + 5 por prenda; Beni 2 + 2 (5 ÷ 2, división entera). Cada fila con su movimiento `ingreso_proveedor`. |
| Usuarios | `admin@`, `encargado.santacruz@`, `cajero.santacruz@`, `encargado.beni@`, `cajero.beni@` (`menshopping.com`), con ficha de empleado y sucursal autorizada. La contraseña inicial no está en el repositorio; cada empleado la cambia en «Mi perfil» (`/admin/perfil`). |
| Ventas | Solo las reales hechas en la caja de cada sucursal después de la carga. No se cargan ventas de ejemplo (cero datos inventados). |

## 2. Reglas

| ID | Regla |
| :--- | :--- |
| R1 | Los datos viven en `scripts/datos/menshopping.json`, sin contraseñas. Cada sucursal y prenda se identifica por `codigo` (no `clave`: la guarda de contraseñas lo tomaría por una). |
| R2 | La contraseña inicial sale de `MENSHOPPING_CLAVE_INICIAL` o de `getpass`, con la complejidad de CU20; nunca se imprime ni se guarda. Esa variable no se declara en el `.env`: `core/config.py` rechaza las desconocidas. |
| R3 | La carga no empieza si falta un PNG. Los PNG deben estar desplegados en Vercel antes de cargar en producción. |
| R4 | Una transacción, todo o nada, como dueño de la base y con `id_tenant` explícito en cada fila. |
| R5 | Sin `--aplicar` hace la carga y la deshace. Si `menshopping` ya existe, se detiene: no es repetible. |
| R6 | El catálogo de Menshopping es masculino y el de FASHION STORE femenino: nunca se mezclan (`CLAUDE.md`, «Cero datos inventados»). |

## 3. Pruebas
- `tests/test_cargar_menshopping.py`: 14 unitarias (reparto del stock, validación de datos y contraseña, PNG ausentes).
- `tests/integracion/test_multitenant.py::test_rf15_carga_de_menshopping_aislada_de_fashion_store`: carga completa con rollback en `pruebas-multitenant` (código `rf15-prueba`), aislamiento en ambos sentidos, directorio, login y catálogo.

## 4. Fuera de alcance
- Portada propia de Menshopping: el portal usa la landing común (limitación conocida de P2-CU02).
- Direcciones y teléfonos reales de las sucursales (T-0-02, opcional): los corrige el administrador en «Sucursales».
