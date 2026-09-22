# Diseno Tecnico: [CU28] Consultar ventas y reservas

**Codigo del Caso de Uso:** CU28  
**Denominacion Oficial:** Consultar ventas y reservas  
**Modulo:** Gestion Comercial / Auditoria y Ventas (`gestion_comercial` / `comercial`)  
**Metodologia:** Spec-Driven Development (SDD) & Clean Architecture Modular  
**Plataformas:** Web Corporativa (`Ec-backend` FastAPI + `Ec-frontend` Angular 19+ Standalone)  
**Exclusion Formal Ratificada:** `Ec-mobile` (Flutter 3.x) 100% excluida  

---

## 1. Arquitectura General del Sistema

El caso de uso "Consultar ventas y reservas" se concibe como un servicio analitico de lectura y agregacion estructurado bajo el patron de Monolito Modular en Capas:
- **Capa de Transporte (FastAPI Router):** Expone endpoints REST protegidos bajo el prefijo `/api/v1/admin/ventas-reservas`. Ejecuta la validacion declarativa de parametros con Pydantic v2 y la autorizacion RBAC con inyeccion de dependencias.
- **Capa de Dominio y Negocio (Service):** Encapsula la orquestacion de consultas consolidadas, la aplicacion forzada de reglas de segregacion por sucursal segun el rol, y el calculo cuantitativo de metricas de red (Total Facturado, Ventas Concluidas, Reservas Activas y Ticket Promedio).
- **Capa de Persistencia (SQLAlchemy 2.0 ORM):** Mapea las tablas preexistentes en el esquema `fashionstore` de PostgreSQL Neon (`ventas`, `venta_detalle`, `pagos`, `reservas`, `reserva_detalle`, `sucursales`, `usuarios`, `clientes`, `variantes_producto`, `productos`), ejecutando joins optimizados con carga anticipada (`joinedload`/`selectinload`) para suprimir problemas de N+1 consultas.
- **Capa de Presentacion Web (Angular 19+ Standalone):** Componente boutique reactivo gobernado por Angular Signals y `ChangeDetectionStrategy.OnPush`, integrando un grid de KPIs, controles de filtrado con debounce y una tabla maestra editorial con modal accesible de detalle transaccional.

---

## 2. Declaracion Formal de Exclusion de Ec-mobile

### 2.1 Justificacion Arquitectonica
La aplicacion movil `Ec-mobile` (Flutter 3.x) tiene un proposito estrictamente B2C centrado en la experiencia del comprador (exploracion de colecciones, probador virtual en Realidad Aumentada y pasarela de pago para checkout individual).  
Las funciones de auditoria transaccional, conciliacion contable, revision de comprobantes y balance consolidado de sucursales son tareas reservadas para la estacion de gestion corporativa en escritorio (`Ec-frontend`).

### 2.2 Directiva de Desarrollo
1. 0 modelos, 0 pantallas, 0 widgets y 0 servicios en `Ec-mobile/`.
2. Las transacciones y reservas generadas desde dispositivos moviles ingresan al repositorio con metadatos de canal (`canal_origen = 'movil'` o `tipo_venta = 'digital_movil'`), permitiendo su auditoria desde la plataforma web sin requerir vistas nativas en Flutter.

---

## 3. Diseno de Persistencia y Modelo Relacional

### 3.1 Tablas Involucradas en PostgreSQL Neon (Esquema `fashionstore`)

