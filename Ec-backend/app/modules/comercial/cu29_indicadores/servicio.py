"""Servicio analitico de inteligencia directiva para CU29.
Nomenclatura oficial: Visualizar indicadores empresariales

Implementa agregaciones y calculos estadisticos sobre transacciones de venta,
aplicando rigurosa segregacion territorial por rol (RBAC) y computo defensivo.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import (
    case,
    desc,
    func,
    select,
)
from sqlalchemy.orm import Session

from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.comercial.cu29_indicadores.errores import (
    AccesoComparativaDenegadoError,
    RangoTemporalInvalidoError,
    SucursalNoAutorizadaError,
)
from modules.comercial.cu29_indicadores.esquemas import (
    CanalDistribucionOut,
    CategoriaDistribucionOut,
    ComparativaSucursalesOut,
    DashboardIndicadoresCompletoOut,
    DistribucionVentasOut,
    IndicadoresFiltrosIn,
    ItemRankingProductoOut,
    PuntoSerieTemporalOut,
    RankingProductosOut,
    ResumenEjecutivoOut,
    SerieTemporalIngresosOut,
    SucursalDesempenoOut,
)
from modules.comercial.cu29_indicadores.modelos import (
    CategoriaORM,
    CiudadORM,
    ProductoORM,
    SucursalORM,
    VarianteProductoORM,
    VentaDetalleORM,
    VentaORM,
)


class ServicioIndicadoresEmpresariales:
    """Motor analitico para la agregacion y visualizacion de indicadores ejecutivos."""

    def resolver_alcance_sucursal(
        self, usuario: UsuarioORM, id_sucursal_solicitado: Optional[int]
    ) -> Optional[int]:
        """Aplica la politica RBAC de segregacion territorial segun rol."""
        rol_nombre = str(getattr(usuario.rol, "nombre", usuario.rol) or "").lower().strip()
        if rol_nombre in ("administrador", "admin"):
            return id_sucursal_solicitado
        elif rol_nombre == "encargado_sucursal":
            if not getattr(usuario, "id_sucursal", None):
                raise SucursalNoAutorizadaError(
                    "El encargado de sucursal no tiene una sede asignada en su perfil."
                )
            return usuario.id_sucursal
        raise SucursalNoAutorizadaError(
            "No cuenta con privilegios autorizados para consultar indicadores empresariales."
        )

    def resolver_intervalos_tiempo(
        self, filtros: IndicadoresFiltrosIn
    ) -> Tuple[datetime, datetime, datetime, datetime, str]:
        """Determina los rangos (actual y precedente) y la granularidad temporal."""
        ahora = datetime.now(timezone.utc)

        if filtros.periodo == "7d":
            fin_actual = ahora
            inicio_actual = ahora - timedelta(days=7)
            delta = timedelta(days=7)
            fin_anterior = inicio_actual
            inicio_anterior = fin_anterior - delta
            agrupacion = "diaria"
        elif filtros.periodo == "30d":
            fin_actual = ahora
            inicio_actual = ahora - timedelta(days=30)
            delta = timedelta(days=30)
            fin_anterior = inicio_actual
            inicio_anterior = fin_anterior - delta
            agrupacion = "diaria"
        elif filtros.periodo == "mes_actual":
            inicio_actual = datetime(ahora.year, ahora.month, 1, 0, 0, 0, tzinfo=timezone.utc)
            fin_actual = ahora
            delta = fin_actual - inicio_actual
            fin_anterior = inicio_actual - timedelta(seconds=1)
            inicio_anterior = fin_anterior - delta
            agrupacion = "diaria"
        elif filtros.periodo == "anio_actual":
            inicio_actual = datetime(ahora.year, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
            fin_actual = ahora
            delta = fin_actual - inicio_actual
            fin_anterior = inicio_actual - timedelta(seconds=1)
            inicio_anterior = fin_anterior - delta
            agrupacion = "mensual"
        elif filtros.periodo == "personalizado":
            if not filtros.fecha_desde or not filtros.fecha_hasta:
                raise RangoTemporalInvalidoError(
                    "Para periodo personalizado debe especificar fecha_desde y fecha_hasta."
                )
            if filtros.fecha_desde > filtros.fecha_hasta:
                raise RangoTemporalInvalidoError(
                    "La fecha_desde no puede ser posterior a fecha_hasta."
                )
            inicio_actual = datetime.combine(
                filtros.fecha_desde, datetime.min.time()
            ).replace(tzinfo=timezone.utc)
            fin_actual = datetime.combine(
                filtros.fecha_hasta, datetime.max.time()
            ).replace(tzinfo=timezone.utc)
            delta = fin_actual - inicio_actual
            fin_anterior = inicio_actual - timedelta(microseconds=1)
            inicio_anterior = fin_anterior - delta
            if delta.days > 90:
                agrupacion = "mensual"
            elif delta.days > 14:
                agrupacion = "semanal"
            else:
                agrupacion = "diaria"
        else:
            fin_actual = ahora
            inicio_actual = ahora - timedelta(days=30)
            delta = timedelta(days=30)
            fin_anterior = inicio_actual
            inicio_anterior = fin_anterior - delta
            agrupacion = "diaria"

        return inicio_actual, fin_actual, inicio_anterior, fin_anterior, agrupacion

    def _calcular_variacion(
        self, valor_actual: Decimal, valor_anterior: Decimal
    ) -> Decimal:
        """Calcula de forma segura la variacion porcentual relativa."""
        if valor_anterior > Decimal("0.00"):
            return round(((valor_actual - valor_anterior) / valor_anterior) * Decimal("100.00"), 2)
        elif valor_actual > Decimal("0.00"):
            return Decimal("100.00")
        return Decimal("0.00")

    def obtener_resumen_ejecutivo(
        self, db: Session, filtros: IndicadoresFiltrosIn, usuario: UsuarioORM
    ) -> ResumenEjecutivoOut:
        """Genera el bloque ejecutivo de KPIs financieros y operativos."""
        id_sucursal = self.resolver_alcance_sucursal(usuario, filtros.id_sucursal)
        ini_act, fin_act, ini_ant, fin_ant, _ = self.resolver_intervalos_tiempo(filtros)

        def _consultar_metricas(desde: datetime, hasta: datetime) -> Tuple[Decimal, int, int]:
            # Consulta de ingresos y transacciones
            stmt_ventas = (
                select(
                    func.coalesce(func.sum(VentaORM.total), 0).label("ingresos"),
                    func.count(VentaORM.id_venta).label("transacciones"),
                )
                .where(VentaORM.estado == "pagada")
                .where(VentaORM.fecha_venta >= desde)
                .where(VentaORM.fecha_venta <= hasta)
            )
            if id_sucursal is not None:
                stmt_ventas = stmt_ventas.where(VentaORM.id_sucursal == id_sucursal)

            res_ventas = db.execute(stmt_ventas).first()
            ingresos = Decimal(res_ventas.ingresos or 0) if res_ventas else Decimal("0.00")
            transacciones = int(res_ventas.transacciones or 0) if res_ventas else 0

            # Consulta de unidades de prendas
            stmt_unidades = (
                select(func.coalesce(func.sum(VentaDetalleORM.cantidad), 0).label("unidades"))
                .select_from(VentaDetalleORM)
                .join(VentaORM, VentaORM.id_venta == VentaDetalleORM.id_venta)
                .where(VentaORM.estado == "pagada")
                .where(VentaORM.fecha_venta >= desde)
                .where(VentaORM.fecha_venta <= hasta)
            )
            if id_sucursal is not None:
                stmt_unidades = stmt_unidades.where(VentaORM.id_sucursal == id_sucursal)

            res_unidades = db.execute(stmt_unidades).first()
            unidades = int(res_unidades.unidades or 0) if res_unidades else 0

            return ingresos, transacciones, unidades

        ing_act, trans_act, unid_act = _consultar_metricas(ini_act, fin_act)
        ing_ant, trans_ant, unid_ant = _consultar_metricas(ini_ant, fin_ant)

        ticket_act = (
            round(ing_act / Decimal(trans_act), 2)
            if trans_act > 0
            else Decimal("0.00")
        )
        ticket_ant = (
            round(ing_ant / Decimal(trans_ant), 2)
            if trans_ant > 0
            else Decimal("0.00")
        )

        var_ingresos = self._calcular_variacion(ing_act, ing_ant)
        var_trans = self._calcular_variacion(Decimal(trans_act), Decimal(trans_ant))
        var_ticket = self._calcular_variacion(ticket_act, ticket_ant)
        var_unidades = self._calcular_variacion(Decimal(unid_act), Decimal(unid_ant))

        # Margen bruto estimado benchmark de la cadena (42.50%)
        margen_estimado = Decimal("42.50")

        return ResumenEjecutivoOut(
            periodo_inicio=ini_act.date(),
            periodo_fin=fin_act.date(),
            ingresos_totales=round(ing_act, 2),
            variacion_porcentual=var_ingresos,
            total_transacciones=trans_act,
            variacion_porcentual_transacciones=var_trans,
            margen_estimado=margen_estimado,
            ticket_promedio=ticket_act,
            variacion_porcentual_ticket=var_ticket,
            unidades_vendidas=unid_act,
            variacion_porcentual_unidades=var_unidades,
        )

    def obtener_serie_temporal(
        self, db: Session, filtros: IndicadoresFiltrosIn, usuario: UsuarioORM
    ) -> SerieTemporalIngresosOut:
        """Calcula la serie cronologica de ingresos agrupada por fecha."""
        id_sucursal = self.resolver_alcance_sucursal(usuario, filtros.id_sucursal)
        ini_act, fin_act, _, _, agrupacion = self.resolver_intervalos_tiempo(filtros)

        # Mapeo a intervalo de date_trunc para PostgreSQL
        trunc_intervalo = "day" if agrupacion == "diaria" else ("week" if agrupacion == "semanal" else "month")

        periodo_col = func.date_trunc(trunc_intervalo, VentaORM.fecha_venta).label("periodo_eje")

        stmt = (
            select(
                periodo_col,
                func.coalesce(func.sum(VentaORM.total), 0).label("monto"),
                func.count(VentaORM.id_venta).label("ordenes"),
            )
            .where(VentaORM.estado == "pagada")
            .where(VentaORM.fecha_venta >= ini_act)
            .where(VentaORM.fecha_venta <= fin_act)
        )
        if id_sucursal is not None:
            stmt = stmt.where(VentaORM.id_sucursal == id_sucursal)

        stmt = stmt.group_by(periodo_col).order_by(periodo_col.asc())
        resultados = db.execute(stmt).all()

        puntos: List[PuntoSerieTemporalOut] = []
        for r in resultados:
            dt_periodo = r.periodo_eje
            if isinstance(dt_periodo, datetime):
                fecha_punto = dt_periodo.date()
                if agrupacion == "mensual":
                    etiqueta = dt_periodo.strftime("%b %Y")
                else:
                    etiqueta = dt_periodo.strftime("%Y-%m-%d")
            elif isinstance(dt_periodo, date):
                fecha_punto = dt_periodo
                etiqueta = dt_periodo.strftime("%Y-%m-%d")
            else:
                fecha_punto = ini_act.date()
                etiqueta = str(dt_periodo or "")

            puntos.append(
                PuntoSerieTemporalOut(
                    etiqueta_tiempo=etiqueta,
                    fecha_inicio=fecha_punto,
                    monto_ingresos=round(Decimal(r.monto or 0), 2),
                    cantidad_ordenes=int(r.ordenes or 0),
                )
            )

        return SerieTemporalIngresosOut(
            agrupacion=agrupacion,  # type: ignore
            puntos=puntos,
        )

    def obtener_top_productos(
        self,
        db: Session,
        filtros: IndicadoresFiltrosIn,
        usuario: UsuarioORM,
        limite: int = 5,
    ) -> RankingProductosOut:
        """Obtiene el ranking de prendas con mayor recaudacion y volumen."""
        id_sucursal = self.resolver_alcance_sucursal(usuario, filtros.id_sucursal)
        ini_act, fin_act, _, _, _ = self.resolver_intervalos_tiempo(filtros)
        limite_efectivo = min(max(limite, 1), 20)

        # 1. Total de ingresos para computar porcentaje de contribucion
        stmt_total = (
            select(func.coalesce(func.sum(VentaORM.total), 0))
            .where(VentaORM.estado == "pagada")
            .where(VentaORM.fecha_venta >= ini_act)
            .where(VentaORM.fecha_venta <= fin_act)
        )
        if id_sucursal is not None:
            stmt_total = stmt_total.where(VentaORM.id_sucursal == id_sucursal)
        total_global = Decimal(db.scalar(stmt_total) or 0)

        # 2. Ranking de prendas
        stmt_ranking = (
            select(
                ProductoORM.id_producto,
                ProductoORM.nombre.label("nombre_producto"),
                func.min(VarianteProductoORM.sku).label("sku_referencia"),
                CategoriaORM.nombre.label("categoria_nombre"),
                func.coalesce(func.sum(VentaDetalleORM.cantidad), 0).label("unidades_vendidas"),
                func.coalesce(
                    func.sum(
                        case(
                            (VentaDetalleORM.subtotal_linea.isnot(None), VentaDetalleORM.subtotal_linea),
                            else_=(VentaDetalleORM.cantidad * VentaDetalleORM.precio_unitario),
                        )
                    ),
                    0,
                ).label("monto_total_generado"),
            )
            .select_from(VentaDetalleORM)
            .join(VentaORM, VentaORM.id_venta == VentaDetalleORM.id_venta)
            .join(VarianteProductoORM, VarianteProductoORM.id_variante == VentaDetalleORM.id_variante)
            .join(ProductoORM, ProductoORM.id_producto == VarianteProductoORM.id_producto)
            .join(CategoriaORM, CategoriaORM.id_categoria == ProductoORM.id_categoria)
            .where(VentaORM.estado == "pagada")
            .where(VentaORM.fecha_venta >= ini_act)
            .where(VentaORM.fecha_venta <= fin_act)
        )
        if id_sucursal is not None:
            stmt_ranking = stmt_ranking.where(VentaORM.id_sucursal == id_sucursal)

        stmt_ranking = (
            stmt_ranking.group_by(
                ProductoORM.id_producto,
                ProductoORM.nombre,
                CategoriaORM.nombre,
            )
            .order_by(desc("monto_total_generado"))
            .limit(limite_efectivo)
        )

        filas = db.execute(stmt_ranking).all()
        ranking: List[ItemRankingProductoOut] = []

        for f in filas:
            monto_f = Decimal(f.monto_total_generado or 0)
            contribucion = (
                round((monto_f / total_global) * Decimal("100.00"), 2)
                if total_global > Decimal("0.00")
                else Decimal("0.00")
            )
            ranking.append(
                ItemRankingProductoOut(
                    id_producto=f.id_producto,
                    nombre_producto=f.nombre_producto,
                    sku_referencia=f.sku_referencia or f"PROD-{f.id_producto:04d}",
                    categoria_nombre=f.categoria_nombre,
                    unidades_vendidas=int(f.unidades_vendidas or 0),
                    monto_total_generado=round(monto_f, 2),
                    porcentaje_contribucion=contribucion,
                )
            )

        return RankingProductosOut(
            limite=limite_efectivo,
            productos=ranking,
        )

    def obtener_distribucion_ventas(
        self, db: Session, filtros: IndicadoresFiltrosIn, usuario: UsuarioORM
    ) -> DistribucionVentasOut:
        """Desglosa las ventas por categoria taxonomica y canal comercial."""
        id_sucursal = self.resolver_alcance_sucursal(usuario, filtros.id_sucursal)
        ini_act, fin_act, _, _, _ = self.resolver_intervalos_tiempo(filtros)

        # 1. Total general de recaudacion
        stmt_total = (
            select(func.coalesce(func.sum(VentaORM.total), 0))
            .where(VentaORM.estado == "pagada")
            .where(VentaORM.fecha_venta >= ini_act)
            .where(VentaORM.fecha_venta <= fin_act)
        )
        if id_sucursal is not None:
            stmt_total = stmt_total.where(VentaORM.id_sucursal == id_sucursal)
        total_global = Decimal(db.scalar(stmt_total) or 0)

        # 2. Desglose por Categoria
        stmt_cat = (
            select(
                CategoriaORM.id_categoria,
                CategoriaORM.nombre.label("nombre_categoria"),
                func.coalesce(
                    func.sum(
                        case(
                            (VentaDetalleORM.subtotal_linea.isnot(None), VentaDetalleORM.subtotal_linea),
                            else_=(VentaDetalleORM.cantidad * VentaDetalleORM.precio_unitario),
                        )
                    ),
                    0,
                ).label("monto_cat"),
                func.coalesce(func.sum(VentaDetalleORM.cantidad), 0).label("unidades_cat"),
            )
            .select_from(VentaDetalleORM)
            .join(VentaORM, VentaORM.id_venta == VentaDetalleORM.id_venta)
            .join(VarianteProductoORM, VarianteProductoORM.id_variante == VentaDetalleORM.id_variante)
            .join(ProductoORM, ProductoORM.id_producto == VarianteProductoORM.id_producto)
            .join(CategoriaORM, CategoriaORM.id_categoria == ProductoORM.id_categoria)
            .where(VentaORM.estado == "pagada")
            .where(VentaORM.fecha_venta >= ini_act)
            .where(VentaORM.fecha_venta <= fin_act)
        )
        if id_sucursal is not None:
            stmt_cat = stmt_cat.where(VentaORM.id_sucursal == id_sucursal)

        stmt_cat = stmt_cat.group_by(CategoriaORM.id_categoria, CategoriaORM.nombre).order_by(
            desc("monto_cat")
        )
        filas_cat = db.execute(stmt_cat).all()

        categorias_out: List[CategoriaDistribucionOut] = []
        for c in filas_cat:
            monto_c = Decimal(c.monto_cat or 0)
            part = (
                round((monto_c / total_global) * Decimal("100.00"), 2)
                if total_global > Decimal("0.00")
                else Decimal("0.00")
            )
            categorias_out.append(
                CategoriaDistribucionOut(
                    id_categoria=c.id_categoria,
                    nombre_categoria=c.nombre_categoria,
                    monto_facturado=round(monto_c, 2),
                    unidades_vendidas=int(c.unidades_cat or 0),
                    porcentaje_participacion=part,
                )
            )

        # 3. Desglose por Canal
        stmt_canal = (
            select(
                VentaORM.tipo_venta,
                func.coalesce(func.sum(VentaORM.total), 0).label("monto_canal"),
                func.count(VentaORM.id_venta).label("total_ordenes"),
            )
            .where(VentaORM.estado == "pagada")
            .where(VentaORM.fecha_venta >= ini_act)
            .where(VentaORM.fecha_venta <= fin_act)
        )
        if id_sucursal is not None:
            stmt_canal = stmt_canal.where(VentaORM.id_sucursal == id_sucursal)

        stmt_canal = stmt_canal.group_by(VentaORM.tipo_venta).order_by(desc("monto_canal"))
        filas_canal = db.execute(stmt_canal).all()

        mapa_canales = {
            "presencial": ("boutique_fisica", "Boutique Fisica"),
            "digital_web": ("tienda_web", "Tienda Web"),
            "digital_movil": ("canal_movil", "Aplicacion Movil"),
        }

        canales_out: List[CanalDistribucionOut] = []
        for cn in filas_canal:
            tipo = str(cn.tipo_venta or "")
            codigo, nombre = mapa_canales.get(tipo, (tipo, tipo.capitalize()))
            monto_cn = Decimal(cn.monto_canal or 0)
            part = (
                round((monto_cn / total_global) * Decimal("100.00"), 2)
                if total_global > Decimal("0.00")
                else Decimal("0.00")
            )
            canales_out.append(
                CanalDistribucionOut(
                    canal_codigo=codigo,
                    canal_nombre=nombre,
                    monto_facturado=round(monto_cn, 2),
                    total_ordenes=int(cn.total_ordenes or 0),
                    porcentaje_participacion=part,
                )
            )

        return DistribucionVentasOut(
            por_categoria=categorias_out,
            por_canal=canales_out,
        )

    def obtener_comparativa_sucursales(
        self, db: Session, filtros: IndicadoresFiltrosIn, usuario: UsuarioORM
    ) -> ComparativaSucursalesOut:
        """Genera el reporte comparativo entre sedes (acceso exclusivo para administrador)."""
        rol_nombre = str(getattr(usuario.rol, "nombre", usuario.rol) or "").lower().strip()
        if rol_nombre not in ("administrador", "admin"):
            raise AccesoComparativaDenegadoError()

        ini_act, fin_act, _, _, _ = self.resolver_intervalos_tiempo(filtros)

        # 1. Total global de la red
        stmt_total_red = (
            select(func.coalesce(func.sum(VentaORM.total), 0))
            .where(VentaORM.estado == "pagada")
            .where(VentaORM.fecha_venta >= ini_act)
            .where(VentaORM.fecha_venta <= fin_act)
        )
        total_red = Decimal(db.scalar(stmt_total_red) or 0)

        # 2. Desempeno por sucursal activa
        stmt_suc = (
            select(
                SucursalORM.id_sucursal,
                SucursalORM.nombre.label("nombre_sucursal"),
                CiudadORM.nombre.label("nombre_ciudad"),
                func.coalesce(func.sum(VentaORM.total), 0).label("monto_suc"),
                func.count(VentaORM.id_venta).label("ventas_suc"),
            )
            .select_from(SucursalORM)
            .join(CiudadORM, CiudadORM.id_ciudad == SucursalORM.id_ciudad)
            .outerjoin(
                VentaORM,
                (VentaORM.id_sucursal == SucursalORM.id_sucursal)
                & (VentaORM.estado == "pagada")
                & (VentaORM.fecha_venta >= ini_act)
                & (VentaORM.fecha_venta <= fin_act),
            )
            .where(SucursalORM.activa.is_(True))
            .group_by(
                SucursalORM.id_sucursal,
                SucursalORM.nombre,
                CiudadORM.nombre,
            )
            .order_by(desc("monto_suc"))
        )

        filas_suc = db.execute(stmt_suc).all()
        sucursales_out: List[SucursalDesempenoOut] = []

        for s in filas_suc:
            monto_s = Decimal(s.monto_suc or 0)
            ventas_s = int(s.ventas_suc or 0)
            ticket_s = (
                round(monto_s / Decimal(ventas_s), 2)
                if ventas_s > 0
                else Decimal("0.00")
            )
            part_red = (
                round((monto_s / total_red) * Decimal("100.00"), 2)
                if total_red > Decimal("0.00")
                else Decimal("0.00")
            )
            sucursales_out.append(
                SucursalDesempenoOut(
                    id_sucursal=s.id_sucursal,
                    nombre_sucursal=s.nombre_sucursal,
                    ciudad=s.nombre_ciudad,
                    monto_facturado=round(monto_s, 2),
                    total_ventas=ventas_s,
                    ticket_promedio=ticket_s,
                    porcentaje_red=part_red,
                )
            )

        return ComparativaSucursalesOut(sucursales=sucursales_out)

    def obtener_dashboard_consolidado(
        self, db: Session, filtros: IndicadoresFiltrosIn, usuario: UsuarioORM
    ) -> DashboardIndicadoresCompletoOut:
        """Genera el paquete analitico completo para inicializar la vista con una sola peticion."""
        resumen = self.obtener_resumen_ejecutivo(db, filtros, usuario)
        serie = self.obtener_serie_temporal(db, filtros, usuario)
        top = self.obtener_top_productos(db, filtros, usuario, limite=5)
        dist = self.obtener_distribucion_ventas(db, filtros, usuario)

        rol_nombre = str(getattr(usuario.rol, "nombre", usuario.rol) or "").lower().strip()
        comp: Optional[ComparativaSucursalesOut] = None
        if rol_nombre in ("administrador", "admin"):
            comp = self.obtener_comparativa_sucursales(db, filtros, usuario)

        return DashboardIndicadoresCompletoOut(
            resumen=resumen,
            serie_temporal=serie,
            top_productos=top,
            distribucion=dist,
            comparativa_sucursales=comp,
        )
