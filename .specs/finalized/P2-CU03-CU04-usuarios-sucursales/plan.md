# Plan — Usuarios y sucursales por empresa (P2-CU03 · P2-CU04)

## Orden
1. **B1 primero, solo:** es una fuga de datos en producción. Se puede publicar sola si el usuario lo prefiere (con su prueba de integración), antes del resto del bloque.
2. Backend:
   - `SucursalesEmpleadoServicio` (B3, B4);
   - `cu20` (B2, B3, B8 al reactivar, B9);
   - `cu21` (B6, B7, B9);
   - `cu12` (`uso` y el bloqueo de B8);
   - los 7 sitios de RN07;
   - `GET /mis-sucursales`.
3. Web: usuarios → sucursales → caja.
4. Cierre: `SI2-Parcial2.md`, `CHANGELOG.md`, spec permanente y aviso a Tony (§6 de la spec).

## Archivos
| Capa | Archivos |
| :--- | :--- |
| Backend | `autenticacion_seguridad/cu20_usuarios_roles/{esquemas,servicio,router,errores}.py` · `gestion_operativa/cu21_sucursales_ciudades/{servicio,router,esquemas}.py` · `plataforma/servicio_sucursales_empleado.py` (nuevo) · `plataforma/cu12_validar_suscripcion/{servicio,repositorio}.py` · los 7 servicios de §0.2 |
| Pruebas | `tests/modules/autenticacion_seguridad/…cu20…`, `tests/modules/gestion_operativa/…cu21…`, pruebas de los 7 sitios, `tests/integracion/test_multitenant.py` |
| Web | `cu20_usuarios_roles/{modelos,servicios,paginas}` · `cu21_sucursales_ciudades/{modelos,servicios,paginas}` · caja `cu31_cu32_punto_venta` |

## Riesgos
- **RN07 en 7 sitios:** cada sitio conserva su código de error, para no romper la web ni el móvil. Se prueba sitio por sitio.
- **Bloqueo de B8:** si un servicio hace `commit` antes de insertar o activar, el bloqueo se libera antes de tiempo. Se revisa que el `commit` ocurra después.
- **Retirar las rutas de ciudades** deja sin alta de ciudades hasta CU08. Las ciudades actuales bastan; si hace falta una, se añade con un script.
- **Sin migración (B10).** Si apareciera una, se coordina el número con Tony y se aplica a producción antes del push.
