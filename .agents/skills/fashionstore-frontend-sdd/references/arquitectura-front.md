# Arquitectura Técnica Frontend Web — FashionStore (Angular 19+)

**Versión:** 1.0.0 Production  
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo (PUDS)  
**Clasificación:** SPA Modular por Paquetes de Dominio y Aislamiento por Caso de Uso  
**Tecnología:** Angular 19+ (Standalone Components, Signals, Typed Reactive Forms y Tailwind CSS)  
**Idioma Normativo:** Español técnico estricto en documentación, directorios, modelos y código.

---

## 1. Clasificación y Organización Modular por Dominio

La aplicación web de **FashionStore** en `Ec-frontend/src/app/` replica fielmente los **6 paquetes oficiales del dominio** definidos en `SI2-Parcial1.md`. Cada paquete encapsula sus casos de uso correspondientes (`cu01_registrarse`, `cu05_consultar_catalogo`, etc.), garantizando que la lógica de negocio, las llamadas HTTP y las vistas se mantengan acotadas y desacopladas.

```text
Ec-frontend/src/app/
├── core/                                       # Servicios singleton, infraestructura y seguridad
│   ├── guards/
│   │   ├── autenticacion.guard.ts              # Valida sesión activa y vigencia de token JWT
│   │   └── rol.guard.ts                        # Control de acceso por rol (cliente, admin, cajero, encargado)
│   ├── interceptors/
│   │   ├── autenticacion.interceptor.ts        # Inyecta encabezado Authorization: Bearer <token>
│   │   └── error.interceptor.ts                # Normaliza excepciones de dominio (DomainError) y HTTP
│   ├── services/
│   │   ├── autenticacion.service.ts            # Signal de usuario actual, login, registro y logout
│   │   ├── almacenamiento_token.service.ts     # Wrapper tipado para localStorage / sessionStorage
│   │   └── notificacion.service.ts             # Alertas toast para feedback de transacciones
│   └── models/
│       ├── usuario.model.ts                    # Modelo de entidad de usuario y enums de roles
│       ├── autenticacion.dto.ts                # Payloads de login, register y refresh token
│       └── respuesta_api.model.ts              # Estructura genérica de respuesta y error
│
├── shared/                                     # Biblioteca visual atómica (FASHION STORE Tokens)
│   ├── components/
│   │   ├── boton/                              # Botón primario, secundario, destructivo con tokens Base-2
│   │   ├── campo_texto/                        # Input con estados reposo, foco, error y password toggle
│   │   ├── pildora_talla/                      # Selector de tallas (XS a XL) con estado agotado
│   │   ├── muestra_color/                      # Selector circular de color con anillo de selección
│   │   ├── tarjeta_producto/                   # Card de catálogo con ratio 3:4 y wishlist
│   │   ├── selector_cantidad/                  # Control [- 1 +] con display a 2 dígitos
│   │   ├── selector_fecha/                     # Selector de fecha para probador físico
│   │   ├── insignia_badge/                     # NEW, SALE -30%, LIMITED EDITION, LOW STOCK
│   │   ├── chip_filtro/                        # Píldora de filtro interactiva con botón descartar [X]
│   │   └── modal_dialogo/                      # Contenedor modal accesible para confirmaciones
│   ├── directives/
│   │   └── trampa_enfoque.directive.ts         # Trampa de foco (focus trap) para accesibilidad WCAG
│   └── pipes/
│       ├── formato_moneda.pipe.ts              # Formato de precios en Bolivianos (Bs.) o Dólares ($)
│       └── imagen_respaldo.pipe.ts             # Sustitución elegante si falla la URL de imagen
│
└── modules/                                    # 6 PAQUETES OFICIALES DEL DOMINIO
    │
    ├── autenticacion_seguridad/                # Paquete 1: Usuarios, Perfil y Seguridad
    │   ├── cu01_registrarse/
    │   │   ├── paginas/registro.component.ts
    │   │   ├── servicios/registro.service.ts
    │   │   └── modelos/registro.dto.ts
    │   ├── cu02_iniciar_sesion/
    │   │   ├── paginas/login.component.ts
    │   │   ├── servicios/login.service.ts
    │   │   └── modelos/login.dto.ts
    │   ├── cu03_cerrar_sesion/
    │   │   └── servicios/logout.service.ts
    │   ├── cu04_gestionar_perfil/
    │   │   ├── paginas/perfil.component.ts
    │   │   └── servicios/perfil.service.ts
    │   ├── cu20_usuarios_roles/
    │   │   ├── paginas/admin_usuarios.component.ts
    │   │   └── servicios/admin_usuarios.service.ts
    │   └── cu33_recuperar_acceso/
    │       ├── paginas/recuperar_acceso.component.ts
    │       └── servicios/recuperar_acceso.service.ts
    │
    ├── catalogo_exploracion/                   # Paquete 2: Exploración, Búsqueda y Variantes
    │   ├── cu05_consultar_catalogo/
    │   │   ├── paginas/catalogo.component.ts
    │   │   ├── componentes/grid_prendas.component.ts
    │   │   └── servicios/catalogo.service.ts
    │   ├── cu06_buscar_filtrar/
    │   │   ├── componentes/barra_busqueda.component.ts
    │   │   ├── componentes/panel_filtros.component.ts
    │   │   └── servicios/busqueda.service.ts
    │   ├── cu07_detalle_producto/
    │   │   ├── paginas/detalle_producto.component.ts
    │   │   └── servicios/detalle_producto.service.ts
    │   ├── cu08_variantes_producto/
    │   │   ├── componentes/selector_variantes.component.ts
    │   │   └── modelos/variante.dto.ts
    │   └── cu09_disponibilidad_sucursal/
    │       ├── componentes/visor_stock_sucursal.component.ts
    │       └── servicios/stock_sucursal.service.ts
    │
    ├── gestion_operativa/                      # Paquete 3: Administración, Sucursales y Stock
    │   ├── cu21_sucursales_ciudades/
    │   │   ├── paginas/admin_sucursales.component.ts
    │   │   └── servicios/sucursales.service.ts
    │   ├── cu22_administrar_productos/
    │   │   ├── paginas/admin_productos.component.ts
    │   │   ├── componentes/formulario_alta_cascada.component.ts
    │   │   └── servicios/admin_productos.service.ts
    │   ├── cu23_administrar_atributos/
    │   │   └── paginas/admin_atributos.component.ts
    │   ├── cu24_temporadas_colecciones/
    │   │   └── paginas/admin_temporadas.component.ts
    │   ├── cu25_proveedores/
    │   │   └── paginas/admin_proveedores.component.ts
    │   └── cu27_promociones/
    │       └── paginas/admin_promociones.component.ts
    │
    ├── reservas/                               # Paquete 4: Citas de Probador Físico
    │   ├── cu12_reservar_prendas/
    │   │   ├── paginas/agendar_reserva.component.ts
    │   │   ├── componentes/calendario_atelier.component.ts
    │   │   └── servicios/reservas.service.ts
    │   ├── cu13_consultar_cancelar/
    │   │   ├── paginas/mis_reservas.component.ts
    │   │   └── componentes/modal_cancelar_reserva.component.ts
    │   └── cu14_consultar_estado/
    │       └── componentes/tarjeta_estado_reserva.component.ts
    │
    ├── compras_pagos/                          # Paquete 5: Carrito, Checkout, POS y Stripe
    │   ├── cu11_carrito/
    │   │   ├── componentes/drawer_bolsa.component.ts
    │   │   ├── paginas/vista_carrito.component.ts
    │   │   └── servicios/carrito.service.ts
    │   ├── cu15_checkout/
    │   │   ├── paginas/checkout.component.ts
    │   │   ├── componentes/formulario_despacho.component.ts
    │   │   └── servicios/checkout.service.ts
    │   ├── cu16_pago_electronico/
    │   │   ├── componentes/formulario_stripe.component.ts
    │   │   └── servicios/pasarela_stripe.service.ts
    │   ├── cu17_historial_compras/
    │   │   └── paginas/historial_pedidos.component.ts
    │   ├── cu31_venta_presencial_pos/
    │   │   ├── paginas/terminal_pos.component.ts
    │   │   └── servicios/pos.service.ts
    │   └── cu32_cobro_comprobante_pos/
    │       └── componentes/visor_ticket_comprobante.component.ts
    │
    └── funciones_avanzadas/                    # Paquete 6: AR, IA, Reportes y Bitácora
        ├── cu10_vestidor_virtual/
        │   ├── paginas/probador_virtual_web.component.ts
        │   └── servicios/sesion_ar.service.ts
        ├── cu18_recomendaciones_ia/
        │   ├── componentes/carrusel_sugerencias.component.ts
        │   └── servicios/recomendaciones.service.ts
        ├── cu19_asistente_chatbot/
        │   ├── componentes/widget_chatbot.component.ts
        │   └── servicios/chatbot.service.ts
        ├── cu26_inventario_global/
        │   └── paginas/reporte_inventario_consolidado.component.ts
        ├── cu28_ventas_reservas_dash/
        │   └── paginas/dashboard_ventas_reservas.component.ts
        ├── cu29_indicadores_kpi/
        │   └── paginas/panel_kpi_gerencial.component.ts
        └── cu30_bitacora_auditoria/
            └── paginas/visor_bitacora_movimientos.component.ts
```

