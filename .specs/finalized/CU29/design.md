# Diseno Tecnico: [CU29] Visualizar indicadores empresariales

**Codigo del Caso de Uso:** CU29  
**Denominacion Oficial:** Visualizar indicadores empresariales  
**Modulo:** Analitica y Reportes / Inteligencia Empresarial (`analitica_reportes` / `comercial`)  
**Metodologia:** Spec-Driven Development (SDD)  
**Patrones Principales:** Domain-Driven Design (DDD), Aggregation Services, Clean Architecture, Angular Signals & OnPush  
**Entorno de Ejecucion:** Web corporativa exclusiva (`Ec-backend` FastAPI y `Ec-frontend` Angular 19+ Standalone)  
**Exclusion Formal:** `Ec-mobile` (Flutter 3.x) 100% excluida  

---

## 1. Vision Arquitectonica y Flujo de Datos

El modulo de Visualizar indicadores empresariales opera como una capa analitica desacoplada de la transaccionalidad ordinaria. Realiza agregaciones en tiempo de consulta sobre las tablas persistidas en PostgreSQL Neon (`fashionstore.ventas`, `fashionstore.venta_detalle`, `fashionstore.variantes_producto`, `fashionstore.productos`, `fashionstore.categorias` y `fashionstore.sucursales`) optimizando los tiempos de respuesta mediante indices relacionales y funciones de agrupacion de SQLAlchemy 2.0.

```
+-----------------------------------------------------------------------------------------+
|                                  ARQUITECTURA DEL CU29                                  |
+-----------------------------------------------------------------------------------------+
                                                                                           
 [ Navegador Web / Ec-frontend ]                                                           
        |                                                                                  
        |  GET /api/v1/admin/indicadores/... (JWT Bearer Token)                            
        v                                                                                  
 [ FastAPI Router (app/modules/comercial/cu29_indicadores/router.py) ]                     
        |                                                                                  
        |--> Inyeccion de Dependencias: require_roles(["administrador", "encargado_sucursal"])
        |--> Validacion de Query Params: IndicadoresFiltrosIn (Pydantic v2)                
        v                                                                                  
 [ Servicio Analitico (app/modules/comercial/cu29_indicadores/servicio.py) ]               
        |                                                                                  
        |--> Gobernanza RBAC: Segregacion territorial obligatoria                          
        |--> Calculo de Rangos Temporales (Actual vs Precedente de igual duracion)         
        |--> Consultas SQL Agregadas (func.sum, func.count, func.coalesce, date_trunc)     
        v                                                                                  
 [ PostgreSQL Neon (Esquema fashionstore) ]                                                
   - fashionstore.ventas (estado='pagada')                                                 
   - fashionstore.venta_detalle                                                            
   - fashionstore.variantes_producto -> productos -> categorias                           
   - fashionstore.sucursales (activa=true)                                                 
```

---

## 2. Declaracion Formal de Exclusion de la Aplicacion Movil (Ec-mobile)

### 2.1 Justificacion y Limites de Dominio
La aplicacion movil (`Ec-mobile`), disenada con Flutter 3.x, atiende exclusivamente la relacion comercial B2C con el consumidor (catalogo, vestidor con Realidad Aumentada, compras y seguimiento de pedidos individuales).  
La inteligencia de negocios, la rentabilidad acumulada, la comparativa de sucursales fisicas y la planificacion comercial son materias reservadas para la direccion ejecutiva y administracion de tiendas en computadoras de escritorio.

### 2.2 Directiva Tecnica de Aislamiento
- Ningun codigo, modelo de datos, widget o peticion HTTP se incorporara en el repositorio `Ec-mobile/`.
- No se exponen endpoints publicos ni accesibles para clientes sobre analitica corporativa.

---

## 3. Diseno del Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0 + PostgreSQL Neon)

### 3.1 Estructura Modular de Archivos
```
Ec-backend/app/modules/comercial/cu29_indicadores/
    __init__.py
    modelos.py        # Importacion/reutilizacion declarativa de entidades relacionales
    esquemas.py       # DTOs y validadores Pydantic v2
    errores.py        # Jerarquia de excepciones semanticas de dominio
    servicio.py       # Motor analitico y agregaciones de base de datos
    router.py         # Endpoints REST protegidos por RBAC
```