```
+---------------------------------------------------------------------------------+
|                                fashionstore.ventas                              |
+---------------------------------------------------------------------------------+
| id_venta: BIGSERIAL (PK)                                                        |
| numero_comprobante: VARCHAR(30) UNIQUE NOT NULL                                 |
| id_cliente: BIGINT (FK -> clientes.id_cliente) NULL                             |
| id_sucursal: INTEGER (FK -> sucursales.id_sucursal) NOT NULL                    |
| id_cajero: BIGINT (FK -> empleados.id_empleado) NULL                            |
| id_reserva: BIGINT (FK -> reservas.id_reserva) NULL                             |
| tipo_venta: ENUM ('presencial', 'digital_web', 'digital_movil') NOT NULL        |
| estado: ENUM ('pendiente', 'pagada', 'anulada', 'devuelta') NOT NULL            |
| subtotal: NUMERIC(12,2) NOT NULL DEFAULT 0                                      |
| descuento: NUMERIC(12,2) NOT NULL DEFAULT 0                                     |
| total: NUMERIC(12,2) NOT NULL DEFAULT 0                                         |
| fecha_venta: TIMESTAMPTZ NOT NULL DEFAULT now()                                 |
+---------------------------------------+-----------------------------------------+
                                        | 1
                                        |
                                        | N
+---------------------------------------v-----------------------------------------+
|                            fashionstore.venta_detalle                           |
+---------------------------------------------------------------------------------+
| id_venta_detalle: BIGSERIAL (PK)                                                |
| id_venta: BIGINT (FK -> ventas.id_venta ON DELETE CASCADE) NOT NULL             |
| id_variante: BIGINT (FK -> variantes_producto.id_variante) NOT NULL             |
| cantidad: INTEGER NOT NULL CHECK (cantidad > 0)                                 |
| precio_unitario: NUMERIC(10,2) NOT NULL                                         |
| subtotal_linea: NUMERIC(12,2) GENERATED (cantidad * precio_unitario) STORED     |
+---------------------------------------------------------------------------------+

+---------------------------------------------------------------------------------+
|                                 fashionstore.pagos                              |
+---------------------------------------------------------------------------------+
| id_pago: BIGSERIAL (PK)                                                         |
| id_venta: BIGINT (FK -> ventas.id_venta ON DELETE CASCADE) NOT NULL             |
| metodo_pago: ENUM ('efectivo', 'tarjeta_debito', 'tarjeta_credito',             |
|                    'pasarela_digital', 'qr', 'transferencia') NOT NULL          |
| monto: NUMERIC(12,2) NOT NULL                                                   |
| estado: ENUM ('pendiente', 'autorizado', 'confirmado', 'rechazado',             |
|               'reembolsado') NOT NULL DEFAULT 'pendiente'                       |
| referencia_pasarela: VARCHAR(150) NULL                                          |
| payload_respuesta: JSONB NULL                                                   |
| creado_en: TIMESTAMPTZ NOT NULL DEFAULT now()                                   |
| confirmado_en: TIMESTAMPTZ NULL                                                 |
+---------------------------------------------------------------------------------+

+---------------------------------------------------------------------------------+
|                               fashionstore.reservas                             |
+---------------------------------------------------------------------------------+
| id_reserva: BIGSERIAL (PK)                                                      |
| id_cliente: BIGINT (FK -> clientes.id_cliente) NOT NULL                         |
| id_sucursal: INTEGER (FK -> sucursales.id_sucursal) NOT NULL                    |
| fecha_hora_atencion: TIMESTAMPTZ NOT NULL                                       |
| estado: ENUM ('pendiente', 'confirmada', 'en_atencion', 'atendida',              |
|               'cancelada', 'vencida') NOT NULL DEFAULT 'pendiente'              |
| canal_origen: ENUM ('web', 'movil', 'sucursal') NOT NULL                        |
| creado_en: TIMESTAMPTZ NOT NULL DEFAULT now()                                   |
| atendido_por: BIGINT (FK -> empleados.id_empleado) NULL                         |
| atendido_en: TIMESTAMPTZ NULL                                                   |
| observacion: TEXT NULL                                                          |
+---------------------------------------+-----------------------------------------+
                                        | 1
                                        |
                                        | N
+---------------------------------------v-----------------------------------------+
|                           fashionstore.reserva_detalle                          |
+---------------------------------------------------------------------------------+
| id_reserva_detalle: BIGSERIAL (PK)                                              |
| id_reserva: BIGINT (FK -> reservas.id_reserva ON DELETE CASCADE) NOT NULL       |
| id_variante: BIGINT (FK -> variantes_producto.id_variante) NOT NULL             |
| cantidad: INTEGER NOT NULL DEFAULT 1 CHECK (cantidad > 0)                       |
+---------------------------------------------------------------------------------+
```

### 3.2 Modelos SQLAlchemy 2.0 ORM (`app/modules/comercial/cu28_ventas_reservas/modelos.py`)

Se implementan las entidades ORM declarativas bajo el esquema `fashionstore`:
- `VentaORM`: Mapea `fashionstore.ventas`. Define relaciones con `ClienteORM` (a traves de `id_cliente`), `SucursalORM`, `UsuarioORM` (cajero), `ReservaORM` y colecciones `detalles` (`VentaDetalleORM`) y `pagos` (`PagoORM`).
- `VentaDetalleORM`: Mapea `fashionstore.venta_detalle`. Define relacion con `VarianteProductoORM` (que a su vez navega a `ProductoORM`, `TallaORM` y `ColorORM`).
- `PagoORM`: Mapea `fashionstore.pagos`.
- `ReservaORM`: Mapea `fashionstore.reservas`. Define relaciones con `ClienteORM`, `SucursalORM`, `EmpleadoORM` y coleccion `detalles` (`ReservaDetalleORM`).
- `ReservaDetalleORM`: Mapea `fashionstore.reserva_detalle`. Relacionada con `VarianteProductoORM`.

