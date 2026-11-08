# Plan — Fundación Multitenant (P2-CU13 · P2-CU12)

## Orden y dependencias

```
Preparación (tú) ──► 0012 tablas nuevas ──► 0013 id_tenant ──► 0014 RLS + vistas + grants
                                                                   │
                     core/tenant.py + deps + login + JWT ◄─────────┘
                                   │
                     modules/plataforma (P2-CU12) ──► conexión a operaciones (F17)
                                   │
                     Pruebas de aislamiento en la rama de Neon ──► ensayo completo ──► producción (con tu OK)
```

## Preparación (la haces tú en la consola de Neon; nada de esto pasa por el chat)
1. Rama de respaldo `respaldo-pre-0012` desde la rama principal.
2. Rama `pruebas-multitenant` desde la principal. Su URL de conexión (como dueño) va a `Ec-backend/.env` como `DATABASE_URL_PRUEBAS`.
3. Rol `fashionstore_app` con contraseña. Lo crea Neon en *Roles*, y se crea en todas las ramas.
4. En `.env`: `DATABASE_URL_MIGRACIONES` = la URL actual (dueño) y, más adelante, `DATABASE_URL` = la del rol `fashionstore_app`.

## Migraciones (Alembic, `down_revision` encadenado desde `0011`)
- **`0012_tenants_planes`:** tablas de §A.1, `citext` (ya instalado), datos iniciales. `downgrade` las borra.
- **`0013_id_tenant`:**
  1. Añade `id_tenant` nulo.
  2. `UPDATE … SET id_tenant = 1` en las tablas de negocio, y en `usuarios` solo para los empleados.
  3. `SET NOT NULL` y `DEFAULT` del contexto.
  4. Índices, `UNIQUE (id_tenant, pk)` y claves únicas por empresa.
  5. Sustituye las FK entre tablas de empresa por FK compuestas, y las FK hacia `clientes` por FK hacia `cliente_tenant`.

  El `downgrade` restaura las FK y claves únicas originales y borra las columnas.
- **`0014_rls`:** `ENABLE ROW LEVEL SECURITY` y políticas, `security_invoker` en las vistas, `ALTER TYPE rol_usuario ADD VALUE 'super_administrador'` y `GRANT` al rol de la aplicación si existe. El `downgrade` lo revierte, salvo el valor del enum, que se deja (PostgreSQL no lo permite quitar).
- `alembic/env.py`: usa `DATABASE_URL_MIGRACIONES` si existe y, si no, `DATABASE_URL`. `render.yaml` declara la variable nueva con `sync: false`.

## Código
1. `core/config.py`: `TENANT_POR_DEFECTO`, `DATABASE_URL_MIGRACIONES`, `DATABASE_URL_PRUEBAS`.
2. `core/tenant.py`: contexto, listener `after_begin` y dependencia global registrada en `main.py`.
3. `core/deps.py` y `core/security.py`: claim `id_tenant`, orden de resolución (F4) y errores nuevos en `core/errors.py`.
4. Login de CU02 (actual): `codigo_empresa` opcional, búsqueda por empresa y `tenant` en la respuesta.
5. Modelos: `id_tenant` con `FetchedValue()` en cada ORM de §A.2; ORM nuevos en `modules/plataforma/modelos.py`.
6. `modules/plataforma/cu12_validar_suscripcion/{servicio,repositorio,dependencias}.py`.
7. Conexión de P2-CU12 a: alta y activación de sucursales, alta de empleados, reservas, checkout, venta en caja y reportes por voz.
8. Webhook y `crear_intento`: metadatos y modo plataforma (F6).

## Pruebas
- **Unitarias (simuladas):** resolución de contexto, errores de P2-CU12 y login con y sin código.
- **Integración contra la rama de Neon** (`tests/integracion/test_multitenant.py`, se saltan sin `DATABASE_URL_PRUEBAS`):
  - una segunda empresa `pruebas-b` creada y borrada en la propia prueba;
  - los escenarios de §A.5 con conexiones del rol `fashionstore_app`.
- La suite completa actual tiene que seguir en verde.
- **Prueba de humo:** todos los endpoints GET con el rol nuevo devuelven lo mismo que antes para FASHION STORE.

## Delta a la constitución (F20)
`.agents/skills/fashionstore-backend-sdd/SKILL.md`: principio 0 por empresa, principio 6 con `super_administrador` y sucursales autorizadas, y una nota sobre el contexto de empresa obligatorio. `CLAUDE.md`: una sección «Multitenancy» con F2, F3, F5 y la regla de que una tabla nueva de negocio debe llevar `id_tenant`, RLS y FK compuestas.
