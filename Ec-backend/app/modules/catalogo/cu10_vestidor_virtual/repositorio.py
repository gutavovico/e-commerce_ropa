"""Repositorio de base de datos para CU10: Vestidor Virtual."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from modules.catalogo.cu10_vestidor_virtual.modelos import SesionVestidorORM
from modules.catalogo.modelos import ProductoORM


class VestidorRepositorio:
    """Acceso a datos para sesiones de vestidor virtual y validación de prendas."""

    def __init__(self, db: Session):
        self.db = db

    def obtener_producto(self, id_producto: int) -> Optional[ProductoORM]:
        """Recupera un producto por su clave primaria."""
        stmt = select(ProductoORM).where(ProductoORM.id_producto == id_producto)
        return self.db.execute(stmt).scalar_one_or_none()

    def crear_sesion(
        self,
        id_cliente: int,
        id_producto: int,
        dispositivo: Optional[str] = None,
        motor: str = "local",
        duracion_segundos: Optional[int] = None,
        resultado_url: Optional[str] = None,
        genero_interes: bool = False,
    ) -> SesionVestidorORM:
        """Inserta un nuevo registro de interacción en sesiones_vestidor_virtual."""
        nueva_sesion = SesionVestidorORM(
            id_cliente=id_cliente,
            id_producto=id_producto,
            dispositivo=dispositivo,
            motor=motor,
            duracion_segundos=duracion_segundos,
            resultado_url=resultado_url,
            genero_interes=genero_interes,
        )
        self.db.add(nueva_sesion)
        self.db.commit()
        self.db.refresh(nueva_sesion)
        return nueva_sesion

    def obtener_sesion(self, id_sesion_ar: int) -> Optional[SesionVestidorORM]:
        """Recupera una sesión de vestidor virtual por su ID."""
        stmt = select(SesionVestidorORM).where(
            SesionVestidorORM.id_sesion_ar == id_sesion_ar
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def actualizar_sesion(
        self,
        sesion: SesionVestidorORM,
        resultado_url: Optional[str] = None,
        genero_interes: Optional[bool] = None,
    ) -> SesionVestidorORM:
        """Actualiza los campos de captura fotográfica o interés comercial."""
        if resultado_url is not None:
            sesion.resultado_url = resultado_url
        if genero_interes is not None:
            sesion.genero_interes = genero_interes

        self.db.commit()
        self.db.refresh(sesion)
        return sesion

