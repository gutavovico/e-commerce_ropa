# Diseno Tecnico de Arquitectura: [CU30] Consultar bitacora

## 1. Arquitectura de Datos (PostgreSQL Neon)

### DDL de la Tabla `fashionstore.bitacora`
```sql
CREATE TABLE IF NOT EXISTS fashionstore.bitacora (
    id_bitacora BIGSERIAL PRIMARY KEY,
    id_usuario INTEGER REFERENCES fashionstore.usuarios(id_usuario) ON DELETE SET NULL,
    usuario_nombre VARCHAR(255),
    accion VARCHAR(100) NOT NULL,
    tabla_modulo VARCHAR(100) NOT NULL,
    direccion_ip VARCHAR(45),
    severidad VARCHAR(20) NOT NULL DEFAULT 'INFO',
    payload_anterior JSONB,
    payload_nuevo JSONB,
    creado_en TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bitacora_creado_en ON fashionstore.bitacora (creado_en DESC);
CREATE INDEX IF NOT EXISTS idx_bitacora_severidad ON fashionstore.bitacora (severidad);
CREATE INDEX IF NOT EXISTS idx_bitacora_modulo ON fashionstore.bitacora (tabla_modulo);
CREATE INDEX IF NOT EXISTS idx_bitacora_usuario ON fashionstore.bitacora (id_usuario);
```

---

## 2. Modelado de Dominio Backend (FastAPI + SQLAlchemy 2.0 + Pydantic v2)

### Modelo ORM (`app/modules/seguridad/cu30_bitacora/modelos.py`)
- Clase `Bitacora(Base)` mapeada a `fashionstore.bitacora`.
- Campos tipados con `Mapped` y `mapped_column`:
  - `id_bitacora: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)`
  - `id_usuario: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("fashionstore.usuarios.id_usuario", ondelete="SET NULL"), nullable=True)`
  - `usuario_nombre: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)`
  - `accion: Mapped[str] = mapped_column(String(100), nullable=False)`
  - `tabla_modulo: Mapped[str] = mapped_column(String(100), nullable=False)`
  - `direccion_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)`
  - `severidad: Mapped[str] = mapped_column(String(20), nullable=False, default="INFO")`
  - `payload_anterior: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)`
  - `payload_nuevo: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)`
  - `creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)`

### Esquemas Pydantic v2 (`app/modules/seguridad/cu30_bitacora/esquemas.py`)
- `SeveridadEnum`: Literal['INFO', 'WARN', 'ERROR', 'CRITICAL']
- `OrdenarPorBitacora`: Literal['creado_en_desc', 'creado_en_asc', 'severidad_desc', 'accion_asc']
- `BitacoraMetricas`: metricas cuantitativas de auditoria.
- `BitacoraEventoResumen`: elemento en tabla cronologica con bandera computada `tiene_payload`.
- `BitacoraEventoDetalle`: incluye `payload_anterior` y `payload_nuevo` deserializados.
- `BitacoraListadoRespuesta`: envoltorio paginado con lista de eventos y metricas agregadas.

### Servicio de Auditoria (`app/modules/seguridad/cu30_bitacora/servicio.py`)
- Clase `ServicioBitacoraAuditoria`:
  - Validacion RBAC estricta: `verificar_permiso_administrador(usuario_actual)`.
  - `listar_eventos(db, filtros)`: construye query con filtrado dinamico y subconsultas de conteo para metricas.
  - `obtener_evento_por_id(db, id_bitacora)`: recupera evento unitario o emite `EventoBitacoraNoEncontradoError`.

---

## 3. Arquitectura Frontend Web (Angular 19+ Standalone, Signals)

### DTOs TypeScript (`src/app/modules/seguridad/cu30_bitacora/modelos/bitacora.dto.ts`)
```typescript
export type SeveridadBitacora = 'INFO' | 'WARN' | 'ERROR' | 'CRITICAL';
export type CriterioOrdenBitacora = 'creado_en_desc' | 'creado_en_asc' | 'severidad_desc' | 'accion_asc';

export interface BitacoraEventoResumen {
  id_bitacora: number;
  id_usuario: number | null;
  usuario_nombre: string | null;
  accion: string;
  tabla_modulo: string;
  direccion_ip: string | null;
  severidad: SeveridadBitacora;
  tiene_payload: boolean;
  creado_en: string;
}

export interface BitacoraEventoDetalle extends BitacoraEventoResumen {
  payload_anterior: Record<string, unknown> | null;
  payload_nuevo: Record<string, unknown> | null;
}

export interface BitacoraMetricas {
  total_eventos: number;
  eventos_criticos: number;
  advertencias_errores: number;
  usuarios_activos: number;
}
```

### Servicio HTTP (`src/app/modules/seguridad/cu30_bitacora/servicios/bitacora-admin.service.ts`)
- Utiliza `HttpClient` con cabecera `Authorization: Bearer <token>`.
- Mantiene senales reactivas: `eventos`, `metricas`, `totalEventos`, `totalPaginas`, `cargando`, `error`, `eventoSeleccionado`.

### Componente de Presentacion (`src/app/modules/seguridad/cu30_bitacora/paginas/bitacora-admin.component.ts`)
- Layout institucional max-w-[1440px].
- Grid de 4 tarjetas KPI con estetica boutique.
- Filtros reactivos con `Subject` y `debounceTime(300)`.
- Modal interactivo para visualizar `payload_anterior` y `payload_nuevo` en bloques de codigo preformateados.
