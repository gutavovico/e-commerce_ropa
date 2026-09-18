# Plantillas y guía de redacción SDD

## Contenido
1. Cómo escribir una buena spec
2. `requirements.md` y notación EARS
3. `design.md`
4. `tasks.md` (tareas atómicas y oleadas)
5. Cambios sobre specs existentes: delta e Impact Report
6. Formato de prueba del proyecto (sección 2.5 del documento)
7. Checklist de revisión en cada puerta

Adapta la extensión a la proporcionalidad: en Nivel 1 usa solo el bloque mínimo de cada plantilla; en Nivel 3 completa todo, incluida la sección de riesgos.

---

## 1. Cómo escribir una buena spec

Cinco principios que evitan los fallos típicos de un agente:

1. **Visión de alto nivel primero.** Una frase de qué problema resuelve y para quién, antes de cualquier detalle. El agente decide mejor cuando entiende el porqué.
2. **Estructura profesional y consistente.** Mismas secciones en todas las specs; así se revisan rápido y el agente sabe dónde buscar.
3. **Modularidad.** Una spec por incremento; si necesita más de ~2 páginas, divídela. El contexto largo degrada la calidad.
4. **Autoverificación.** Cada requisito lleva un criterio comprobable y cada tarea un comando de verificación. "Es rápido" no es verificable; "responde en menos de 500 ms en el 95 % de las consultas con 10 000 productos" sí.
5. **Mantenimiento vivo.** La spec se actualiza cuando cambia el comportamiento (mediante delta); una spec desactualizada es peor que ninguna.

Evita dos extremos: la **infraespecificación** (el agente rellena huecos a su manera) y la **sobreespecificación** (pseudocódigo en el diseño; entonces se revisa el código dos veces). El diseño fija decisiones y restricciones; la implementación queda al agente.

## 2. `requirements.md` y notación EARS

```markdown
# CUxx · <nombre>            Nivel: 1|2|3     Estado: borrador|aprobado
Aprobado por: <nombre/rol>   Fecha: <aaaa-mm-dd>

## Propósito
<Una o dos frases: qué problema resuelve y para quién.>

## Actores y precondiciones
- Actor: <cliente | administrador | encargado_sucursal | cajero | proveedor | sistema>
- Precondiciones: <sesión iniciada, rol, datos existentes…>

## Requisitos (EARS)
- **AC-1** Cuando <evento>, el sistema deberá <respuesta verificable>.
- **AC-2** Si <condición no deseada>, entonces el sistema deberá <respuesta>.
- **AC-3** Mientras <estado>, el sistema deberá <respuesta>.

## Casos de error y borde
<Cada excepción del CU convertida en AC con su código HTTP.>

## Fuera de alcance
<Lo que NO se hace en este incremento.>

## Preguntas abiertas
<Lo que el humano debe decidir antes de aprobar. Vacío si no hay.>
```

**Patrones EARS** (Easy Approach to Requirements Syntax): reducen la ambigüedad porque cada requisito tiene una forma fija.

| Patrón | Forma | Ejemplo FashionStore |
|---|---|---|
| Ubicuo | El sistema deberá `<resp>`. | El sistema deberá almacenar contraseñas únicamente como hash. |
| Por evento | Cuando `<evento>`, el sistema deberá `<resp>`. | Cuando el cliente agrega una variante al carrito, el sistema deberá verificar que `cantidad_disponible` en la sucursal indicada sea ≥ a la cantidad solicitada. |
| Por estado | Mientras `<estado>`, el sistema deberá `<resp>`. | Mientras una reserva esté en estado `atendida`, el sistema deberá rechazar su cancelación. |
| Conducta no deseada | Si `<condición>`, entonces el sistema deberá `<resp>`. | Si la cantidad solicitada supera lo disponible, entonces el sistema deberá responder 409 e indicar el máximo permitido. |
| Opcional | Donde `<característica>`, el sistema deberá `<resp>`. | Donde el producto tenga `modelo_ar_url`, el sistema deberá permitir registrar sesiones de vestidor. |
| Complejo | Combinación de los anteriores. | Cuando el pago sea rechazado, si la venta está `pendiente`, entonces el sistema deberá pasarla a `anulada` y liberar el stock. |

Convierte cada **Excepción** de los casos de uso del documento en un AC de conducta no deseada: ahí están la mayoría de los errores que un agente omitiría.

## 3. `design.md`

