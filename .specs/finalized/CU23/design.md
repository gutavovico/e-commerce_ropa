# Diseno Tecnico: CU23 - Gestionar Categorias, Tallas y Colores

**ID del Caso de Uso:** CU23  
**Nombre:** Gestionar Categorias, Tallas y Colores  
**Paquete Arquitectonico:** `gestion_operativa`  
**Modulo Backend:** `app/modules/gestion_operativa/cu23_categorias_tallas_colores`  
**Modulo Frontend Web:** `src/app/modules/gestion_operativa/cu23_categorias_tallas_colores`  
**Referencia de Requisitos:** `.specs/changes/CU23/spec.md`  
**Estado:** En Revision Tecnica (Fase 2 - Diseno)  

---

## 1. Arquitectura General y Enfoque

El caso de uso CU23 centraliza la administracion de los atributos taxonomicos y de catalogacion de la cadena FashionStore. A diferencia de casos de uso transversales a las tres plataformas, CU23 adopta una arquitectura bipartita justificada:

1. **Backend (`Ec-backend`):** Monolito modular en capas (`Router -> Service -> ORM/Model`). Utiliza SQLAlchemy 2.0 y Pydantic v2 sobre el esquema relacional `fashionstore` en PostgreSQL Neon. Implementa control transaccional estricto, deteccion de ciclos aciclicos dirigidos (DAG) en la jerarquia de categorias y validaciones de integridad referencial previo a cualquier operacion de eliminacion.
2. **Frontend Web (`Ec-frontend`):** Componente Standalone de Angular 19+ (`CategoriasTallasColoresAdminComponent`) con deteccion de cambios `OnPush` e inyeccion moderna mediante `inject()`. La reactividad se implementa con Angular Signals. La interfaz organiza la administracion en tres pestañas editoriales independientes ("Categorias", "Tallas", "Colores"), empleando formularios fuertemente tipados con `NonNullableFormBuilder` y selectores visuales sincronizados.
3. **Exclusion de Mobile (`Ec-mobile`):** Se ratifica la exclusion de componentes de gestion en la aplicacion movil, dado que los operarios y clientes moviles unicamente consumen estos catalogos en modo lectura mediante los endpoints publicos ya expuestos.

---

## 2. Diseno Backend (`Ec-backend`)

### 2.1 Modelo de Persistencia (SQLAlchemy 2.0)

Mapeo sobre las tablas existentes en el esquema `fashionstore` de PostgreSQL:

```python
# app/modules/gestion_operativa/cu23_categorias_tallas_colores/modelos.py

from typing import List, Optional
from sqlalchemy import (
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class CategoriaORM(Base):
    """Mapeo de la tabla `fashionstore.categorias`.
    
    Soporta jerarquia auto-referencial (padre/hijas) para clasificacion taxonomica.
    """
    __tablename__ = "categorias"
    __table_args__ = {"schema": "fashionstore"}

    id_categoria: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    id_categoria_padre: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("fashionstore.categorias.id_categoria", ondelete="RESTRICT"), nullable=True, index=True
    )

    # Relaciones auto-referenciales
    categoria_padre: Mapped[Optional["CategoriaORM"]] = relationship(
        "CategoriaORM", remote_side=[id_categoria], back_populates="subcategorias"
    )
    subcategorias: Mapped[List["CategoriaORM"]] = relationship(
        "CategoriaORM", back_populates="categoria_padre", cascade="all"
    )


class TallaORM(Base):
    """Mapeo de la tabla `fashionstore.tallas`.
    
    Estandariza los codigos de talla con un orden secuencial numerico estricto.
    """
    __tablename__ = "tallas"
    __table_args__ = {"schema": "fashionstore"}

    id_talla: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    orden: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)


class ColorORM(Base):
    """Mapeo de la tabla `fashionstore.colores`.
    
    Configura la paleta textil con denominacion de diseno y representacion hexadecimal #HEX.
    """
    __tablename__ = "colores"
    __table_args__ = {"schema": "fashionstore"}

    id_color: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    codigo_hex: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
```

---

### 2.2 Schemas Pydantic v2

