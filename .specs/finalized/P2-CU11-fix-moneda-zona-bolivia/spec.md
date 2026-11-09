# Especificación Técnica: Moneda y zona horaria de Bolivia (fix de P2-CU11)

**ID del cambio:** `P2-CU11-fix-moneda-zona-bolivia`
**Fuente:** petición del usuario del 2026-11-09, que **modifica** la decisión C2 de P2-CU11, y sus respuestas:
- FASHION STORE pasa a BOB con el mismo número;
- la moneda solo cambia si la empresa no tiene ventas;
- el IVA pasa al 13 % de Bolivia.

**Depende de:** `P2-CU11-parametros-empresa` (en producción).
**Nivel SDD:** **3 (alto riesgo)**: migración con cambio de datos en producción, cobro en Stripe y cálculo de «hoy» en todo el backend.
**Bloques:** Backend (con migración `0016`) → Web → Mobile.
**Responsable:** Gustavo.
**Estado:** 🟢 Aprobada e implementada (2026-11-09). Spec permanente: `.specs/modules/plataforma/P2-CU11-parametros-empresa.md` (C2 superada).
**Fecha:** 2026-11-09

---

## 0. Hallazgos (código al 2026-11-09)

### 0.1 Zona horaria: hoy no se usa la de Bolivia
`configuracion_tenant.zona_horaria` vale `Europe/Madrid`, pero ningún código la lee. Cada sitio que necesita «hoy» o «ahora» resuelve la hora por su cuenta:

| Dónde | Cómo calcula «hoy» o «ahora» | Efecto en Bolivia (UTC−4) |
| :--- | :--- | :--- |
| Catálogo, detalle, colecciones y carrito (`date.today()`, 4 sitios): promociones y temporadas vigentes | Zona del servidor (UTC en Render) | De 20:00 a 24:00 ya aplica las promociones del día siguiente |
| Caja, «ventas del día» (`_ahora().replace(hour=0…)`) | Medianoche UTC | A las 20:00 la lista se vacía |
| Suscripción vigente (CU12) y función `empresas_disponibles()` (`current_date`) | UTC | Una suscripción vence 4 h antes |
| Indicadores (`date_trunc` en PostgreSQL) | Sesión de Neon en UTC | Las ventas de 20:00 a 24:00 caen en el día siguiente |
| Reportes por voz (`datetime.now()`, 5 sitios): fecha de emisión y nombre de archivo | Zona del servidor | La hora impresa va 4 h adelantada |

Web y móvil muestran las horas en la zona del navegador o del teléfono, que en Bolivia es correcta.

### 0.2 Moneda: el euro está fijo
| Capa | Dónde |
| :--- | :--- |
| Stripe | `stripe_service.py`: `currency="eur"` (2 sitios) |
| Esquemas | `moneda: str = "EUR"` en carrito, checkout y pago (4) |
| Textos del backend | «Desde X €» (colecciones), «3 pagos de X €» (detalle), comprobante PDF |
| Web | 74 apariciones en 18 archivos (`{{ x }} €` y `currency:'EUR'`) |
| Móvil | 41 apariciones en 11 archivos (`'${x} €'`) |
| Empresa | `configuracion_tenant.moneda = 'EUR'`; ni web ni móvil saben la moneda de la tienda |

### 0.3 IVA
`TASA_IVA = Decimal("0.21")` en `cu11_gestionar_carrito/servicio.py`. El desglose y su texto «21 %» aparecen en la web (carrito, checkout, ticket) y en el móvil.

### 0.4 Stripe y el boliviano
Stripe acepta BOB como moneda de cobro con decimales (no es *zero-decimal*), igual que USD. El mínimo por cargo equivale a 0,50 USD. Se comprueba en modo de prueba antes de cerrar (T-PR-02).

---

## 1. Decisiones

