"""Servicio de dominio para CU23: Gestionar Categorias, Tallas y Colores.

Implementa la logica transaccional, deteccion de ciclos aciclicos en el arbol de categorias,
y verificaciones de integridad relacional previo a cualquier eliminacion de atributos.
"""

from typing import List, Optional, Set
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

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
from modules.gestion_operativa.cu23_categorias_tallas_colores.modelos import (
    CategoriaORM,
    ColorORM,
    ProductoORM,
    TallaORM,
    VarianteProductoORM,
)


class ServicioGestionAtributos:
    """Servicio de aplicacion para la administracion de atributos maestros del catalogo."""

    def __init__(self, db: Session):
        self.db = db

    # =========================================================================
    # GESTION DE CATEGORIAS
    # =========================================================================

    def _verificar_ciclo_jerarquico(self, id_categoria: int, nuevo_id_padre: int) -> None:
        """Verifica que nuevo_id_padre no sea igual a id_categoria ni sea uno de sus descendientes.

        Raises:
            ReferenciaCircularError: Si se detecta auto-referencia directa o ciclo indirecto.
        """
        if id_categoria == nuevo_id_padre:
            raise ReferenciaCircularError(id_categoria=id_categoria, id_padre=nuevo_id_padre)

        # Recorrer ancestros del nuevo padre hacia arriba
        ancestro_actual_id: Optional[int] = nuevo_id_padre
        visitados: Set[int] = set()

        while ancestro_actual_id is not None:
            if ancestro_actual_id == id_categoria:
                raise ReferenciaCircularError(id_categoria=id_categoria, id_padre=nuevo_id_padre)
            if ancestro_actual_id in visitados:
                break
            visitados.add(ancestro_actual_id)

            padre = self.db.get(CategoriaORM, ancestro_actual_id)
            ancestro_actual_id = padre.id_categoria_padre if padre else None

    def listar_categorias_publicas(self) -> List[CategoriaOut]:
        """Consulta publica del arbol de categorias ordenado alfabeticamente."""
        stmt = (
            select(CategoriaORM)
            .options(joinedload(CategoriaORM.categoria_padre))
            .order_by(CategoriaORM.nombre.asc())
        )
        resultados = self.db.execute(stmt).scalars().all()
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
        """Consulta administrativa enriquecida con metricas de uso en catalogo."""
        sub_prod = (
            select(
                ProductoORM.id_categoria,
                func.count(ProductoORM.id_producto).label("total_productos"),
            )
            .group_by(ProductoORM.id_categoria)
            .subquery()
        )

        sub_hijas = (
            select(
                CategoriaORM.id_categoria_padre.label("id_padre"),
                func.count(CategoriaORM.id_categoria).label("total_subcategorias"),
            )
            .where(CategoriaORM.id_categoria_padre.isnot(None))
            .group_by(CategoriaORM.id_categoria_padre)
            .subquery()
        )

        stmt = (
            select(
                CategoriaORM,
                func.coalesce(sub_prod.c.total_productos, 0).label("tot_p"),
                func.coalesce(sub_hijas.c.total_subcategorias, 0).label("tot_h"),
            )
            .options(joinedload(CategoriaORM.categoria_padre))
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
                total_productos=int(tot_p),
                total_subcategorias=int(tot_h),
            )
            for cat, tot_p, tot_h in filas
        ]

    def crear_categoria(self, datos: CategoriaCrearIn) -> CategoriaOut:
        """Crea una nueva categoria taxonomica."""
        # 1. Validar duplicidad insensible a mayusculas/minusculas
        existente = self.db.execute(
            select(CategoriaORM).where(func.lower(CategoriaORM.nombre) == datos.nombre.lower())
        ).scalar_one_or_none()
        if existente:
            raise CategoriaDuplicadaError(datos.nombre)

        # 2. Validar existencia de categoria padre si se proporciono
        padre_nombre: Optional[str] = None
        if datos.id_categoria_padre:
            padre = self.db.get(CategoriaORM, datos.id_categoria_padre)
            if not padre:
                raise CategoriaNoEncontradaError(datos.id_categoria_padre)
            padre_nombre = padre.nombre

        nueva = CategoriaORM(nombre=datos.nombre, id_categoria_padre=datos.id_categoria_padre)
        self.db.add(nueva)
        self.db.commit()
        self.db.refresh(nueva)

        return CategoriaOut(
            id_categoria=nueva.id_categoria,
            nombre=nueva.nombre,
            id_categoria_padre=nueva.id_categoria_padre,
            padre_nombre=padre_nombre,
        )

    def actualizar_categoria(self, id_categoria: int, datos: CategoriaActualizarIn) -> CategoriaOut:
        """Actualiza una categoria existente previniendo ciclos jerarquicos."""
        cat = self.db.get(CategoriaORM, id_categoria)
        if not cat:
            raise CategoriaNoEncontradaError(id_categoria)

        # Validar nuevo nombre si cambia
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

        # Validar nuevo padre
        if datos.id_categoria_padre is not None:
            if datos.id_categoria_padre == 0:
                cat.id_categoria_padre = None
            elif datos.id_categoria_padre != cat.id_categoria_padre:
                padre = self.db.get(CategoriaORM, datos.id_categoria_padre)
                if not padre:
                    raise CategoriaNoEncontradaError(datos.id_categoria_padre)
                self._verificar_ciclo_jerarquico(id_categoria, datos.id_categoria_padre)
                cat.id_categoria_padre = datos.id_categoria_padre

        self.db.commit()
        self.db.refresh(cat)

        padre_nombre: Optional[str] = None
        if cat.id_categoria_padre:
            padre_rec = self.db.get(CategoriaORM, cat.id_categoria_padre)
            padre_nombre = padre_rec.nombre if padre_rec else None

        return CategoriaOut(
            id_categoria=cat.id_categoria,
            nombre=cat.nombre,
            id_categoria_padre=cat.id_categoria_padre,
            padre_nombre=padre_nombre,
        )

    def eliminar_categoria(self, id_categoria: int) -> None:
        """Elimina una categoria si no tiene dependencias activas (subcategorias o productos)."""
        cat = self.db.get(CategoriaORM, id_categoria)
        if not cat:
            raise CategoriaNoEncontradaError(id_categoria)

        # 1. Validar subcategorias dependientes
        hijas_conteo = self.db.execute(
            select(func.count(CategoriaORM.id_categoria)).where(CategoriaORM.id_categoria_padre == id_categoria)
        ).scalar() or 0
        if hijas_conteo > 0:
            raise CategoriaConDependenciasError(f"Posee {hijas_conteo} subcategorias dependientes.")

        # 2. Validar productos vinculados
        prod_conteo = self.db.execute(
            select(func.count(ProductoORM.id_producto)).where(ProductoORM.id_categoria == id_categoria)
        ).scalar() or 0
        if prod_conteo > 0:
            raise CategoriaConDependenciasError(f"Posee {prod_conteo} productos vinculados en el catalogo.")

        self.db.delete(cat)
        self.db.commit()

    # =========================================================================
    # GESTION DE TALLAS
    # =========================================================================

    def listar_tallas_publicas(self) -> List[TallaOut]:
        """Consulta publica de tallas ordenadas secuencialmente."""
        stmt = select(TallaORM).order_by(TallaORM.orden.asc(), TallaORM.codigo.asc())
        tallas = self.db.execute(stmt).scalars().all()
        return [TallaOut.model_validate(t) for t in tallas]

    def listar_tallas_admin(self) -> List[TallaAdminOut]:
        """Consulta administrativa de tallas con total de variantes vinculadas."""
        sub_var = (
            select(
                VarianteProductoORM.id_talla,
                func.count(VarianteProductoORM.id_variante).label("total_variantes"),
            )
            .group_by(VarianteProductoORM.id_talla)
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
            TallaAdminOut(
                id_talla=t.id_talla,
                codigo=t.codigo,
                orden=t.orden,
                total_variantes=int(tot_var),
            )
            for t, tot_var in filas
        ]

    def crear_talla(self, datos: TallaCrearIn) -> TallaOut:
        """Crea una nueva talla comercial estandarizada."""
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
        """Actualiza el codigo o el orden secuencial de una talla."""
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
        """Elimina una talla verificando que no este en uso en variantes de inventario."""
        talla = self.db.get(TallaORM, id_talla)
        if not talla:
            raise TallaNoEncontradaError(id_talla)

        var_conteo = self.db.execute(
            select(func.count(VarianteProductoORM.id_variante)).where(VarianteProductoORM.id_talla == id_talla)
        ).scalar() or 0

        if var_conteo > 0:
            raise TallaEnUsoError(var_conteo)

        self.db.delete(talla)
        self.db.commit()

    # =========================================================================
    # GESTION DE COLORES
    # =========================================================================

    def listar_colores_publicos(self) -> List[ColorOut]:
        """Consulta publica de colores textiles ordenados alfabeticamente."""
        stmt = select(ColorORM).order_by(ColorORM.nombre.asc())
        colores = self.db.execute(stmt).scalars().all()
        return [ColorOut.model_validate(c) for c in colores]

    def listar_colores_admin(self) -> List[ColorAdminOut]:
        """Consulta administrativa de colores con total de variantes vinculadas."""
        sub_var = (
            select(
                VarianteProductoORM.id_color,
                func.count(VarianteProductoORM.id_variante).label("total_variantes"),
            )
            .group_by(VarianteProductoORM.id_color)
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
            ColorAdminOut(
                id_color=c.id_color,
                nombre=c.nombre,
                codigo_hex=c.codigo_hex,
                total_variantes=int(tot_var),
            )
            for c, tot_var in filas
        ]

    def crear_color(self, datos: ColorCrearIn) -> ColorOut:
        """Crea un nuevo color textil corporativo."""
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
        """Actualiza la denominacion o el codigo hexadecimal de un color."""
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
        """Elimina un color textil verificando que no este asignado a variantes de prendas."""
        color = self.db.get(ColorORM, id_color)
        if not color:
            raise ColorNoEncontradoError(id_color)

        var_conteo = self.db.execute(
            select(func.count(VarianteProductoORM.id_variante)).where(VarianteProductoORM.id_color == id_color)
        ).scalar() or 0

        if var_conteo > 0:
            raise ColorEnUsoError(var_conteo)

        self.db.delete(color)
        self.db.commit()
