# Especificacion Tecnica Permanente: CU21 - Gestionar Sucursales y Ciudades

**Codigo:** CU21  
**Nombre:** Gestionar Sucursales y Ciudades  
**Paquete de Dominio:** `gestion_operativa`  
**Directorio Funcional Backend:** `app/modules/gestion_operativa/cu21_sucursales_ciudades`  
**Directorio Funcional Frontend:** `src/app/modules/gestion_operativa/cu21_sucursales_ciudades`  
**Directorio Funcional Mobile:** `lib/src/features/gestion_operativa/cu21_sucursales_ciudades`  
**Actores Primarios:** Administrador (Acceso total de administracion)  
**Actores Secundarios:** Cliente, Encargado de Sucursal, Cajero, Sistema (Consulta publica de red de tiendas)  
**Metodologia:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Version:** 1.0.0 (Linea Base Permanente)  
**Estado:** Aprobado y Promovido a Permanente  
**Fuentes de Verdad:**
- Documentacion Funcional: `SI2-Parcial1.md` (Seccion 1.2.2 Objetivo 2, Seccion 1.4 Alcance, Seccion 2.1.1.1 Administrador, Seccion 2.1.1.2 CU21, Seccion 2.1.3 CU21 Lineas 807-823).
- Arquitectura de Referencia: `.agents/skills/fashionstore-backend-sdd/references/arquitectura.md` (Paquete Gestion Operativa: `RouterSucursal`, `ServicioGestionSucursal`, `SucursalORM`, `CiudadORM`).
- Modelo de Dominio: `.agents/skills/fashionstore-backend-sdd/references/dominio.md` (Invariantes de sucursales, unicidad `UNIQUE(id_ciudad, nombre)` y relaciones foraneas).
- Design System Multiplataforma: `.agents/skills/fashionstore-frontend-sdd/references/fashionstore-tokens.md` (Sistema de espaciado Base-2, tipografia Outfit, paleta Slate/Camel/Obsidian).

---

## 1. Definicion Funcional y Reglas de Negocio

### 1.1 Proposito y Alcance
El caso de uso CU21 proporciona las capacidades de administracion territorial y operativa para la red de boutiques de alta costura de FashionStore. Permite gestionar de manera centralizada las ciudades autorizadas para la actividad comercial y las boutiques fisicas asociadas, salvaguardando la integridad referencial del inventario, la asignacion de personal y las reservas activas de clientes.

### 1.2 Reglas de Negocio Estrictas

1. **RB-1: Autenticacion y Autorizacion Administrativa:**
   - Toda operacion de modificacion (creacion, actualizacion, cambio de estado y eliminacion) en ciudades y sucursales exige token JWT valido con rol `administrador`.
   - La consulta publica de tiendas activas se expone de forma abierta para clientes y aplicaciones de consulta general.

2. **RB-2: Unicidad y Normalizacion Territorial:**
   - Los nombres de las ciudades deben ser unicos en el sistema (insensible a mayusculas, minusculas y espacios perimetrales).
   - Se requiere un codigo de pais valido (estandar ISO Alpha-2, valor por defecto "BO").

3. **RB-3: Invariantes Temporales de Sucursal:**
   - Toda boutique fisica debe definir un horario de apertura (`horario_apertura`) y de cierre (`horario_cierre`) en formato `HH:mm`.
   - El `horario_cierre` debe ser cronologicamente posterior al `horario_apertura`. Una solicitud que contravenga esta regla es rechazada con error de validacion 422.

4. **RB-4: Unicidad de Boutique por Ciudad:**
   - La combinacion `(id_ciudad, nombre)` es estrictamente unica en la persistencia relacional. No pueden coexistir dos sucursales con el mismo nombre comercial dentro de una misma ciudad.

5. **RB-5: Integridad Territorial y Proteccion de Dependencias (Ciudad):**
   - Una ciudad no puede eliminarse si cuenta con sucursales asociadas (activas o inactivas) o si existen clientes con dicha ciudad registrada como preferida.
   - El intento de eliminacion devuelve codigo HTTP 409 Conflict (`CIUDAD_CON_DEPENDENCIAS_ACTIVAS`).

6. **RB-6: Integridad Operativa y Proteccion de Operaciones Cautivas (Sucursal):**
   - Una sucursal no puede ser desactivada (`activa = false`) ni eliminada si posee reservas activas pendientes de atencion (`pendiente`, `confirmada`, `en_atencion`) o si conserva unidades de inventario fisico disponible (`cantidad_disponible > 0`).
   - El sistema bloquea la transicion y devuelve codigo HTTP 409 Conflict (`SUCURSAL_CON_OPERACIONES_PENDIENTES`).

