# Diseno Tecnico: CU21 - Gestionar Sucursales y Ciudades

**ID del Caso de Uso:** CU21  
**Nombre:** Gestionar Sucursales y Ciudades  
**Paquete Arquitectonico:** `gestion_operativa`  
**Modulo Backend:** `app/modules/gestion_operativa/cu21_sucursales_ciudades`  
**Referencia de Requisitos:** `.specs/changes/CU21/spec.md`  
**Estado:** Aprobado e Implementado  

---

## 1. Arquitectura General y Enfoque

El caso de uso CU21 administra la infraestructura fisica de la cadena FashionStore. Se organiza horizontalmente a traves de las tres capas del sistema:

1. **Backend (`Ec-backend`):** Monolito modular en capas (`Router -> Service -> ORM/Model`). Utiliza SQLAlchemy 2.0 y Pydantic v2 sobre el esquema `fashionstore` en PostgreSQL. Todas las operaciones de modificacion requieren transacciones explicitas y validacion de roles administrativos mediante dependencias FastAPI.
2. **Frontend Web (`Ec-frontend`):** Componentes Standalone de Angular 19+ con deteccion de cambios `OnPush` e inyeccion moderna mediante `inject()`. La reactividad se implementa con Angular Signals. La maquetacion utiliza el sistema de tokens Base-2 y la tipografia Outfit en un layout maximo de 1440px.
3. **Mobile (`Ec-mobile`):** Arquitectura Feature-First (`datos/`, `dominio/`, `presentacion/`) estructurada en Flutter 3.x y Dart 3. La logica de presentacion se gobierna mediante BLoC con eventos y estados sellados inmutables (`sealed class`), consumiendo tokens de diseno de `AppTheme` y almacenamiento seguro de sesion.

---

## 2. Diseno Backend (`Ec-backend`)

### 2.1 Modelo de Persistencia (SQLAlchemy 2.0)

Mapeo sobre las tablas existentes en el esquema `fashionstore`:

```python
# app/modules/gestion_operativa/modelos.py

from datetime import datetime, time
from typing import List, Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class CiudadORM(Base):
    __tablename__ = "ciudades"
    __table_args__ = {"schema": "fashionstore"}

    id_ciudad: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    pais: Mapped[str] = mapped_column(String(100), nullable=False, default="Bolivia")
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    sucursales: Mapped[List["SucursalORM"]] = relationship(
        "SucursalORM", back_populates="ciudad", cascade="all, delete-orphan"
    )


class SucursalORM(Base):
    __tablename__ = "sucursales"
    __table_args__ = (
        UniqueConstraint("id_ciudad", "nombre", name="uq_sucursales_ciudad_nombre"),
        {"schema": "fashionstore"},
    )

    id_sucursal: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_ciudad: Mapped[int] = mapped_column(
        Integer, ForeignKey("fashionstore.ciudades.id_ciudad"), nullable=False, index=True
    )
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    direccion: Mapped[str] = mapped_column(String(255), nullable=False)
    telefono: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    horario_apertura: Mapped[time] = mapped_column(Time, nullable=False, default=time(9, 0))
    horario_cierre: Mapped[time] = mapped_column(Time, nullable=False, default=time(20, 0))
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    ciudad: Mapped["CiudadORM"] = relationship("CiudadORM", back_populates="sucursales")
```

### 2.2 Schemas Pydantic v2