### 3.2 Jerarquia de Excepciones Semanticas (`errores.py`)
```python
class IndicadoresEmpresarialesError(Exception):
    """Excepcion base para anomalias del modulo de indicadores analiticos."""
    def __init__(self, mensaje: str, codigo_error: str, status_code: int = 400):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo_error = codigo_error
        self.status_code = status_code

class RangoFechasInvalidoError(IndicadoresEmpresarialesError):
    def __init__(self, mensaje: str = "El rango temporal es inconsistente: fecha_desde posterior a fecha_hasta."):
        super().__init__(mensaje, codigo_error="RANGO_FECHAS_INVALIDO", status_code=422)

class SucursalNoAutorizadaError(IndicadoresEmpresarialesError):
    def __init__(self, mensaje: str = "No cuenta con privilegios para consultar indicadores de otra sucursal."):
        super().__init__(mensaje, codigo_error="SUCURSAL_NO_AUTORIZADA", status_code=403)

class ComparativaRestringidaError(IndicadoresEmpresarialesError):
    def __init__(self, mensaje: str = "La comparativa de rendimiento entre sucursales es de acceso exclusivo para administradores."):
        super().__init__(mensaje, codigo_error="SUCURSAL_COMPARATIVA_RESTRINGIDA_ADMIN", status_code=403)
```

### 3.3 Esquemas Pydantic v2 (`esquemas.py`)
```python
from datetime import date, datetime
from decimal import Decimal
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

PeriodoPreset = Literal["7d", "30d", "mes_actual", "anio_actual", "personalizado"]

class IndicadoresFiltrosIn(BaseModel):
    """Filtros de consulta analitica con validacion cronologica estricta."""
    periodo: PeriodoPreset = Field(default="30d")
    fecha_desde: Optional[date] = Field(default=None)
    fecha_hasta: Optional[date] = Field(default=None)
    id_sucursal: Optional[int] = Field(default=None, description="Filtro opcional para administradores")

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validar_fechas(self) -> "IndicadoresFiltrosIn":
        if self.periodo == "personalizado":
            if not self.fecha_desde or not self.fecha_hasta:
                raise ValueError("Para periodo personalizado debe especificar fecha_desde y fecha_hasta.")
            if self.fecha_desde > self.fecha_hasta:
                raise ValueError("La fecha_desde no puede ser posterior a fecha_hasta.")
        return self

class MetricaVariacionItem(BaseModel):
    valor_actual: Decimal
    valor_anterior: Decimal
    variacion_porcentaje: Decimal
    tendencia: Literal["positivo", "negativo", "neutro"]

class ResumenEjecutivoOut(BaseModel):
    periodo_inicio: date
    periodo_fin: date
    ingresos_totales: MetricaVariacionItem
    total_transacciones: MetricaVariacionItem
    ticket_promedio: MetricaVariacionItem
    unidades_vendidas: MetricaVariacionItem
    margen_bruto_estimado: Decimal

class PuntoSerieTemporalOut(BaseModel):
    etiqueta_tiempo: str
    fecha_inicio: date
    monto_ingresos: Decimal
    cantidad_ordenes: int

class SerieTemporalOut(BaseModel):
    agrupacion: Literal["diaria", "semanal", "mensual"]
    puntos: List[PuntoSerieTemporalOut]

class ProductoTopOut(BaseModel):
    id_producto: int
    nombre_producto: str
    sku_referencia: str
    categoria_nombre: str
    unidades_vendidas: int
    monto_total_generado: Decimal
    porcentaje_contribucion: Decimal

class TopProductosOut(BaseModel):
    limite: int
    productos: List[ProductoTopOut]

class CategoriaDistribucionOut(BaseModel):
    id_categoria: int
    nombre_categoria: str
    monto_facturado: Decimal
    unidades_vendidas: int
    porcentaje_participacion: Decimal

class DistribucionCategoriasOut(BaseModel):
    items: List[CategoriaDistribucionOut]

class CanalDistribucionOut(BaseModel):
    canal_codigo: str
    canal_nombre: str
    monto_facturado: Decimal
    total_ordenes: int
    porcentaje_participacion: Decimal

class DistribucionCanalesOut(BaseModel):
    items: List[CanalDistribucionOut]

class SucursalComparativaOut(BaseModel):
    id_sucursal: int
    nombre_sucursal: str
    ciudad: str
    monto_facturado: Decimal
    total_ventas: int
    ticket_promedio: Decimal
    porcentaje_red: Decimal

class ComparativaSucursalesOut(BaseModel):
    sucursales: List[SucursalComparativaOut]
```

### 3.4 Motor Analitico (`servicio.py`)
La clase `ServicioIndicadoresEmpresariales` encapsulara las reglas de agrupacion relacional:
1. **Resolucion de Fechas:** Metodo `_resolver_rango_fechas(filtros)` calcula `(inicio_actual, fin_actual)` y `(inicio_anterior, fin_anterior)` preservando una longitud de intervalo identica para computar variaciones relativas.
2. **Segregacion por Sede:**
   - Si `usuario.rol.nombre == 'encargado_sucursal'`, se fuerza `id_sucursal = usuario.id_sucursal`.
   - Si es `administrador`, se permite `id_sucursal` voluntario o `None` (global).
3. **Consultas Agregadas Clave:**
   - **Resumen:** Agregacion sobre ventas pagadas y computo sin division entre cero.
   - **Serie Temporal:** Agrupacion con date_trunc.
   - **Top Productos:** Ranking agregado con limite parametrizable.
   - **Canales:** Agrupacion por v.tipo_venta (presencial, digital_web, digital_movil).
   - **Comparativa de Sucursales:** Agrupacion por v.id_sucursal con validacion de rol admin.

