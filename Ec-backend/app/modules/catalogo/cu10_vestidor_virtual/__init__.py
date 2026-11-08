"""Módulo para el Caso de Uso CU10: Utilizar Vestidor Virtual (Dos Motores)."""

from modules.catalogo.cu10_vestidor_virtual.modelos import SesionVestidorORM
from modules.catalogo.cu10_vestidor_virtual.router import router

__all__ = ["SesionVestidorORM", "router"]