```markdown
# Diseño · CUxx <nombre>
Requisitos: specs/<CU>-<slug>/requirements.md (aprobado)

## Enfoque
<Decisión principal en 3–5 líneas y alternativas descartadas con el porqué.>

## Contrato de API
| Método y ruta | Rol permitido | Entrada (schema) | Salida (schema) | Códigos |
Ejemplos JSON de entrada y salida (uno por caso relevante).

## Capas afectadas
Router: <archivo/función> · Service: <caso de uso> · ORM/Model: <tablas> · Integración: <si aplica>

## Datos y migraciones
Tablas/columnas/índices nuevos o modificados; ¿migración reversible?; impacto sobre triggers y vistas.

## Reglas, transacciones y concurrencia
Qué se ejecuta en una sola transacción; qué se bloquea y cómo; idempotencia.

## Errores
Excepciones de dominio → código HTTP → mensaje.

## No funcionales
Rendimiento, seguridad y autorización (rol y alcance por sucursal), auditoría/movimientos.

## Riesgos y decisiones pendientes   (Nivel 3: obligatorio)
<Referencia a los riesgos de references/dominio.md que aplican y la decisión tomada.>

## Estrategia de pruebas
AC → tipo de prueba (unitaria del service, integración de endpoint, concurrencia).
```

## 4. `tasks.md` (tareas atómicas y oleadas)

Una tarea es **atómica** si un agente puede completarla y un humano revisarla en una sola pasada: un cambio coherente, archivos acotados, verificación automática. Agrúpalas en **oleadas**: las tareas de una misma oleada no dependen entre sí (pueden ejecutarse en paralelo); una oleada empieza cuando termina la anterior.

```markdown
# Tareas · CUxx <nombre>

## Oleada 1 — Cimientos (sin dependencias)
- [ ] T1 Modelos ORM y migración de <tablas>
- [ ] T2 Schemas Pydantic de entrada/salida

## Oleada 2 — Negocio
- [ ] T3 Service <caso_de_uso> (depende de T1, T2)

## Oleada 3 — Exposición y pruebas
- [ ] T4 Router y dependencias de auth (depende de T3)
- [ ] T5 Tests de AC-1…AC-n (depende de T3, T4)
```

Cada tarea usa este **prompt estructurado**:

```markdown
### T3 · Service crear_reserva
- Contexto: specs/<CU>-<slug>/{requirements,design}.md; references/dominio.md §3
- Objetivo: <resultado en una frase>
- Archivos permitidos: app/modules/reservas/service.py, tests/reservas/test_service.py
- Criterios: AC-1, AC-3, AC-4
- Boundaries: no tocar esquema; no llamar a Stripe; sin cambios de contrato
- Verificación: `pytest tests/reservas -k service`
- Hecho cuando: los tests pasan y no hay archivos fuera de la lista
```

## 5. Cambios sobre specs existentes: delta e Impact Report

Cuando el cambio afecta a una spec o a código ya hecho, no reescribas todo: describe el **delta**.

```markdown
# Delta · CUxx <motivo del cambio>
## ADDED
- AC-7 …
## MODIFIED
- AC-2: antes «…» → ahora «…»  (motivo)
## REMOVED
- AC-5 (motivo)
```

Antes de implementarlo, redacta un **Impact Report** breve: endpoints y schemas afectados, tablas/triggers/vistas, consumidores (Angular, Flutter) que romperían, tests a actualizar y migración necesaria. Si hay impacto en consumidores, el cambio es *Ask First*.

## 6. Formato de prueba del proyecto (sección 2.5 del documento)

Cuando el usuario pida documentar pruebas para el entregable académico, usa esta estructura por prueba:

```
Prueba N: CUxx – <nombre>
Características de la API: Ruta · Descripción · Tipo (GET/POST/…)
Datos de entrada: <JSON>
Datos esperados: <JSON>
Resultado: <qué valida el sistema, qué tablas toca y el código HTTP>
```

## 7. Checklist de revisión en cada puerta

- **Requisitos**: ¿cada AC es verificable? ¿cada excepción del CU está cubierta? ¿hay fuera de alcance? ¿preguntas abiertas resueltas?
- **Diseño**: ¿respeta la constitución (capas, transacción única, servidor fuente de verdad)? ¿contrato compatible con Angular/Flutter? ¿riesgos de `dominio.md` decididos? ¿sin pseudocódigo?
- **Tareas**: ¿atómicas? ¿oleadas sin dependencias internas? ¿cada una con verificación y archivos permitidos?
- **Implementación**: ¿cada AC tiene test? ¿código revisado contra la spec? ¿DoD cumplida?
