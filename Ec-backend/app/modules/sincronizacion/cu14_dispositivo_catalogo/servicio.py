"""P2-CU14 · Descargar catálogo y registrar dispositivo (AC-14.1 a AC-14.4, AC-14.8).

El paquete sale solo de la empresa de la cabecera `X-Tenant` (RLS). La app lo guarda en IndexedDB
o SQLite y solo reemplaza lo anterior cuando la descarga termina (A2, lo garantiza la app).
"""

import uuid
from decimal import Decimal
from typing import Literal

from sqlalchemy.orm import Session

from core.errors import ConflictError, NotFoundError
from core.tiempo import ahora
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.plataforma.cu11_parametros_empresa.servicio import ParametrosEmpresaServicio
from modules.plataforma.cu12_validar_suscripcion.servicio import SuscripcionServicio
from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria
from modules.sincronizacion.comun import exigir_cliente, nombre_usuario
from modules.sincronizacion.cu14_dispositivo_catalogo.esquemas import (
    CatalogoLocalOut,
    CategoriaLocalOut,
    ColorLocalOut,
    DispositivoIn,
    DispositivoOut,
    DispositivoTokenPushIn,
    DispositivoTokenPushOut,
    ExistenciaLocalOut,
    ProductoLocalOut,
    PromocionLocalOut,
    SucursalLocalOut,
    TallaLocalOut,
    VarianteLocalOut,
)
from modules.sincronizacion.cu14_dispositivo_catalogo.repositorio import (
    CatalogoLocalRepositorio,
    DispositivoRepositorio,
)
from modules.sincronizacion.modelos import DispositivoORM


def codigo_corto(identificador: uuid.UUID) -> str:
    """Los 4 primeros caracteres hexadecimales del UUID, en mayúsculas (RN34)."""
    return identificador.hex[:4].upper()


class DispositivoServicio:
    @staticmethod
    def registrar(db: Session, usuario: UsuarioORM, datos: DispositivoIn) -> tuple[DispositivoOut, bool]:
        """Registra o reutiliza el dispositivo (A1). Devuelve la salida y si lo creó."""
        id_cliente = exigir_cliente(db, usuario)
        # RN16: el plan debe incluir la operación sin conexión (403 FUNCIONALIDAD_NO_INCLUIDA).
        SuscripcionServicio.validar(db, funcionalidad="operacion_offline")
        creado = DispositivoRepositorio.insertar_si_falta(
            db,
            datos.identificador,
            id_cliente,
            datos.plataforma,
            codigo_corto(datos.identificador),
            datos.token_push,
        )
        dispositivo = DispositivoRepositorio.por_identificador(db, datos.identificador)
        if dispositivo is None or dispositivo.id_cliente != id_cliente:
            # La app genera el identificador por cliente y empresa: otro cliente no puede reusarlo.
            db.rollback()
            raise ConflictError(
                "Este dispositivo está registrado para otra cuenta. Cierra sesión y vuelve a entrar.",
                code="DISPOSITIVO_DE_OTRO_CLIENTE",
            )
        if not creado and datos.token_push and getattr(dispositivo, "token_push", None) != datos.token_push:
            dispositivo.token_push = datos.token_push
        if creado:
            ServicioBitacoraAuditoria.registrar_evento_seguro(
                id_usuario=usuario.id_usuario,
                usuario_nombre=nombre_usuario(usuario),
                accion="DISPOSITIVO_REGISTRADO",
                tabla_modulo="dispositivos",
                payload_nuevo={
                    "id_dispositivo": dispositivo.id_dispositivo,
                    "plataforma": dispositivo.plataforma,
                    "codigo_corto": dispositivo.codigo_corto,
                },
                db=db,
            )
        db.commit()
        db.refresh(dispositivo)
        return DispositivoServicio._salida(db, dispositivo), creado

    @staticmethod
    def actualizar_token_push(
        db: Session, usuario: UsuarioORM, datos: DispositivoTokenPushIn
    ) -> DispositivoTokenPushOut:
        """Actualiza o registra el token push del dispositivo del cliente (AC-C1).

        Si el token llega vacío, desasocia las notificaciones push del dispositivo.
        Si el dispositivo aún no existía (p. ej. tienda sin operación offline), lo da de alta
        para garantizar que las notificaciones push (RF37) funcionen en cualquier plan.
        """
        id_cliente = exigir_cliente(db, usuario)
        token_limpio = datos.token_push.strip() or None
        dispositivo = DispositivoRepositorio.por_identificador(db, datos.identificador, bloquear=True)
        if dispositivo is None:
            DispositivoRepositorio.insertar_si_falta(
                db,
                datos.identificador,
                id_cliente,
                "flutter",
                codigo_corto(datos.identificador),
                token_limpio,
            )
            dispositivo = DispositivoRepositorio.por_identificador(db, datos.identificador, bloquear=True)
        if dispositivo is None or dispositivo.id_cliente != id_cliente:
            db.rollback()
            raise ConflictError(
                "Este dispositivo está registrado para otra cuenta. Cierra sesión y vuelve a entrar.",
                code="DISPOSITIVO_DE_OTRO_CLIENTE",
            )
        dispositivo.token_push = token_limpio
        db.commit()
        db.refresh(dispositivo)
        return DispositivoTokenPushOut(
            ok=True,
            identificador=dispositivo.identificador,
            token_push=dispositivo.token_push or "",
        )

    @staticmethod
    def del_cliente(db: Session, usuario: UsuarioORM, identificador: uuid.UUID, bloquear: bool = False) -> DispositivoORM:
        """El dispositivo debe existir en esta empresa y ser del cliente (404 si no)."""
        id_cliente = exigir_cliente(db, usuario)
        dispositivo = DispositivoRepositorio.por_identificador(db, identificador, bloquear=bloquear)
        if dispositivo is None or dispositivo.id_cliente != id_cliente:
            raise NotFoundError(
                "El dispositivo no está registrado en esta tienda.", code="DISPOSITIVO_NO_ENCONTRADO"
            )
        return dispositivo

    @staticmethod
    def _salida(db: Session, dispositivo: DispositivoORM) -> DispositivoOut:
        parametros = ParametrosEmpresaServicio.vigentes(db)
        return DispositivoOut(
            id_dispositivo=dispositivo.id_dispositivo,
            identificador=dispositivo.identificador,
            plataforma=dispositivo.plataforma,
            codigo_corto=dispositivo.codigo_corto,
            registrado_en=dispositivo.registrado_en,
            ultima_descarga_en=dispositivo.ultima_descarga_en,
            token_push=getattr(dispositivo, "token_push", None),
            operacion_offline_habilitada=parametros.operacion_offline_habilitada,
            dias_antiguedad_offline=parametros.dias_antiguedad_offline,
            horas_vencimiento_reserva=parametros.horas_vencimiento_reserva,
            moneda=parametros.moneda,
        )


