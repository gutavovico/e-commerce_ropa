"""Repositorio de consultas controladas por empresa y persistencia de solicitudes IA (P2-CU21)."""

from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from modules.comercial.cu21_reportes_ia.modelos import SolicitudReporteIaORM
from modules.plataforma.cu22_catalogo_reportes.modelos import CatalogoReporteIaORM
from modules.plataforma.modelos import ConfiguracionTenantORM, TenantORM


class ReportesIaRepositorio:
    """Ejecuta únicamente las consultas cerradas del catálogo CU22 filtradas por `id_tenant` (RN45, RN46)."""

    @staticmethod
    def obtener_tenant(db: Session, id_tenant: int) -> Optional[TenantORM]:
        return db.get(TenantORM, id_tenant)

    @staticmethod
    def obtener_moneda_empresa(db: Session, id_tenant: int) -> str:
        cfg = db.get(ConfiguracionTenantORM, id_tenant)
        if cfg and cfg.moneda:
            return cfg.moneda.upper()
        return "BOB"

    @staticmethod
    def listar_catalogo_activo(db: Session) -> list[CatalogoReporteIaORM]:
        stmt = (
            select(CatalogoReporteIaORM)
            .where(CatalogoReporteIaORM.activo.is_(True))
            .order_by(CatalogoReporteIaORM.id_reporte_catalogo.asc())
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def listar_sucursales_empresa(db: Session, id_tenant: int) -> list[dict[str, Any]]:
        filas = db.execute(
            text(
                "SELECT id_sucursal, nombre, direccion "
                "FROM fashionstore.sucursales "
                "WHERE id_tenant = :t AND activa = true "
                "ORDER BY id_sucursal ASC"
            ),
            {"t": id_tenant},
        ).all()
        return [{"id_sucursal": int(f[0]), "nombre": str(f[1]), "direccion": f[2]} for f in filas]

    @staticmethod
    def listar_categorias_empresa(db: Session, id_tenant: int) -> list[dict[str, Any]]:
        filas = db.execute(
            text(
                "SELECT id_categoria, nombre "
                "FROM fashionstore.categorias "
                "WHERE id_tenant = :t "
                "ORDER BY nombre ASC"
            ),
            {"t": id_tenant},
        ).all()
        return [{"id_categoria": int(f[0]), "nombre": str(f[1])} for f in filas]

    @staticmethod
    def registrar_solicitud(
        db: Session,
        *,
        id_tenant: int,
        id_usuario: int,
        comando_voz_texto: str,
        tipo_reporte: Optional[str],
        estado: str,
        interpretacion: Optional[dict[str, Any]],
        formato_visualizacion: str,
        mensaje_estado: str,
    ) -> SolicitudReporteIaORM:
        item = SolicitudReporteIaORM(
            id_tenant=id_tenant,
            id_usuario=id_usuario,
            comando_voz_texto=comando_voz_texto,
            tipo_reporte=tipo_reporte,
            estado=estado,
            interpretacion=interpretacion,
            formato_visualizacion=formato_visualizacion,
            mensaje_estado=mensaje_estado,
            exportaciones=[],
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def obtener_solicitud_empresa(
        db: Session, id_tenant: int, id_solicitud: int
    ) -> Optional[SolicitudReporteIaORM]:
        stmt = select(SolicitudReporteIaORM).where(
            SolicitudReporteIaORM.id_solicitud == id_solicitud,
            SolicitudReporteIaORM.id_tenant == id_tenant,
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def listar_historial_empresa(
        db: Session, id_tenant: int, limite: int = 30
    ) -> list[SolicitudReporteIaORM]:
        stmt = (
            select(SolicitudReporteIaORM)
            .where(SolicitudReporteIaORM.id_tenant == id_tenant)
            .order_by(SolicitudReporteIaORM.id_solicitud.desc())
            .limit(limite)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def registrar_exportacion_en_solicitud(
        db: Session,
        solicitud: SolicitudReporteIaORM,
        formato: str,
        usuario_email: str,
    ) -> None:
        actuales = list(solicitud.exportaciones or [])
        actuales.append(
            {
                "formato": formato,
                "usuario": usuario_email,
                "exportado_en": datetime.now(timezone.utc).isoformat(),
            }
        )
        solicitud.exportaciones = actuales
        db.commit()
        db.refresh(solicitud)

    # ----------------------------------------------------------------------------------
    # Consultas controladas del catálogo permitido (RN45, RN46)
    # ----------------------------------------------------------------------------------

    @staticmethod
    def ejecutar_ventas_por_sucursal(
        db: Session,
        *,
        id_tenant: int,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        id_sucursal: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        filtros_sql = ["v.id_tenant = :t", "v.estado::text = 'pagada'"]
        params: dict[str, Any] = {"t": id_tenant}

        if fecha_inicio:
            filtros_sql.append("v.fecha_venta >= :f_ini")
            params["f_ini"] = datetime.combine(fecha_inicio, time.min, tzinfo=timezone.utc)
        if fecha_fin:
            filtros_sql.append("v.fecha_venta <= :f_fin")
            params["f_fin"] = datetime.combine(fecha_fin, time.max, tzinfo=timezone.utc)
        if id_sucursal:
            filtros_sql.append("v.id_sucursal = :id_suc")
            params["id_suc"] = id_sucursal

        where_clause = " AND ".join(filtros_sql)
        sql = text(
            f"""
            SELECT
                COALESCE(s.nombre, 'Venta Digital / Web') AS sucursal,
                COUNT(v.id_venta) AS cantidad_ventas,
                COALESCE(SUM(v.total), 0) AS ingresos_totales,
                COALESCE(AVG(v.total), 0) AS ticket_promedio
            FROM fashionstore.ventas v
            LEFT JOIN fashionstore.sucursales s
                ON s.id_tenant = v.id_tenant AND s.id_sucursal = v.id_sucursal
            WHERE {where_clause}
            GROUP BY COALESCE(s.nombre, 'Venta Digital / Web')
            ORDER BY ingresos_totales DESC
            """
        )
        filas = db.execute(sql, params).all()
        return [
            {
                "sucursal": str(f[0]),
                "cantidad_ventas": int(f[1] or 0),
                "ingresos_totales": Decimal(str(f[2] or "0.00")),
                "ticket_promedio": Decimal(str(f[3] or "0.00")),
            }
            for f in filas
        ]

    @staticmethod
    def ejecutar_top_productos_vendidos(
        db: Session,
        *,
        id_tenant: int,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        id_sucursal: Optional[int] = None,
        id_categoria: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        filtros_sql = ["v.id_tenant = :t", "v.estado::text = 'pagada'"]
        params: dict[str, Any] = {"t": id_tenant}

        if fecha_inicio:
            filtros_sql.append("v.fecha_venta >= :f_ini")
            params["f_ini"] = datetime.combine(fecha_inicio, time.min, tzinfo=timezone.utc)
        if fecha_fin:
            filtros_sql.append("v.fecha_venta <= :f_fin")
            params["f_fin"] = datetime.combine(fecha_fin, time.max, tzinfo=timezone.utc)
        if id_sucursal:
            filtros_sql.append("v.id_sucursal = :id_suc")
            params["id_suc"] = id_sucursal
        if id_categoria:
            filtros_sql.append("p.id_categoria = :id_cat")
            params["id_cat"] = id_categoria

        where_clause = " AND ".join(filtros_sql)
        sql = text(
            f"""
            SELECT
                p.nombre AS producto,
                COALESCE(c.nombre, 'General') AS categoria,
                COALESCE(SUM(vd.cantidad), 0) AS unidades_vendidas,
                COALESCE(SUM(vd.cantidad * vd.precio_unitario), 0) AS ingresos_producto
            FROM fashionstore.venta_detalle vd
            JOIN fashionstore.ventas v
                ON v.id_tenant = vd.id_tenant AND v.id_venta = vd.id_venta
            JOIN fashionstore.variantes_producto vp
                ON vp.id_tenant = vd.id_tenant AND vp.id_variante = vd.id_variante
            JOIN fashionstore.productos p
                ON p.id_tenant = vp.id_tenant AND p.id_producto = vp.id_producto
            LEFT JOIN fashionstore.categorias c
                ON c.id_tenant = p.id_tenant AND c.id_categoria = p.id_categoria
            WHERE {where_clause}
            GROUP BY p.nombre, COALESCE(c.nombre, 'General')
            ORDER BY unidades_vendidas DESC, ingresos_producto DESC
            LIMIT 10
            """
        )
        filas = db.execute(sql, params).all()
        return [
            {
                "producto": str(f[0]),
                "categoria": str(f[1]),
                "unidades_vendidas": int(f[2] or 0),
                "ingresos_producto": Decimal(str(f[3] or "0.00")),
            }
            for f in filas
        ]

    @staticmethod
    def ejecutar_inventario_por_sucursal(
        db: Session,
        *,
        id_tenant: int,
        id_sucursal: Optional[int] = None,
        id_categoria: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        filtros_sql = ["inv.id_tenant = :t"]
        params: dict[str, Any] = {"t": id_tenant}

        if id_sucursal:
            filtros_sql.append("inv.id_sucursal = :id_suc")
            params["id_suc"] = id_sucursal
        if id_categoria:
            filtros_sql.append("p.id_categoria = :id_cat")
            params["id_cat"] = id_categoria

        where_clause = " AND ".join(filtros_sql)
        sql = text(
            f"""
            SELECT
                s.nombre AS sucursal,
                COALESCE(c.nombre, 'General') AS categoria,
                COALESCE(SUM(inv.cantidad_disponible), 0) AS stock_disponible,
                COALESCE(SUM(inv.cantidad_reservada), 0) AS stock_reservado,
                COALESCE(SUM(inv.cantidad_disponible * p.precio_base), 0) AS valor_inventario
            FROM fashionstore.inventario_sucursal inv
            JOIN fashionstore.sucursales s
                ON s.id_tenant = inv.id_tenant AND s.id_sucursal = inv.id_sucursal
            JOIN fashionstore.variantes_producto vp
                ON vp.id_tenant = inv.id_tenant AND vp.id_variante = inv.id_variante
            JOIN fashionstore.productos p
                ON p.id_tenant = vp.id_tenant AND p.id_producto = vp.id_producto
            LEFT JOIN fashionstore.categorias c
                ON c.id_tenant = p.id_tenant AND c.id_categoria = p.id_categoria
            WHERE {where_clause}
            GROUP BY s.nombre, COALESCE(c.nombre, 'General')
            ORDER BY stock_disponible DESC
            """
        )
        filas = db.execute(sql, params).all()
        return [
            {
                "sucursal": str(f[0]),
                "categoria": str(f[1]),
                "stock_disponible": int(f[2] or 0),
                "stock_reservado": int(f[3] or 0),
                "valor_inventario": Decimal(str(f[4] or "0.00")),
            }
            for f in filas
        ]

    @staticmethod
    def ejecutar_reservas_por_estado_sucursal(
        db: Session,
        *,
        id_tenant: int,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        id_sucursal: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        filtros_sql = ["r.id_tenant = :t"]
        params: dict[str, Any] = {"t": id_tenant}

        if fecha_inicio:
            filtros_sql.append("r.creado_en >= :f_ini")
            params["f_ini"] = datetime.combine(fecha_inicio, time.min, tzinfo=timezone.utc)
        if fecha_fin:
            filtros_sql.append("r.creado_en <= :f_fin")
            params["f_fin"] = datetime.combine(fecha_fin, time.max, tzinfo=timezone.utc)
        if id_sucursal:
            filtros_sql.append("r.id_sucursal = :id_suc")
            params["id_suc"] = id_sucursal

        where_clause = " AND ".join(filtros_sql)
        sql = text(
            f"""
            SELECT
                s.nombre AS sucursal,
                r.estado::text AS estado,
                COUNT(DISTINCT r.id_reserva) AS total_reservas,
                COALESCE(SUM(rd.cantidad), 0) AS prendas_reservadas
            FROM fashionstore.reservas r
            JOIN fashionstore.sucursales s
                ON s.id_tenant = r.id_tenant AND s.id_sucursal = r.id_sucursal
            LEFT JOIN fashionstore.reserva_detalle rd
                ON rd.id_tenant = r.id_tenant AND rd.id_reserva = r.id_reserva
            WHERE {where_clause}
            GROUP BY s.nombre, r.estado::text
            ORDER BY total_reservas DESC
            """
        )
        filas = db.execute(sql, params).all()
        return [
            {
                "sucursal": str(f[0]),
                "estado": str(f[1]),
                "total_reservas": int(f[2] or 0),
                "prendas_reservadas": int(f[3] or 0),
            }
            for f in filas
        ]