---

## 4. Contratos de Datos y Esquemas Pydantic v2 (`esquemas.py`)

### 4.1 Enums y Tipos Literales

```python
class TipoOperacionFiltroEnum(str, Enum):
    VENTA = "venta"
    RESERVA = "reserva"
    TODAS = "todas"

class CriterioOrdenTransaccionEnum(str, Enum):
    CREADO_EN_DESC = "creado_en_desc"
    CREADO_EN_ASC = "creado_en_asc"
    TOTAL_DESC = "total_desc"
    TOTAL_ASC = "total_asc"
    FECHA_DESC = "fecha_desc"
```

### 4.2 Esquemas de Entrada (Filtros de Consulta)

```python
class TransaccionFiltrosIn(BaseModel):
    q: Optional[str] = Field(None, max_length=100, description="Busqueda textual")
    tipo_operacion: Optional[Literal["venta", "reserva", "todas"]] = "todas"
    estado: Optional[str] = Field("todos", description="Estado especifico o 'todos'")
    id_sucursal: Optional[int] = Field(None, description="Filtro de sucursal para admin")
    fecha_desde: Optional[datetime] = Field(None, description="Limite inferior temporal")
    fecha_hasta: Optional[datetime] = Field(None, description="Limite superior temporal")
    metodo_pago: Optional[str] = Field(None, description="Metodo de pago especifico")
    canal_origen: Optional[Literal["web", "movil", "sucursal", "todos"]] = "todos"
    ordenar_por: Optional[
        Literal[
            "creado_en_desc",
            "creado_en_asc",
            "total_desc",
            "total_asc",
            "fecha_desc",
        ]
    ] = "creado_en_desc"
    pagina: int = Field(default=1, ge=1)
    limite: int = Field(default=10, ge=1, le=100)

    @model_validator(mode="after")
    def validar_rango_fechas(self) -> "TransaccionFiltrosIn":
        if self.fecha_desde and self.fecha_hasta:
            if self.fecha_desde > self.fecha_hasta:
                raise ValueError("La fecha_desde no puede ser posterior a fecha_hasta.")
        return self
```

### 4.3 Esquemas de Salida (DTOs de Respuesta)

```python
class LineaDetalleOut(BaseModel):
    id_detalle: int
    id_variante: int
    sku: str
    nombre_producto: str
    talla: str
    color: str
    codigo_hex: Optional[str]
    cantidad: int
    precio_unitario: Decimal
    subtotal_linea: Decimal
    imagen_url: Optional[str] = None

class PagoItemOut(BaseModel):
    id_pago: int
    metodo_pago: str
    monto: Decimal
    estado: str
    referencia_pasarela: Optional[str] = None
    creado_en: datetime
    confirmado_en: Optional[datetime] = None

class TransaccionResumenItemOut(BaseModel):
    id_transaccion: int
    tipo_operacion: Literal["venta", "reserva"]
    codigo_comprobante: str
    fecha: datetime
    id_cliente: Optional[int] = None
    nombre_cliente: str
    email_cliente: Optional[str] = None
    telefono_cliente: Optional[str] = None
    id_sucursal: int
    nombre_sucursal: str
    ciudad_sucursal: str
    canal: str
    estado: str
    total_monto: Decimal
    cantidad_items: int

class MetricasTransaccionalesOut(BaseModel):
    monto_total_facturado: Decimal
    total_ventas_concluidas: int
    reservas_activas: int
    ticket_promedio: Decimal

class RespuestaPaginadaTransaccionesOut(BaseModel):
    items: List[TransaccionResumenItemOut]
    metricas: MetricasTransaccionalesOut
    total: int
    pagina: int
    limite: int
    total_paginas: int

class VentaDetalleCompletoOut(BaseModel):
    id_venta: int
    numero_comprobante: str
    fecha_venta: datetime
    estado: str
    tipo_venta: str
    subtotal: Decimal
    descuento: Decimal
    total: Decimal
    id_sucursal: int
    nombre_sucursal: str
    id_cliente: Optional[int]
    nombre_cliente: str
    email_cliente: Optional[str]
    telefono_cliente: Optional[str]
    cajero_nombre: Optional[str]
    lineas: List[LineaDetalleOut]
    pagos: List[PagoItemOut]

class ReservaDetalleCompletoOut(BaseModel):
    id_reserva: int
    codigo_reserva: str
    fecha_hora_atencion: datetime
    creado_en: datetime
    estado: str
    canal_origen: str
    observacion: Optional[str]
    id_sucursal: int
    nombre_sucursal: str
    id_cliente: int
    nombre_cliente: str
    email_cliente: Optional[str]
    telefono_cliente: Optional[str]
    atendido_por_nombre: Optional[str]
    lineas: List[LineaDetalleOut]
```