```python
# app/modules/gestion_operativa/cu23_categorias_tallas_colores/esquemas.py

import re
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

REGEX_HEX_COLOR = r"^#[0-9A-Fa-f]{6}$"


# =============================================================================
# SCHEMAS: CATEGORIAS
# =============================================================================

class CategoriaBaseIn(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre de la categoria")
    id_categoria_padre: Optional[int] = Field(None, gt=0, description="ID de la categoria padre si es subcategoria")

    @field_validator("nombre")
    @classmethod
    def normalizar_nombre(cls, v: str) -> str:
        v_limpio = " ".join(v.strip().split())
        if len(v_limpio) < 2:
            raise ValueError("El nombre de la categoria debe contener al menos 2 caracteres.")
        return v_limpio


class CategoriaCrearIn(CategoriaBaseIn):
    pass


class CategoriaActualizarIn(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    id_categoria_padre: Optional[int] = Field(None, description="Nuevo ID de padre o null para convertir en raiz")

    @field_validator("nombre")
    @classmethod
    def normalizar_nombre_opcional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_limpio = " ".join(v.strip().split())
            if len(v_limpio) < 2:
                raise ValueError("El nombre de la categoria debe contener al menos 2 caracteres.")
            return v_limpio
        return v


class CategoriaOut(BaseModel):
    id_categoria: int
    nombre: str
    id_categoria_padre: Optional[int] = None
    padre_nombre: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CategoriaAdminOut(CategoriaOut):
    total_productos: int = 0
    total_subcategorias: int = 0


class CategoriaJerarquicaOut(CategoriaOut):
    subcategorias: List["CategoriaJerarquicaOut"] = []


# =============================================================================
# SCHEMAS: TALLAS
# =============================================================================

class TallaBaseIn(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=10, description="Codigo comercial de la talla (ej. XS, S, 38)")
    orden: int = Field(default=0, ge=0, le=32767, description="Orden secuencial de presentacion comercial")

    @field_validator("codigo")
    @classmethod
    def normalizar_codigo(cls, v: str) -> str:
        v_limpio = v.strip().upper()
        if not v_limpio:
            raise ValueError("El codigo de talla no puede estar vacio.")
        return v_limpio


class TallaCrearIn(TallaBaseIn):
    pass


class TallaActualizarIn(BaseModel):
    codigo: Optional[str] = Field(None, min_length=1, max_length=10)
    orden: Optional[int] = Field(None, ge=0, le=32767)

    @field_validator("codigo")
    @classmethod
    def normalizar_codigo_opcional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_limpio = v.strip().upper()
            if not v_limpio:
                raise ValueError("El codigo de talla no puede estar vacio.")
            return v_limpio
        return v


class TallaOut(BaseModel):
    id_talla: int
    codigo: str
    orden: int

    model_config = ConfigDict(from_attributes=True)


class TallaAdminOut(TallaOut):
    total_variantes: int = 0


# =============================================================================
# SCHEMAS: COLORES
# =============================================================================

class ColorBaseIn(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=50, description="Denominacion textil del color")
    codigo_hex: str = Field(..., description="Codigo hexadecimal estandar de 7 caracteres (ej. #991B1B)")

    @field_validator("nombre")
    @classmethod
    def normalizar_nombre_color(cls, v: str) -> str:
        v_limpio = " ".join(v.strip().split())
        if len(v_limpio) < 2:
            raise ValueError("El nombre del color debe contener al menos 2 caracteres.")
        return v_limpio

    @field_validator("codigo_hex")
    @classmethod
    def validar_formato_hex(cls, v: str) -> str:
        v_limpio = v.strip()
        if not re.match(REGEX_HEX_COLOR, v_limpio):
            raise ValueError("El codigo hexadecimal debe iniciar con '#' seguido de 6 digitos hexadecimales (ej. #FFFFFF).")
        return v_limpio.upper()


class ColorCrearIn(ColorBaseIn):
    pass


class ColorActualizarIn(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=50)
    codigo_hex: Optional[str] = Field(None)

    @field_validator("nombre")
    @classmethod
    def normalizar_nombre_opcional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_limpio = " ".join(v.strip().split())
            if len(v_limpio) < 2:
                raise ValueError("El nombre del color debe contener al menos 2 caracteres.")
            return v_limpio
        return v

    @field_validator("codigo_hex")
    @classmethod
    def validar_formato_hex_opcional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_limpio = v.strip()
            if not re.match(REGEX_HEX_COLOR, v_limpio):
                raise ValueError("El codigo hexadecimal debe iniciar con '#' seguido de 6 digitos hexadecimales (ej. #FFFFFF).")
            return v_limpio.upper()
        return v


class ColorOut(BaseModel):
    id_color: int
    nombre: str
    codigo_hex: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ColorAdminOut(ColorOut):
    total_variantes: int = 0
```

---

### 2.3 Catalogo de Errores de Dominio y Mapeo HTTP

```python
# app/modules/gestion_operativa/cu23_categorias_tallas_colores/errores.py

from core.errors import ConflictError, DomainError, NotFoundError


# --- Categorias ---
class CategoriaNoEncontradaError(NotFoundError):
    def __init__(self, id_categoria: int):
        super().__init__(
            message=f"La categoria con ID {id_categoria} no existe en el catalogo.",
            code="CATEGORIA_NO_ENCONTRADA",
        )


class CategoriaDuplicadaError(ConflictError):
    def __init__(self, nombre: str):
        super().__init__(
            message=f"Ya existe una categoria registrada con el nombre '{nombre}'.",
            code="CATEGORIA_DUPLICADA",
        )


class ReferenciaCircularError(DomainError):
    def __init__(self, id_categoria: int, id_padre: int):
        super().__init__(
            message=(
                f"No se permite asignar la categoria ID {id_padre} como padre de ID {id_categoria} "
                "debido a que generaria una referencia circular o bucle jerarquico."
            ),
            code="REFERENCIA_CIRCULAR_NO_PERMITIDA",
        )


class CategoriaConDependenciasError(ConflictError):
    def __init__(self, motivo: str):
        super().__init__(
            message=f"No se puede eliminar la categoria: {motivo}.",
            code="CATEGORIA_CON_PRODUCTOS_O_SUBCATEGORIAS",
        )


# --- Tallas ---
class TallaNoEncontradaError(NotFoundError):
    def __init__(self, id_talla: int):
        super().__init__(
            message=f"La talla con ID {id_talla} no existe en el sistema.",
            code="TALLA_NO_ENCONTRADA",
        )


class TallaDuplicadaError(ConflictError):
    def __init__(self, codigo: str):
        super().__init__(
            message=f"Ya existe una talla registrada con el codigo comercial '{codigo}'.",
            code="TALLA_DUPLICADA",
        )


class TallaEnUsoError(ConflictError):
    def __init__(self, total_variantes: int):
        super().__init__(
            message=(
                f"No se puede eliminar la talla porque se encuentra asociada a {total_variantes} "
                "variantes de producto en el catalogo e inventario."
            ),
            code="TALLA_EN_USO_EN_VARIANTES",
        )


# --- Colores ---
class ColorNoEncontradoError(NotFoundError):
    def __init__(self, id_color: int):
        super().__init__(
            message=f"El color con ID {id_color} no existe en el sistema.",
            code="COLOR_NO_ENCONTRADO",
        )


class ColorDuplicadoError(ConflictError):
    def __init__(self, nombre: str):
        super().__init__(
            message=f"Ya existe un color textil registrado con el nombre '{nombre}'.",
            code="COLOR_DUPLICADO",
        )


class ColorEnUsoError(ConflictError):
    def __init__(self, total_variantes: int):
        super().__init__(
            message=(
                f"No se puede eliminar el color porque se encuentra asignado a {total_variantes} "
                "variantes de prendas en el catalogo."
            ),
            code="COLOR_EN_USO_EN_VARIANTES",
        )
```

