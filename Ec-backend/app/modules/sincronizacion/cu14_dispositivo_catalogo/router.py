"""Router de P2-CU14 · Descargar catálogo y registrar dispositivo. Solo HTTP."""

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_roles
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.sincronizacion.cu14_dispositivo_catalogo.esquemas import (
    CatalogoLocalOut,
    DispositivoIn,
    DispositivoOut,
    DispositivoTokenPushIn,
    DispositivoTokenPushOut,
    ProbarPushOut,
)
from modules.sincronizacion.cu14_dispositivo_catalogo.servicio import (
    CatalogoSinConexionServicio,
    DispositivoServicio,
)

router = APIRouter(prefix="/sin-conexion", tags=["P2-CU14 Catálogo sin conexión"])

_cliente = require_roles(["cliente"])


@router.post(
    "/dispositivos",
    response_model=DispositivoOut,
    summary="Registrar (o reutilizar) el dispositivo del cliente",
    responses={201: {"description": "Dispositivo nuevo"}, 200: {"description": "Ya estaba registrado (A1)"}},
)
def registrar_dispositivo(
    datos: DispositivoIn,
    response: Response,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(_cliente),
) -> DispositivoOut:
    salida, creado = DispositivoServicio.registrar(db, usuario, datos)
    response.status_code = status.HTTP_201_CREATED if creado else status.HTTP_200_OK
    return salida


@router.post(
    "/dispositivos/token-push",
    response_model=DispositivoTokenPushOut,
    summary="Asociar o renovar el token FCM de un dispositivo",
)
def registrar_token_push(
    datos: DispositivoTokenPushIn,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(_cliente),
) -> DispositivoTokenPushOut:
    return DispositivoServicio.actualizar_token_push(db, usuario, datos)


@router.post(
    "/dispositivos/probar-push",
    response_model=ProbarPushOut,
    summary="Enviar notificación push de verificación al cliente autenticado",
)
def probar_notificacion_push(
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(_cliente),
) -> ProbarPushOut:
    from integrations.fcm_service import notificar_cliente
    from modules.sincronizacion.comun import exigir_cliente

    id_cliente = exigir_cliente(db, usuario)
    enviados = notificar_cliente(
        db,
        id_cliente=id_cliente,
        titulo="Notificaciones activadas",
        cuerpo="Recibirás avisos de tus reservas, pedidos y asistente de estilo.",
        datos={"pantalla": "reservas"},
    )
    db.commit()
    return ProbarPushOut(
        ok=True,
        dispositivos_notificados=enviados,
        mensaje=(
            "Notificación de prueba despachada."
            if enviados > 0
            else "Sin dispositivos con token push registrado en esta tienda."
        ),
    )


@router.get("/catalogo", response_model=CatalogoLocalOut, summary="Paquete de catálogo para usar sin conexión")
def descargar_catalogo(
    dispositivo: uuid.UUID = Query(..., description="Identificador del dispositivo"),
    modo: Literal["completo", "indispensable"] = Query("completo"),
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(_cliente),
) -> CatalogoLocalOut:
    return CatalogoSinConexionServicio.descargar(db, usuario, dispositivo, modo)
