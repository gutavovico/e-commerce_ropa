import 'package:flutter/foundation.dart';

/// Nombre de la plataforma, fuera de una tienda (login, registro, selección de tienda).
const String nombrePlataforma = 'FashionStore';

/// Datos públicos de una empresa (tienda). Contrato de `EmpresaOut` / `TenantSesionOut` del backend.
@immutable
class EmpresaTienda {
  final String codigo;
  final String nombre;

  const EmpresaTienda({required this.codigo, required this.nombre});

  factory EmpresaTienda.fromJson(Map<String, dynamic> json) => EmpresaTienda(
        codigo: json['codigo'] as String? ?? '',
        nombre: json['nombre'] as String? ?? '',
      );

  Map<String, dynamic> toJson() => {'codigo': codigo, 'nombre': nombre};

  @override
  bool operator ==(Object other) => other is EmpresaTienda && other.codigo == codigo && other.nombre == nombre;

  @override
  int get hashCode => Object.hash(codigo, nombre);
}

/// P2-CU02 · Tienda en la que navega la sesión del móvil.
///
/// - Cliente: la elige en `PantallaSeleccionEmpresa` y puede cambiarla desde Perfil sin volver a
///   iniciar sesión (su token no lleva empresa, decisión A10).
/// - Empleado: la de su cuenta, que llega en la respuesta del login.
///
/// `ClienteHttpApi` la envía en la cabecera `X-Tenant` de cada petición a la API, igual que el
/// interceptor de la web dentro de un portal. Se limpia al cerrar sesión.
class EmpresaActual extends ChangeNotifier {
  EmpresaActual._();

  static final EmpresaActual instancia = EmpresaActual._();

  EmpresaTienda? _empresa;

  EmpresaTienda? get empresa => _empresa;

  /// Nombre visible de la marca: la tienda elegida o, sin tienda, la plataforma.
  String get marca => _empresa?.nombre ?? nombrePlataforma;

  /// Cabeceras que identifican la tienda ante el backend (vacías sin tienda elegida).
  Map<String, String> cabeceras() => _empresa == null ? const {} : {'X-Tenant': _empresa!.codigo};

  void elegir(EmpresaTienda empresa) {
    _empresa = empresa;
    notifyListeners();
  }

  void limpiar() {
    if (_empresa == null) return;
    _empresa = null;
    notifyListeners();
  }
}