---

## 2. Contratos de Servicios HTTP y Tipado Estricto (TypeScript DTOs)

Cada servicio HTTP de cada caso de uso consume los endpoints expuestos en `/api/v1/...` respetando fielmente el contrato de datos.

### 2.1 Paquete: Autenticación y Seguridad

#### Caso de Uso CU01 (Registrarse)
```typescript
// modules/autenticacion_seguridad/cu01_registrarse/modelos/registro.dto.ts
export interface PeticionRegistroUsuario {
  nombre: string;
  apellido: string;
  email: string;
  password: string;
  telefono?: string;
  ci_nit?: string;
}

export interface RespuestaRegistroUsuario {
  id_usuario: number;
  email: string;
  nombre: string;
  apellido: string;
  rol: 'cliente';
}
```

```typescript
// modules/autenticacion_seguridad/cu01_registrarse/servicios/registro.service.ts
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { PeticionRegistroUsuario, RespuestaRegistroUsuario } from '../modelos/registro.dto';

@Injectable({ providedIn: 'root' })
export class ServicioRegistroUsuario {
  private readonly http = inject(HttpClient);
  private readonly urlBase = `${environment.apiUrl}/api/v1/auth`;

  registrar(datos: PeticionRegistroUsuario): Observable<RespuestaRegistroUsuario> {
    return this.http.post<RespuestaRegistroUsuario>(`${this.urlBase}/register`, datos);
  }
}
```