7. **RB-7: Separacion Estricta de Vistas Publica y Administrativa:**
   - Endpoint publico `/api/v1/sucursales`: Filtra estrictamente `activa = true`, ordenado por ciudad y nombre, exponiendo direccion, telefono y horarios para atencion a clientes.
   - Endpoint administrativo `/api/v1/admin/sucursales`: Retorna el universo completo (activas e inactivas) enriquecido con metricas de negocio (total de empleados asignados, unidades de inventario en custodia).

8. **RB-8: Consistencia de Estado Reactivo y UX:**
   - En entornos frontend (Web y Mobile), cualquier mutacion exitosa actualiza inmediatamente las colecciones locales sin recargas forzadas de pagina, y ante errores 409/422 se preservan los formularios con mensajes contextuales.

---

## 2. Arquitectura de Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0 + PostgreSQL Neon)

### 2.1 Modelos de Persistencia ORM (`app/modules/gestion_operativa/modelos.py`)
Mapeo sobre esquema `fashionstore`:

```python
class CiudadORM(Base):
    __tablename__ = "ciudades"
    __table_args__ = {"schema": "fashionstore"}

    id_ciudad: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    pais: Mapped[str] = mapped_column(String(50), nullable=False, default="Bolivia")
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    sucursales: Mapped[list["SucursalORM"]] = relationship(
        "SucursalORM", back_populates="ciudad", cascade="all, delete-orphan"
    )

class SucursalORM(Base):
    __tablename__ = "sucursales"
    __table_args__ = (
        UniqueConstraint("id_ciudad", "nombre", name="uq_sucursal_ciudad_nombre"),
        {"schema": "fashionstore"},
    )

    id_sucursal: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_ciudad: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fashionstore.ciudades.id_ciudad", ondelete="RESTRICT"), nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    direccion: Mapped[str] = mapped_column(String(255), nullable=False)
    telefono: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    horario_apertura: Mapped[time] = mapped_column(Time, nullable=False)
    horario_cierre: Mapped[time] = mapped_column(Time, nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    ciudad: Mapped["CiudadORM"] = relationship("CiudadORM", back_populates="sucursales")
```

### 2.2 Esquemas Pydantic v2 (`app/modules/gestion_operativa/cu21_sucursales_ciudades/esquemas.py`)
- `CiudadCreateIn`: Nombre obligatorio (2-100 caracteres normalizados), codigo o nombre de pais.
- `CiudadUpdateIn`: Nombre y pais opcionales.
- `CiudadOut`: Identificador, nombre, pais, fecha de creacion.
- `CiudadConSucursalesOut`: Extiende `CiudadOut` con conteo de boutiques asociadas.
- `SucursalCreateIn`: Identificador de ciudad, nombre de boutique, direccion, telefono, horarios de apertura y cierre con validador de secuencia temporal.
- `SucursalUpdateIn`: Atributos mutables de sucursal con validador de secuencia temporal.
- `SucursalEstadoIn`: Booleano `activa` para alternancia rapida de estado operativo.
- `SucursalOut`: Identificador, ciudad, nombre, direccion, telefono, horarios formateados (`HH:mm`), estado activo y marca de tiempo.
- `SucursalAdminOut`: Extiende `SucursalOut` con nombre de ciudad, empleados asignados y total de stock inventariado.
- `SucursalPublicaOut`: DTO limpio optimizado para clientes y visitantes.

### 2.3 Excepciones de Dominio (`app/modules/gestion_operativa/cu21_sucursales_ciudades/errores.py`)
- `CiudadNoEncontradaError` -> HTTP 404 (`CIUDAD_NO_ENCONTRADA`)
- `CiudadDuplicadaError` -> HTTP 409 (`CIUDAD_DUPLICADA`)
- `CiudadConDependenciasError` -> HTTP 409 (`CIUDAD_CON_DEPENDENCIAS_ACTIVAS`)
- `SucursalNoEncontradaError` -> HTTP 404 (`SUCURSAL_NO_ENCONTRADA`)
- `SucursalDuplicadaError` -> HTTP 409 (`SUCURSAL_DUPLICADA`)
- `SucursalConOperacionesError` -> HTTP 409 (`SUCURSAL_CON_OPERACIONES_PENDIENTES`)
- `HorarioInvalidoError` -> HTTP 422 (`HORARIO_INVALIDO`)

