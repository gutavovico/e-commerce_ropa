"""Alta o rotación fuera de banda de la cuenta `super_administrador` (P2-CU05, decisión S2).

Por seguridad en un repositorio público, ninguna migración de Alembic debe contener
contraseñas ni hashes de `super_administrador`. Este script crea o rota la credencial
leyendo el correo y la contraseña exclusivamente de variables de entorno
(`SUPERADMIN_EMAIL`, `SUPERADMIN_PASSWORD`) o de entrada interactiva oculta (`getpass`),
y bloquea permanentemente cualquier contraseña expuesta en el historial de Git.

Uso (desde Ec-backend/):
    ./.venv/Scripts/python.exe scripts/crear_superadmin.py [--email correo@dominio.com] [--aplicar]
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "app"))
sys.path.insert(0, str(RAIZ))

from sqlalchemy import text  # noqa: E402

from core.database import SessionLocal  # noqa: E402
from core.security import hash_password  # noqa: E402
from core.tenant import fijar_contexto  # noqa: E402
from modules.plataforma.dependencias import validar_contrasena_superadmin_segura  # noqa: E402


def obtener_credenciales(email_arg: str | None) -> tuple[str, str]:
    """Obtiene correo y contraseña de variables de entorno o prompt interactivo."""
    email = (email_arg or os.getenv("SUPERADMIN_EMAIL") or "").strip().lower()
    if not email:
        email = input("Correo del super_administrador: ").strip().lower()
    if not email or "@" not in email:
        raise ValueError("Debe proporcionar un correo electrónico válido para el super_administrador.")

    password = os.getenv("SUPERADMIN_PASSWORD") or ""
    if not password:
        password = getpass.getpass("Nueva contraseña del super_administrador (mín. 12 caracteres): ")
        confirmacion = getpass.getpass("Confirmar contraseña: ")
        if password != confirmacion:
            raise ValueError("Las contraseñas ingresadas no coinciden.")

    validar_contrasena_superadmin_segura(password)
    return email, password


def aprovisionar_superadmin(email: str, password: str, aplicar: bool) -> None:
    """Crea o actualiza de forma idempotente la cuenta `super_administrador` (`id_tenant IS NULL`)."""
    validar_contrasena_superadmin_segura(password)
    nuevo_hash = hash_password(password)

    db = SessionLocal()
    try:
        fijar_contexto(db, None, id_usuario=None, plataforma=True)
        existente = db.execute(
            text(
                "SELECT id_usuario, rol::text, id_tenant "
                "FROM fashionstore.usuarios "
                "WHERE lower(email::text) = lower(:email)"
            ),
            {"email": email},
        ).first()

        if existente is not None and existente[1] != "super_administrador":
            raise RuntimeError(
                f"El correo '{email}' ya pertenece a una cuenta con rol '{existente[1]}' "
                "y no puede convertirse en super_administrador."
            )

        if not aplicar:
            accion = "Actualizaría contraseña de" if existente else "Crearía cuenta"
            print(f"[Simulación] {accion} super_administrador '{email}'. Añade --aplicar para guardar.")
            return

        if existente is not None:
            db.execute(
                text(
                    "UPDATE fashionstore.usuarios "
                    "SET password_hash = :password_hash, activo = true, id_tenant = NULL, id_sucursal = NULL "
                    "WHERE id_usuario = :id_usuario"
                ),
                {"password_hash": nuevo_hash, "id_usuario": int(existente[0])},
            )
            db.commit()
            print(f"Contraseña de super_administrador actualizada para '{email}' (id_usuario={existente[0]}).")
        else:
            fila = db.execute(
                text(
                    "INSERT INTO fashionstore.usuarios "
                    "(email, password_hash, nombres, apellidos, rol, id_tenant, id_sucursal, activo) "
                    "VALUES (:email, :password_hash, 'Super', 'Administrador', "
                    "'super_administrador'::fashionstore.rol_usuario, NULL, NULL, true) "
                    "RETURNING id_usuario"
                ),
                {"email": email, "password_hash": nuevo_hash},
            ).first()
            db.commit()
            id_creado = fila[0] if fila else None
            print(f"Cuenta super_administrador creada para '{email}' (id_usuario={id_creado}).")
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Crea o rota fuera de banda la cuenta de super_administrador."
    )
    parser.add_argument("--email", help="Correo del super_administrador (o variable SUPERADMIN_EMAIL).")
    parser.add_argument(
        "--aplicar",
        action="store_true",
        help="Ejecuta el INSERT/UPDATE en la base de datos (sin este flag solo simula).",
    )
    args = parser.parse_args()

    try:
        email, password = obtener_credenciales(args.email)
        aprovisionar_superadmin(email=email, password=password, aplicar=args.aplicar)
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

