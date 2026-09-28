"""Servicio de dominio transaccional para CU31: Generar reportes ejecutivos y consultas por voz."""

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from modules.autenticacion_seguridad.modelos import ClienteORM, UsuarioORM
from modules.catalogo.modelos import InventarioSucursalORM, ProductoORM, VarianteProductoORM
from modules.comercial.cu28_ventas_reservas.modelos import ReservaORM, VentaORM
from modules.comercial.cu31_reportes_voz.errores import (
    AccesoReporteDenegadoError,
    FormatoNoSoportadoError,
    ModuloReporteInvalidoError,
)
from modules.comercial.cu31_reportes_voz.esquemas import (
    ComandoVozIn,
    ComandoVozOut,
    FormatoReporteEnum,
    ModuloReporteEnum,
    RangoTemporalEnum,
    ReporteFiltrosIn,
    ReportePrevisualizacionOut,
)
from modules.comercial.cu31_reportes_voz.generadores.generador_csv import GeneradorCSV
from modules.comercial.cu31_reportes_voz.generadores.generador_excel import GeneradorExcel
from modules.comercial.cu31_reportes_voz.generadores.generador_pdf import GeneradorPDF
from modules.comercial.cu31_reportes_voz.parser_voz import ParserComandosVoz
from modules.gestion_operativa.modelos import SucursalORM
from modules.seguridad.cu30_bitacora.modelos import Bitacora
from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria


class ServicioReportesVoz:
    """Logica de negocio, autorizacion RBAC y despacho de generacion de reportes."""

    ROLES_ADMIN = {"administrador", "admin"}
    ROLES_PERMITIDOS = {"administrador", "admin", "encargado_sucursal"}

    @classmethod
    def validar_permisos(
        cls,
        usuario: Optional[UsuarioORM],
        modulo: ModuloReporteEnum,
        id_sucursal_solicitada: Optional[int],
    ) -> None:
        """Aplica las reglas de autorizacion institucional RBAC."""
        if not usuario:
            raise AccesoReporteDenegadoError("Sesion no autenticada.")

        rol = str(getattr(usuario, "rol", "") or "").lower().strip()
        if rol not in cls.ROLES_PERMITIDOS:
            raise AccesoReporteDenegadoError(f"El rol '{rol}' no tiene autorizacion para acceder al centro de reportes.")

        if rol == "encargado_sucursal":
            if modulo == ModuloReporteEnum.BITACORA:
                raise AccesoReporteDenegadoError(
                    "Los encargados de sucursal tienen prohibido el acceso a la bitacora corporativa."
                )
            if id_sucursal_solicitada is None:
                raise AccesoReporteDenegadoError(
                    "Los encargados de sucursal no pueden emitir reportes globales consolidados."
                )
            if usuario.id_sucursal != id_sucursal_solicitada:
                raise AccesoReporteDenegadoError(
                    "No tienes autorizacion para emitir reportes de una sucursal distinta a la asignada."
                )

    @staticmethod
    def calcular_rango_fechas(
        periodo: RangoTemporalEnum,
        fecha_inicio_in: Optional[date] = None,
        fecha_fin_in: Optional[date] = None,
    ) -> Tuple[datetime, datetime]:
        """Calcula los limites de fecha y hora UTC para el periodo seleccionado."""
        ahora = datetime.now(timezone.utc)
        hoy = ahora.date()

        if periodo == RangoTemporalEnum.HOY:
            ini = datetime.combine(hoy, time.min, tzinfo=timezone.utc)
            fin = datetime.combine(hoy, time.max, tzinfo=timezone.utc)
        elif periodo == RangoTemporalEnum.AYER:
            ayer = hoy - timedelta(days=1)
            ini = datetime.combine(ayer, time.min, tzinfo=timezone.utc)
            fin = datetime.combine(ayer, time.max, tzinfo=timezone.utc)
        elif periodo == RangoTemporalEnum.ESTA_SEMANA:
            lunes = hoy - timedelta(days=hoy.weekday())
            domingo = lunes + timedelta(days=6)
            ini = datetime.combine(lunes, time.min, tzinfo=timezone.utc)
            fin = datetime.combine(domingo, time.max, tzinfo=timezone.utc)
        elif periodo == RangoTemporalEnum.ESTE_MES:
            primer_dia = hoy.replace(day=1)
            # Ultimo dia del mes
            if hoy.month == 12:
                ultimo_dia = hoy.replace(year=hoy.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                ultimo_dia = hoy.replace(month=hoy.month + 1, day=1) - timedelta(days=1)
            ini = datetime.combine(primer_dia, time.min, tzinfo=timezone.utc)
            fin = datetime.combine(ultimo_dia, time.max, tzinfo=timezone.utc)
        elif periodo == RangoTemporalEnum.ANIO_ACTUAL:
            primer_dia = hoy.replace(month=1, day=1)
            ultimo_dia = hoy.replace(month=12, day=31)
            ini = datetime.combine(primer_dia, time.min, tzinfo=timezone.utc)
            fin = datetime.combine(ultimo_dia, time.max, tzinfo=timezone.utc)
        else:
            # Personalizado
            f_ini = fecha_inicio_in or (hoy - timedelta(days=30))
            f_fin = fecha_fin_in or hoy
            ini = datetime.combine(f_ini, time.min, tzinfo=timezone.utc)
            fin = datetime.combine(f_fin, time.max, tzinfo=timezone.utc)

        return ini, fin

    @classmethod
    def obtener_sucursales_activas(cls, db: Session) -> List[Tuple[int, str]]:
        """Recupera la lista de sucursales activas para resolucion semantica."""
        try:
            stmt = select(SucursalORM.id_sucursal, SucursalORM.nombre).where(SucursalORM.activa.is_(True))
            return list(db.execute(stmt).all())
        except Exception:
            return []

    @classmethod
    def interpretar_comando(
        cls,
        db: Session,
        peticion: ComandoVozIn,
        usuario_actual: UsuarioORM,
    ) -> ComandoVozOut:
        """Interpreta la peticion verbal del operador, ajustando el alcance a sus privilegios RBAC."""
        rol = str(getattr(usuario_actual, "rol", "") or "").lower().strip()
        sucursales = cls.obtener_sucursales_activas(db)

        comando = ParserComandosVoz.interpretar(
            texto_original=peticion.texto_dictado,
            sucursales_conocidas=sucursales,
        )

        # Si el usuario es encargado de sucursal, forzar sucursal asignada y validar
        if rol == "encargado_sucursal":
            if comando.modulo == ModuloReporteEnum.BITACORA:
                comando.modulo = ModuloReporteEnum.VENTAS  # Degradacion contextual segura
            comando.id_sucursal = usuario_actual.id_sucursal
            if sucursales and usuario_actual.id_sucursal:
                nombre_asignado = next((n for sid, n in sucursales if sid == usuario_actual.id_sucursal), None)
                comando.nombre_sucursal = nombre_asignado

        # Calcular fechas concretas si es un rango conocido
        ini_dt, fin_dt = cls.calcular_rango_fechas(comando.periodo)
        comando.fecha_inicio = ini_dt.date()
        comando.fecha_fin = fin_dt.date()

        return comando

    @classmethod
    def previsualizar_reporte(
        cls,
        db: Session,
        filtros: ReporteFiltrosIn,
        usuario_actual: UsuarioORM,
    ) -> ReportePrevisualizacionOut:
        """Obtiene el conteo y resumen financiero estimado previo a compilar el reporte."""
        cls.validar_permisos(usuario_actual, filtros.modulo, filtros.id_sucursal)

        ini_dt, fin_dt = cls.calcular_rango_fechas(filtros.periodo, filtros.fecha_inicio, filtros.fecha_fin)
        total_registros = 0
        resumen_fin: Optional[Dict[str, Any]] = None

        if filtros.modulo == ModuloReporteEnum.VENTAS:
            condiciones = [VentaORM.fecha_venta >= ini_dt, VentaORM.fecha_venta <= fin_dt]
            if filtros.id_sucursal:
                condiciones.append(VentaORM.id_sucursal == filtros.id_sucursal)
            stmt = select(func.count(VentaORM.id_venta), func.coalesce(func.sum(VentaORM.total), Decimal("0.00"))).where(*condiciones)
            fila = db.execute(stmt).first()
            try:
                total_registros = int(fila[0]) if fila and fila[0] is not None else 0
            except (TypeError, ValueError):
                total_registros = 0
            try:
                monto_total = float(fila[1]) if fila and fila[1] is not None else 0.0
            except (TypeError, ValueError):
                monto_total = 0.0
            divisor = total_registros if total_registros > 0 else 1
            resumen_fin = {"monto_total_bob": monto_total, "ventas_promedio_bob": round(monto_total / divisor, 2)}

        elif filtros.modulo == ModuloReporteEnum.RESERVAS:
            condiciones = [ReservaORM.creado_en >= ini_dt, ReservaORM.creado_en <= fin_dt]
            if filtros.id_sucursal:
                condiciones.append(ReservaORM.id_sucursal == filtros.id_sucursal)
            stmt = select(func.count(ReservaORM.id_reserva)).where(*condiciones)
            res = db.scalar(stmt)
            try:
                total_registros = int(res) if res is not None else 0
            except (TypeError, ValueError):
                total_registros = 0
            resumen_fin = {"total_reservas": total_registros}

        elif filtros.modulo == ModuloReporteEnum.INVENTARIO:
            condiciones = []
            if filtros.id_sucursal:
                condiciones.append(InventarioSucursalORM.id_sucursal == filtros.id_sucursal)
            stmt = select(func.count(InventarioSucursalORM.id_inventario), func.coalesce(func.sum(InventarioSucursalORM.cantidad_disponible), 0)).where(*condiciones)
            fila = db.execute(stmt).first()
            try:
                total_registros = int(fila[0]) if fila and fila[0] is not None else 0
            except (TypeError, ValueError):
                total_registros = 0
            try:
                unidades_totales = int(fila[1]) if fila and fila[1] is not None else 0
            except (TypeError, ValueError):
                unidades_totales = 0
            resumen_fin = {"unidades_en_stock": unidades_totales}

        elif filtros.modulo == ModuloReporteEnum.BITACORA:
            condiciones = [Bitacora.creado_en >= ini_dt, Bitacora.creado_en <= fin_dt]
            stmt = select(func.count(Bitacora.id_bitacora)).where(*condiciones)
            res = db.scalar(stmt)
            try:
                total_registros = int(res) if res is not None else 0
            except (TypeError, ValueError):
                total_registros = 0
            resumen_fin = {"total_eventos_auditoria": total_registros}

        fecha_str = datetime.now().strftime("%Y%m%d")
        ext = "xlsx" if filtros.formato == FormatoReporteEnum.EXCEL else filtros.formato.value
        nombre_sugerido = f"reporte_{filtros.modulo.value}_{fecha_str}.{ext}"

        return ReportePrevisualizacionOut(
            modulo=filtros.modulo,
            formato=filtros.formato,
            total_registros=total_registros,
            fecha_corte=datetime.now(timezone.utc),
            nombre_archivo_sugerido=nombre_sugerido,
            resumen_financiero=resumen_fin,
        )

    @classmethod
    def extraer_datos_modulo(
        cls,
        db: Session,
        filtros: ReporteFiltrosIn,
    ) -> Tuple[str, str, List[str], List[List[Any]], Optional[Dict[str, Any]], Dict[str, str]]:
        """Ejecuta la consulta correspondiente al modulo y estructura columnas y filas."""
        ini_dt, fin_dt = cls.calcular_rango_fechas(filtros.periodo, filtros.fecha_inicio, filtros.fecha_fin)
        nombre_sucursal_txt = "Consolidado Todas las Sucursales"

        if filtros.id_sucursal:
            suc = db.get(SucursalORM, filtros.id_sucursal)
            if suc:
                nombre_sucursal_txt = suc.nombre

        metadatos = {
            "Sucursal": nombre_sucursal_txt,
            "Periodo": f"{ini_dt.strftime('%Y-%m-%d')} a {fin_dt.strftime('%Y-%m-%d')}",
        }

        # 1. Modulo Ventas
        if filtros.modulo == ModuloReporteEnum.VENTAS:
            titulo = "Reporte Ejecutivo de Ventas y Facturacion"
            subtitulo = f"Ventas registradas ({filtros.periodo.value})"
            columnas = ["CODIGO", "FECHA", "CLIENTE", "SUCURSAL", "METODO PAGO", "ESTADO", "TOTAL (BOB)"]

            condiciones = [VentaORM.fecha_venta >= ini_dt, VentaORM.fecha_venta <= fin_dt]
            if filtros.id_sucursal:
                condiciones.append(VentaORM.id_sucursal == filtros.id_sucursal)

            stmt = (
                select(VentaORM)
                .options(
                    joinedload(VentaORM.cliente).joinedload(ClienteORM.usuario),
                    joinedload(VentaORM.sucursal),
                )
                .where(*condiciones)
                .order_by(VentaORM.fecha_venta.desc())
                .limit(5000)
            )
            ventas = db.execute(stmt).scalars().all()

            filas = []
            suma_total = Decimal("0.00")
            for v in ventas:
                nom_cliente = "Venta Mostrador"
                if v.cliente and v.cliente.usuario:
                    nom_cliente = f"{v.cliente.usuario.nombres} {v.cliente.usuario.apellidos}".strip() or v.cliente.usuario.email
                elif v.cliente:
                    nom_cliente = f"Cliente #{v.id_cliente}"

                nom_suc = v.sucursal.nombre if v.sucursal else "Central"
                tot_val = float(v.total or Decimal("0.00"))
                suma_total += (v.total or Decimal("0.00"))
                filas.append([v.numero_comprobante, v.fecha_venta, nom_cliente, nom_suc, v.tipo_venta, v.estado, tot_val])

            totales = {"TOTAL (BOB)": float(suma_total)}
            return titulo, subtitulo, columnas, filas, totales, metadatos

        # 2. Modulo Reservas
        elif filtros.modulo == ModuloReporteEnum.RESERVAS:
            titulo = "Reporte Ejecutivo de Reservas de Boutique"
            subtitulo = f"Citas de fitting presencial ({filtros.periodo.value})"
            columnas = ["CODIGO", "FECHA CITA", "CLIENTE", "SUCURSAL", "CANAL", "ESTADO", "REGISTRADO"]

            condiciones = [ReservaORM.creado_en >= ini_dt, ReservaORM.creado_en <= fin_dt]
            if filtros.id_sucursal:
                condiciones.append(ReservaORM.id_sucursal == filtros.id_sucursal)

            stmt = (
                select(ReservaORM)
                .options(
                    joinedload(ReservaORM.cliente).joinedload(ClienteORM.usuario),
                    joinedload(ReservaORM.sucursal),
                )
                .where(*condiciones)
                .order_by(ReservaORM.creado_en.desc())
                .limit(5000)
            )
            reservas = db.execute(stmt).scalars().all()

            filas = []
            for r in reservas:
                nom_cliente = "Cliente Atelier"
                if r.cliente and r.cliente.usuario:
                    nom_cliente = f"{r.cliente.usuario.nombres} {r.cliente.usuario.apellidos}".strip() or r.cliente.usuario.email
                elif r.cliente:
                    nom_cliente = f"Cliente #{r.id_cliente}"

                nom_suc = r.sucursal.nombre if r.sucursal else "Boutique"
                cod_reserva = f"RES-{r.id_reserva:05d}" if r.id_reserva else "RES-00000"
                filas.append([cod_reserva, r.fecha_hora_atencion, nom_cliente, nom_suc, r.canal_origen, r.estado, r.creado_en])

            totales = {"CODIGO": f"Total: {len(filas)} reservas"}
            return titulo, subtitulo, columnas, filas, totales, metadatos

        # 3. Modulo Inventario
        elif filtros.modulo == ModuloReporteEnum.INVENTARIO:
            titulo = "Reporte Ejecutivo de Inventario y Stock"
            subtitulo = "Existencias fisicas en sucursales"
            columnas = ["SKU", "PRENDA", "TALLA", "COLOR", "SUCURSAL", "DISPONIBLE", "ESTADO"]

            condiciones = []
            if filtros.id_sucursal:
                condiciones.append(InventarioSucursalORM.id_sucursal == filtros.id_sucursal)

            stmt = (
                select(InventarioSucursalORM)
                .options(
                    joinedload(InventarioSucursalORM.variante).joinedload(VarianteProductoORM.producto),
                    joinedload(InventarioSucursalORM.variante).joinedload(VarianteProductoORM.talla),
                    joinedload(InventarioSucursalORM.variante).joinedload(VarianteProductoORM.color),
                    joinedload(InventarioSucursalORM.sucursal),
                )
                .where(*condiciones)
                .order_by(InventarioSucursalORM.id_inventario.asc())
                .limit(5000)
            )
            inventarios = db.execute(stmt).scalars().all()

            filas = []
            total_unidades = 0
            for inv in inventarios:
                var = inv.variante
                prod_nombre = var.producto.nombre if var and var.producto else "Prenda"
                talla_txt = var.talla.codigo if var and var.talla else "-"
                color_txt = var.color.nombre if var and var.color else "-"
                sku_txt = var.sku if var else "-"
                nom_suc = inv.sucursal.nombre if inv.sucursal else "Almacen"
                disp = inv.cantidad_disponible
                total_unidades += disp
                filas.append([sku_txt, prod_nombre, talla_txt, color_txt, nom_suc, disp, inv.estado])

            totales = {"DISPONIBLE": total_unidades}
            return titulo, subtitulo, columnas, filas, totales, metadatos

        # 4. Modulo Bitacora
        elif filtros.modulo == ModuloReporteEnum.BITACORA:
            titulo = "Reporte Ejecutivo de Auditoria y Bitacora"
            subtitulo = f"Trazabilidad de operaciones ({filtros.periodo.value})"
            columnas = ["ID", "FECHA", "OPERADOR", "MODULO", "ACCION", "SEVERIDAD", "IP ORIGEN"]

            condiciones = [Bitacora.creado_en >= ini_dt, Bitacora.creado_en <= fin_dt]
            stmt = select(Bitacora).where(*condiciones).order_by(Bitacora.creado_en.desc()).limit(5000)
            eventos = db.execute(stmt).scalars().all()

            filas = []
            for ev in eventos:
                filas.append([ev.id_bitacora, ev.creado_en, ev.usuario_nombre or "Sistema", ev.tabla_modulo, ev.accion, ev.severidad, ev.direccion_ip or "-"])

            totales = {"ID": f"Total: {len(filas)} eventos"}
            return titulo, subtitulo, columnas, filas, totales, metadatos

        raise ModuloReporteInvalidoError(filtros.modulo.value)

    @classmethod
    def generar_archivo_reporte(
        cls,
        db: Session,
        filtros: ReporteFiltrosIn,
        usuario_actual: UsuarioORM,
    ) -> Tuple[bytes, str, str]:
        """Compila y genera el archivo binario, registrando la auditoria correspondiente.

        Returns:
            Tupla con (contenido_bytes, nombre_archivo, media_type).
        """
        cls.validar_permisos(usuario_actual, filtros.modulo, filtros.id_sucursal)

        titulo, subtitulo, columnas, filas, totales, metadatos = cls.extraer_datos_modulo(db, filtros)
        fecha_str = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 1. Despachar a generador binario
        if filtros.formato == FormatoReporteEnum.EXCEL:
            contenido = GeneradorExcel.generar(
                titulo=titulo, subtitulo=subtitulo, columnas=columnas,
                filas=filas, totales=totales, metadatos=metadatos,
            )
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            nombre_archivo = f"reporte_{filtros.modulo.value}_{fecha_str}.xlsx"

        elif filtros.formato == FormatoReporteEnum.PDF:
            contenido = GeneradorPDF.generar(
                titulo=titulo, subtitulo=subtitulo, columnas=columnas,
                filas=filas, totales=totales, metadatos=metadatos,
            )
            media_type = "application/pdf"
            nombre_archivo = f"reporte_{filtros.modulo.value}_{fecha_str}.pdf"

        elif filtros.formato == FormatoReporteEnum.CSV:
            contenido = GeneradorCSV.generar(
                titulo=titulo, subtitulo=subtitulo, columnas=columnas,
                filas=filas, totales=totales, metadatos=metadatos,
            )
            media_type = "text/csv; charset=utf-8"
            nombre_archivo = f"reporte_{filtros.modulo.value}_{fecha_str}.csv"

        else:
            raise FormatoNoSoportadoError(filtros.formato.value)

        # 2. Registrar evento en bitacora de auditoria (CU30) de forma segura
        nombre_u = f"{usuario_actual.nombres} {usuario_actual.apellidos}".strip() or usuario_actual.email
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario_actual.id_usuario,
            usuario_nombre=nombre_u,
            accion="EXPORTAR_REPORTE",
            tabla_modulo="reportes",
            severidad="INFO",
            payload_anterior=None,
            payload_nuevo={
                "modulo": filtros.modulo.value,
                "formato": filtros.formato.value,
                "periodo": filtros.periodo.value,
                "id_sucursal": filtros.id_sucursal,
                "total_registros": len(filas),
                "nombre_archivo": nombre_archivo,
            },
            db=db,
        )

        return contenido, nombre_archivo, media_type