---

### 2.4 Servicio de Dominio (`ServicioGestionAtributos`)

```python
# app/modules/gestion_operativa/cu23_categorias_tallas_colores/servicio.py

from typing import List, Optional, Set
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from modules.gestion_operativa.cu23_categorias_tallas_colores.modelos import (
    CategoriaORM,
    ColorORM,
    TallaORM,
)
from modules.gestion_operativa.cu23_categorias_tallas_colores.esquemas import (
    CategoriaActualizarIn,
    CategoriaAdminOut,
    CategoriaCrearIn,
    CategoriaJerarquicaOut,
    CategoriaOut,
    ColorActualizarIn,
    ColorAdminOut,
    ColorCrearIn,
    ColorOut,
    TallaActualizarIn,
    TallaAdminOut,
    TallaCrearIn,
    TallaOut,
)
from modules.gestion_operativa.cu23_categorias_tallas_colores.errores import (
    CategoriaConDependenciasError,
    CategoriaDuplicadaError,
    CategoriaNoEncontradaError,
    ColorDuplicadoError,
    ColorEnUsoError,
    ColorNoEncontradoError,
    ReferenciaCircularError,
    TallaDuplicadaError,
    TallaEnUsoError,
    TallaNoEncontradaError,
)


class ServicioGestionAtributos:
    """Servicio de dominio para la administracion de Categorias, Tallas y Colores."""

    def __init__(self, db: Session):
        self.db = db

    # -------------------------------------------------------------------------
    # GESTION DE CATEGORIAS
    # -------------------------------------------------------------------------

    def _verificar_ciclo_jerarquico(self, id_categoria: int, nuevo_id_padre: int) -> None:
        """Verifica que nuevo_id_padre no sea igual a id_categoria ni sea uno de sus descendientes."""
        if id_categoria == nuevo_id_padre:
            raise ReferenciaCircularError(id_categoria=id_categoria, id_padre=nuevo_id_padre)

        # Recorrer ancestros del nuevo padre hacia arriba
        ancestro_actual_id = nuevo_id_padre
        visitados: Set[int] = set()

        while ancestro_actual_id is not None:
            if ancestro_actual_id == id_categoria:
                raise ReferenciaCircularError(id_categoria=id_categoria, id_padre=nuevo_id_padre)
            if ancestro_actual_id in visitados:
                break
            visitados.add(ancestro_actual_id)

            padre = self.db.execute(
                select(CategoriaORM.id_categoria_padre).where(CategoriaORM.id_categoria == ancestro_actual_id)
            ).scalar_one_or_none()
            ancestro_actual_id = padre

    def listar_categorias_publicas(self) -> List[CategoriaOut]:
        stmt = (
            select(CategoriaORM, CategoriaORM.categoria_padre)
            .order_by(CategoriaORM.nombre.asc())
        )
        resultados = self.db.scalars(select(CategoriaORM).order_by(CategoriaORM.nombre.asc())).all()
        return [
            CategoriaOut(
                id_categoria=c.id_categoria,
                nombre=c.nombre,
                id_categoria_padre=c.id_categoria_padre,
                padre_nombre=c.categoria_padre.nombre if c.categoria_padre else None,
            )
            for c in resultados
        ]

    def listar_categorias_admin(self) -> List[CategoriaAdminOut]:
        # Consulta enriquecida con agregaciones de productos y subcategorias
        sub_prod = (
            select(
                text("id_categoria"),
                func.count().label("total_productos"),
            )
            .select_from(text("fashionstore.productos"))
            .group_by(text("id_categoria"))
            .subquery()
        )

        sub_hijas = (
            select(
                CategoriaORM.id_categoria_padre.label("id_padre"),
                func.count().label("total_subcategorias"),
            )
            .where(CategoriaORM.id_categoria_padre.isnot(None))
            .group_by(CategoriaORM.id_categoria_padre)
            .subquery()
        )

        stmt = (
            select(
                CategoriaORM,
                func.coalesce(sub_prod.c.total_productos, 0).label("total_prod"),
                func.coalesce(sub_hijas.c.total_subcategorias, 0).label("total_hijas"),
            )
            .outerjoin(sub_prod, CategoriaORM.id_categoria == sub_prod.c.id_categoria)
            .outerjoin(sub_hijas, CategoriaORM.id_categoria == sub_hijas.c.id_padre)
            .order_by(CategoriaORM.nombre.asc())
        )

        filas = self.db.execute(stmt).all()
        return [
            CategoriaAdminOut(
                id_categoria=cat.id_categoria,
                nombre=cat.nombre,
                id_categoria_padre=cat.id_categoria_padre,
                padre_nombre=cat.categoria_padre.nombre if cat.categoria_padre else None,
                total_productos=tot_p,
                total_subcategorias=tot_h,
            )
            for cat, tot_p, tot_h in filas
        ]

    def crear_categoria(self, datos: CategoriaCrearIn) -> CategoriaOut:
        # Validar duplicidad
        existente = self.db.execute(
            select(CategoriaORM).where(func.lower(CategoriaORM.nombre) == datos.nombre.lower())
        ).scalar_one_or_none()
        if existente:
            raise CategoriaDuplicadaError(datos.nombre)

        # Validar padre si aplica
        if datos.id_categoria_padre:
            padre = self.db.get(CategoriaORM, datos.id_categoria_padre)
            if not padre:
                raise CategoriaNoEncontradaError(datos.id_categoria_padre)

        nueva = CategoriaORM(nombre=datos.nombre, id_categoria_padre=datos.id_categoria_padre)
        self.db.add(nueva)
        self.db.commit()
        self.db.refresh(nueva)

        return CategoriaOut(
            id_categoria=nueva.id_categoria,
            nombre=nueva.nombre,
            id_categoria_padre=nueva.id_categoria_padre,
            padre_nombre=nueva.categoria_padre.nombre if nueva.categoria_padre else None,
        )

    def actualizar_categoria(self, id_categoria: int, datos: CategoriaActualizarIn) -> CategoriaOut:
        cat = self.db.get(CategoriaORM, id_categoria)
        if not cat:
            raise CategoriaNoEncontradaError(id_categoria)

        if datos.nombre and datos.nombre.lower() != cat.nombre.lower():
            duplicado = self.db.execute(
                select(CategoriaORM).where(
                    func.lower(CategoriaORM.nombre) == datos.nombre.lower(),
                    CategoriaORM.id_categoria != id_categoria,
                )
            ).scalar_one_or_none()
            if duplicado:
                raise CategoriaDuplicadaError(datos.nombre)
            cat.nombre = datos.nombre

        if datos.id_categoria_padre is not None:
            if datos.id_categoria_padre != cat.id_categoria_padre:
                padre = self.db.get(CategoriaORM, datos.id_categoria_padre)
                if not padre:
                    raise CategoriaNoEncontradaError(datos.id_categoria_padre)
                self._verificar_ciclo_jerarquico(id_categoria, datos.id_categoria_padre)
                cat.id_categoria_padre = datos.id_categoria_padre

        self.db.commit()
        self.db.refresh(cat)
        return CategoriaOut(
            id_categoria=cat.id_categoria,
            nombre=cat.nombre,
            id_categoria_padre=cat.id_categoria_padre,
            padre_nombre=cat.categoria_padre.nombre if cat.categoria_padre else None,
        )

    def eliminar_categoria(self, id_categoria: int) -> None:
        cat = self.db.get(CategoriaORM, id_categoria)
        if not cat:
            raise CategoriaNoEncontradaError(id_categoria)

        # Validar subcategorias dependientes
        hijas_conteo = self.db.execute(
            select(func.count()).select_from(CategoriaORM).where(CategoriaORM.id_categoria_padre == id_categoria)
        ).scalar() or 0
        if hijas_conteo > 0:
            raise CategoriaConDependenciasError(f"Posee {hijas_conteo} subcategorias dependientes.")

        # Validar productos dependientes
        prod_conteo = self.db.execute(
            select(func.count()).select_from(text("fashionstore.productos")).where(text("id_categoria = :id")),
            {"id": id_categoria},
        ).scalar() or 0
        if prod_conteo > 0:
            raise CategoriaConDependenciasError(f"Posee {prod_conteo} productos vinculados en el catalogo.")

        self.db.delete(cat)
        self.db.commit()

    # -------------------------------------------------------------------------
    # GESTION DE TALLAS
    # -------------------------------------------------------------------------

    def listar_tallas_publicas(self) -> List[TallaOut]:
        tallas = self.db.scalars(select(TallaORM).order_by(TallaORM.orden.asc(), TallaORM.codigo.asc())).all()
        return [TallaOut.model_validate(t) for t in tallas]

    def listar_tallas_admin(self) -> List[TallaAdminOut]:
        sub_var = (
            select(
                text("id_talla"),
                func.count().label("total_variantes"),
            )
            .select_from(text("fashionstore.variantes_producto"))
            .group_by(text("id_talla"))
            .subquery()
        )

        stmt = (
            select(
                TallaORM,
                func.coalesce(sub_var.c.total_variantes, 0).label("tot_var"),
            )
            .outerjoin(sub_var, TallaORM.id_talla == sub_var.c.id_talla)
            .order_by(TallaORM.orden.asc(), TallaORM.codigo.asc())
        )
        filas = self.db.execute(stmt).all()
        return [
            TallaAdminOut(id_talla=t.id_talla, codigo=t.codigo, orden=t.orden, total_variantes=tot)
            for t, tot in filas
        ]

    def crear_talla(self, datos: TallaCrearIn) -> TallaOut:
        existente = self.db.execute(
            select(TallaORM).where(TallaORM.codigo == datos.codigo)
        ).scalar_one_or_none()
        if existente:
            raise TallaDuplicadaError(datos.codigo)

        nueva = TallaORM(codigo=datos.codigo, orden=datos.orden)
        self.db.add(nueva)
        self.db.commit()
        self.db.refresh(nueva)
        return TallaOut.model_validate(nueva)

    def actualizar_talla(self, id_talla: int, datos: TallaActualizarIn) -> TallaOut:
        talla = self.db.get(TallaORM, id_talla)
        if not talla:
            raise TallaNoEncontradaError(id_talla)

        if datos.codigo and datos.codigo != talla.codigo:
            duplicado = self.db.execute(
                select(TallaORM).where(TallaORM.codigo == datos.codigo, TallaORM.id_talla != id_talla)
            ).scalar_one_or_none()
            if duplicado:
                raise TallaDuplicadaError(datos.codigo)
            talla.codigo = datos.codigo

        if datos.orden is not None:
            talla.orden = datos.orden

        self.db.commit()
        self.db.refresh(talla)
        return TallaOut.model_validate(talla)

    def eliminar_talla(self, id_talla: int) -> None:
        talla = self.db.get(TallaORM, id_talla)
        if not talla:
            raise TallaNoEncontradaError(id_talla)

        var_conteo = self.db.execute(
            select(func.count()).select_from(text("fashionstore.variantes_producto")).where(text("id_talla = :id")),
            {"id": id_talla},
        ).scalar() or 0

        if var_conteo > 0:
            raise TallaEnUsoError(var_conteo)

        self.db.delete(talla)
        self.db.commit()

    # -------------------------------------------------------------------------
    # GESTION DE COLORES
    # -------------------------------------------------------------------------

    def listar_colores_publicos(self) -> List[ColorOut]:
        colores = self.db.scalars(select(ColorORM).order_by(ColorORM.nombre.asc())).all()
        return [ColorOut.model_validate(c) for c in colores]

    def listar_colores_admin(self) -> List[ColorAdminOut]:
        sub_var = (
            select(
                text("id_color"),
                func.count().label("total_variantes"),
            )
            .select_from(text("fashionstore.variantes_producto"))
            .group_by(text("id_color"))
            .subquery()
        )

        stmt = (
            select(
                ColorORM,
                func.coalesce(sub_var.c.total_variantes, 0).label("tot_var"),
            )
            .outerjoin(sub_var, ColorORM.id_color == sub_var.c.id_color)
            .order_by(ColorORM.nombre.asc())
        )
        filas = self.db.execute(stmt).all()
        return [
            ColorAdminOut(id_color=c.id_color, nombre=c.nombre, codigo_hex=c.codigo_hex, total_variantes=tot)
            for c, tot in filas
        ]

    def crear_color(self, datos: ColorCrearIn) -> ColorOut:
        existente = self.db.execute(
            select(ColorORM).where(func.lower(ColorORM.nombre) == datos.nombre.lower())
        ).scalar_one_or_none()
        if existente:
            raise ColorDuplicadoError(datos.nombre)

        nuevo = ColorORM(nombre=datos.nombre, codigo_hex=datos.codigo_hex)
        self.db.add(nuevo)
        self.db.commit()
        self.db.refresh(nuevo)
        return ColorOut.model_validate(nuevo)

    def actualizar_color(self, id_color: int, datos: ColorActualizarIn) -> ColorOut:
        color = self.db.get(ColorORM, id_color)
        if not color:
            raise ColorNoEncontradoError(id_color)

        if datos.nombre and datos.nombre.lower() != color.nombre.lower():
            duplicado = self.db.execute(
                select(ColorORM).where(
                    func.lower(ColorORM.nombre) == datos.nombre.lower(),
                    ColorORM.id_color != id_color,
                )
            ).scalar_one_or_none()
            if duplicado:
                raise ColorDuplicadoError(datos.nombre)
            color.nombre = datos.nombre

        if datos.codigo_hex is not None:
            color.codigo_hex = datos.codigo_hex

        self.db.commit()
        self.db.refresh(color)
        return ColorOut.model_validate(color)

    def eliminar_color(self, id_color: int) -> None:
        color = self.db.get(ColorORM, id_color)
        if not color:
            raise ColorNoEncontradoError(id_color)

        var_conteo = self.db.execute(
            select(func.count()).select_from(text("fashionstore.variantes_producto")).where(text("id_color = :id")),
            {"id": id_color},
        ).scalar() or 0

        if var_conteo > 0:
            raise ColorEnUsoError(var_conteo)

        self.db.delete(color)
        self.db.commit()
```

