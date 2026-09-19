# Arquitectura Técnica Móvil — FashionStore (Flutter 3.x & Dart)

**Versión:** 1.0.0 Production  
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo (PUDS)  
**Clasificación:** Clean Architecture Feature-First por Paquetes de Dominio y Casos de Uso  
**Tecnología:** Flutter 3.x, Dart 3+, BLoC / Cubit, `flutter_secure_storage` y AR Nativo  
**Idioma Normativo:** Español técnico estricto en documentación, directorios, clases y código.

---

## 1. Clasificación y Organización Modular por Dominio

La aplicación móvil de **FashionStore** en `Ec-mobile/lib/src/` implementa una arquitectura limpia (*Clean Architecture*) organizada por los **6 paquetes oficiales del dominio** de `SI2-Parcial1.md`. Cada caso de uso correspondiente al rol **Cliente** está aislado en su propio subdirectorio con separación estricta de capas (`datos`, `dominio` y `presentacion`).

```text
Ec-mobile/lib/
├── main.dart                                   # Punto de arranque, inicialización de dependencias y tema
└── src/
    ├── nucleo/                                 # Componentes transversales y de infraestructura
    │   ├── tema/
    │   │   ├── tema_app.dart                   # ThemeData de Flutter configurado con Material 3
    │   │   ├── colores_app.dart                # Paleta FASHION STORE (Obsidian, Camel, Neutros)
    │   │   ├── tipografia_app.dart             # Escala tipográfica Outfit con tracking estricto
    │   │   ├── espaciado_app.dart              # Constantes de rejilla Base-2 (espacio1 a espacio7)
    │   │   ├── radio_borde_app.dart            # Radios de curvatura geométricos (xs a full)
    │   │   └── sombras_app.dart                # Elevaciones ópticas sutiles (0 a 4)
    │   │
    │   ├── red/
    │   │   ├── cliente_api.dart                # Cliente HTTP (Dio) con timeouts y reintentos
    │   │   ├── rutas_api.dart                  # Constantes de endpoints (/api/v1/...)
    │   │   ├── interceptor_autenticacion.dart  # Inyector de cabecera Bearer JWT
    │   │   └── excepciones_red.dart            # Mapeo de DomainError del backend a excepciones Dart
    │   │
    │   ├── almacenamiento/
    │   │   └── servicio_almacenamiento_seguro.dart # Envoltorio de flutter_secure_storage para tokens
    │   │
    │   └── widgets_comunes/                    # Biblioteca de átomos visuales compartidos
    │       ├── boton_lujo.dart                 # Botones primarios, secundarios, destructivos
    │       ├── campo_texto_lujo.dart           # Input con estados reposo, foco, error y candado
    │       ├── pildora_talla_widget.dart       # Selector de tallas (XS a XL)
    │       ├── muestra_color_widget.dart       # Muestrario circular con halo de selección
    │       └── tarjeta_prenda_widget.dart      # Card con ratio 3:4 y botón de wishlist
    │
    └── modulos/                                # 6 PAQUETES OFICIALES DEL DOMINIO
        │
        ├── autenticacion_seguridad/            # Paquete 1: Usuarios, Sesión y Acceso
        │   ├── cu01_registrarse/
        │   │   ├── datos/modelos/registro_dto.dart
        │   │   ├── dominio/repositorios/registro_repositorio.dart
        │   │   └── presentacion/pantallas/pantalla_registro.dart
        │   ├── cu02_iniciar_sesion/
        │   │   ├── datos/modelos/login_dto.dart
        │   │   ├── presentacion/bloc/autenticacion_bloc.dart
        │   │   └── presentacion/pantallas/pantalla_login.dart
        │   ├── cu04_gestionar_perfil/
        │   │   ├── datos/modelos/perfil_dto.dart
        │   │   └── presentacion/pantallas/pantalla_perfil_cliente.dart
        │   └── cu33_recuperar_acceso/
        │       └── presentacion/pantallas/pantalla_recuperar_clave.dart
        │
        ├── catalogo_exploracion/               # Paquete 2: Exploración, Búsqueda y Variantes
        │   ├── cu05_consultar_catalogo/
        │   │   ├── datos/modelos/catalogo_dto.dart
        │   │   ├── presentacion/bloc/catalogo_bloc.dart
        │   │   └── presentacion/pantallas/pantalla_catalogo.dart
        │   ├── cu06_buscar_filtrar/
        │   │   ├── datos/modelos/busqueda_dto.dart
        │   │   ├── presentacion/delegados/delegado_busqueda_prendas.dart
        │   │   └── presentacion/widgets/panel_filtros_inferior.dart
        │   ├── cu07_detalle_producto/
        │   │   └── presentacion/pantallas/pantalla_detalle_prenda.dart
        │   ├── cu08_variantes_producto/
        │   │   └── presentacion/widgets/selector_talla_color.dart
        │   └── cu09_disponibilidad_sucursal/
        │       └── presentacion/widgets/indicador_stock_sucursales.dart
        │
        ├── gestion_operativa/                  # Paquete 3: Información de Sucursales y Promociones
        │   ├── cu21_sucursales_ciudades/
        │   │   ├── datos/modelos/sucursal_dto.dart
        │   │   └── presentacion/pantallas/pantalla_selector_sucursal.dart
        │   └── cu27_promociones/
        │       └── presentacion/widgets/carrusel_promociones.dart
        │
        ├── reservas/                           # Paquete 4: Citas de Probador Físico
        │   ├── cu12_reservar_prendas/
        │   │   ├── datos/modelos/reserva_dto.dart
        │   │   ├── presentacion/bloc/reserva_bloc.dart
        │   │   ├── presentacion/widgets/calendario_atelier_movil.dart
        │   │   └── presentacion/pantallas/pantalla_agendar_reserva.dart
        │   ├── cu13_consultar_cancelar/
        │   │   └── presentacion/pantallas/pantalla_mis_reservas.dart
        │   └── cu14_consultar_estado/
        │       └── presentacion/widgets/tarjeta_reserva_activa.dart
        │
        ├── compras_pagos/                      # Paquete 5: Carrito, Checkout Móvil y Pedidos
        │   ├── cu11_carrito/
        │   │   ├── datos/modelos/carrito_dto.dart
        │   │   ├── presentacion/bloc/carrito_bloc.dart
        │   │   └── presentacion/pantallas/pantalla_bolsa_compras.dart
        │   ├── cu15_checkout/
        │   │   ├── datos/modelos/checkout_movil_dto.dart
        │   │   ├── presentacion/bloc/checkout_bloc.dart
        │   │   └── presentacion/pantallas/pantalla_checkout_movil.dart
        │   ├── cu16_pago_electronico/
        │   │   └── datos/servicios/manejador_stripe_movil.dart
        │   └── cu17_historial_compras/
        │       └── presentacion/pantallas/pantalla_historial_pedidos.dart
        │
        └── funciones_avanzadas/                # Paquete 6: Vestidor AR, Recomendaciones y Chatbot
            ├── cu10_vestidor_virtual/
            │   ├── datos/modelos/sesion_ar_dto.dart
            │   ├── dominio/entidades/configuracion_ar.dart
            │   ├── presentacion/controladores/controlador_camara_ar.dart
            │   ├── presentacion/widgets/superposicion_prenda_ar.dart
            │   └── presentacion/pantallas/pantalla_probador_virtual.dart
            ├── cu18_recomendaciones_ia/
            │   └── presentacion/widgets/carrusel_recomendaciones_ia.dart
            └── cu19_asistente_chatbot/
                └── presentacion/pantallas/pantalla_asistente_estilo.dart
```