```python
# app/modules/gestion_operativa/cu21_sucursales_ciudades/esquemas.py

from datetime import datetime, time
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CiudadBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    pais: str = Field(default="Bolivia", min_length=2, max_length=100)


class CiudadCrearIn(CiudadBase):
    pass


class CiudadActualizarIn(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    pais: Optional[str] = Field(None, min_length=2, max_length=100)


class CiudadOut(CiudadBase):
    id_ciudad: int
    creado_en: datetime
    total_sucursales: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class SucursalBase(BaseModel):
    id_ciudad: int = Field(..., gt=0)
    nombre: str = Field(..., min_length=2, max_length=150)
    direccion: str = Field(..., min_length=5, max_length=255)
    telefono: Optional[str] = Field(None, max_length=30)
    horario_apertura: time = Field(default=time(9, 0))
    horario_cierre: time = Field(default=time(20, 0))


class SucursalCrearIn(SucursalBase):
    @field_validator("horario_cierre")
    @classmethod
    def validar_horarios(cls, v: time, info) -> time:
        apertura = info.data.get("horario_apertura")
        if apertura and v <= apertura:
            raise ValueError("El horario de cierre debe ser cronologicamente posterior al de apertura.")
        return v


class SucursalActualizarIn(BaseModel):
    id_ciudad: Optional[int] = Field(None, gt=0)
    nombre: Optional[str] = Field(None, min_length=2, max_length=150)
    direccion: Optional[str] = Field(None, min_length=5, max_length=255)
    telefono: Optional[str] = Field(None, max_length=30)
    horario_apertura: Optional[time] = None
    horario_cierre: Optional[time] = None


class SucursalEstadoIn(BaseModel):
    activa: bool


class SucursalPublicaOut(BaseModel):
    id_sucursal: int
    id_ciudad: int
    ciudad_nombre: str
    nombre: str
    direccion: str
    telefono: Optional[str]
    horario_apertura: str
    horario_cierre: str

    model_config = ConfigDict(from_attributes=True)


class SucursalAdminOut(SucursalPublicaOut):
    activa: bool
    creado_en: datetime
    total_empleados: int = 0
    total_prendas_stock: int = 0
    reservas_activas_conteo: int = 0
```

### 2.3 Excepciones de Dominio y Mapeo HTTP

```python
# app/modules/gestion_operativa/cu21_sucursales_ciudades/errores.py

from core.errors import DomainError


class CiudadDuplicadaError(DomainError):
    def __init__(self, nombre: str):
        super().__init__(
            message=f"La ciudad '{nombre}' ya se encuentra registrada en el sistema.",
            code="CIUDAD_DUPLICADA",
            status_code=409,
        )


class CiudadNoEncontradaError(DomainError):
    def __init__(self, id_ciudad: int):
        super().__init__(
            message=f"La ciudad con identificador {id_ciudad} no existe.",
            code="CIUDAD_NO_ENCONTRADA",
            status_code=404,
        )


class CiudadConDependenciasError(DomainError):
    def __init__(self, id_ciudad: int, detalle: str):
        super().__init__(
            message=f"No se puede eliminar la ciudad {id_ciudad}: {detalle}.",
            code="CIUDAD_CON_DEPENDENCIAS_ACTIVAS",
            status_code=409,
        )


class SucursalDuplicadaError(DomainError):
    def __init__(self, nombre: str, id_ciudad: int):
        super().__init__(
            message=f"Ya existe una sucursal con el nombre '{nombre}' en la ciudad {id_ciudad}.",
            code="SUCURSAL_DUPLICADA",
            status_code=409,
        )


class SucursalNoEncontradaError(DomainError):
    def __init__(self, id_sucursal: int):
        super().__init__(
            message=f"La sucursal con identificador {id_sucursal} no fue encontrada.",
            code="SUCURSAL_NO_ENCONTRADA",
            status_code=404,
        )


class SucursalConOperacionesPendientesError(DomainError):
    def __init__(self, id_sucursal: int, motivo: str):
        super().__init__(
            message=f"No se puede desactivar o eliminar la sucursal {id_sucursal}: {motivo}.",
            code="SUCURSAL_CON_OPERACIONES_PENDIENTES",
            status_code=409,
        )


class HorarioSucursalInvalidoError(DomainError):
    def __init__(self):
        super().__init__(
            message="El horario de cierre debe ser posterior a la hora de apertura.",
            code="HORARIO_INVALIDO",
            status_code=422,
        )
```

### 2.4 Contratos de API REST

| Metodo | Ruta | Rol Requerido | Entrada | Salida | Respuestas |
|---|---|---|---|---|---|
| `GET` | `/api/v1/sucursales` | Publico / Cualquiera | Query: `id_ciudad?` | `List[SucursalPublicaOut]` | 200 |
| `GET` | `/api/v1/admin/ciudades` | `administrador` | Ninguno | `List[CiudadOut]` | 200, 401, 403 |
| `POST` | `/api/v1/admin/ciudades` | `administrador` | `CiudadCrearIn` | `CiudadOut` | 201, 400, 401, 403, 409 |
| `PUT` | `/api/v1/admin/ciudades/{id}` | `administrador` | `CiudadActualizarIn` | `CiudadOut` | 200, 400, 401, 403, 404, 409 |
| `DELETE`| `/api/v1/admin/ciudades/{id}` | `administrador` | Param: `id_ciudad` | `{"mensaje": str}` | 200, 401, 403, 404, 409 |
| `GET` | `/api/v1/admin/sucursales` | `administrador` | Query: `id_ciudad?`, `activa?`, `q?` | `List[SucursalAdminOut]` | 200, 401, 403 |
| `GET` | `/api/v1/admin/sucursales/{id}` | `administrador` | Param: `id_sucursal` | `SucursalAdminOut` | 200, 401, 403, 404 |
| `POST` | `/api/v1/admin/sucursales` | `administrador` | `SucursalCrearIn` | `SucursalAdminOut` | 201, 400, 401, 403, 409, 422 |
| `PUT` | `/api/v1/admin/sucursales/{id}` | `administrador` | `SucursalActualizarIn` | `SucursalAdminOut` | 200, 400, 401, 403, 404, 409, 422 |
| `PATCH`| `/api/v1/admin/sucursales/{id}/estado` | `administrador` | `SucursalEstadoIn` | `SucursalAdminOut` | 200, 401, 403, 404, 409 |
| `DELETE`| `/api/v1/admin/sucursales/{id}` | `administrador` | Param: `id_sucursal` | `{"mensaje": str}` | 200, 401, 403, 404, 409 |

