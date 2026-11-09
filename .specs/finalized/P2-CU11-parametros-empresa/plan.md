# Plan — Parámetros de la empresa (P2-CU11)

## Orden
1. Backend: `plataforma/cu11_parametros_empresa/{esquemas,repositorio,servicio,router}.py`, registro del router en `main.py` y pruebas.
2. Web: `modules/plataforma/cu11_parametros_empresa/{modelos,servicios,paginas}`, ruta, tarjeta del panel y specs.
3. Cierre: `CHANGELOG.md`, spec permanente y nota en `CLAUDE.md` sobre la regla C7.

## Archivos
| Capa | Archivos |
| :--- | :--- |
| Backend | `app/modules/plataforma/cu11_parametros_empresa/` (nuevo) · `app/main.py` (una línea) |
| Pruebas | `tests/modules/plataforma/test_p2_cu11_parametros_empresa.py` (nuevo) · `tests/integracion/test_multitenant.py` |
| Web | `src/app/modules/plataforma/cu11_parametros_empresa/` (nuevo) · `app.routes.ts` · tarjeta en el panel `/admin` · `app.routes.spec.ts` |

## Riesgos
- **Choque con Tony:** `main.py`, `app.routes.ts` y el panel `/admin` son archivos de registro; solo se añaden líneas.
- **Fila ausente:** `INSERT … ON CONFLICT DO NOTHING` dentro de la transacción del caso de uso; con RLS, el `id_tenant` lo pone el valor por defecto del contexto.