---

## 2. Sistema Centralizado de Tokens de Diseño (`nucleo/tema/`)

En cumplimiento de la norma de **FASHION STORE**, queda prohibido el uso de valores numéricos de color o márgenes literales en las pantallas.

### 2.1 Espaciado Base-2 (`espaciado_app.dart`)
```dart
class EspaciadoApp {
  EspaciadoApp._();

  static const double espacio1 = 2.0;   // space-1: micro bordes, anillos de color
  static const double espacio2 = 4.0;   // space-2: padding vertical de píldoras
  static const double espacio3 = 8.0;   // space-3: padding de botón, title-to-price
  static const double espacio4 = 16.0;  // space-4: padding de tarjetas, margen de pantalla
  static const double espacio5 = 32.0;  // space-5: separación entre bloques de contenido
  static const double espacio6 = 64.0;  // space-6: ritmo de secciones mayores
  static const double espacio7 = 128.0; // space-7: respiro en lookbook editorial
}
```

### 2.2 Paleta Cromática (`colores_app.dart`)
```dart
import 'package:flutter/material.dart';

class ColoresApp {
  ColoresApp._();

  // Semánticos FASHION STORE
  static const Color primario = Color(0xFF000000);
  static const Color sobrePrimario = Color(0xFFFFFFFF);
  static const Color contenedorPrimario = Color(0xFF1B1C1D);

  static const Color secundario = Color(0xFF675D4E); // Camel / Cashmere
  static const Color sobreSecundario = Color(0xFFFFFFFF);
  static const Color contenedorSecundario = Color(0xFFECDECB);
  static const Color sobreContenedorSecundario = Color(0xFF6B6152);

  static const Color fondo = Color(0xFFF9F9FB);
  static const Color sobreFondo = Color(0xFF1A1C1D);
  static const Color superficie = Color(0xFFF9F9FB);
  static const Color sobreSuperficie = Color(0xFF1A1C1D);

  static const Color contenedorSuperficieMasBajo = Color(0xFFFFFFFF);
  static const Color contenedorSuperficieBajo = Color(0xFFF3F3F5);
  static const Color contenedorSuperficie = Color(0xFFEDEEF0);
  static const Color contenedorSuperficieAlto = Color(0xFFE8E8EA);
  static const Color contenedorSuperficieMasAlto = Color(0xFFE2E2E4);

  static const Color contorno = Color(0xFF75777A);
  static const Color varianteContorno = Color(0xFFC5C6C9);

  // Semántica de Feedback
  static const Color exito = Color(0xFF16A34A);
  static const Color fondoExito = Color(0xFFF0FDF4);
  static const Color advertencia = Color(0xFFD97706);
  static const Color fondoAdvertencia = Color(0xFFFFFBEB);
  static const Color error = Color(0xFFDC2626);
  static const Color fondoError = Color(0xFFFEF2F2);
  static const Color info = Color(0xFF0284C7);
  static const Color fondoInfo = Color(0xFFF0F9FF);
}
```