#### Caso de Uso CU02 (Iniciar Sesión)
```typescript
// modules/autenticacion_seguridad/cu02_iniciar_sesion/modelos/login.dto.ts
export interface PeticionLogin {
  email: string;
  password: string;
}

export interface RespuestaAutenticacion {
  access_token: string;
  token_type: 'bearer';
  expires_in: number;
  usuario: {
    id_usuario: number;
    email: string;
    nombre: string;
    apellido: string;
    rol: 'cliente' | 'administrador' | 'encargado_sucursal' | 'cajero' | 'proveedor';
    id_sucursal: number | null;
  };
}
```

---

### 2.2 Paquete: Catálogo y Exploración

#### Caso de Uso CU06 (Buscar y Filtrar con `pg_trgm`)
```typescript
// modules/catalogo_exploracion/cu06_buscar_filtrar/modelos/busqueda.dto.ts
export interface FiltrosCatalogoDTO {
  id_categoria?: number;
  id_talla?: number;
  id_color?: number;
  precio_min?: number;
  precio_max?: number;
  id_sucursal?: number;
}

export interface PeticionBuscarCatalogo {
  termino_busqueda?: string;
  filtros?: FiltrosCatalogoDTO;
  pagina?: number;
  limite?: number;
}

export interface PrendaCatalogoDTO {
  id_producto: number;
  nombre: string;
  descripcion: string;
  precio_base: number;
  precio_final: number;
  porcentaje_descuento?: number;
  modelo_ar_url?: string;
  imagenes: string[];
}

export interface RespuestaBuscarCatalogo {
  total_resultados: number;
  pagina_actual: number;
  productos: PrendaCatalogoDTO[];
}
```

---

### 2.3 Paquete: Compras y Pagos

#### Caso de Uso CU11 (Gestión de Carrito)
```typescript
// modules/compras_pagos/cu11_carrito/modelos/carrito.dto.ts
export interface PeticionAgregarItemCarrito {
  id_variante: number;
  id_sucursal: number;
  cantidad: number;
}

export interface ItemCarritoDTO {
  id_detalle: number;
  id_variante: number;
  sku: string;
  nombre_producto: string;
  talla: string;
  color: string;
  id_sucursal: number;
  nombre_sucursal: string;
  cantidad: number;
  precio_unitario: number;
  subtotal: number;
}

export interface ResumenCarritoDTO {
  subtotal: number;
  descuentos_aplicados: number;
  total_estimado: number;
}

export interface RespuestaCarrito {
  id_carrito: number;
  id_cliente: number;
  items: ItemCarritoDTO[];
  resumen: ResumenCarritoDTO;
}
```

#### Caso de Uso CU15 (Checkout y Comprobante)
```typescript
// modules/compras_pagos/cu15_checkout/modelos/checkout.dto.ts
export interface PeticionCheckout {
  id_carrito: number;
  tipo_venta: 'digital_web' | 'digital_movil';
  metodo_pago: 'tarjeta_credito' | 'tarjeta_debito' | 'qr_transferencia';
  direccion_entrega?: string;
  id_metodo_pago_stripe?: string;
}

export interface RespuestaCheckout {
  id_venta: number;
  numero_comprobante: string;
  estado: 'pendiente' | 'pagada';
  subtotal: number;
  descuento: number;
  total: number;
  secreto_cliente_stripe?: string;
}
```

