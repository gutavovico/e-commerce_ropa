"""Servicio de aplicación y dominio para P2-CU08: Gestionar catálogos globales (ciudades, tallas, colores)."""

from typing import Optional

from sqlalchemy.orm import Session

from core.errors import ConflictError, NotFoundError
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.plataforma.cu08_catalogos_globales.esquemas import (
    CambiarEstadoCatalogoIn,
    CiudadGlobalIn,
    CiudadGlobalOut,
    ColorGlobalIn,
    ColorGlobalOut,
    EliminacionCatalogoOut,
    TallaGlobalIn,
    TallaGlobalOut,
)
from modules.plataforma.cu08_catalogos_globales.repositorio import CatalogosGlobalesRepositorio
from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria


class CatalogosGlobalesServicio:
    """Casos de uso de administración de ciudades, tallas y colores globales (RN21)."""

    # --- Ciudades ---

    @staticmethod
    def listar_ciudades(db: Session, *, solo_activas: bool = False) -> list[CiudadGlobalOut]:
        filas = CatalogosGlobalesRepositorio.listar_ciudades(db, solo_activas=solo_activas)
        return [CiudadGlobalOut(**f) for f in filas]

    @staticmethod
    def crear_ciudad(
        db: Session,
        datos: CiudadGlobalIn,
        usuario_actual: UsuarioORM,
        direccion_ip: Optional[str] = None,
    ) -> CiudadGlobalOut:
        nombre_norm = datos.nombre.strip()
        pais_norm = datos.pais.strip()
        if CatalogosGlobalesRepositorio.buscar_ciudad_por_nombre(db, nombre_norm) is not None:
            raise ConflictError(
                f"Ya existe una ciudad registrada con el nombre '{nombre_norm}'.",
                code="CIUDAD_DUPLICADA",
            )
        creada = CatalogosGlobalesRepositorio.crear_ciudad(db, nombre=nombre_norm, pais=pais_norm)
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario_actual.id_usuario,
            usuario_nombre=usuario_actual.email,
            accion="CREAR_CIUDAD_GLOBAL",
            tabla_modulo="plataforma.ciudades",
            direccion_ip=direccion_ip,
            severidad="INFO",
            payload_nuevo=creada,
            db=db,
        )
        return CiudadGlobalOut(**creada)

    @staticmethod
    def actualizar_ciudad(
        db: Session,
        id_ciudad: int,
        datos: CiudadGlobalIn,
        usuario_actual: UsuarioORM,
        direccion_ip: Optional[str] = None,
    ) -> CiudadGlobalOut:
        actual = CatalogosGlobalesRepositorio.obtener_ciudad(db, id_ciudad)
        if not actual:
            raise NotFoundError(
                f"La ciudad con identificador {id_ciudad} no existe.",
                code="CIUDAD_NO_ENCONTRADA",
            )
        nombre_norm = datos.nombre.strip()
        pais_norm = datos.pais.strip()
        if (
            CatalogosGlobalesRepositorio.buscar_ciudad_por_nombre(
                db, nombre_norm, excluir_id=id_ciudad
            )
            is not None
        ):
            raise ConflictError(
                f"Ya existe otra ciudad registrada con el nombre '{nombre_norm}'.",
                code="CIUDAD_DUPLICADA",
            )
        actualizada = CatalogosGlobalesRepositorio.actualizar_ciudad(
            db, id_ciudad, nombre=nombre_norm, pais=pais_norm
        )
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario_actual.id_usuario,
            usuario_nombre=usuario_actual.email,
            accion="ACTUALIZAR_CIUDAD_GLOBAL",
            tabla_modulo="plataforma.ciudades",
            direccion_ip=direccion_ip,
            severidad="INFO",
            payload_anterior={"nombre": actual["nombre"], "pais": actual["pais"]},
            payload_nuevo={"id_ciudad": id_ciudad, "nombre": nombre_norm, "pais": pais_norm},
            db=db,
        )
        return CiudadGlobalOut(**actualizada)

    @staticmethod
    def cambiar_estado_ciudad(
        db: Session,
        id_ciudad: int,
        datos: CambiarEstadoCatalogoIn,
        usuario_actual: UsuarioORM,
        direccion_ip: Optional[str] = None,
    ) -> CiudadGlobalOut:
        actual = CatalogosGlobalesRepositorio.obtener_ciudad(db, id_ciudad)
        if not actual:
            raise NotFoundError(
                f"La ciudad con identificador {id_ciudad} no existe.",
                code="CIUDAD_NO_ENCONTRADA",
            )
        actualizada = CatalogosGlobalesRepositorio.cambiar_estado_ciudad(
            db, id_ciudad, activo=datos.activo
        )
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario_actual.id_usuario,
            usuario_nombre=usuario_actual.email,
            accion="ESTADO_CIUDAD_GLOBAL",
            tabla_modulo="plataforma.ciudades",
            direccion_ip=direccion_ip,
            severidad="INFO" if datos.activo else "WARN",
            payload_anterior={"id_ciudad": id_ciudad, "activo": actual["activo"]},
            payload_nuevo={"id_ciudad": id_ciudad, "activo": datos.activo},
            db=db,
        )
        return CiudadGlobalOut(**actualizada)

    @staticmethod
    def eliminar_ciudad(
        db: Session,
        id_ciudad: int,
        usuario_actual: UsuarioORM,
        direccion_ip: Optional[str] = None,
    ) -> EliminacionCatalogoOut:
        actual = CatalogosGlobalesRepositorio.obtener_ciudad(db, id_ciudad)
        if not actual:
            raise NotFoundError(
                f"La ciudad con identificador {id_ciudad} no existe.",
                code="CIUDAD_NO_ENCONTRADA",
            )
        sucursales_uso = int(actual.get("sucursales_asociadas", 0))
        if sucursales_uso > 0:
            raise ConflictError(
                f"La ciudad '{actual['nombre']}' está referenciada por {sucursales_uso} sucursal(es). "
                "No puede eliminarse; puede desactivarla para que no se asigne a nuevas sucursales (CU08 A2).",
                code="ELEMENTO_CATALOGO_EN_USO",
            )
        CatalogosGlobalesRepositorio.eliminar_ciudad(db, id_ciudad)
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario_actual.id_usuario,
            usuario_nombre=usuario_actual.email,
            accion="ELIMINAR_CIUDAD_GLOBAL",
            tabla_modulo="plataforma.ciudades",
            direccion_ip=direccion_ip,
            severidad="WARN",
            payload_anterior={"id_ciudad": id_ciudad, "nombre": actual["nombre"]},
            db=db,
        )
        return EliminacionCatalogoOut(
            eliminado=True,
            mensaje=f"Ciudad '{actual['nombre']}' eliminada correctamente.",
        )

    # --- Tallas ---

    @staticmethod
    def listar_tallas(db: Session, *, solo_activas: bool = False) -> list[TallaGlobalOut]:
        filas = CatalogosGlobalesRepositorio.listar_tallas(db, solo_activas=solo_activas)
        return [TallaGlobalOut(**f) for f in filas]

    @staticmethod
    def crear_talla(
        db: Session,
        datos: TallaGlobalIn,
        usuario_actual: UsuarioORM,
        direccion_ip: Optional[str] = None,
    ) -> TallaGlobalOut:
        codigo_norm = datos.codigo.strip().upper()
        if CatalogosGlobalesRepositorio.buscar_talla_por_codigo(db, codigo_norm) is not None:
            raise ConflictError(
                f"Ya existe una talla registrada con el código '{codigo_norm}'.",
                code="TALLA_DUPLICADA",
            )
        creada = CatalogosGlobalesRepositorio.crear_talla(
            db, codigo=codigo_norm, orden=datos.orden
        )
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario_actual.id_usuario,
            usuario_nombre=usuario_actual.email,
            accion="CREAR_TALLA_GLOBAL",
            tabla_modulo="plataforma.tallas",
            direccion_ip=direccion_ip,
            severidad="INFO",
            payload_nuevo=creada,
            db=db,
        )
        return TallaGlobalOut(**creada)

    @staticmethod
    def actualizar_talla(
        db: Session,
        id_talla: int,
        datos: TallaGlobalIn,
        usuario_actual: UsuarioORM,
        direccion_ip: Optional[str] = None,
    ) -> TallaGlobalOut:
        actual = CatalogosGlobalesRepositorio.obtener_talla(db, id_talla)
        if not actual:
            raise NotFoundError(
                f"La talla con identificador {id_talla} no existe.",
                code="TALLA_NO_ENCONTRADA",
            )
        codigo_norm = datos.codigo.strip().upper()
        if (
            CatalogosGlobalesRepositorio.buscar_talla_por_codigo(
                db, codigo_norm, excluir_id=id_talla
            )
            is not None
        ):
            raise ConflictError(
                f"Ya existe otra talla registrada con el código '{codigo_norm}'.",
                code="TALLA_DUPLICADA",
            )
        actualizada = CatalogosGlobalesRepositorio.actualizar_talla(
            db, id_talla, codigo=codigo_norm, orden=datos.orden
        )
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario_actual.id_usuario,
            usuario_nombre=usuario_actual.email,
            accion="ACTUALIZAR_TALLA_GLOBAL",
            tabla_modulo="plataforma.tallas",
            direccion_ip=direccion_ip,
            severidad="INFO",
            payload_anterior={"codigo": actual["codigo"], "orden": actual["orden"]},
            payload_nuevo={"id_talla": id_talla, "codigo": codigo_norm, "orden": datos.orden},
            db=db,
        )
        return TallaGlobalOut(**actualizada)

    @staticmethod
    def cambiar_estado_talla(
        db: Session,
        id_talla: int,
        datos: CambiarEstadoCatalogoIn,
        usuario_actual: UsuarioORM,
        direccion_ip: Optional[str] = None,
    ) -> TallaGlobalOut:
        actual = CatalogosGlobalesRepositorio.obtener_talla(db, id_talla)
        if not actual:
            raise NotFoundError(
                f"La talla con identificador {id_talla} no existe.",
                code="TALLA_NO_ENCONTRADA",
            )
        actualizada = CatalogosGlobalesRepositorio.cambiar_estado_talla(
            db, id_talla, activo=datos.activo
        )
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario_actual.id_usuario,
            usuario_nombre=usuario_actual.email,
            accion="ESTADO_TALLA_GLOBAL",
            tabla_modulo="plataforma.tallas",
            direccion_ip=direccion_ip,
            severidad="INFO" if datos.activo else "WARN",
            payload_anterior={"id_talla": id_talla, "activo": actual["activo"]},
            payload_nuevo={"id_talla": id_talla, "activo": datos.activo},
            db=db,
        )
        return TallaGlobalOut(**actualizada)

    @staticmethod
    def eliminar_talla(
        db: Session,
        id_talla: int,
        usuario_actual: UsuarioORM,
        direccion_ip: Optional[str] = None,
    ) -> EliminacionCatalogoOut:
        actual = CatalogosGlobalesRepositorio.obtener_talla(db, id_talla)
        if not actual:
            raise NotFoundError(
                f"La talla con identificador {id_talla} no existe.",
                code="TALLA_NO_ENCONTRADA",
            )
        variantes_uso = int(actual.get("variantes_asociadas", 0))
        if variantes_uso > 0:
            raise ConflictError(
                f"La talla '{actual['codigo']}' está referenciada por {variantes_uso} variante(s) de producto. "
                "No puede eliminarse; puede desactivarla para que no se asigne a nuevas variantes (CU08 A2).",
                code="ELEMENTO_CATALOGO_EN_USO",
            )
        CatalogosGlobalesRepositorio.eliminar_talla(db, id_talla)
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario_actual.id_usuario,
            usuario_nombre=usuario_actual.email,
            accion="ELIMINAR_TALLA_GLOBAL",
            tabla_modulo="plataforma.tallas",
            direccion_ip=direccion_ip,
            severidad="WARN",
            payload_anterior={"id_talla": id_talla, "codigo": actual["codigo"]},
            db=db,
        )
        return EliminacionCatalogoOut(
            eliminado=True,
            mensaje=f"Talla '{actual['codigo']}' eliminada correctamente.",
        )

    # --- Colores ---

    @staticmethod
    def listar_colores(db: Session, *, solo_activos: bool = False) -> list[ColorGlobalOut]:
        filas = CatalogosGlobalesRepositorio.listar_colores(db, solo_activos=solo_activos)
        return [ColorGlobalOut(**f) for f in filas]

    @staticmethod
    def crear_color(
        db: Session,
        datos: ColorGlobalIn,
        usuario_actual: UsuarioORM,
        direccion_ip: Optional[str] = None,
    ) -> ColorGlobalOut:
        nombre_norm = datos.nombre.strip()
        hex_norm = datos.codigo_hex.strip().upper()
        if CatalogosGlobalesRepositorio.buscar_color_por_nombre(db, nombre_norm) is not None:
            raise ConflictError(
                f"Ya existe un color registrado con el nombre '{nombre_norm}'.",
                code="COLOR_DUPLICADO",
            )
        creado = CatalogosGlobalesRepositorio.crear_color(
            db, nombre=nombre_norm, codigo_hex=hex_norm
        )
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario_actual.id_usuario,
            usuario_nombre=usuario_actual.email,
            accion="CREAR_COLOR_GLOBAL",
            tabla_modulo="plataforma.colores",
            direccion_ip=direccion_ip,
            severidad="INFO",
            payload_nuevo=creado,
            db=db,
        )
        return ColorGlobalOut(**creado)

    @staticmethod
    def actualizar_color(
        db: Session,
        id_color: int,
        datos: ColorGlobalIn,
        usuario_actual: UsuarioORM,
        direccion_ip: Optional[str] = None,
    ) -> ColorGlobalOut:
        actual = CatalogosGlobalesRepositorio.obtener_color(db, id_color)
        if not actual:
            raise NotFoundError(
                f"El color con identificador {id_color} no existe.",
                code="COLOR_NO_ENCONTRADO",
            )
        nombre_norm = datos.nombre.strip()
        hex_norm = datos.codigo_hex.strip().upper()
        if (
            CatalogosGlobalesRepositorio.buscar_color_por_nombre(
                db, nombre_norm, excluir_id=id_color
            )
            is not None
        ):
            raise ConflictError(
                f"Ya existe otro color registrado con el nombre '{nombre_norm}'.",
                code="COLOR_DUPLICADO",
            )
        actualizado = CatalogosGlobalesRepositorio.actualizar_color(
            db, id_color, nombre=nombre_norm, codigo_hex=hex_norm
        )
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario_actual.id_usuario,
            usuario_nombre=usuario_actual.email,
            accion="ACTUALIZAR_COLOR_GLOBAL",
            tabla_modulo="plataforma.colores",
            direccion_ip=direccion_ip,
            severidad="INFO",
            payload_anterior={"nombre": actual["nombre"], "codigo_hex": actual["codigo_hex"]},
            payload_nuevo={"id_color": id_color, "nombre": nombre_norm, "codigo_hex": hex_norm},
            db=db,
        )
        return ColorGlobalOut(**actualizado)

    @staticmethod
    def cambiar_estado_color(
        db: Session,
        id_color: int,
        datos: CambiarEstadoCatalogoIn,
        usuario_actual: UsuarioORM,
        direccion_ip: Optional[str] = None,
    ) -> ColorGlobalOut:
        actual = CatalogosGlobalesRepositorio.obtener_color(db, id_color)
        if not actual:
            raise NotFoundError(
                f"El color con identificador {id_color} no existe.",
                code="COLOR_NO_ENCONTRADO",
            )
        actualizado = CatalogosGlobalesRepositorio.cambiar_estado_color(
            db, id_color, activo=datos.activo
        )
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario_actual.id_usuario,
            usuario_nombre=usuario_actual.email,
            accion="ESTADO_COLOR_GLOBAL",
            tabla_modulo="plataforma.colores",
            direccion_ip=direccion_ip,
            severidad="INFO" if datos.activo else "WARN",
            payload_anterior={"id_color": id_color, "activo": actual["activo"]},
            payload_nuevo={"id_color": id_color, "activo": datos.activo},
            db=db,
        )
        return ColorGlobalOut(**actualizado)

    @staticmethod
    def eliminar_color(
        db: Session,
        id_color: int,
        usuario_actual: UsuarioORM,
        direccion_ip: Optional[str] = None,
    ) -> EliminacionCatalogoOut:
        actual = CatalogosGlobalesRepositorio.obtener_color(db, id_color)
        if not actual:
            raise NotFoundError(
                f"El color con identificador {id_color} no existe.",
                code="COLOR_NO_ENCONTRADO",
            )
        variantes_uso = int(actual.get("variantes_asociadas", 0))
        if variantes_uso > 0:
            raise ConflictError(
                f"El color '{actual['nombre']}' está referenciado por {variantes_uso} variante(s) de producto. "
                "No puede eliminarse; puede desactivarlo para que no se asigne a nuevas variantes (CU08 A2).",
                code="ELEMENTO_CATALOGO_EN_USO",
            )
        CatalogosGlobalesRepositorio.eliminar_color(db, id_color)
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario_actual.id_usuario,
            usuario_nombre=usuario_actual.email,
            accion="ELIMINAR_COLOR_GLOBAL",
            tabla_modulo="plataforma.colores",
            direccion_ip=direccion_ip,
            severidad="WARN",
            payload_anterior={"id_color": id_color, "nombre": actual["nombre"]},
            db=db,
        )
        return EliminacionCatalogoOut(
            eliminado=True,
            mensaje=f"Color '{actual['nombre']}' eliminado correctamente.",
        )

