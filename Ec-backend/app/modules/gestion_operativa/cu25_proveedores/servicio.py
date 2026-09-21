"""Servicio de logica de negocio transaccional para CU25: Gestionar Proveedores."""

from datetime import datetime, timezone
import math
from typing import Optional
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from modules.autenticacion_seguridad.modelos import UsuarioORM
from .errores import ProveedorDuplicadoError, ProveedorNoEncontradoError
from .esquemas import (
    ListaPaginadaProveedoresOut,
    ProveedorActualizarIn,
    ProveedorCrearIn,
    ProveedorFiltrosIn,
    ProveedorItemOut,
)
from .modelos import ProveedorORM


class ServicioGestionProveedores:
    """Logica de negocio transaccional para la administracion de proveedores."""

    def _to_proveedor_item_out(self, r: ProveedorORM) -> ProveedorItemOut:
        """Serializacion defensiva tolerante a valores nulos o campos incompletos en base de datos."""
        return ProveedorItemOut(
            id_proveedor=r.id_proveedor,
            id_usuario=r.id_usuario,
            razon_social=r.razon_social or "Sin razon social",
            nit_rut=r.nit_rut or "SIN-NIT",
            contacto_nombre=r.contacto_nombre or "Contacto no registrado",
            telefono=r.telefono or "No registrado",
            email=str(r.email) if r.email else "sin-correo@fashionstore.com",
            direccion=r.direccion or "Direccion no registrada",
            ciudad=r.ciudad or "La Paz",
            rubro=r.rubro or "Confeccion Textil",
            estado_activo=bool(r.estado_activo) if r.estado_activo is not None else True,
            creado_en=r.creado_en or datetime.now(timezone.utc),
            actualizado_en=r.actualizado_en or r.creado_en or datetime.now(timezone.utc),
        )

    def listar_proveedores(
        self, db: Session, filtros: ProveedorFiltrosIn, usuario_sesion: UsuarioORM
    ) -> ListaPaginadaProveedoresOut:
        condiciones = []

        if filtros.estado_activo is not None:
            condiciones.append(ProveedorORM.estado_activo == filtros.estado_activo)

        if filtros.rubro and filtros.rubro.strip():
            condiciones.append(ProveedorORM.rubro.ilike(f"%{filtros.rubro.strip()}%"))

        if filtros.q and filtros.q.strip():
            termino = f"%{filtros.q.strip()}%"
            condiciones.append(
                or_(
                    ProveedorORM.razon_social.ilike(termino),
                    ProveedorORM.nit_rut.ilike(termino),
                    ProveedorORM.contacto_nombre.ilike(termino),
                )
            )

        stmt = select(ProveedorORM)
        if condiciones:
            stmt = stmt.where(and_(*condiciones))

        # Conteo total
        stmt_count = select(func.count(ProveedorORM.id_proveedor))
        if condiciones:
            stmt_count = stmt_count.where(and_(*condiciones))
        total = db.scalar(stmt_count) or 0

        # Paginacion y ordenamiento descendente
        offset = (filtros.pagina - 1) * filtros.limite
        stmt = stmt.order_by(ProveedorORM.id_proveedor.desc()).offset(offset).limit(filtros.limite)
        registros = db.scalars(stmt).all()

        items = [self._to_proveedor_item_out(r) for r in registros]
        total_paginas = math.ceil(total / filtros.limite) if total > 0 else 1

        return ListaPaginadaProveedoresOut(
            items=items,
            total=total,
            pagina=filtros.pagina,
            limite=filtros.limite,
            total_paginas=total_paginas,
        )

    def obtener_proveedor_por_id(
        self, db: Session, id_proveedor: int, usuario_sesion: UsuarioORM
    ) -> ProveedorItemOut:
        prov = db.get(ProveedorORM, id_proveedor)
        if not prov:
            raise ProveedorNoEncontradoError(id_proveedor)
        return self._to_proveedor_item_out(prov)

    def crear_proveedor(
        self, db: Session, payload: ProveedorCrearIn, usuario_sesion: UsuarioORM
    ) -> ProveedorItemOut:
        # 1. Validar no duplicidad de nit_rut
        duplicado_nit = db.scalar(
            select(ProveedorORM).where(ProveedorORM.nit_rut.ilike(payload.nit_rut.strip()))
        )
        if duplicado_nit:
            raise ProveedorDuplicadoError("NIT/RUT", payload.nit_rut)

        # 2. Validar no duplicidad de razon_social
        duplicado_rs = db.scalar(
            select(ProveedorORM).where(ProveedorORM.razon_social.ilike(payload.razon_social.strip()))
        )
        if duplicado_rs:
            raise ProveedorDuplicadoError("Razon Social", payload.razon_social)

        # 3. Persistir entidad
        ahora = datetime.now(timezone.utc)
        nuevo_prov = ProveedorORM(
            razon_social=payload.razon_social.strip(),
            nit_rut=payload.nit_rut.strip(),
            contacto_nombre=payload.contacto_nombre.strip(),
            telefono=payload.telefono.strip(),
            email=str(payload.email).strip().lower(),
            direccion=payload.direccion.strip(),
            ciudad=payload.ciudad.strip(),
            rubro=payload.rubro.strip(),
            estado_activo=True,
            creado_en=ahora,
            actualizado_en=ahora,
        )
        db.add(nuevo_prov)
        db.commit()
        db.refresh(nuevo_prov)

        return self._to_proveedor_item_out(nuevo_prov)

    def actualizar_proveedor(
        self, db: Session, id_proveedor: int, payload: ProveedorActualizarIn, usuario_sesion: UsuarioORM
    ) -> ProveedorItemOut:
        prov = db.get(ProveedorORM, id_proveedor)
        if not prov:
            raise ProveedorNoEncontradoError(id_proveedor)

        # Validar no duplicidad si nit_rut cambia
        if payload.nit_rut and payload.nit_rut.strip().lower() != prov.nit_rut.lower():
            colision_nit = db.scalar(
                select(ProveedorORM).where(
                    and_(
                        ProveedorORM.nit_rut.ilike(payload.nit_rut.strip()),
                        ProveedorORM.id_proveedor != id_proveedor,
                    )
                )
            )
            if colision_nit:
                raise ProveedorDuplicadoError("NIT/RUT", payload.nit_rut)
            prov.nit_rut = payload.nit_rut.strip()

        # Validar no duplicidad si razon_social cambia
        if payload.razon_social and payload.razon_social.strip().lower() != prov.razon_social.lower():
            colision_rs = db.scalar(
                select(ProveedorORM).where(
                    and_(
                        ProveedorORM.razon_social.ilike(payload.razon_social.strip()),
                        ProveedorORM.id_proveedor != id_proveedor,
                    )
                )
            )
            if colision_rs:
                raise ProveedorDuplicadoError("Razon Social", payload.razon_social)
            prov.razon_social = payload.razon_social.strip()

        if payload.contacto_nombre:
            prov.contacto_nombre = payload.contacto_nombre.strip()
        if payload.telefono:
            prov.telefono = payload.telefono.strip()
        if payload.email:
            prov.email = str(payload.email).strip().lower()
        if payload.direccion:
            prov.direccion = payload.direccion.strip()
        if payload.ciudad:
            prov.ciudad = payload.ciudad.strip()
        if payload.rubro:
            prov.rubro = payload.rubro.strip()

        prov.actualizado_en = datetime.now(timezone.utc)
        db.commit()
        db.refresh(prov)

        return self._to_proveedor_item_out(prov)

    def cambiar_estado_proveedor(
        self, db: Session, id_proveedor: int, estado_activo: bool, usuario_sesion: UsuarioORM
    ) -> ProveedorItemOut:
        prov = db.get(ProveedorORM, id_proveedor)
        if not prov:
            raise ProveedorNoEncontradoError(id_proveedor)

        prov.estado_activo = estado_activo
        prov.actualizado_en = datetime.now(timezone.utc)
        db.commit()
        db.refresh(prov)

        return self._to_proveedor_item_out(prov)


servicio_gestion_proveedores = ServicioGestionProveedores()
