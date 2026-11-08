import 'package:flutter/material.dart';

import '../../../../../core/empresa_actual.dart';
import '../../datos/fuentes_datos/empresas_remoto_datasource.dart';
import '../bloc/seleccion_empresa_bloc.dart';

/// P2-CU02 · Pantalla intermedia entre el login y el hub: el cliente elige la tienda en la que navega
/// entre aquellas en las que está registrado.
///
/// No es una raíz Hub-and-Spoke: no tiene barra de navegación. El registro en tiendas nuevas es
/// exclusivo de la web (decisión A8); sin tiendas se muestra el estado vacío (A6).
class PantallaSeleccionEmpresa extends StatefulWidget {
  final String token;
  final String? nombreUsuario;

  /// Tiendas que ya trajo el login (A15). Si es null (p. ej. «Cambiar de tienda»), se piden al backend.
  final List<EmpresaTienda>? empresasIniciales;
  final ValueChanged<EmpresaTienda> alElegir;
  final VoidCallback alCerrarSesion;
  final EmpresasRemotoDatasource? datasource;

  const PantallaSeleccionEmpresa({
    super.key,
    required this.token,
    required this.alElegir,
    required this.alCerrarSesion,
    this.nombreUsuario,
    this.empresasIniciales,
    this.datasource,
  });

  @override
  State<PantallaSeleccionEmpresa> createState() => _PantallaSeleccionEmpresaState();
}

class _PantallaSeleccionEmpresaState extends State<PantallaSeleccionEmpresa> {
  late final SeleccionEmpresaBloc _bloc;

  @override
  void initState() {
    super.initState();
    _bloc = SeleccionEmpresaBloc(
      token: widget.token,
      iniciales: widget.empresasIniciales,
      datasource: widget.datasource,
    );
    if (widget.empresasIniciales == null) {
      _bloc.cargar();
    }
  }

  @override
  void dispose() {
    _bloc.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final saludo = (widget.nombreUsuario ?? '').trim();
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        automaticallyImplyLeading: false,
        title: const Text(
          nombrePlataforma,
          style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, letterSpacing: 3),
        ),
        actions: [
          TextButton(
            onPressed: widget.alCerrarSesion,
            child: const Text('Cerrar sesión', style: TextStyle(color: Colors.black54, fontSize: 12)),
          ),
        ],
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 16),
              Text(
                saludo.isEmpty ? 'Elige una tienda' : 'Hola, $saludo. Elige una tienda',
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 4),
              const Text(
                'Puedes cambiar de tienda más tarde desde tu perfil.',
                style: TextStyle(fontSize: 13, color: Colors.black54),
              ),
              const SizedBox(height: 20),
              Expanded(
                child: AnimatedBuilder(
                  animation: _bloc,
                  builder: (context, _) => _contenido(_bloc.estado),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _contenido(SeleccionEmpresaEstado estado) {
    return switch (estado) {
      SeleccionEmpresaCargando() => const Center(child: CircularProgressIndicator(color: Colors.black)),
      SeleccionEmpresaVacia() => _Mensaje(
          key: const Key('seleccion_empresa_vacia'),
          titulo: 'Tu cuenta aún no está registrada en ninguna tienda',
          detalle: 'Regístrate en una tienda desde la web: entra en su página y elige '
              '«Registrarme en esta tienda». Después aparecerá aquí.',
          alReintentar: _bloc.cargar,
        ),
      SeleccionEmpresaError(:final mensaje) => _Mensaje(
          titulo: 'No se pudieron cargar tus tiendas',
          detalle: mensaje,
          alReintentar: _bloc.cargar,
        ),
      SeleccionEmpresaLista(:final empresas) => RefreshIndicator(
          color: Colors.black,
          onRefresh: _bloc.cargar,
          child: ListView.separated(
            key: const Key('seleccion_empresa_lista'),
            itemCount: empresas.length,
            separatorBuilder: (_, _) => const SizedBox(height: 12),
            itemBuilder: (context, i) {
              final empresa = empresas[i];
              return Material(
                color: Colors.white,
                shape: RoundedRectangleBorder(
                  side: const BorderSide(color: Color(0xFFE5E5E5)),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: ListTile(
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  title: Text(
                    empresa.nombre,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontWeight: FontWeight.w600, letterSpacing: 1.5),
                  ),
                  subtitle: Text(empresa.codigo, maxLines: 1, overflow: TextOverflow.ellipsis),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => widget.alElegir(empresa),
                ),
              );
            },
          ),
        ),
    };
  }
}

class _Mensaje extends StatelessWidget {
  final String titulo;
  final String detalle;
  final Future<void> Function() alReintentar;

  const _Mensaje({super.key, required this.titulo, required this.detalle, required this.alReintentar});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.storefront_outlined, size: 48, color: Colors.black38),
          const SizedBox(height: 16),
          Text(titulo, textAlign: TextAlign.center, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          Text(detalle, textAlign: TextAlign.center, style: const TextStyle(fontSize: 13, color: Colors.black54)),
          const SizedBox(height: 16),
          OutlinedButton(
            onPressed: alReintentar,
            style: OutlinedButton.styleFrom(foregroundColor: Colors.black),
            child: const Text('Volver a comprobar'),
          ),
        ],
      ),
    );
  }
}