### 2.5 Firmas del Servicio de Dominio

```python
# app/modules/gestion_operativa/cu21_sucursales_ciudades/servicio.py

from typing import List, Optional
from sqlalchemy.orm import Session
from app.modules.gestion_operativa.cu21_sucursales_ciudades.esquemas import (
    CiudadActualizarIn,
    CiudadCrearIn,
    CiudadOut,
    SucursalActualizarIn,
    SucursalAdminOut,
    SucursalCrearIn,
    SucursalPublicaOut,
)


class ServicioGestionSucursal:
    def __init__(self, db: Session):
        self.db = db

    def crear_ciudad(self, datos: CiudadCrearIn) -> CiudadOut:
        """Registra una nueva ciudad previa validacion de unicidad."""
        ...

    def listar_ciudades(self) -> List[CiudadOut]:
        """Obtiene el listado de ciudades con conteo de sucursales asociadas."""
        ...

    def actualizar_ciudad(self, id_ciudad: int, datos: CiudadActualizarIn) -> CiudadOut:
        """Actualiza el nombre o pais de una ciudad."""
        ...

    def eliminar_ciudad(self, id_ciudad: int) -> None:
        """Elimina una ciudad si no posee dependencias activas (sucursales o clientes)."""
        ...

    def crear_sucursal(self, datos: SucursalCrearIn) -> SucursalAdminOut:
        """Crea una sucursal validando horarios y unicidad por ciudad."""
        ...

    def listar_sucursales_publicas(self, id_ciudad: Optional[int] = None) -> List[SucursalPublicaOut]:
        """Consulta publica de boutiques operativas y activas."""
        ...

    def listar_sucursales_admin(
        self,
        id_ciudad: Optional[int] = None,
        activa: Optional[bool] = None,
        q: Optional[str] = None,
    ) -> List[SucursalAdminOut]:
        """Consulta administrativa integral con estadisticas de personal e inventario."""
        ...

    def obtener_sucursal(self, id_sucursal: int) -> SucursalAdminOut:
        """Obtiene el detalle completo de una sucursal."""
        ...

    def actualizar_sucursal(self, id_sucursal: int, datos: SucursalActualizarIn) -> SucursalAdminOut:
        """Modifica datos de contacto, direccion o franja horaria."""
        ...

    def cambiar_estado_sucursal(self, id_sucursal: int, activa: bool) -> SucursalAdminOut:
        """Activa o desactiva la sucursal, bloqueando desactivacion si hay reservas o stock."""
        ...

    def eliminar_sucursal(self, id_sucursal: int) -> None:
        """Eliminacion fisica controlada si no cuenta con historial de operaciones."""
        ...
```

---

## 3. Diseno Frontend Web (`Ec-frontend` - Angular 19+)

### 3.1 Modelos y DTOs TypeScript

