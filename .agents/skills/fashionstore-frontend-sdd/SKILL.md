---
name: fashionstore-frontend-sdd
description: Desarrollo del FRONTEND WEB de FashionStore (e-commerce omnicanal de ropa de lujo) con Angular 19+ (Standalone Components, Signals, TypeScript estricto y Tailwind CSS), guiado por Spec-Driven Development (SDD). Úsala SIEMPRE que se pida crear, modificar, revisar, depurar, maquetar o probar componentes, páginas, servicios HTTP, interceptores, guards, estado reactivo o formularios en Ec-frontend/.
---

# FashionStore · Frontend Web con SDD (Angular 19+)

Esta skill guía el desarrollo del cliente web de **FashionStore** bajo la disciplina de **Spec-Driven Development (SDD)**: ningún componente o servicio se programa sin haber validado previamente el contrato de API del backend y los requerimientos aprobados en `.specs/`.

El frontend web es el consumidor principal del contrato de API expuesto por FastAPI en `/api/v1/...`. Opera como una galería de moda digital de alta costura, aplicando rigurosamente los tokens de diseño matemáticos de **FASHION STORE**.

---

## 1. Alcance y Rol del Agente

* **Entorno:** Directorio `Ec-frontend/` (Angular 19+, Node.js, TypeScript 5.5+ estricto, Tailwind CSS).
* **Rol:** Principal Frontend Architect & Angular Specialist.
* **Consumo de Contratos:** Los endpoints, payloads y códigos de error provienen del documento [SI2-Parcial1.md](file:///c:/Users/tonys/OneDrive/Documentos/contenido/SI2/Parcial1-Ecommerce/SI2-Parcial1.md) y de la constitución del backend en [.agents/skills/fashionstore-backend-sdd/SKILL.md](file:///c:/Users/tonys/OneDrive/Documentos/contenido/SI2/Parcial1-Ecommerce/.agents/skills/fashionstore-backend-sdd/SKILL.md).
* **Documentación Técnica de Referencia:**
  * [references/arquitectura-front.md](file:///c:/Users/tonys/OneDrive/Documentos/contenido/SI2/Parcial1-Ecommerce/.agents/skills/fashionstore-frontend-sdd/references/arquitectura-front.md) → Estructura de carpetas modular por features, servicios HTTP, interceptores JWT y guards de roles.
  * [references/fashionstore-tokens.md](file:///c:/Users/tonys/OneDrive/Documentos/contenido/SI2/Parcial1-Ecommerce/.agents/skills/fashionstore-frontend-sdd/references/fashionstore-tokens.md) → Diccionario de tokens, colores Slate/Camel/Neutros, tipografía Outfit, cadencia Base-2 y elevaciones.

---

## 2. Flujo SDD Obligatorio en Frontend

Antes de crear o modificar cualquier archivo en `Ec-frontend/`, debes ejecutar secuencialmente las siguientes fases:

```
┌──────────────────────────────────────────────────────────┐
│ 1. Inspeccionar Especificación y Contrato de API        │
│    Leer .specs/changes/<CU>/spec.md o finalized/         │
├──────────────────────────────────────────────────────────┤
│ 2. Validar Contrato de Integración Backend              │
│    Verificar DTOs, query params y códigos HTTP           │
├──────────────────────────────────────────────────────────┤
│ 3. Actualizar Plan y Tareas                             │
│    Reflejar oleadas en plan.md y tasks.md                │
├──────────────────────────────────────────────────────────┤
│ 4. Implementar bajo Standalone + Signals + Tokens       │
│    Respetar OnPush, inject(), tipado y Base-2            │
├──────────────────────────────────────────────────────────┤
│ 5. Registrar Checkpoint                                 │
│    Actualizar .specs/changes/<CU>/checkpoint.md          │
└──────────────────────────────────────────────────────────┘
```

1. **Lectura de Spec:** Verifica el caso de uso (`CU01` a `CU35`). Si existe `.specs/changes/<CU>/spec.md`, básate en él; si no, consulta la spec consolidada en `.specs/finalized/<CU>/spec.md`.
2. **Validación del Contrato:** Comprueba que las rutas `/api/v1/...`, parámetros y modelos Pydantic del backend coincidan exactamente con las interfaces TypeScript del frontend.
3. **Plan y Tareas:** Mantén al día `plan.md` y `tasks.md` antes de implementar componentes complejos (checkout, catálogo con variantes, administración).
4. **Implementación por Oleadas:**
   * *Oleada 1:* Modelos e interfaces TypeScript en `core/models/` o `modules/<paquete_dominio>/<cu>/modelos/`.
   * *Oleada 2:* Servicios HTTP tipados con `HttpClient` y `inject()`.
   * *Oleada 3:* Componentes UI Standalone con Signals y control flow (`@if`, `@for`).
   * *Oleada 4:* Pruebas unitarias con Jasmine/Karma (`.spec.ts`).
5. **Cierre de Sesión:** Deja documentado el estado en `checkpoint.md` antes de transferir el control al usuario.

---

## 3. Principios de Código Angular (Constitución Frontend)

### 3.1 Componentes Standalone Exclusivos
* Prohibido crear o utilizar `NgModule`. Todos los componentes, directivas y pipes deben declarar `standalone: true`.
* Todo componente debe configurar explícitamente `changeDetection: ChangeDetectionStrategy.OnPush`.

### 3.2 Reactividad con Angular Signals
* El estado local del componente se gestiona con `signal()`, `computed()` y `effect()`.
* Prohibido almacenar estado síncrono mutable en propiedades públicas desnudas.
* Para flujos asíncronos derivados de `HttpClient`, convertir a Signal utilizando `toSignal()` del paquete `@angular/core/rxjs-interop` o consumir con control flow reactivo.

### 3.3 Inyección de Dependencias Moderna
* Prohibida la inyección tradicional en constructor (`constructor(private service: Service)`).
* Usar siempre la función `inject()`:
  ```typescript
  export class ProductListComponent {
    private readonly catalogService = inject(CatalogService);
    private readonly router = inject(Router);
    protected readonly products = toSignal(this.catalogService.searchProducts(), { initialValue: [] });
  }
  ```

### 3.4 Formularios Reactivos Tipados (Strict Typed Forms)
* Todos los formularios de autenticación, checkout, filtrado y administración deben construirse con `NonNullableFormBuilder` o `FormGroup<T>` fuertemente tipado:
  ```typescript
  interface LoginForm {
    email: FormControl<string>;
    password: FormControl<string>;
  }
  ```
* Las validaciones deben mapear los límites del modelo del backend (longitud, email válido, números positivos).

### 3.5 Control Flow Moderno
* Prohibido el uso de directivas estructurales legadas (`*ngIf`, `*ngFor`, `*ngSwitch`).
* Usar la sintaxis integrada de Angular:
  ```html
  @if (isLoading()) {
    <div class="p-space-4 text-outline">Cargando colección...</div>
  } @else {
    @for (item of products(); track item.id_producto) {
      <app-product-card [product]="item" />
    } @empty {
      <p class="font-body-md text-on-surface-variant">No se encontraron prendas.</p>
    }
  }
  ```

---

## 4. Restricciones Estrictas de Estilo y Maquetación

### 4.1 Prohibición Absoluta de Valores Arbitrarios (Hard Constraint)
* **PROHIBIDO** el uso de clases arbitrarias de Tailwind para espaciados y dimensiones:
  ❌ `p-[10px]`, `m-[15px]`, `h-[35px]`, `gap-[18px]`, `top-[14px]`.
* **OBLIGATORIO** usar exclusivamente los tokens Base-2 de FASHION STORE:
  ✔ `space-1` (2px), `space-2` (4px), `space-3` (8px), `space-4` (16px), `space-5` (32px), `space-6` (64px), `space-7` (128px).

### 4.2 Nomenclatura Normativa
* Todo comentario, texto, título y metadata debe utilizar el nombre oficial: **FASHION STORE** (nunca "AURA STUDIO").
* Paleta cromática: Utilizar las clases semánticas (`bg-surface`, `text-primary`, `bg-surface-container-lowest`, `border-outline-variant`). Para acentos de lujo usar la escala `camel` y para profundidad neutra la escala `slate`.

---

## 5. Definition of Ready (DoR) para Frontend
Una tarea frontend está lista para implementarse solo si:
1. El caso de uso (`CUxx`) está identificado en `SI2-Parcial1.md`.
2. Los contratos de API `/api/v1/...` existen en el backend o cuentan con especificación aprobada en `.specs/`.
3. Se han definido los estados de interfaz: reposo, carga (`skeleton`), error y vacío (`empty state`).
4. Se conocen los permisos requeridos (roles: `cliente`, `administrador`, `encargado_sucursal`, `cajero`).

## 6. Definition of Done (DoD) para Frontend
Una tarea frontend se considera terminada únicamente cuando:
1. El componente es Standalone, tiene `OnPush` y no genera memory leaks.
2. No contiene estilos inline ni valores arbitrarios no permitidos.
3. El manejo de errores traduce los códigos HTTP (400, 401, 403, 404, 409, 422, 500) a notificaciones visuales legibles.
4. La compilación de TypeScript no produce advertencias de tipos (`any` prohibido).
5. Las rutas están protegidas con los guards correspondientes (`authGuard`, `roleGuard`).
6. El archivo `checkpoint.md` de la spec queda actualizado.