---

### 2.5 Especificacion de Rutas/Endpoints (Router FastAPI)

Los endpoints se exponen montados sobre el prefijo `/api/v1`:

```python
# app/modules/gestion_operativa/cu23_categorias_tallas_colores/router.py

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from core.database import get_db
from core.deps import require_roles
from modules.gestion_operativa.cu23_categorias_tallas_colores.esquemas import (
    CategoriaActualizarIn,
    CategoriaAdminOut,
    CategoriaCrearIn,
    CategoriaOut,
    ColorActualizarIn,
    ColorAdminOut,
    ColorCrearIn,
    ColorOut,
    TallaActualizarIn,
    TallaAdminOut,
    TallaCrearIn,
    TallaOut,
)
from modules.gestion_operativa.cu23_categorias_tallas_colores.servicio import (
    ServicioGestionAtributos,
)

router = APIRouter()

# --- Publicos: Lectura de Taxonomias ---
@router.get("/categorias", response_model=List[CategoriaOut], status_code=status.HTTP_200_OK, tags=["Atributos Publicos"])
def listar_categorias_publicas(db: Session = Depends(get_db)):
    return ServicioGestionAtributos(db).listar_categorias_publicas()

@router.get("/tallas", response_model=List[TallaOut], status_code=status.HTTP_200_OK, tags=["Atributos Publicos"])
def listar_tallas_publicas(db: Session = Depends(get_db)):
    return ServicioGestionAtributos(db).listar_tallas_publicas()

@router.get("/colores", response_model=List[ColorOut], status_code=status.HTTP_200_OK, tags=["Atributos Publicos"])
def listar_colores_publicos(db: Session = Depends(get_db)):
    return ServicioGestionAtributos(db).listar_colores_publicos()

# --- Administrativos: Categorias (Requiere rol administrador) ---
@router.get("/admin/categorias", response_model=List[CategoriaAdminOut], dependencies=[Depends(require_roles(["administrador"]))], tags=["Admin - Atributos"])
def listar_categorias_admin(db: Session = Depends(get_db)):
    return ServicioGestionAtributos(db).listar_categorias_admin()

@router.post("/admin/categorias", response_model=CategoriaOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(["administrador"]))], tags=["Admin - Atributos"])
def crear_categoria(datos: CategoriaCrearIn, db: Session = Depends(get_db)):
    return ServicioGestionAtributos(db).crear_categoria(datos)

@router.put("/admin/categorias/{id_categoria}", response_model=CategoriaOut, dependencies=[Depends(require_roles(["administrador"]))], tags=["Admin - Atributos"])
def actualizar_categoria(id_categoria: int, datos: CategoriaActualizarIn, db: Session = Depends(get_db)):
    return ServicioGestionAtributos(db).actualizar_categoria(id_categoria, datos)

@router.delete("/admin/categorias/{id_categoria}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_roles(["administrador"]))], tags=["Admin - Atributos"])
def eliminar_categoria(id_categoria: int, db: Session = Depends(get_db)):
    ServicioGestionAtributos(db).eliminar_categoria(id_categoria)

# --- Administrativos: Tallas ---
@router.get("/admin/tallas", response_model=List[TallaAdminOut], dependencies=[Depends(require_roles(["administrador"]))], tags=["Admin - Atributos"])
def listar_tallas_admin(db: Session = Depends(get_db)):
    return ServicioGestionAtributos(db).listar_tallas_admin()

@router.post("/admin/tallas", response_model=TallaOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(["administrador"]))], tags=["Admin - Atributos"])
def crear_talla(datos: TallaCrearIn, db: Session = Depends(get_db)):
    return ServicioGestionAtributos(db).crear_talla(datos)

@router.put("/admin/tallas/{id_talla}", response_model=TallaOut, dependencies=[Depends(require_roles(["administrador"]))], tags=["Admin - Atributos"])
def actualizar_talla(id_talla: int, datos: TallaActualizarIn, db: Session = Depends(get_db)):
    return ServicioGestionAtributos(db).actualizar_talla(id_talla, datos)

@router.delete("/admin/tallas/{id_talla}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_roles(["administrador"]))], tags=["Admin - Atributos"])
def eliminar_talla(id_talla: int, db: Session = Depends(get_db)):
    ServicioGestionAtributos(db).eliminar_talla(id_talla)

# --- Administrativos: Colores ---
@router.get("/admin/colores", response_model=List[ColorAdminOut], dependencies=[Depends(require_roles(["administrador"]))], tags=["Admin - Atributos"])
def listar_colores_admin(db: Session = Depends(get_db)):
    return ServicioGestionAtributos(db).listar_colores_admin()

@router.post("/admin/colores", response_model=ColorOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles(["administrador"]))], tags=["Admin - Atributos"])
def crear_color(datos: ColorCrearIn, db: Session = Depends(get_db)):
    return ServicioGestionAtributos(db).crear_color(datos)

@router.put("/admin/colores/{id_color}", response_model=ColorOut, dependencies=[Depends(require_roles(["administrador"]))], tags=["Admin - Atributos"])
def actualizar_color(id_color: int, datos: ColorActualizarIn, db: Session = Depends(get_db)):
    return ServicioGestionAtributos(db).actualizar_color(id_color, datos)

@router.delete("/admin/colores/{id_color}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_roles(["administrador"]))], tags=["Admin - Atributos"])
def eliminar_color(id_color: int, db: Session = Depends(get_db)):
    ServicioGestionAtributos(db).eliminar_color(id_color)
```