```typescript
// src/app/modules/gestion_operativa/cu21_sucursales_ciudades/modelos/sucursal.model.ts

export interface Ciudad {
  id_ciudad: number;
  nombre: string;
  pais: string;
  creado_en: string;
  total_sucursales?: number;
}

export interface CiudadCrearPayload {
  nombre: string;
  pais: string;
}

export interface CiudadActualizarPayload {
  nombre?: string;
  pais?: string;
}

export interface SucursalPublica {
  id_sucursal: number;
  id_ciudad: number;
  ciudad_nombre: string;
  nombre: string;
  direccion: string;
  telefono: string | null;
  horario_apertura: string;
  horario_cierre: string;
}

export interface SucursalAdmin extends SucursalPublica {
  activa: boolean;
  creado_en: string;
  total_empleados: number;
  total_prendas_stock: number;
  reservas_activas_conteo: number;
}

export interface SucursalCrearPayload {
  id_ciudad: number;
  nombre: string;
  direccion: string;
  telefono?: string | null;
  horario_apertura: string; // formato "HH:mm"
  horario_cierre: string;   // formato "HH:mm"
}

export interface SucursalActualizarPayload {
  id_ciudad?: number;
  nombre?: string;
  direccion?: string;
  telefono?: string | null;
  horario_apertura?: string;
  horario_cierre?: string;
}

export interface SucursalEstadoPayload {
  activa: boolean;
}

export interface FiltrosSucursalAdmin {
  id_ciudad?: number | null;
  activa?: boolean | null;
  q?: string;
}
```

### 3.2 Contrato de Servicio HTTP (`SucursalesAdminService`)

```typescript
// src/app/modules/gestion_operativa/cu21_sucursales_ciudades/servicios/sucursales-admin.service.ts

import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  Ciudad,
  CiudadCrearPayload,
  CiudadActualizarPayload,
  SucursalAdmin,
  SucursalCrearPayload,
  SucursalActualizarPayload,
  SucursalEstadoPayload,
  FiltrosSucursalAdmin,
} from '../modelos/sucursal.model';

@Injectable({
  providedIn: 'root',
})
export class SucursalesAdminService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/admin';

  // --- CIUDADES ---
  obtenerCiudades(): Observable<Ciudad[]> {
    return this.http.get<Ciudad[]>(`${this.baseUrl}/ciudades`);
  }

  crearCiudad(payload: CiudadCrearPayload): Observable<Ciudad> {
    return this.http.post<Ciudad>(`${this.baseUrl}/ciudades`, payload);
  }

  actualizarCiudad(idCiudad: number, payload: CiudadActualizarPayload): Observable<Ciudad> {
    return this.http.put<Ciudad>(`${this.baseUrl}/ciudades/${idCiudad}`, payload);
  }

  eliminarCiudad(idCiudad: number): Observable<{ mensaje: string }> {
    return this.http.delete<{ mensaje: string }>(`${this.baseUrl}/ciudades/${idCiudad}`);
  }

  // --- SUCURSALES ---
  obtenerSucursales(filtros?: FiltrosSucursalAdmin): Observable<SucursalAdmin[]> {
    let params = new HttpParams();
    if (filtros?.id_ciudad) {
      params = params.set('id_ciudad', filtros.id_ciudad.toString());
    }
    if (filtros?.activa !== undefined && filtros?.activa !== null) {
      params = params.set('activa', filtros.activa.toString());
    }
    if (filtros?.q) {
      params = params.set('q', filtros.q);
    }
    return this.http.get<SucursalAdmin[]>(`${this.baseUrl}/sucursales`, { params });
  }

  obtenerSucursal(idSucursal: number): Observable<SucursalAdmin> {
    return this.http.get<SucursalAdmin>(`${this.baseUrl}/sucursales/${idSucursal}`);
  }

  crearSucursal(payload: SucursalCrearPayload): Observable<SucursalAdmin> {
    return this.http.post<SucursalAdmin>(`${this.baseUrl}/sucursales`, payload);
  }

  actualizarSucursal(idSucursal: number, payload: SucursalActualizarPayload): Observable<SucursalAdmin> {
    return this.http.put<SucursalAdmin>(`${this.baseUrl}/sucursales/${idSucursal}`, payload);
  }

  cambiarEstado(idSucursal: number, activa: boolean): Observable<SucursalAdmin> {
    return this.http.patch<SucursalAdmin>(`${this.baseUrl}/sucursales/${idSucursal}/estado`, { activa });
  }

  eliminarSucursal(idSucursal: number): Observable<{ mensaje: string }> {
    return this.http.delete<{ mensaje: string }>(`${this.baseUrl}/sucursales/${idSucursal}`);
  }
}
```

### 3.3 Diseno de Estado Reactivo con Angular Signals

En el componente `SucursalesAdminComponent`:

```typescript
// Estado principal
readonly ciudades = signal<Ciudad[]>([]);
readonly sucursales = signal<SucursalAdmin[]>([]);
readonly cargando = signal<boolean>(false);
readonly guardando = signal<boolean>(false);
readonly mensajeError = signal<string | null>(null);
readonly mensajeExito = signal<string | null>(null);

// Filtros reactivos
readonly filtroCiudad = signal<number | null>(null);
readonly filtroActiva = signal<boolean | null>(null);
readonly filtroBusqueda = signal<string>('');

// Estado de modales y formularios
readonly pestanaActiva = signal<'sucursales' | 'ciudades'>('sucursales');
readonly modalSucursalAbierto = signal<boolean>(false);
readonly modalCiudadAbierto = signal<boolean>(false);
readonly sucursalEnEdicion = signal<SucursalAdmin | null>(null);

// Computed Signals
readonly sucursalesFiltradas = computed(() => {
  const lista = this.sucursales();
  const ciudadId = this.filtroCiudad();
  const activa = this.filtroActiva();
  const q = this.filtroBusqueda().trim().toLowerCase();

  return lista.filter((s) => {
    const coincideCiudad = ciudadId === null || s.id_ciudad === ciudadId;
    const coincideEstado = activa === null || s.activa === activa;
    const coincideTexto =
      !q ||
      s.nombre.toLowerCase().includes(q) ||
      s.direccion.toLowerCase().includes(q) ||
      s.ciudad_nombre.toLowerCase().includes(q);

    return coincideCiudad && coincideEstado && coincideTexto;
  });
});

readonly totalBoutiquesActivas = computed(() =>
  this.sucursales().filter((s) => s.activa).length
);
```

---

## 4. Diseno Mobile (`Ec-mobile` - Flutter 3.x + BLoC)

### 4.1 Entidades y DTOs en Dart

```dart
// lib/src/features/gestion_operativa/cu21_sucursales_ciudades/dominio/entidades/sucursal.dart

class Ciudad {
  final int idCiudad;
  final String nombre;
  final String pais;
  final int totalSucursales;

  const Ciudad({
    required this.idCiudad,
    required this.nombre,
    required this.pais,
    this.totalSucursales = 0,
  });
}

class Sucursal {
  final int idSucursal;
  final int idCiudad;
  final String ciudadNombre;
  final String nombre;
  final String direccion;
  final String? telefono;
  final String horarioApertura;
  final String horarioCierre;
  final bool activa;
  final int totalEmpleados;
  final int totalPrendasStock;
  final int reservasActivasConteo;

  const Sucursal({
    required this.idSucursal,
    required this.idCiudad,
    required this.ciudadNombre,
    required this.nombre,
    required this.direccion,
    this.telefono,
    required this.horarioApertura,
    required this.horarioCierre,
    required this.activa,
    this.totalEmpleados = 0,
    this.totalPrendasStock = 0,
    this.reservasActivasConteo = 0,
  });
}
```

```dart
// lib/src/features/gestion_operativa/cu21_sucursales_ciudades/datos/modelos/sucursal_dto.dart

class SucursalDto {
  static Sucursal fromJson(Map<String, dynamic> json) {
    return Sucursal(
      idSucursal: json['id_sucursal'] as int,
      idCiudad: json['id_ciudad'] as int,
      ciudadNombre: json['ciudad_nombre'] as String? ?? '',
      nombre: json['nombre'] as String,
      direccion: json['direccion'] as String,
      telefono: json['telefono'] as String?,
      horarioApertura: json['horario_apertura'] as String,
      horarioCierre: json['horario_cierre'] as String,
      activa: json['activa'] as bool? ?? true,
      totalEmpleados: json['total_empleados'] as int? ?? 0,
      totalPrendasStock: json['total_prendas_stock'] as int? ?? 0,
      reservasActivasConteo: json['reservas_activas_conteo'] as int? ?? 0,
    );
  }

  static Map<String, dynamic> toCrearJson({
    required int idCiudad,
    required String nombre,
    required String direccion,
    String? telefono,
    required String horarioApertura,
    required String horarioCierre,
  }) {
    return {
      'id_ciudad': idCiudad,
      'nombre': nombre,
      'direccion': direccion,
      'telefono': telefono,
      'horario_apertura': horarioApertura,
      'horario_cierre': horarioCierre,
    };
  }
}
```

### 4.2 Eventos y Estados Sellados de `SucursalesBloc`

