import 'package:flutter/material.dart';
import 'package:ec_mobile/src/core/theme/app_theme.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu07_detalle_producto/presentacion/pantallas/pantalla_producto_detalle.dart';

import '../../datos/modelos/chatbot_dto.dart';
import '../bloc/chatbot_bloc.dart';

/// Pantalla del Asistente de Estilo Inteligente (CU19)
/// Proporciona una interfaz conversacional de alta costura con recomendaciones
/// directas de prendas del catálogo y boutique asociadas.
class PantallaAsistenteEstilo extends StatefulWidget {
  final String? token;
  final bool habilitarImagenesRed;
  final ChatbotBloc? bloc;

  const PantallaAsistenteEstilo({
    super.key,
    this.token,
    this.habilitarImagenesRed = true,
    this.bloc,
  });

  @override
  State<PantallaAsistenteEstilo> createState() =>
      _PantallaAsistenteEstiloState();
}

class _PantallaAsistenteEstiloState extends State<PantallaAsistenteEstilo> {
  late final ChatbotBloc _bloc;
  final TextEditingController _controladorTexto = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _bloc = widget.bloc ??
        ChatbotBloc.obtenerInstanciaCompartida(token: widget.token);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _bloc.marcarChatAbierto();
    });
    _bloc.addListener(_alCambiarEstado);
  }

  void _alCambiarEstado() {
    _scrollAlFondo();
  }

  @override
  void dispose() {
    _bloc.removeListener(_alCambiarEstado);
    _controladorTexto.dispose();
    _scrollController.dispose();
    // Se preserva el bloc para que el chat no se reinicie al presionar el botón "atrás"
    super.dispose();
  }

  void _scrollAlFondo() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _enviarMensaje([String? textoDirecto]) {
    final texto = textoDirecto ?? _controladorTexto.text;
    if (texto.trim().isEmpty) return;

    _bloc.enviarMensaje(texto);
    if (textoDirecto == null) {
      _controladorTexto.clear();
    }
    _scrollAlFondo();
  }

  void _abrirDetallePrenda(int idProducto) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => PantallaProductoDetalle(
          idProducto: idProducto,
          token: widget.token,
          habilitarImagenesRed: widget.habilitarImagenesRed,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.slate50,
      appBar: AppBar(
        backgroundColor: AppColors.primaryDark,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: AppColors.white),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: Row(
          children: [
            Container(
              width: 38,
              height: 38,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: const LinearGradient(
                  colors: [AppColors.secondary500, AppColors.secondaryDark],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                border: Border.all(color: AppColors.secondaryDark, width: 1.5),
              ),
              child: const Icon(
                Icons.auto_awesome,
                color: AppColors.primaryDark,
                size: 20,
              ),
            ),
            const SizedBox(width: AppSpacing.space3),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text(
                    'ATELIER VIRTUAL',
                    style: TextStyle(
                      fontFamily: 'Playfair',
                      fontSize: 15,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1.2,
                      color: AppColors.white,
                    ),
                  ),
                  Row(
                    children: [
                      Container(
                        width: 7,
                        height: 7,
                        decoration: const BoxDecoration(
                          shape: BoxShape.circle,
                          color: Color(0xFF10B981), // Emerald online badge
                        ),
                      ),
                      const SizedBox(width: 5),
                      const Text(
                        'Asesor de Estilismo IA',
                        style: TextStyle(
                          fontFamily: 'Outfit',
                          fontSize: 11,
                          color: AppColors.slate300,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: AppColors.secondary500),
            tooltip: 'Reiniciar conversación',
            onPressed: () {
              _bloc.reiniciarConversacion();
              _scrollAlFondo();
            },
          ),
        ],
      ),
      body: AnimatedBuilder(
        animation: _bloc,
        builder: (context, _) {
          final state = _bloc.estado;
          return Column(
            children: [
              // 1. Lista de Mensajes
              Expanded(
                child: ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.all(AppSpacing.space4),
                  itemCount: state.mensajes.length + (state.cargando ? 1 : 0),
                  itemBuilder: (context, index) {
                    if (index == state.mensajes.length && state.cargando) {
                      return _construirIndicadorCarga();
                    }
                    final mensaje = state.mensajes[index];
                    return _construirBurbuja(mensaje);
                  },
                ),
              ),

              // 2. Chips de Sugerencias Rápidas
              if (state.sugerenciasRapidas.isNotEmpty && !state.cargando)
                Container(
                  height: 44,
                  color: AppColors.white,
                  child: ListView.separated(
                    scrollDirection: Axis.horizontal,
                    padding: const EdgeInsets.symmetric(
                      horizontal: AppSpacing.space4,
                      vertical: AppSpacing.space2,
                    ),
                    itemCount: state.sugerenciasRapidas.length,
                    separatorBuilder: (context, index) =>
                        const SizedBox(width: AppSpacing.space2),
                    itemBuilder: (context, index) {
                      final sug = state.sugerenciasRapidas[index];
                      return ActionChip(
                        label: Text(
                          sug,
                          style: const TextStyle(
                            fontFamily: 'Outfit',
                            fontSize: 11,
                            fontWeight: FontWeight.w500,
                            color: AppColors.slate800,
                          ),
                        ),
                        backgroundColor: AppColors.slate100,
                        side: const BorderSide(
                          color: AppColors.slate300,
                          width: 0.8,
                        ),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                        ),
                        onPressed: () => _enviarMensaje(sug),
                      );
                    },
                  ),
                ),

              // 3. Área de Entrada de Texto
              _construirEntradaTexto(state.cargando),
            ],
          );
        },
      ),
    );
  }

  Widget _construirIndicadorCarga() {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.space3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 32,
            height: 32,
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              color: AppColors.primaryDark,
            ),
            child: const Icon(
              Icons.auto_awesome,
              size: 16,
              color: AppColors.secondary500,
            ),
          ),
          const SizedBox(width: AppSpacing.space3),
          Container(
            padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.space4,
              vertical: AppSpacing.space3,
            ),
            decoration: BoxDecoration(
              color: AppColors.white,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.slate200),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const SizedBox(
                  width: 14,
                  height: 14,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    valueColor: AlwaysStoppedAnimation<Color>(
                      AppColors.secondary500,
                    ),
                  ),
                ),
                const SizedBox(width: AppSpacing.space3),
                const Text(
                  'El atelier está buscando la mejor respuesta...',
                  style: TextStyle(
                    fontFamily: 'Outfit',
                    fontSize: 12,
                    fontStyle: FontStyle.italic,
                    color: AppColors.slate500,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _construirBurbuja(BurbujaMensajeChatbot mensaje) {
    if (mensaje.esUsuario) {
      return _construirBurbujaUsuario(mensaje);
    } else {
      return _construirBurbujaAsistente(mensaje);
    }
  }

  Widget _construirBurbujaUsuario(BurbujaMensajeChatbot mensaje) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.space2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.end,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Flexible(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: AppSpacing.space4,
                    vertical: AppSpacing.space3,
                  ),
                  decoration: const BoxDecoration(
                    color: AppColors.primaryDark,
                    borderRadius: BorderRadius.only(
                      topLeft: Radius.circular(18),
                      topRight: Radius.circular(18),
                      bottomLeft: Radius.circular(18),
                    ),
                  ),
                  child: Text(
                    mensaje.texto,
                    style: const TextStyle(
                      fontFamily: 'Outfit',
                      fontSize: 13,
                      color: AppColors.white,
                      height: 1.4,
                    ),
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  mensaje.hora,
                  style: const TextStyle(
                    fontFamily: 'Outfit',
                    fontSize: 10,
                    color: AppColors.slate400,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: AppSpacing.space2),
          Container(
            width: 28,
            height: 28,
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              color: AppColors.slate300,
            ),
            child: const Icon(
              Icons.person,
              size: 16,
              color: AppColors.slate700,
            ),
          ),
        ],
      ),
    );
  }

  Widget _construirBurbujaAsistente(BurbujaMensajeChatbot mensaje) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.space2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 32,
            height: 32,
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              color: AppColors.primaryDark,
            ),
            child: const Icon(
              Icons.auto_awesome,
              size: 16,
              color: AppColors.secondary500,
            ),
          ),
          const SizedBox(width: AppSpacing.space3),
          Flexible(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.all(AppSpacing.space4),
                  decoration: BoxDecoration(
                    color: AppColors.white,
                    borderRadius: const BorderRadius.only(
                      topLeft: Radius.circular(18),
                      topRight: Radius.circular(18),
                      bottomRight: Radius.circular(18),
                    ),
                    border: Border.all(color: AppColors.slate200),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.02),
                        blurRadius: 4,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        mensaje.texto,
                        style: const TextStyle(
                          fontFamily: 'Outfit',
                          fontSize: 13,
                          color: AppColors.slate900,
                          height: 1.4,
                        ),
                      ),

                      // Prendas recomendadas
                      if (mensaje.productos.isNotEmpty) ...[
                        const SizedBox(height: AppSpacing.space4),
                        const Divider(height: 1, color: AppColors.slate200),
                        const SizedBox(height: AppSpacing.space3),
                        Row(
                          children: [
                            const Icon(
                              Icons.checkroom,
                              size: 14,
                              color: AppColors.secondary500,
                            ),
                            const SizedBox(width: 6),
                            Text(
                              'Prendas Recomendadas (${mensaje.productos.length})',
                              style: const TextStyle(
                                fontFamily: 'Playfair',
                                fontSize: 12,
                                fontWeight: FontWeight.bold,
                                color: AppColors.primaryDark,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: AppSpacing.space2),
                        Column(
                          children: mensaje.productos
                              .map((prod) => _construirTarjetaPrenda(prod))
                              .toList(),
                        ),
                      ],

                      // Sucursales sugeridas
                      if (mensaje.sucursales.isNotEmpty) ...[
                        const SizedBox(height: AppSpacing.space3),
                        const Divider(height: 1, color: AppColors.slate200),
                        const SizedBox(height: AppSpacing.space3),
                        Row(
                          children: [
                            const Icon(
                              Icons.storefront,
                              size: 14,
                              color: AppColors.secondary500,
                            ),
                            const SizedBox(width: 6),
                            Text(
                              'Boutiques Recomendadas (${mensaje.sucursales.length})',
                              style: const TextStyle(
                                fontFamily: 'Playfair',
                                fontSize: 12,
                                fontWeight: FontWeight.bold,
                                color: AppColors.primaryDark,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: AppSpacing.space2),
                        Column(
                          children: mensaje.sucursales
                              .map((suc) => _construirTarjetaSucursal(suc))
                              .toList(),
                        ),
                      ],
                    ],
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  mensaje.hora,
                  style: const TextStyle(
                    fontFamily: 'Outfit',
                    fontSize: 10,
                    color: AppColors.slate400,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _construirTarjetaPrenda(ProductoChatbotSugeridoDto prod) {
    return InkWell(
      onTap: () => _abrirDetallePrenda(prod.idProducto),
      borderRadius: BorderRadius.circular(10),
      child: Container(
        margin: const EdgeInsets.only(bottom: AppSpacing.space2),
        padding: const EdgeInsets.all(AppSpacing.space2),
        decoration: BoxDecoration(
          color: AppColors.slate50,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: AppColors.slate200),
        ),
        child: Row(
          children: [
            // Thumbnail
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: Container(
                width: 52,
                height: 52,
                color: AppColors.slate200,
                child: widget.habilitarImagenesRed &&
                        prod.imagenUrl != null &&
                        prod.imagenUrl!.isNotEmpty
                    ? Image.network(
                        prod.imagenUrl!,
                        fit: BoxFit.cover,
                        errorBuilder: (context, error, stackTrace) => const Icon(
                          Icons.checkroom,
                          color: AppColors.slate400,
                          size: 24,
                        ),
                      )
                    : const Icon(
                        Icons.checkroom,
                        color: AppColors.slate400,
                        size: 24,
                      ),
              ),
            ),
            const SizedBox(width: AppSpacing.space3),
            // Info
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    prod.nombre,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontFamily: 'Outfit',
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: AppColors.primaryDark,
                    ),
                  ),
                  Text(
                    '\$${prod.precio.toStringAsFixed(2)}',
                    style: const TextStyle(
                      fontFamily: 'Outfit',
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: AppColors.secondaryDark,
                    ),
                  ),
                  if (prod.motivo != null && prod.motivo!.isNotEmpty)
                    Text(
                      prod.motivo!,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontFamily: 'Outfit',
                        fontSize: 10,
                        color: AppColors.slate500,
                        fontStyle: FontStyle.italic,
                      ),
                    ),
                ],
              ),
            ),
            const SizedBox(width: AppSpacing.space2),
            // Botón Ver
            ElevatedButton(
              onPressed: () => _abrirDetallePrenda(prod.idProducto),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primaryDark,
                foregroundColor: AppColors.white,
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                minimumSize: Size.zero,
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(6),
                ),
              ),
              child: const Text(
                'Ver',
                style: TextStyle(
                  fontFamily: 'Outfit',
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _construirTarjetaSucursal(SucursalChatbotSugeridaDto suc) {
    return Container(
      margin: const EdgeInsets.only(bottom: AppSpacing.space2),
      padding: const EdgeInsets.all(AppSpacing.space2),
      decoration: BoxDecoration(
        color: AppColors.slate50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppColors.slate200),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(
            Icons.location_on,
            size: 16,
            color: AppColors.secondary500,
          ),
          const SizedBox(width: 6),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${suc.nombre} (${suc.ciudad})',
                  style: const TextStyle(
                    fontFamily: 'Outfit',
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                    color: AppColors.slate900,
                  ),
                ),
                Text(
                  suc.direccion,
                  style: const TextStyle(
                    fontFamily: 'Outfit',
                    fontSize: 10,
                    color: AppColors.slate600,
                  ),
                ),
                if (suc.horarioAtencion != null &&
                    suc.horarioAtencion!.isNotEmpty)
                  Text(
                    'Horario: ${suc.horarioAtencion}',
                    style: const TextStyle(
                      fontFamily: 'Outfit',
                      fontSize: 10,
                      color: AppColors.slate500,
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _construirEntradaTexto(bool cargando) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.space4,
        vertical: AppSpacing.space3,
      ),
      decoration: BoxDecoration(
        color: AppColors.white,
        border: const Border(
          top: BorderSide(color: AppColors.slate200, width: 1),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.03),
            blurRadius: 6,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: SafeArea(
        child: Row(
          children: [
            Expanded(
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.space3,
                ),
                decoration: BoxDecoration(
                  color: AppColors.slate50,
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(color: AppColors.slate300),
                ),
                child: TextField(
                  controller: _controladorTexto,
                  enabled: !cargando,
                  textInputAction: TextInputAction.send,
                  onSubmitted: (_) => _enviarMensaje(),
                  decoration: const InputDecoration(
                    hintText: 'Consulte sobre prendas, estilos, boutiques...',
                    hintStyle: TextStyle(
                      fontFamily: 'Outfit',
                      fontSize: 12,
                      color: AppColors.slate400,
                    ),
                    border: InputBorder.none,
                    isDense: true,
                    contentPadding: EdgeInsets.symmetric(vertical: 10),
                  ),
                  style: const TextStyle(
                    fontFamily: 'Outfit',
                    fontSize: 13,
                    color: AppColors.slate900,
                  ),
                ),
              ),
            ),
            const SizedBox(width: AppSpacing.space2),
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: cargando ? AppColors.slate300 : AppColors.primaryDark,
              ),
              child: IconButton(
                icon: const Icon(Icons.arrow_upward, size: 20),
                color: cargando ? AppColors.slate500 : AppColors.secondary500,
                onPressed: cargando ? null : () => _enviarMensaje(),
                tooltip: 'Enviar mensaje',
              ),
            ),
          ],
        ),
      ),
    );
  }
}