---

## 3. Diseno Frontend Web (`Ec-frontend` - Angular 19+ Standalone)

### 3.1 Modelos e Interfaces TypeScript

```typescript
// src/app/modules/gestion_operativa/cu23_categorias_tallas_colores/modelos/atributos.dto.ts

export interface CategoriaAdmin {
  id_categoria: number;
  nombre: str;
  id_categoria_padre: number | null;
  padre_nombre?: string | null;
  total_productos: number;
  total_subcategorias: number;
}

export interface CategoriaCrearPeticion {
  nombre: string;
  id_categoria_padre: number | null;
}

export interface CategoriaActualizarPeticion {
  nombre?: string;
  id_categoria_padre?: number | null;
}

export interface TallaAdmin {
  id_talla: number;
  codigo: string;
  orden: number;
  total_variantes: number;
}

export interface TallaCrearPeticion {
  codigo: string;
  orden: number;
}

export interface TallaActualizarPeticion {
  codigo?: string;
  orden?: number;
}

export interface ColorAdmin {
  id_color: number;
  nombre: string;
  codigo_hex: string;
  total_variantes: number;
}

export interface ColorCrearPeticion {
  nombre: string;
  codigo_hex: string;
}

export interface ColorActualizarPeticion {
  nombre?: string;
  codigo_hex?: string;
}
```