### 2.4 Endpoints HTTP Registrados (`app/modules/gestion_operativa/cu21_sucursales_ciudades/router.py`)
- `GET /api/v1/ciudades`: Listado de ciudades (publico).
- `GET /api/v1/sucursales`: Listado de sucursales activas con filtro opcional `?id_ciudad=` (publico).
- `GET /api/v1/admin/ciudades`: Listado administrativo de ciudades con conteo de sucursales.
- `POST /api/v1/admin/ciudades`: Creacion de ciudad (exclusivo admin).
- `PUT /api/v1/admin/ciudades/{id_ciudad}`: Modificacion de ciudad (exclusivo admin).
- `DELETE /api/v1/admin/ciudades/{id_ciudad}`: Baja fisica de ciudad con validacion de integridad referencial.
- `GET /api/v1/admin/sucursales`: Listado de sucursales con metricas de inventario y empleados.
- `POST /api/v1/admin/sucursales`: Registro de boutique fisica con validacion de invariantes.
- `GET /api/v1/admin/sucursales/{id_sucursal}`: Detalle de boutique.
- `PUT /api/v1/admin/sucursales/{id_sucursal}`: Modificacion de boutique.
- `PATCH /api/v1/admin/sucursales/{id_sucursal}/estado`: Alternancia de estado con verificacion de stock y reservas.
- `DELETE /api/v1/admin/sucursales/{id_sucursal}`: Eliminacion de sucursal.

---

## 3. Arquitectura Frontend Web (`Ec-frontend` - Angular 19+)

### 3.1 Componente de Pagina Standalone
- **Ruta:** `/admin/sucursales` protegida por `authGuard`.
- **Archivo:** `src/app/modules/gestion_operativa/cu21_sucursales_ciudades/paginas/sucursales-admin.component.ts`.
- **Estrategia:** `ChangeDetectionStrategy.OnPush`, 100% Standalone (`standalone: true`).

### 3.2 Estado Reactivo con Angular Signals
- `pestanaActiva = signal<'sucursales' | 'ciudades'>('sucursales')`
- `sucursales = signal<SucursalAdmin[]>`
- `ciudades = signal<CiudadConSucursales[]>`
- `filtroCiudad = signal<number | null>(null)`
- `terminoBusqueda = signal<string>('')`
- `cargando = signal<boolean>(false)`
- `guardando = signal<boolean>(false)`
- `errorMensaje = signal<string | null>(null)`
- `exitoMensaje = signal<string | null>(null)`
- `sucursalesFiltradas = computed(...)`: Computo reactivo en memoria que filtra por ciudad y termino de busqueda sobre nombre y direccion.

### 3.3 Formularios Reactivos Fuertemente Tipados
- Uso de `NonNullableFormBuilder`.
- `sucursalForm`: Controles para `id_ciudad`, `nombre`, `direccion`, `telefono`, `horario_apertura`, `horario_cierre`, `activa`.
- `ciudadForm`: Controles para `nombre` y `pais`.
- Validador sincrono personalizado `validarHorarios` que compara cadenas `HH:mm` e invalida el formulario si el cierre no es estrictamente posterior a la apertura.

### 3.4 Sistema de Diseno y Estilos
- Respeto riguroso a la escala de espaciado Base-2 de FashionStore (`p-4`, `p-6`, `space-y-4`, `gap-3`).
- Tipografia institucional **Outfit** (`font-sans font-semibold tracking-tight`).
- Badges de estado con contrastes editoriales: `ACTIVA` (`bg-emerald-50 text-emerald-800 border-emerald-200`), `INACTIVA` (`bg-slate-100 text-slate-700 border-slate-300`).
- Modal reactivo centrado con backdrop difuminado y banners de alerta dismissibles.

---

## 4. Arquitectura de Aplicacion Movil (`Ec-mobile` - Flutter 3.x + BLoC)

### 4.1 Topologia Feature-First Canónica
Ubicacion: `lib/src/features/gestion_operativa/cu21_sucursales_ciudades/`

1. **Capa de Dominio (`dominio/`):**
   - Entidades inmutables: `Ciudad` (`idCiudad`, `nombre`, `pais`, `totalSucursales`), `Sucursal` (`idSucursal`, `idCiudad`, `nombre`, `direccion`, `telefono`, `horarioApertura`, `horarioCierre`, `activa`, `nombreCiudad`, `totalEmpleados`, `totalInventario`).
   - Contrato abstracto: `SucursalesRepositorio`.