class CatalogoSinConexionServicio:
    @staticmethod
    def descargar(
        db: Session,
        usuario: UsuarioORM,
        identificador: uuid.UUID,
        modo: Literal["completo", "indispensable"] = "completo",
    ) -> CatalogoLocalOut:
        dispositivo = DispositivoServicio.del_cliente(db, usuario, identificador, bloquear=True)
        SuscripcionServicio.validar(db, funcionalidad="operacion_offline")
        inicio = ahora()
        completo = modo == "completo"

        productos = CatalogoLocalRepositorio.productos_activos(db)
        ids_talla: set[int] = set()
        ids_color: set[int] = set()
        productos_out = []
        for producto in productos:
            variantes = [v for v in producto.variantes if v.activo]
            if not variantes:
                continue
            for variante in variantes:
                ids_talla.add(variante.id_talla)
                ids_color.add(variante.id_color)
            productos_out.append(
                ProductoLocalOut(
                    id_producto=producto.id_producto,
                    nombre=producto.nombre,
                    descripcion=producto.descripcion if completo else None,
                    id_categoria=producto.id_categoria,
                    precio_base=producto.precio_base,
                    imagen_url=producto.imagen_url,
                    variantes=[
                        VarianteLocalOut(
                            id_variante=v.id_variante,
                            sku=v.sku,
                            id_talla=v.id_talla,
                            id_color=v.id_color,
                            precio=producto.precio_base + (v.precio_extra or Decimal("0.00")),
                        )
                        for v in variantes
                    ],
                )
            )

        promociones_out = []
        if completo:
            promociones = CatalogoLocalRepositorio.promociones_vigentes(db, inicio)
            productos_por_promocion = CatalogoLocalRepositorio.productos_de_promociones(
                db, [p.id_promocion for p in promociones]
            )
            # Sin `codigo_cupon`: un cupón no se publica en el dispositivo.
            promociones_out = [
                PromocionLocalOut(
                    id_promocion=p.id_promocion,
                    nombre=p.nombre,
                    tipo_descuento=p.tipo_descuento,
                    valor_descuento=p.valor_descuento,
                    alcance=p.alcance,
                    id_categoria=p.id_categoria,
                    id_producto=p.id_producto,
                    productos=productos_por_promocion.get(p.id_promocion, []),
                    fecha_fin=p.fecha_fin,
                )
                for p in promociones
                if not p.codigo_cupon
            ]

        sucursales = CatalogoLocalRepositorio.sucursales_activas(db)
        existencias = CatalogoLocalRepositorio.existencias(db, [s.id_sucursal for s in sucursales])
        moneda = ParametrosEmpresaServicio.vigentes(db).moneda

        paquete = CatalogoLocalOut(
            generado_en=inicio,
            modo=modo,
            moneda=moneda,
            productos=productos_out,
            categorias=[
                CategoriaLocalOut(
                    id_categoria=c.id_categoria, nombre=c.nombre, id_categoria_padre=c.id_categoria_padre
                )
                for c in CatalogoLocalRepositorio.categorias(db)
            ],
            tallas=[
                TallaLocalOut(id_talla=t.id_talla, codigo=t.codigo, orden=t.orden)
                for t in CatalogoLocalRepositorio.tallas(db, ids_talla)
            ],
            colores=[
                ColorLocalOut(id_color=c.id_color, nombre=c.nombre, codigo_hex=c.codigo_hex)
                for c in CatalogoLocalRepositorio.colores(db, ids_color)
            ],
            promociones=promociones_out,
            sucursales=[
                SucursalLocalOut(
                    id_sucursal=s.id_sucursal,
                    nombre=s.nombre,
                    direccion=s.direccion,
                    ciudad=s.ciudad.nombre if getattr(s, "ciudad", None) else None,
                    horario_apertura=s.horario_apertura.strftime("%H:%M") if s.horario_apertura else None,
                    horario_cierre=s.horario_cierre.strftime("%H:%M") if s.horario_cierre else None,
                )
                for s in sucursales
            ],
            existencias=[
                ExistenciaLocalOut(id_variante=v, id_sucursal=s, cantidad_disponible=c)
                for v, s, c in existencias
            ],
        )

        fin = ahora()
        dispositivo.ultima_descarga_en = fin
        DispositivoRepositorio.registrar_log(
            db,
            id_dispositivo=dispositivo.id_dispositivo,
            tipo="descarga",
            iniciado_en=inicio,
            finalizado_en=fin,
            resultado="ok",
            mensaje=f"Catálogo {modo}: {len(productos_out)} productos, {len(sucursales)} sucursales.",
        )
        db.commit()
        return paquete