---

### 3.2 Contrato del Servicio HTTP (`AtributosAdminService`)

```typescript
// src/app/modules/gestion_operativa/cu23_categorias_tallas_colores/servicios/atributos-admin.service.ts

import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  CategoriaAdmin,
  CategoriaCrearPeticion,
  CategoriaActualizarPeticion,
  TallaAdmin,
  TallaCrearPeticion,
  TallaActualizarPeticion,
  ColorAdmin,
  ColorCrearPeticion,
  ColorActualizarPeticion,
} from '../modelos/atributos.dto';

@Injectable({
  providedIn: 'root',
})
export class AtributosAdminService {
  private readonly http = inject(HttpClient);

  private obtenerCabecerasAuth(): HttpHeaders {
    const token = typeof window !== 'undefined' ? localStorage.getItem('fashionstore_token') : null;
    return new HttpHeaders({
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token || ''}`,
    });
  }

  // --- Categorias ---
  obtenerCategorias(): Observable<CategoriaAdmin[]> {
    return this.http.get<CategoriaAdmin[]>('/api/v1/admin/categorias', { headers: this.obtenerCabecerasAuth() });
  }

  crearCategoria(peticion: CategoriaCrearPeticion): Observable<CategoriaAdmin> {
    return this.http.post<CategoriaAdmin>('/api/v1/admin/categorias', peticion, { headers: this.obtenerCabecerasAuth() });
  }

  actualizarCategoria(id: number, peticion: CategoriaActualizarPeticion): Observable<CategoriaAdmin> {
    return this.http.put<CategoriaAdmin>(`/api/v1/admin/categorias/${id}`, peticion, { headers: this.obtenerCabecerasAuth() });
  }

  eliminarCategoria(id: number): Observable<void> {
    return this.http.delete<void>(`/api/v1/admin/categorias/${id}`, { headers: this.obtenerCabecerasAuth() });
  }

  // --- Tallas ---
  obtenerTallas(): Observable<TallaAdmin[]> {
    return this.http.get<TallaAdmin[]>('/api/v1/admin/tallas', { headers: this.obtenerCabecerasAuth() });
  }

  crearTalla(peticion: TallaCrearPeticion): Observable<TallaAdmin> {
    return this.http.post<TallaAdmin>('/api/v1/admin/tallas', peticion, { headers: this.obtenerCabecerasAuth() });
  }

  actualizarTalla(id: number, peticion: TallaActualizarPeticion): Observable<TallaAdmin> {
    return this.http.put<TallaAdmin>(`/api/v1/admin/tallas/${id}`, peticion, { headers: this.obtenerCabecerasAuth() });
  }

  eliminarTalla(id: number): Observable<void> {
    return this.http.delete<void>(`/api/v1/admin/tallas/${id}`, { headers: this.obtenerCabecerasAuth() });
  }

  // --- Colores ---
  obtenerColores(): Observable<ColorAdmin[]> {
    return this.http.get<ColorAdmin[]>('/api/v1/admin/colores', { headers: this.obtenerCabecerasAuth() });
  }

  crearColor(peticion: ColorCrearPeticion): Observable<ColorAdmin> {
    return this.http.post<ColorAdmin>('/api/v1/admin/colores', peticion, { headers: this.obtenerCabecerasAuth() });
  }

  actualizarColor(id: number, peticion: ColorActualizarPeticion): Observable<ColorAdmin> {
    return this.http.put<ColorAdmin>(`/api/v1/admin/colores/${id}`, peticion, { headers: this.obtenerCabecerasAuth() });
  }

  eliminarColor(id: number): Observable<void> {
    return this.http.delete<void>(`/api/v1/admin/colores/${id}`, { headers: this.obtenerCabecerasAuth() });
  }
}
```

---

### 3.3 Componente Standalone de Pagina y Estado Reactivo con Signals

- **Selector:** `app-atributos-admin`
- **Ruta Angular:** `/admin/atributos` (protegida bajo `authGuard`).
- **Layout y Contenedor:** `max-w-[1440px] px-6 mx-auto` con `scrollbar-gutter: stable`.
- **Estrategia:** `ChangeDetectionStrategy.OnPush`.

**Senales Reactivas del Estado:**
```typescript
// Estados de interfaz y colecciones
readonly pestanaActiva = signal<'categorias' | 'tallas' | 'colores'>('categorias');
readonly categorias = signal<CategoriaAdmin[]>([]);
readonly tallas = signal<TallaAdmin[]>([]);
readonly colores = signal<ColorAdmin[]>([]);

