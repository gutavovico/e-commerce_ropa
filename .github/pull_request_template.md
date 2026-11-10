## Qué cambia

<!-- Caso de uso y resumen en dos o tres líneas. -->

**Spec:** `.specs/changes/<id>/` (aprobada el AAAA-MM-DD)

## Bloques

- [ ] Backend
- [ ] Web
- [ ] Móvil

## Antes de pedir revisión

- [ ] La rama está al día con `main` (sin commits de `main` pendientes de integrar).
- [ ] Las tres suites pasan en local (`pytest`, `ng test`, `flutter test`) y `dart analyze` no da incidencias.
- [ ] No hay contraseñas, hashes ni claves en el código, en comentarios ni en migraciones.
- [ ] Si corrige un defecto, tiene su entrada en `CHANGELOG.md`, sin número (el número se pone al fusionar).

## Migraciones (borrar si no hay)

- [ ] Número avisado al resto del equipo antes de crearla; `down_revision` = la última de `main`.
- [ ] Ensayada en `pruebas-multitenant` con `upgrade → downgrade → upgrade`.
- [ ] Rama de respaldo de producción creada justo antes de aplicarla (`respaldo-pre-NNNN`, RNF18).
- [ ] **Aplicada en producción antes de fusionar** (`alembic current` = esta migración). La aplica: @gutavovico

## Cómo probarlo

<!-- Pasos en la web o en el móvil para comprobar el cambio. -->