### 3.5 Router REST FastAPI (`router.py`)
Rutas expuestas bajo `/api/v1/admin/indicadores`:
- `GET /resumen`: Retorna `ResumenEjecutivoOut`.
- `GET /serie-temporal`: Retorna `SerieTemporalOut`.
- `GET /top-productos`: Retorna `TopProductosOut` con parametro opcional `limite: int = 5`.
- `GET /distribucion-categorias`: Retorna `DistribucionCategoriasOut`.
- `GET /distribucion-canales`: Retorna `DistribucionCanalesOut`.
- `GET /sucursales-comparativa`: Retorna `ComparativaSucursalesOut` (valida rol admin, arroja HTTP 403 si encargado).

---

## 4. Diseno del Frontend Web (`Ec-frontend` - Angular 19+ Standalone)

### 4.1 Modulo y Enrutamiento
- **Ubicacion de Componentes:** `src/app/modules/comercial/cu29_indicadores/`
  - `modelos/indicadores.dto.ts`
  - `servicios/indicadores-admin.service.ts`
  - `servicios/indicadores-admin.service.spec.ts`
  - `paginas/indicadores-admin.component.ts`
  - `paginas/indicadores-admin.component.html`
  - `paginas/indicadores-admin.component.scss`
  - `paginas/indicadores-admin.component.spec.ts`
- **Ruta Oficial:** `/admin/indicadores` registrada en `app.routes.ts` con guards `[authGuard, roleGuard(['administrador', 'encargado_sucursal'])]`.

### 4.2 Integracion en AdminDashboardComponent (Regla Anti-Botones Estaticos)
En `src/app/modules/admin/dashboard/admin-dashboard.component.html`:
Tarjeta corporativa con badge "Business Intelligence", directiva dual `routerLink="/admin/indicadores"` y `(click)="navegar('/admin/indicadores', $event)"`, boton `#btn-visualizar-indicadores-empresariales` e icono vectorial SVG limpio.

En `src/app/modules/admin/dashboard/admin-dashboard.component.spec.ts`:
Prueba unitaria de despacho de evento click sobre `#btn-visualizar-indicadores-empresariales` verificando la invocacion de navegacion.

### 4.3 Servicio HTTP Reactivo (`IndicadoresAdminService`)
Manejara Signals reactivos para almacenamiento en cache y refresco sincronizado:
- `resumen = signal<ResumenEjecutivo | null>(null)`
- `serieTemporal = signal<SerieTemporal | null>(null)`
- `topProductos = signal<ProductoTop[]>([]);`
- `distribucionCategorias = signal<CategoriaDistribucion[]>([]);`
- `distribucionCanales = signal<CanalDistribucion[]>([]);`
- `comparativaSucursales = signal<SucursalComparativa[]>([]);`
- `filtros = signal<IndicadoresFiltros>({ periodo: '30d' });`
- `cargando = signal<boolean>(false);`
- `error = signal<string | null>(null);`

### 4.4 Componente Principal y Visualizaciones Graficas en SVG Nativo
`IndicadoresAdminComponent` utilizara ChangeDetectionStrategy.OnPush:
1. **Header Editorial:** Con H1 "Visualizar indicadores empresariales", breadcrumbs corporativos y selector de sucursal (deshabilitado con badge para encargados).
2. **Selector Temporal Dinamico:** Grupo de botones segmented control para periodos rapidos y campos inline para fechas personalizadas.
3. **Tarjetas de KPIs:** Despliegue de valores monetarios formateados en moneda local (Bs.) e indicador porcentual de variacion cromatica discreta.
4. **Grafica SVG Nativa 1: Curva de Serie Temporal:** Ejes X e Y con lineas SVG `<line>`, cuadricula, puntos interactivos `<circle>` con tooltips nativos y gradiente lineal SVG `<linearGradient>`.
5. **Grafica SVG Nativa 2: Barras Horizontales Top Productos:** Barras relativas de ancho porcentual proporcionales al maximo.
6. **Grafica SVG Nativa 3: Distribucion por Canal y Categoria:** Barras de segmento porcentual con codificacion cromatica clara.
7. **Tabla / Comparativa de Red:** Exclusiva para administradores (`esAdmin()`).

---

## 5. Estrategia de Pruebas Automatizadas

### 5.1 Backend (`pytest` en `Ec-backend`)
Archivo: `tests/modules/comercial/test_cu29_indicadores.py` con 17 pruebas automatizadas.

### 5.2 Frontend Web (`vitest` en `Ec-frontend`)
1. `admin-dashboard.component.spec.ts`: 21 pruebas unitarias.
2. `indicadores-admin.service.spec.ts`: 10 pruebas unitarias.
3. `indicadores-admin.component.spec.ts`: 11 pruebas unitarias.