// Filtros y busqueda reactiva
readonly terminoBusqueda = signal<string>('');

// Estados de carga y feedback
readonly cargando = signal<boolean>(false);
readonly guardando = signal<boolean>(false);
readonly errorMensaje = signal<string | null>(null);
readonly exitoMensaje = signal<string | null>(null);

// Estados de modales
readonly modalCategoriaAbierto = signal<boolean>(false);
readonly modalTallaAbierto = signal<boolean>(false);
readonly modalColorAbierto = signal<boolean>(false);
readonly elementoEnEdicionId = signal<number | null>(null);
```

---

### 3.4 Especificacion de Formularios Reactivos y Sincronizacion de Color

Se empleara `NonNullableFormBuilder` con validaciones rigurosas:

1. **Formulario de Categorias:**
   ```typescript
   readonly categoriaForm = this.fb.group({
     nombre: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(100)]],
     id_categoria_padre: [null as number | null],
   });
   ```
   *Regla de Interfaz:* En modo edicion, el selector de categorias padre excluye automaticamente la propia categoria seleccionada para impedir intentos de auto-referencia directa desde el cliente.

2. **Formulario de Tallas:**
   ```typescript
   readonly tallaForm = this.fb.group({
     codigo: ['', [Validators.required, Validators.minLength(1), Validators.maxLength(10)]],
     orden: [0, [Validators.required, Validators.min(0), Validators.max(32767)]],
   });
   ```
   *Regla de Interfaz:* Transformacion automatica del texto del codigo a mayusculas (`toUpperCase()`) en el evento de entrada (`input`).

3. **Formulario de Colores y Sincronizacion Swatch:**
   ```typescript
   readonly colorForm = this.fb.group({
     nombre: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(50)]],
     codigo_hex: ['#000000', [Validators.required, Validators.pattern(/^#[0-9A-Fa-f]{6}$/)]],
   });
   ```
   *Sincronizacion Bidireccional:*
   - El selector nativo `<input type="color" [value]="colorForm.controls.codigo_hex.value" (input)="actualizarHexDesdePicker($event)">` actualiza el campo de texto.
   - El campo de texto `<input type="text" formControlName="codigo_hex">` actualiza la muestra cromatica visual y el selector si cumple la expresion regular.

---

### 3.5 Manejo de Errores de Integridad Referencial (Luxury Banners)

Cuando el backend retorne un codigo HTTP `409 Conflict` (ej. `CATEGORIA_CON_PRODUCTOS_O_SUBCATEGORIAS`, `TALLA_EN_USO_EN_VARIANTES` o `COLOR_EN_USO_EN_VARIANTES`):

1. El interceptor/servicio captura el objeto de error `{ detail: string, code: string }`.
2. El componente asigna el mensaje descriptivo a `errorMensaje`.
3. Se despliega en la parte superior del modal o de la tabla un **Luxury Banner** con fondo ambar oscuro o carmin Atelier, borde fino e icono SVG sobrio sin emojis.
4. El modal de edicion y los valores digitados por el administrador **se conservan intactos**, permitiendo corregir los datos o cancelar la operacion sin perdida de contexto.

---

## 4. Estrategia de Pruebas Automatizadas

### 4.1 Backend (`Ec-backend` - Pytest)
Se disenara la suite `tests/modules/gestion_operativa/test_cu23_categorias_tallas_colores.py` cubriendo al menos 20 escenarios:
- Validacion de DTOs Pydantic (nombres sin espacios perimetrales, validacion regex `#HEX`, codigos de talla vacios o fuera de rango).
- Deteccion de ciclos jerarquicos en categorias (auto-referencia directa, ancestro de segundo nivel).
- Bloqueo 409 ante duplicidad en categorias, tallas y colores.
- Bloqueo 409 de eliminacion ante categorias con subcategorias o productos.
- Bloqueo 409 de eliminacion ante tallas y colores vinculados a variantes.
- Eliminacion exitosa (HTTP 204) cuando no existen dependencias activas.
- Verificacion de endpoints protegidos (401 sin token, 403 con rol cliente).

### 4.2 Frontend Web (`Ec-frontend` - Vitest)
Se disenaran las suites unitarias:
- `atributos-admin.service.spec.ts`: pruebas de llamadas HTTP y cabeceras Bearer.
- `atributos-admin.component.spec.ts`: inicializacion, alternancia fluida de pestanas, apertura/cierre de modales, sincronizacion bidireccional de color y despliegue de mensajes de error 409.

---

## 5. Matriz de Trazabilidad de Criterios EARS

| Criterio | Componente Tecnico Backend | Componente Tecnico Web | Metodo / Endpoint |
|:---|:---|:---|:---|
| **AC-1** | `require_roles(["administrador"])` | `authGuard` | `/api/v1/admin/*` |
| **AC-2** | `ServicioGestionAtributos.crear_categoria` | `modalCategoriaAbierto` / `categoriaForm` | `POST /api/v1/admin/categorias` |
| **AC-3** | `CategoriaDuplicadaError` (409) | `errorMensaje` en banner | `POST /api/v1/admin/categorias` |
| **AC-4** | `_verificar_ciclo_jerarquico` (422) | Excluir ID propio en selector padre | `PUT /api/v1/admin/categorias/{id}` |
| **AC-5** | `CategoriaConDependenciasError` (409) | Captura de error 409 | `DELETE /api/v1/admin/categorias/{id}` |
| **AC-6** | `ServicioGestionAtributos.crear_talla` | `modalTallaAbierto` / `tallaForm` | `POST /api/v1/admin/tallas` |
| **AC-7** | `TallaDuplicadaError` (409) | Validacion en vivo `toUpperCase()` | `POST /api/v1/admin/tallas` |
| **AC-8** | `TallaEnUsoError` (409) | Captura de error 409 | `DELETE /api/v1/admin/tallas/{id}` |
| **AC-9** | `ServicioGestionAtributos.crear_color` | `modalColorAbierto` / `colorForm` | `POST /api/v1/admin/colores` |
| **AC-10** | `REGEX_HEX_COLOR` / `ColorDuplicadoError` | Sincronizacion picker `<input type="color">` | `POST /api/v1/admin/colores` |
| **AC-11** | `ColorEnUsoError` (409) | Captura de error 409 | `DELETE /api/v1/admin/colores/{id}` |
| **AC-12** | Consultas publicas y enriquecidas | `obtenerCategorias`, `obtenerTallas`, `obtenerColores` | `GET /api/v1/admin/*` |
| **AC-13** | Monolito FastAPI | `CategoriasTallasColoresAdminComponent` | Standalone + Signals |
| **AC-14** | N/A | Base-2 / Outfit / Slate-Camel-Obsidian | Tailwind CSS institucional |
| **AC-15** | N/A | `pestanaActiva = signal<'categorias'\|'tallas'\|'colores'>` | Vistas y tablas editoriales |
| **AC-16** | Pydantic v2 mode='after' | `NonNullableFormBuilder` | Modales interactivos |
| **AC-17** | Codigos de error tipados (`code`) | Luxury Banners sin perdida de formulario | Feedback visual |