| ID | Decisión |
| :--- | :--- |
| **M1** | **Monedas admitidas: `BOB` y `USD`** (CHECK en la base). Por defecto, `BOB`. |
| **M2** | **Migración `0016`:** todas las empresas pasan a `moneda='BOB'` y `zona_horaria='America/La_Paz'` **sin convertir importes** (120 € pasan a Bs 120, decisión del usuario). Las ventas y pagos pasados se ven en Bs. |
| **M3** | **La moneda solo cambia sin operaciones:** si la empresa tiene alguna venta o pago, `PUT /admin/configuracion` con otra moneda → 409 `MONEDA_CON_OPERACIONES`. Así el historial nunca cambia de moneda (CU11 A3) y no hace falta guardar la moneda en cada venta. |
| **M4** | **Zona horaria:** el campo es editable, pero la única opción es `America/La_Paz` (CHECK en la base). Como todas las empresas la tienen, el código usa la constante `ZONA_EMPRESA` de `core/tiempo.py` en lugar de leerla de cada empresa. Si algún día se admite otra zona, eso cambia (queda documentado en `CLAUDE.md`). |
| **M5** | **«Hoy» en todo el backend con la hora de Bolivia:** <br>- `core/tiempo.py` con `ahora()` (UTC con zona), `hoy()` y `inicio_del_dia()` en `America/La_Paz`; sustituyen a `date.today()` y `datetime.now()` en los sitios de §0.1. <br>- PostgreSQL: el listener `after_begin` añade `set_config('TimeZone', 'America/La_Paz', true)`, de modo que `current_date`, `date_trunc` y los `::date` usan Bolivia. <br>- Las columnas siguen siendo `TIMESTAMPTZ`: no se migra ningún instante guardado. |
| **M6** | **Moneda en todas las respuestas que muestran importes:** <br>- `moneda` sale de la configuración de la empresa (sustituye a los `"EUR"` fijos). <br>- `EmpresaOut` (directorio, portal, `mis-empresas`) y el `tenant` del login añaden `moneda`. Para el directorio, `empresas_disponibles()` la devuelve; la migración `0016` cambia la función. |
| **M7** | **Stripe cobra en la moneda de la empresa** (`currency=moneda.lower()`). |
| **M8** | **Formato:** `Bs 1.234,50` para BOB y `US$ 1.234,50` para USD (separadores de Bolivia). <br>- Backend: `formatear_importe(valor, moneda)`, para el PDF y los textos. <br>- Web: pipe `importe` con la moneda de la tienda actual. <br>- Móvil: `formatoImporte(valor)` con `EmpresaActual.instancia.moneda`. |
| **M9** | **IVA del 13 %** (Bolivia), incluido en el precio y solo informativo; se actualizan los textos «21 %». No se persiste, así que no cambia nada guardado. |
| **M10** | **Configuración web:** selector de moneda (Boliviano / Dólar). Si la empresa tiene operaciones, se deshabilita con el motivo. La zona horaria es un selector con una sola opción, «Bolivia (America/La_Paz)». |

## 2. Base de datos — migración `0016_moneda_zona_bolivia`

```
down_revision = "0015"
-- avisar a Tony antes: «tomo la 0016»
ALTER TABLE configuracion_tenant ALTER moneda SET DEFAULT 'BOB', ALTER zona_horaria SET DEFAULT 'America/La_Paz';
UPDATE configuracion_tenant SET moneda = 'BOB', zona_horaria = 'America/La_Paz';
ADD CONSTRAINT chk_config_moneda CHECK (moneda IN ('BOB', 'USD'));
ADD CONSTRAINT chk_config_zona CHECK (zona_horaria = 'America/La_Paz');
empresas_disponibles() → (id_tenant, codigo, nombre, moneda)   -- DROP + CREATE, mismos permisos
```

El `downgrade` restaura `EUR` y `Europe/Madrid`, los valores por defecto y la función de tres columnas. Se aplica primero en `pruebas-multitenant` (`upgrade → downgrade → upgrade`) y después en producción, **a mano y antes del push**.

## 3. Contratos (cambios)

| Contrato | Cambio |
| :--- | :--- |
| `GET/PUT /admin/configuracion` | `moneda` y `zona_horaria` editables (M1, M4); 422 con un valor no admitido; 409 `MONEDA_CON_OPERACIONES` (M3). La respuesta añade `moneda_bloqueada: bool`, para la pantalla. |
| `GET /tenants`, `GET /tenants/{codigo}`, `GET /mis-empresas`, `POST /mis-empresas` | `EmpresaOut` + `moneda`. |
| `POST /autenticacion/login` | `tenant` y `empresas[]` + `moneda`. |
| Carrito, checkout, pago | `moneda` = la de la empresa. |

## 4. Web
- `TenantService` guarda la moneda de la tienda del portal; en el panel, la del `tenant` del login.
- Pipe `importe` y sustitución de las 74 apariciones de §0.2. IVA «13 %».
- Configuración: selectores de moneda y zona (M10).

## 5. Móvil
- `EmpresaTienda.moneda` desde el login y `/mis-empresas`; `formatoImporte` y sustitución de las 41 apariciones. IVA «13 %».

## 6. Pruebas
- **Backend:**
  - `core/tiempo.py`: a las 22:00 de Bolivia, «hoy» sigue siendo el mismo día.
  - Caja «del día» con hora de Bolivia.
  - Configuración: BOB y USD válidos, otra moneda 422, cambio con ventas 409.
  - Stripe recibe `bob`.
  - `formatear_importe`.
  - IVA del 13 %.
  - **Integración:** `0016` aplicada (`current_date` y `TimeZone` de la sesión en Bolivia, CHECK de moneda, `empresas_disponibles` con moneda, 409 con ventas reales de FASHION STORE).
- **Web y móvil:** pipe y formateador con BOB y USD; payloads literales con `moneda`; pantallas sin «€».
- **Guardia:** búsqueda en las pruebas de que no queda ningún `€` ni `'EUR'` en `src/app` ni en `lib/` (salvo comentarios de historial).

## 7. Riesgos y coordinación
- **Tony:** la migración `0016` se anuncia antes de crearla. Su CU05 debe crear la fila de configuración con `BOB` y `America/La_Paz` (los nuevos valores por defecto lo hacen solos). CU09 y CU10 cobran en Stripe con la moneda de la empresa.
- **Producción:** tras la migración, los precios de FASHION STORE se leen en Bs con el mismo número (decisión M2). Las suscripciones (`planes.precio_mensual`) no tienen moneda propia: se entienden en la de la plataforma; queda fuera de este fix (CU06/CU10 de Tony).
- **APK:** las apps móviles anteriores siguen mostrando «€» hasta instalar la nueva.
