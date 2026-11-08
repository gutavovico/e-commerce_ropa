"""Regularización única (CU31-CU32, decisión D3): ficha en `fashionstore.empleados` para el personal
existente que no la tiene.

`ventas.id_cajero` referencia `empleados`; hasta este cambio CU20 no creaba la ficha al dar de alta a
un cajero o encargado. Desde ahora lo hace `asegurar_ficha_empleado`; este script cubre a los usuarios
creados antes. Es idempotente (`ON CONFLICT DO NOTHING`).

Uso (desde Ec-backend/):  ./.venv/Scripts/python.exe scripts/regularizar_fichas_empleado.py [--aplicar]
Sin --aplicar solo lista lo que haría.
"""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "app"))
sys.path.insert(0, str(RAIZ))

from sqlalchemy import text  # noqa: E402

from core.database import SessionLocal  # noqa: E402
from modules.autenticacion_seguridad.cu20_usuarios_roles.servicio import (  # noqa: E402
    CARGOS_PERSONAL,
    asegurar_ficha_empleado,
)


def main(aplicar: bool) -> None:
    db = SessionLocal()
    try:
        pendientes = db.execute(
            text(
                "SELECT u.id_usuario, u.rol::text FROM fashionstore.usuarios u "
                "LEFT JOIN fashionstore.empleados e ON e.id_empleado = u.id_usuario "
                "WHERE e.id_empleado IS NULL AND u.rol::text = ANY(:roles) ORDER BY u.id_usuario"
            ),
            {"roles": list(CARGOS_PERSONAL)},
        ).all()

        if not pendientes:
            print("Todo el personal tiene ficha de empleado. Nada que hacer.")
            return

        for id_usuario, rol in pendientes:
            print(f"{'Creando' if aplicar else 'Faltaría'} ficha EMP-{id_usuario} ({rol})")
            if aplicar:
                asegurar_ficha_empleado(db, id_usuario, rol)

        if aplicar:
            db.commit()
            print(f"Hecho: {len(pendientes)} ficha(s) creada(s).")
        else:
            print("Simulación: añade --aplicar para escribir.")
    finally:
        db.close()


if __name__ == "__main__":
    main("--aplicar" in sys.argv)
