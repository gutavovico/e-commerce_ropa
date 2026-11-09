"""Repositorio de persistencia SQLAlchemy 2.0 para P2-CU23, P2-CU24 y P2-CU25 (Aprendizaje Automático)."""

from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import func, select, text, update
from sqlalchemy.orm import Session

from modules.comercial.cu23_cu25_aprendizaje_ml.modelos import (
    DatasetMlORM,
    ModeloMlORM,
    PrediccionMlORM,
    SegmentoClienteMlORM,
)
from modules.plataforma.modelos import ConfiguracionTenantORM, TenantORM


class AprendizajeMlRepositorio:
    """Consultas y escrituras de datasets, modelos, predicciones y segmentos aisladas por `id_tenant`."""

    @staticmethod
    def obtener_tenant(db: Session, id_tenant: int) -> Optional[TenantORM]:
        return db.get(TenantORM, id_tenant)

    @staticmethod
    def obtener_moneda_empresa(db: Session, id_tenant: int) -> str:
        cfg = db.get(ConfiguracionTenantORM, id_tenant)
        if cfg and cfg.moneda:
            return cfg.moneda.strip().upper()
        return "BOB"

    @staticmethod
    def contar_ventas_reales_empresa(db: Session, id_tenant: int) -> int:
        res = db.execute(
            text(
                """
                SELECT COUNT(id_venta)
                FROM fashionstore.ventas
                WHERE id_tenant = :id_tenant AND estado = 'PAGADA'
                """
            ),
            {"id_tenant": id_tenant},
        ).scalar()
        return int(res or 0)

    @staticmethod
    def listar_productos_empresa(db: Session, id_tenant: int) -> list[dict[str, Any]]:
        filas = db.execute(
            text(
                """
                SELECT id_producto, nombre, COALESCE(precio_base, 450.00) AS precio_base
                FROM fashionstore.productos
                WHERE id_tenant = :id_tenant AND activo = true
                ORDER BY nombre ASC
                LIMIT 25
                """
            ),
            {"id_tenant": id_tenant},
        ).fetchall()
        return [
            {
                "id_producto": int(r.id_producto),
                "nombre": str(r.nombre),
                "precio_base": Decimal(str(r.precio_base)),
            }
            for r in filas
        ]

    @staticmethod
    def listar_sucursales_empresa(db: Session, id_tenant: int) -> list[dict[str, Any]]:
        filas = db.execute(
            text(
                """
                SELECT id_sucursal, nombre
                FROM fashionstore.sucursales
                WHERE id_tenant = :id_tenant AND activa = true
                ORDER BY nombre ASC
                """
            ),
            {"id_tenant": id_tenant},
        ).fetchall()
        return [{"id_sucursal": int(r.id_sucursal), "nombre": str(r.nombre)} for r in filas]

    @staticmethod
    def listar_clientes_con_actividad_empresa(
        db: Session, id_tenant: int, factor_bob: Decimal
    ) -> list[dict[str, Any]]:
        """Obtiene clientes que han comprado o reservado en la empresa (CU25 paso 4)."""
        filas = db.execute(
            text(
                """
                SELECT
                    u.id_usuario,
                    TRIM(COALESCE(u.nombres, '') || ' ' || COALESCE(u.apellidos, '')) AS nombre_completo,
                    u.email,
                    COUNT(DISTINCT v.id_venta) AS compras_realizadas,
                    COUNT(DISTINCT r.id_reserva) AS reservas_realizadas,
                    COALESCE(SUM(v.total), 0) AS monto_total_raw
                FROM fashionstore.usuarios u
                LEFT JOIN fashionstore.ventas v
                    ON v.id_usuario = u.id_usuario AND v.id_tenant = :id_tenant AND v.estado = 'PAGADA'
                LEFT JOIN fashionstore.reservas r
                    ON r.id_usuario = u.id_usuario AND r.id_tenant = :id_tenant
                WHERE v.id_venta IS NOT NULL OR r.id_reserva IS NOT NULL
                GROUP BY u.id_usuario, u.nombres, u.apellidos, u.email
                ORDER BY monto_total_raw DESC
                LIMIT 50
                """
            ),
            {"id_tenant": id_tenant},
        ).fetchall()

        resultado: list[dict[str, Any]] = []
        for f in filas:
            monto_bob = (Decimal(str(f.monto_total_raw or 0)) * factor_bob).quantize(
                Decimal("0.01")
            )
            resultado.append(
                {
                    "id_usuario": int(f.id_usuario),
                    "nombre_completo": str(f.nombre_completo or f.email),
                    "email": str(f.email),
                    "compras_realizadas": int(f.compras_realizadas or 0),
                    "reservas_realizadas": int(f.reservas_realizadas or 0),
                    "monto_total_bob": float(monto_bob),
                }
            )
        return resultado

    # --- Datasets (CU23) ---

    @staticmethod
    def listar_datasets(db: Session, id_tenant: int) -> list[DatasetMlORM]:
        stmt = (
            select(DatasetMlORM)
            .where(DatasetMlORM.id_tenant == id_tenant)
            .order_by(DatasetMlORM.creado_en.desc(), DatasetMlORM.id_dataset.desc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def obtener_dataset(
        db: Session, id_tenant: int, id_dataset: int
    ) -> Optional[DatasetMlORM]:
        stmt = select(DatasetMlORM).where(
            DatasetMlORM.id_tenant == id_tenant,
            DatasetMlORM.id_dataset == id_dataset,
        )
        return db.scalar(stmt)

    @staticmethod
    def crear_dataset(db: Session, datos: dict[str, Any]) -> DatasetMlORM:
        item = DatasetMlORM(**datos)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    # --- Modelos (CU23) ---

    @staticmethod
    def listar_modelos(db: Session, id_tenant: int) -> list[ModeloMlORM]:
        stmt = (
            select(ModeloMlORM)
            .where(ModeloMlORM.id_tenant == id_tenant)
            .order_by(ModeloMlORM.creado_en.desc(), ModeloMlORM.id_modelo.desc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def obtener_modelo(
        db: Session, id_tenant: int, id_modelo: int
    ) -> Optional[ModeloMlORM]:
        stmt = select(ModeloMlORM).where(
            ModeloMlORM.id_tenant == id_tenant,
            ModeloMlORM.id_modelo == id_modelo,
        )
        return db.scalar(stmt)

    @staticmethod
    def obtener_modelo_activo_por_tipo(
        db: Session, id_tenant: int, tipo_modelo: str
    ) -> Optional[ModeloMlORM]:
        stmt = (
            select(ModeloMlORM)
            .where(
                ModeloMlORM.id_tenant == id_tenant,
                ModeloMlORM.tipo_modelo == tipo_modelo,
                ModeloMlORM.activo.is_(True),
            )
            .order_by(ModeloMlORM.actualizado_en.desc(), ModeloMlORM.id_modelo.desc())
        )
        return db.scalar(stmt)

    @staticmethod
    def crear_modelo_con_resultados(
        db: Session,
        *,
        datos_modelo: dict[str, Any],
        predicciones: list[dict[str, Any]],
        segmentos: list[dict[str, Any]],
        activar_inmediatamente: bool = False,
    ) -> ModeloMlORM:
        id_tenant = int(datos_modelo["id_tenant"])
        tipo_modelo = str(datos_modelo["tipo_modelo"])

        if activar_inmediatamente and datos_modelo.get("estado") != "fallido":
            db.execute(
                update(ModeloMlORM)
                .where(
                    ModeloMlORM.id_tenant == id_tenant,
                    ModeloMlORM.tipo_modelo == tipo_modelo,
                    ModeloMlORM.activo.is_(True),
                )
                .values(activo=False, estado="evaluado", actualizado_en=func.now())
            )
            datos_modelo["activo"] = True
            datos_modelo["estado"] = "activo"

        modelo = ModeloMlORM(**datos_modelo)
        db.add(modelo)
        db.flush()

        for p in predicciones:
            db.add(
                PrediccionMlORM(
                    id_tenant=id_tenant,
                    id_modelo=modelo.id_modelo,
                    **p,
                )
            )

        for s in segmentos:
            db.add(
                SegmentoClienteMlORM(
                    id_tenant=id_tenant,
                    id_modelo=modelo.id_modelo,
                    **s,
                )
            )

        db.commit()
        db.refresh(modelo)
        return modelo

    @staticmethod
    def activar_modelo(db: Session, modelo: ModeloMlORM) -> ModeloMlORM:
        db.execute(
            update(ModeloMlORM)
            .where(
                ModeloMlORM.id_tenant == modelo.id_tenant,
                ModeloMlORM.tipo_modelo == modelo.tipo_modelo,
                ModeloMlORM.id_modelo != modelo.id_modelo,
                ModeloMlORM.activo.is_(True),
            )
            .values(activo=False, estado="evaluado", actualizado_en=func.now())
        )
        modelo.activo = True
        modelo.estado = "activo"
        modelo.actualizado_en = func.now()
        db.commit()
        db.refresh(modelo)
        return modelo

    @staticmethod
    def archivar_modelo(db: Session, modelo: ModeloMlORM) -> ModeloMlORM:
        modelo.activo = False
        modelo.estado = "archivado"
        modelo.actualizado_en = func.now()
        db.commit()
        db.refresh(modelo)
        return modelo

    # --- Predicciones (CU24) y Segmentos (CU25) ---

    @staticmethod
    def listar_predicciones_modelo(
        db: Session,
        *,
        id_tenant: int,
        id_modelo: int,
        id_producto: Optional[int] = None,
        id_sucursal: Optional[int] = None,
        periodo: Optional[str] = None,
    ) -> list[PrediccionMlORM]:
        stmt = select(PrediccionMlORM).where(
            PrediccionMlORM.id_tenant == id_tenant,
            PrediccionMlORM.id_modelo == id_modelo,
        )
        if id_producto is not None:
            stmt = stmt.where(PrediccionMlORM.id_producto == id_producto)
        if id_sucursal is not None:
            stmt = stmt.where(PrediccionMlORM.id_sucursal == id_sucursal)
        if periodo:
            stmt = stmt.where(PrediccionMlORM.periodo == periodo.strip())
        stmt = stmt.order_by(
            PrediccionMlORM.ingresos_esperados_bob.desc(),
            PrediccionMlORM.id_prediccion.asc(),
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def listar_segmentos_modelo(
        db: Session,
        *,
        id_tenant: int,
        id_modelo: int,
    ) -> list[SegmentoClienteMlORM]:
        stmt = (
            select(SegmentoClienteMlORM)
            .where(
                SegmentoClienteMlORM.id_tenant == id_tenant,
                SegmentoClienteMlORM.id_modelo == id_modelo,
            )
            .order_by(
                SegmentoClienteMlORM.cantidad_clientes.desc(),
                SegmentoClienteMlORM.id_segmento.asc(),
            )
        )
        return list(db.scalars(stmt).all())