### 2.3 Tipografía Outfit (`tipografia_app.dart`)
```dart
import 'package:flutter/material.dart';
import 'colores_app.dart';

class TipografiaApp {
  TipografiaApp._();

  static const String familiaFuente = 'Outfit';

  static const TextStyle displayHeroMovil = TextStyle(
    fontFamily: familiaFuente,
    fontSize: 40.0,
    height: 48.0 / 40.0,
    letterSpacing: -0.8,
    fontWeight: FontWeight.w300,
    color: ColoresApp.primario,
  );

  static const TextStyle titularGrande = TextStyle(
    fontFamily: familiaFuente,
    fontSize: 32.0,
    height: 40.0 / 32.0,
    letterSpacing: -0.32,
    fontWeight: FontWeight.w400,
    color: ColoresApp.primario,
  );

  static const TextStyle tituloMedio = TextStyle(
    fontFamily: familiaFuente,
    fontSize: 20.0,
    height: 28.0 / 20.0,
    letterSpacing: 0.0,
    fontWeight: FontWeight.w500,
    color: ColoresApp.primario,
  );

  static const TextStyle cuerpoMedio = TextStyle(
    fontFamily: familiaFuente,
    fontSize: 14.0,
    height: 22.0 / 14.0,
    letterSpacing: 0.14,
    fontWeight: FontWeight.w400,
    color: ColoresApp.sobreSuperficie,
  );

  static const TextStyle etiquetaMayusculas = TextStyle(
    fontFamily: familiaFuente,
    fontSize: 11.0,
    height: 16.0 / 11.0,
    letterSpacing: 1.32, // 0.12em tracking
    fontWeight: FontWeight.w600,
    color: ColoresApp.primario,
  );
}
```

---

## 3. Contratos de Datos y DTOs en Dart

### 3.1 Búsqueda y Catálogo (`CU06`)
```dart
// modulos/catalogo_exploracion/cu06_buscar_filtrar/datos/modelos/busqueda_dto.dart
class PeticionBuscarPrendasDTO {
  final String? terminoBusqueda;
  final int? idCategoria;
  final int? idTalla;
  final int? idColor;
  final double? precioMin;
  final double? precioMax;
  final int? idSucursal;

  const PeticionBuscarPrendasDTO({
    this.terminoBusqueda,
    this.idCategoria,
    this.idTalla,
    this.idColor,
    this.precioMin,
    this.precioMax,
    this.idSucursal,
  });

  Map<String, dynamic> toJson() => {
    if (terminoBusqueda != null) 'termino_busqueda': terminoBusqueda,
    'filtros': {
      if (idCategoria != null) 'id_categoria': idCategoria,
      if (idTalla != null) 'id_talla': idTalla,
      if (idColor != null) 'id_color': idColor,
      if (precioMin != null) 'precio_min': precioMin,
      if (precioMax != null) 'precio_max': precioMax,
      if (idSucursal != null) 'id_sucursal': idSucursal,
    },
  };
}

class PrendaItemDTO {
  final int idProducto;
  final String nombre;
  final String descripcion;
  final double precioBase;
  final double precioFinal;
  final String? modeloArUrl;
  final List<String> imagenes;

  const PrendaItemDTO({
    required this.idProducto,
    required this.nombre,
    required this.descripcion,
    required this.precioBase,
    required this.precioFinal,
    this.modeloArUrl,
    required this.imagenes,
  });

  factory PrendaItemDTO.fromJson(Map<String, dynamic> json) {
    return PrendaItemDTO(
      idProducto: json['id_producto'] as int,
      nombre: json['nombre'] as String,
      descripcion: json['descripcion'] as String? ?? '',
      precioBase: (json['precio_base'] as num).toDouble(),
      precioFinal: (json['precio_final'] as num?)?.toDouble() ?? (json['precio_base'] as num).toDouble(),
      modeloArUrl: json['modelo_ar_url'] as String?,
      imagenes: (json['imagenes'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
    );
  }
}
```