```dart
// lib/src/features/gestion_operativa/cu21_sucursales_ciudades/presentacion/bloc/sucursales_event.dart

sealed class SucursalesEvent {
  const SucursalesEvent();
}

final class CargarSucursalesYCiudadesEvent extends SucursalesEvent {
  final int? idCiudad;
  final bool? activa;
  const CargarSucursalesYCiudadesEvent({this.idCiudad, this.activa});
}

final class FiltrarPorCiudadEvent extends SucursalesEvent {
  final int? idCiudad;
  const FiltrarPorCiudadEvent(this.idCiudad);
}

final class CambiarEstadoSucursalEvent extends SucursalesEvent {
  final int idSucursal;
  final bool nuevaActiva;
  const CambiarEstadoSucursalEvent({required this.idSucursal, required this.nuevaActiva});
}

final class GuardarSucursalEvent extends SucursalesEvent {
  final int? idSucursal; // null si es creacion
  final int idCiudad;
  final String nombre;
  final String direccion;
  final String? telefono;
  final String horarioApertura;
  final String horarioCierre;

  const GuardarSucursalEvent({
    this.idSucursal,
    required this.idCiudad,
    required this.nombre,
    required this.direccion,
    this.telefono,
    required this.horarioApertura,
    required this.horarioCierre,
  });
}
```

```dart
// lib/src/features/gestion_operativa/cu21_sucursales_ciudades/presentacion/bloc/sucursales_state.dart

sealed class SucursalesState {
  const SucursalesState();
}

final class SucursalesInicial extends SucursalesState {
  const SucursalesInicial();
}

final class SucursalesCargando extends SucursalesState {
  const SucursalesCargando();
}

final class SucursalesCargadas extends SucursalesState {
  final List<Ciudad> ciudades;
  final List<Sucursal> sucursales;
  final int? idCiudadSeleccionada;

  const SucursalesCargadas({
    required this.ciudades,
    required this.sucursales,
    this.idCiudadSeleccionada,
  });

  List<Sucursal> get sucursalesFiltradas {
    if (idCiudadSeleccionada == null) return sucursales;
    return sucursales.where((s) => s.idCiudad == idCiudadSeleccionada).toList();
  }
}

final class SucursalesOperacionExitosa extends SucursalesState {
  final String mensaje;
  const SucursalesOperacionExitosa(this.mensaje);
}

final class SucursalesError extends SucursalesState {
  final String mensaje;
  final String? codigo;
  const SucursalesError({required this.mensaje, this.codigo});
}
```

### 4.3 Firma del Repositorio de Infraestructura

```dart
// lib/src/features/gestion_operativa/cu21_sucursales_ciudades/dominio/repositorios/sucursales_repositorio.dart

abstract interface class SucursalesRepositorio {
  Future<List<Ciudad>> obtenerCiudades();
  Future<Ciudad> crearCiudad(String nombre, String pais);
  Future<List<Sucursal>> obtenerSucursales({int? idCiudad, bool? activa, String? q});
  Future<Sucursal> crearSucursal({
    required int idCiudad,
    required String nombre,
    required String direccion,
    String? telefono,
    required String horarioApertura,
    required String horarioCierre,
  });
  Future<Sucursal> actualizarSucursal({
    required int idSucursal,
    int? idCiudad,
    String? nombre,
    String? direccion,
    String? telefono,
    String? horarioApertura,
    String? horarioCierre,
  });
  Future<void> cambiarEstadoSucursal(int idSucursal, bool activa);
  Future<void> eliminarSucursal(int idSucursal);
}
```

---

## 5. Estrategia de Verificacion y Pruebas

1. **Backend (`pytest`):**
   - Creacion exitosa de ciudad y validacion de unicidad.
   - Creacion exitosa de sucursal con horarios validos (`201 Created`).
   - Verificacion de rechazo ante horarios invertidos (`422 Unprocessable Entity`).
   - Intento de baja de ciudad con sucursales asociadas (`409 Conflict`).
   - Intento de desactivacion de sucursal con reservas pendientes o stock disponible (`409 Conflict`).
   - Acceso denegado para roles no administradores (`403 Forbidden`).
2. **Frontend (`Vitest` / `Angular CLI`):**
   - Inyeccion y llamada a metodos de `SucursalesAdminService`.
   - Estado reactivo con Signals: filtrado dinamico por ciudad y texto.
   - Manejo y transformacion de errores HTTP 409 a mensajes legibles de advertencia.
3. **Mobile (`flutter test`):**
   - Pruebas unitarias de `SucursalesBloc` emitiendo estados `SucursalesCargando` y `SucursalesCargadas`.
   - Emision de `SucursalesError` ante fallo de red o rechazo de integridad.
   - Mocks tipados de `SucursalesRepositorio`.