---

## 5. Jerarquia de Excepciones Semanticas (`errores.py`)

```python
class VentasReservasError(Exception):
    """Excepcion base para errores del modulo de ventas y reservas."""
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class VentaNoEncontradaError(VentasReservasError):
    def __init__(self, id_venta: int):
        super().__init__(
            code="VENTA_NO_ENCONTRADA",
            message=f"La transaccion de venta con ID {id_venta} no fue localizada.",
            status_code=404,
        )

class ReservaNoEncontradaError(VentasReservasError):
    def __init__(self, id_reserva: int):
        super().__init__(
            code="RESERVA_NO_ENCONTRADA",
            message=f"La reserva con ID {id_reserva} no fue localizada.",
            status_code=404,
        )

class SucursalNoAutorizadaError(VentasReservasError):
    def __init__(self):
        super().__init__(
            code="SUCURSAL_NO_AUTORIZADA",
            message="No cuenta con autorizacion para consultar transacciones de una sucursal distinta a su sede.",
            status_code=403,
        )

class RangoFechasInvalidoError(VentasReservasError):
    def __init__(self, detalle: str):
        super().__init__(
            code="RANGO_FECHAS_INVALIDO",
            message=f"El rango cronologico especificado es invalido: {detalle}",
            status_code=422,
        )
```

---

## 6. Logica de Negocio y Capa de Servicio (`servicio.py`)

### 6.1 Clase `ServicioConsultarVentasReservas`
La clase centraliza los flujos analiticos:

1. **Segregacion de Alcance (RBAC):**
   ```python
   def _resolver_alcance_sucursal(self, usuario: UsuarioORM, id_sucursal_solicitado: Optional[int]) -> Optional[int]:
       rol = str(usuario.rol or "").lower().strip()
       if rol in ("administrador", "admin"):
           return id_sucursal_solicitado
       elif rol == "encargado_sucursal":
           return usuario.id_sucursal
       raise AccesoDenegadoError()
   ```

2. **Algoritmo de Listado Paginado Unificado:**
   - Si `tipo_operacion == 'venta'`: Consulta exclusivamente sobre `VentaORM`.
   - Si `tipo_operacion == 'reserva'`: Consulta exclusivamente sobre `ReservaORM`.
   - Si `tipo_operacion == 'todas'`: Ejecuta consultas paralelas deterministas con conteo de registros, unificando los items mediante ordenacion de memoria por `creado_en`/`fecha` o subconsultas UNION ALL estructuradas.
   - Aplica filtros de texto `q` sobre numero de comprobante, nombre/email del cliente asociado y SKU de las variantes vinculadas.

3. **Calculo de Metricas Cuantitativas de Red (`obtener_metricas`):**
   - `monto_total_facturado`: Sumatoria de `VentaORM.total` donde `estado == 'pagada'` dentro de la sucursal autorizada.
   - `total_ventas_concluidas`: Total de filas en `ventas` con `estado == 'pagada'`.
   - `reservas_activas`: Conteo de reservas con `estado.in_(['pendiente', 'confirmada', 'en_atencion'])`.
   - `ticket_promedio`: `monto_total_facturado / total_ventas_concluidas` si `total_ventas_concluidas > 0`, caso contrario `Decimal("0.00")`.

4. **Desglose de Detalle Transaccional:**
   - `obtener_detalle_venta(id_venta, usuario)`: Valida existencia y pertenencia de sucursal. Resuelve lineas de prenda uniendo variante, modelo, talla, color y los pagos vinculados.
   - `obtener_detalle_reserva(id_reserva, usuario)`: Valida existencia y sucursal. Recupera variantes y prendas reservadas.

---

