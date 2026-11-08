import 'package:flutter/foundation.dart';

import '../../../../../core/empresa_actual.dart';
import '../../datos/fuentes_datos/empresas_remoto_datasource.dart';

/// Estados de la pantalla de selección de tienda (P2-CU02).
sealed class SeleccionEmpresaEstado {
  const SeleccionEmpresaEstado();
}

class SeleccionEmpresaCargando extends SeleccionEmpresaEstado {
  const SeleccionEmpresaCargando();
}

class SeleccionEmpresaLista extends SeleccionEmpresaEstado {
  final List<EmpresaTienda> empresas;
  const SeleccionEmpresaLista(this.empresas);
}

/// A6: el cliente no está registrado en ninguna tienda disponible.
class SeleccionEmpresaVacia extends SeleccionEmpresaEstado {
  const SeleccionEmpresaVacia();
}

class SeleccionEmpresaError extends SeleccionEmpresaEstado {
  final String mensaje;
  const SeleccionEmpresaError(this.mensaje);
}

class SeleccionEmpresaBloc extends ChangeNotifier {
  final String token;
  final EmpresasRemotoDatasource _datasource;

  SeleccionEmpresaEstado _estado = const SeleccionEmpresaCargando();
  SeleccionEmpresaEstado get estado => _estado;

  SeleccionEmpresaBloc({
    required this.token,
    List<EmpresaTienda>? iniciales,
    EmpresasRemotoDatasource? datasource,
  }) : _datasource = datasource ?? EmpresasRemotoDatasource() {
    if (iniciales != null) {
      _estado = _desde(iniciales);
    }
  }

  /// Vuelve a pedir las tiendas al backend (al abrir desde Perfil o al deslizar para refrescar).
  Future<void> cargar() async {
    if (_estado is! SeleccionEmpresaLista) {
      _estado = const SeleccionEmpresaCargando();
      notifyListeners();
    }
    try {
      _estado = _desde(await _datasource.misEmpresas(token));
    } on EmpresasExcepcion catch (e) {
      _estado = SeleccionEmpresaError(e.mensaje);
    }
    notifyListeners();
  }

  static SeleccionEmpresaEstado _desde(List<EmpresaTienda> empresas) =>
      empresas.isEmpty ? const SeleccionEmpresaVacia() : SeleccionEmpresaLista(empresas);
}