2. **Capa de Datos (`datos/`):**
   - Modelos DTO con serializacion json: `CiudadDto`, `SucursalDto`.
   - Datasource HTTP: `SucursalesRemotoDataSource` con cabeceras `Authorization: Bearer <token>` gestionadas mediante `SecureStorageService`.
   - Repositorio concreto: `SucursalesRepositorioImpl`.

3. **Capa de Presentacion (`presentacion/`):**
   - **BLoC de Gestion Territorial (`sucursales_bloc.dart`):**
     - Eventos: `CargarSucursalesCiudades`, `FiltrarPorCiudad`, `FiltrarPorTermino`, `CambiarEstadoSucursal`, `CrearSucursal`, `ActualizarSucursal`, `CrearCiudad`.
     - Estados sellados inmutables: `SucursalesInicial`, `SucursalesCargando`, `SucursalesCargado`, `SucursalesError`, `SucursalOperacionExitosa`.
   - **Pantalla Administrativa (`sucursales_admin_pantalla.dart`):**
     - Cabecera editorial Atelier con contador dinamico de sedes.
     - Campo de busqueda rapida en tiempo real y selector horizontal de chips de ciudades.
     - Tarjetas de boutique con insignia de estado y `Switch` interactivo con dialogo de confirmacion.
     - Formulario Bottom Sheet modal para creacion y edicion con selectores de hora nativos de 24 horas y validacion de inconsistencias horarias.

---

## 5. Matriz de Trazabilidad de Criterios de Aceptacion

| Criterio | Descripcion | Backend | Frontend Web | Mobile |
|:---|:---|:---:|:---:|:---:|
| **AC-1** | Autenticacion y Autorizacion de Administrador | Implementado | Implementado | Implementado |
| **AC-2** | Registro de Ciudades con Unicidad | Implementado | Implementado | Implementado |
| **AC-3** | Manejo de Conflicto en Ciudad Duplicada (409) | Implementado | Implementado | Implementado |
| **AC-4** | Registro de Sucursal con Invariantes de Negocio | Implementado | Implementado | Implementado |
| **AC-5** | Rechazo de Horarios Inconsistentes (422) | Implementado | Implementado | Implementado |
| **AC-6** | Proteccion de Integridad Territorial en Baja de Ciudad (409) | Implementado | Implementado | N/A |
| **AC-7** | Restriccion de Integridad en Desactivacion de Sucursal (409) | Implementado | Implementado | Implementado |
| **AC-8** | Consulta Publica de Sucursales Activas | Implementado | N/A | N/A |
| **AC-9** | Consulta Administrativa con Metricas de Inventario | Implementado | Implementado | Implementado |
| **AC-10** | Arquitectura Angular Standalone + Signals + Guards | N/A | Implementado | N/A |
| **AC-11** | Estandarizacion de Tokens Base-2 y Tipografia Outfit | N/A | Implementado | Implementado |
| **AC-12** | Interfaz con Tabs Editoriales (Boutiques y Ciudades) | N/A | Implementado | N/A |
| **AC-13** | Modal Reactivo con Validadores de Horario | N/A | Implementado | Implementado |
| **AC-14** | Despliegue de Advertencias ante Restricciones de Negocio | N/A | Implementado | Implementado |

---

## 6. Verificacion y Pruebas Automatizadas

La implementacion de CU21 fue validada de extremo a extremo en las tres plataformas tecnicas del ecosistema FashionStore:

1. **Backend (`Ec-backend`):**
   - Comando: `pytest`
   - Cobertura: 103/103 tests en verde (20 tests especificos para CU21 cubriendo modelos, endpoints publicos/privados, validacion de horarios, prevencion de desactivacion por inventario/reservas y eliminacion protegida).

2. **Frontend Web (`Ec-frontend`):**
   - Comandos: `ng test --watch=false` y `ng build`
   - Cobertura: 62/62 tests unitarios en verde (21 tests especificos para CU21 cubriendo servicio HTTP y componente de pagina). Compilacion de produccion limpia con 0 errores.

3. **Aplicacion Movil (`Ec-mobile`):**
   - Comandos: `flutter test` y `flutter analyze`
   - Cobertura: 73/73 tests en verde (17 tests especificos para CU21 cubriendo DTOs, datasource, repositorio, BLoC y widget de pantalla). 0 advertencias o incidencias reportadas por el analizador estatico de Dart.