---

### 3.2 Carrito y Checkout Móvil (`CU11`, `CU15`)
```dart
// modulos/compras_pagos/cu15_checkout/datos/modelos/checkout_movil_dto.dart
class PeticionCheckoutMovilDTO {
  final int idCarrito;
  final String tipoVenta; // Siempre "digital_movil" en Flutter
  final String metodoPago;
  final String? direccionEntrega;

  const PeticionCheckoutMovilDTO({
    required this.idCarrito,
    this.tipoVenta = 'digital_movil',
    required this.metodoPago,
    this.direccionEntrega,
  });

  Map<String, dynamic> toJson() => {
    'id_carrito': idCarrito,
    'tipo_venta': tipoVenta,
    'metodo_pago': metodoPago,
    if (direccionEntrega != null) 'direccion_entrega': direccionEntrega,
  };
}

class RespuestaCheckoutMovilDTO {
  final int idVenta;
  final String numeroComprobante;
  final String estado;
  final double subtotal;
  final double descuento;
  final double total;
  final String? secretoClienteStripe;

  const RespuestaCheckoutMovilDTO({
    required this.idVenta,
    required this.numeroComprobante,
    required this.estado,
    required this.subtotal,
    required this.descuento,
    required this.total,
    this.secretoClienteStripe,
  });

  factory RespuestaCheckoutMovilDTO.fromJson(Map<String, dynamic> json) {
    return RespuestaCheckoutMovilDTO(
      idVenta: json['id_venta'] as int,
      numeroComprobante: json['numero_comprobante'] as String,
      estado: json['estado'] as String,
      subtotal: (json['subtotal'] as num).toDouble(),
      descuento: (json['descuento'] as num).toDouble(),
      total: (json['total'] as num).toDouble(),
      secretoClienteStripe: json['client_secret_stripe'] as String?,
    );
  }
}
```

---

## 4. Subsistema de Realidad Aumentada (CU10 - Vestidor Virtual)

El vestidor virtual permite al cliente enfocar la cámara y visualizar en tiempo real la prenda vinculada al producto (`modelo_ar_url`).

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Flujo de Cámara Nativa (Camera Controller a 60 fps)     │
├─────────────────────────────────────────────────────────────┤
│ 2. Detección de Postura Corporal (Pose Estimation)          │
│    Mapeo de puntos de anclaje anatómicos (hombros, torso)   │
├─────────────────────────────────────────────────────────────┤
│ 3. Superposición del Asset 3D (.glb) desde `modelo_ar_url`  │
│    Ajuste y escalado proporcional al cuerpo del usuario     │
├─────────────────────────────────────────────────────────────┤
│ 4. Registro de Sesión en Backend                            │
│    POST /api/v1/vestidor/sesion con dispositivo:            │
│    "app_flutter" y resultado de intención (genero_interes)  │
└─────────────────────────────────────────────────────────────┘
```

```dart
// modulos/funciones_avanzadas/cu10_vestidor_virtual/datos/modelos/sesion_ar_dto.dart
class PeticionRegistrarSesionARDTO {
  final int idProducto;
  final String dispositivo;
  final String? resultadoUrl;
  final bool generoInteres;

  const PeticionRegistrarSesionARDTO({
    required this.idProducto,
    this.dispositivo = 'app_flutter',
    this.resultadoUrl,
    required this.generoInteres,
  });

  Map<String, dynamic> toJson() => {
    'id_producto': idProducto,
    'dispositivo': dispositivo,
    if (resultadoUrl != null) 'resultado_url': resultadoUrl,
    'genero_interes': generoInteres,
  };
}
```

---

## 5. Almacenamiento Seguro de Sesión (`ServicioAlmacenamientoSeguro`)

```dart
// nucleo/almacenamiento/servicio_almacenamiento_seguro.dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ServicioAlmacenamientoSeguro {
  final FlutterSecureStorage _almacenamiento;

  ServicioAlmacenamientoSeguro({FlutterSecureStorage? almacenamiento})
      : _almacenamiento = almacenamiento ??
            const FlutterSecureStorage(
              aOptions: AndroidOptions(encryptedSharedPreferences: true),
              iOptions: IOSOptions(accessibility: KeychainAccessibility.first_unlock),
            );

  static const String _claveToken = 'fashionstore_jwt_token';

  Future<void> guardarToken(String token) async {
    await _almacenamiento.write(key: _claveToken, value: token);
  }

  Future<String?> obtenerToken() async {
    return await _almacenamiento.read(key: _claveToken);
  }

  Future<void> borrarSesion() async {
    await _almacenamiento.delete(key: _claveToken);
  }
}
```