---

### 2.4 Paquete: Funciones Avanzadas

#### Caso de Uso CU10 (Vestidor Virtual AR)
```typescript
// modules/funciones_avanzadas/cu10_vestidor_virtual/modelos/vestidor_ar.dto.ts
export interface PeticionSesionVestidorAR {
  id_producto: number;
  dispositivo: 'web_desktop' | 'web_mobile' | 'app_flutter';
  resultado_url?: string;
  genero_interes: boolean;
}

export interface RespuestaSesionVestidorAR {
  id_sesion_ar: number;
  id_cliente: number;
  id_producto: number;
  modelo_ar_url: string;
  fecha_hora_inicio: string;
}
```

---

## 3. Interceptores de Red en Español

### 3.1 Interceptor de Autenticación (`autenticacion.interceptor.ts`)
```typescript
// core/interceptors/autenticacion.interceptor.ts
import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AlmacenamientoTokenService } from '../services/almacenamiento_token.service';
import { environment } from '../../../environments/environment';

export const interceptorAutenticacion: HttpInterceptorFn = (req, next) => {
  const almacenamiento = inject(AlmacenamientoTokenService);
  const token = almacenamiento.obtenerToken();
  const esUrlApi = req.url.startsWith(environment.apiUrl);

  if (token && esUrlApi) {
    const reqAutenticada = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
    return next(reqAutenticada);
  }

  return next(req);
};
```

### 3.2 Interceptor de Errores de Dominio (`error.interceptor.ts`)
```typescript
// core/interceptors/error.interceptor.ts
import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { Router } from '@angular/router';
import { NotificacionService } from '../services/notificacion.service';

export const interceptorError: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  const notificacion = inject(NotificacionService);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      let mensajeError = 'Ocurrió un error inesperado en FashionStore.';

      if (error.error && typeof error.error === 'object' && error.error.detail) {
        mensajeError = error.error.detail;
      }

      switch (error.status) {
        case 401:
          notificacion.error('Sesión vencida. Ingrese sus credenciales nuevamente.');
          router.navigate(['/autenticacion/iniciar-sesion']);
          break;
        case 403:
          notificacion.error('Acceso denegado: Privilegios insuficientes.');
          break;
        case 404:
          notificacion.error(mensajeError || 'Registro no encontrado.');
          break;
        case 409:
          // Conflicto de negocio: stock insuficiente, SKU existente, reserva vencida
          notificacion.alerta(mensajeError);
          break;
        case 422:
          notificacion.error('Datos del formulario inválidos.');
          break;
        case 502:
          notificacion.error('Error de pasarela externa o servicio de IA.');
          break;
        default:
          notificacion.error(mensajeError);
      }

      return throwError(() => error);
    })
  );
};
```

---

## 4. Control de Acceso y Enrutamiento (Guards)

### 4.1 Guard de Rol Jerárquico (`rol.guard.ts`)
```typescript
// core/guards/rol.guard.ts
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AutenticacionService } from '../services/autenticacion.service';
import { RolUsuario } from '../models/usuario.model';

export const guardRol = (rolesPermitidos: RolUsuario[]): CanActivateFn => {
  return () => {
    const authService = inject(AutenticacionService);
    const router = inject(Router);
    const rolActual = authService.rolUsuario();

    if (rolActual && rolesPermitidos.includes(rolActual)) {
      return true;
    }

    router.navigate(['/']);
    return false;
  };
};
```

**Ejemplo de Enrutamiento en `app.routes.ts`:**
```typescript
export const rutasAplicacion: Routes = [
  {
    path: 'catalogo',
    loadChildren: () => import('./modules/catalogo_exploracion/catalogo.routes').then(m => m.RUTAS_CATALOGO)
  },
  {
    path: 'gestion-operativa',
    canActivate: [guardAutenticacion, guardRol(['administrador', 'encargado_sucursal'])],
    loadChildren: () => import('./modules/gestion_operativa/gestion.routes').then(m => m.RUTAS_GESTION)
  },
  {
    path: 'pos',
    canActivate: [guardAutenticacion, guardRol(['cajero', 'encargado_sucursal'])],
    loadChildren: () => import('./modules/compras_pagos/cu31_venta_presencial_pos/pos.routes').then(m => m.RUTAS_POS)
  }
];
```