## 7. Diseno de la API REST (`router.py`)

### 7.1 Tabla de Endpoints

| Metodo | Ruta | Rol Minimo | Codigo Exito | Descripcion |
|---|---|---|---|---|
| `GET` | `/api/v1/admin/ventas-reservas` | Encargado / Admin | 200 OK | Listado paginado unificado de ventas y reservas con KPIs |
| `GET` | `/api/v1/admin/ventas-reservas/ventas/{id_venta}` | Encargado / Admin | 200 OK | Detalle completo de comprobante de venta, lineas y pagos |
| `GET` | `/api/v1/admin/ventas-reservas/reservas/{id_reserva}` | Encargado / Admin | 200 OK | Detalle completo de orden de reserva y prendas apartadas |

---

## 8. Diseno Frontend Web Angular 19+ Standalone

### 8.1 Modulo y Rutas
- Directorio: `src/app/modules/comercial/cu28_ventas_reservas/`
- Ruta en `app.routes.ts`:
  ```typescript
  {
    path: 'admin/ventas-reservas',
    canActivate: [authGuard, roleGuard(['administrador', 'encargado_sucursal'])],
    loadComponent: () =>
      import(
        './modules/comercial/cu28_ventas_reservas/paginas/ventas-reservas-admin.component'
      ).then((m) => m.VentasReservasAdminComponent),
  }
  ```

### 8.2 Integracion en AdminDashboardComponent
- En `admin-dashboard.component.html`, tarjeta de "Gestion Comercial" con:
  * ID del boton: `btn-consultar-ventas-reservas`
  * Directiva dual anti-botones estaticos:
    ```html
    <a
      id="btn-consultar-ventas-reservas"
      routerLink="/admin/ventas-reservas"
      (click)="navegar('/admin/ventas-reservas', $event)"
      class="w-full inline-flex items-center justify-center gap-2 bg-[#0F172A] hover:bg-black text-white text-xs font-bold uppercase tracking-wider py-3 px-4 rounded-xl shadow-xs transition-all cursor-pointer"
    >
      <span>Consultar ventas y reservas</span>
      <svg class="w-3.5 h-3.5 text-[#AD8C63] group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
      </svg>
    </a>
    ```

### 8.3 Estado Reactivo con Angular Signals (`VentasReservasAdminService`)
- `transacciones = signal<TransaccionResumenItemOut[]>([])`
- `metricas = signal<MetricasTransaccionalesOut>(...)`
- `totalItems = signal<number>(0)`
- `totalPaginas = signal<number>(1)`
- `cargando = signal<boolean>(false)`
- `error = signal<string | null>(null)`

### 8.4 Componente Principal `VentasReservasAdminComponent`
- Grid de 4 tarjetas KPIs:
  1. Monto Facturado (`metricas().monto_total_facturado`)
  2. Ventas Concluidas (`metricas().total_ventas_concluidas`)
  3. Reservas Activas (`metricas().reservas_activas`)
  4. Ticket Promedio (`metricas().ticket_promedio`)
- Filtros reactivos con debounce de 300 ms.
- Tabla editorial con pagination controls.
- Modal de comprobante/detalle accesible.

---

## 9. Estrategia de Pruebas y Aseguramiento de Calidad

### 9.1 Backend (`tests/modules/comercial/test_cu28_ventas_reservas.py`)
- Test de autorizacion obligatoria JWT (HTTP 401).
- Test de bloqueo RBAC para rol `cajero` y `cliente` (HTTP 403).
- Test de segregacion: encargado_sucursal solo accede a su sucursal.
- Test de listado con filtros (tipo_operacion, estado, fechas, q).
- Test de validacion de rango de fechas cronologico (fecha_desde > fecha_hasta -> 422).
- Test de calculo de metricas cuantitativas.
- Test de detalle de venta y reserva (200 OK y 404 Not Found).

### 9.2 Frontend (`src/app/modules/comercial/cu28_ventas_reservas/...spec.ts`)
- Test de renderizado de KPIs cuantitativos.
- Test de filtrado reactivo con debounce.
- Test de apertura y cierre de modal accesible de comprobante.
- Test obligatorio en `admin-dashboard.component.spec.ts`:
  * Verificacion de existencia de `#btn-consultar-ventas-reservas`.
  * Verificacion de atributo `routerLink="/admin/ventas-reservas"`.
  * Despacho de evento `click` sobre el boton y llamada a `navegar('/admin/ventas-reservas', event)`.
