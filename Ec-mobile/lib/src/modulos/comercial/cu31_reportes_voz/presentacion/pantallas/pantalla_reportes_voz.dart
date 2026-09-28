import 'package:flutter/material.dart';
import '../../datos/modelos/reportes_voz_dto.dart';
import '../bloc/reportes_bloc.dart';

/// Pantalla institucional para CU31: Generar reportes ejecutivos y consultas por voz
class PantallaReportesVoz extends StatefulWidget {
  final String token;
  final ReportesBloc? bloc;

  const PantallaReportesVoz({
    super.key,
    required this.token,
    this.bloc,
  });

  @override
  State<PantallaReportesVoz> createState() => _PantallaReportesVozState();
}

class _PantallaReportesVozState extends State<PantallaReportesVoz> {
  late final ReportesBloc _bloc;
  final TextEditingController _comandoVozController = TextEditingController();

  final List<String> _ejemplosVoz = const [
    'Ventas de este mes en Excel',
    'Cuanto se vendio hoy',
    'Ventas en Madrid en PDF',
    'Stock en Equipetrol',
    'Citas en Santa Cruz',
    'Bitacora de seguridad',
  ];

  @override
  void initState() {
    super.initState();
    _bloc = widget.bloc ?? ReportesBloc();
    _bloc.addListener(_alCambiarEstado);
    _bloc.inicializar(widget.token);
  }

  @override
  void dispose() {
    _bloc.removeListener(_alCambiarEstado);
    _comandoVozController.dispose();
    if (widget.bloc == null) {
      _bloc.dispose();
    }
    super.dispose();
  }

  void _alCambiarEstado() {
    setState(() {});
  }

  void _procesarComando(String texto) {
    final orden = texto.trim();
    if (orden.isEmpty) return;
    _comandoVozController.text = orden;
    _bloc.interpretarVoz(widget.token, orden);
  }

  @override
  Widget build(BuildContext context) {
    final estado = _bloc.estado;
    final filtros = _bloc.filtros;

    ReportePrevisualizacionDto? previsualizacion;
    ComandoVozOut? comandoVoz;
    String? mensajeExito;
    String? errorMensaje;
    bool estaCargando = false;
    bool estaExportando = false;

    if (estado is ReportesCargando) {
      estaCargando = true;
    } else if (estado is ReportesExportando) {
      estaExportando = true;
      previsualizacion = estado.previsualizacion;
    } else if (estado is ReportesListo) {
      previsualizacion = estado.previsualizacion;
      comandoVoz = estado.comandoVoz;
      mensajeExito = estado.mensajeExito;
    } else if (estado is ReportesError) {
      errorMensaje = estado.mensaje;
      previsualizacion = estado.ultimaPrevisualizacion;
    }

    return Scaffold(
      backgroundColor: const Color(0xFFFAF9F7),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0.5,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, size: 16, color: Colors.black),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text(
          'FASHION STORE  |  REPORTES',
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w700,
            letterSpacing: 2.0,
            color: Colors.black,
          ),
        ),
        centerTitle: true,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 1. Cabecera Institucional
              _construirCabecera(),
              const SizedBox(height: 16),

              // Banners de Notificacion
              if (mensajeExito != null) ...[
                _construirBannerExito(mensajeExito),
                const SizedBox(height: 12),
              ],
              if (errorMensaje != null) ...[
                _construirBannerError(errorMensaje),
                const SizedBox(height: 12),
              ],

              // 2. Tarjeta de Dictado e Inteligencia por Voz
              _construirTarjetaDictadoVoz(estaCargando, comandoVoz),
              const SizedBox(height: 18),

              // 3. Tarjeta de Previsualizacion Cuantitativa
              _construirTarjetaPrevisualizacion(previsualizacion, estaCargando),
              const SizedBox(height: 18),

              // 4. Panel de Filtros Parametricos
              _construirPanelFiltros(filtros, estaCargando),
              const SizedBox(height: 24),

              // 5. Boton de Exportacion Binaria Streaming
              _construirBotonExportacion(estaExportando || estaCargando),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }

  Widget _construirCabecera() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: const Color(0xFFF5EFEB),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Text(
                '• ANALITICA Y GESTION EJECUTIVA',
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.0,
                  color: Color(0xFF8A6D3B),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        const Text(
          'Generar reportes ejecutivos y consultas por voz',
          style: TextStyle(
            fontSize: 22,
            fontWeight: FontWeight.w800,
            color: Colors.black,
            letterSpacing: -0.5,
            height: 1.2,
          ),
        ),
        const SizedBox(height: 4),
        const Text(
          'Centro corporativo de inteligencia comercial, metricas consolidadas y descarga binaria.',
          style: TextStyle(
            fontSize: 12,
            color: Color(0xFF666666),
            height: 1.4,
          ),
        ),
      ],
    );
  }

  Widget _construirBannerExito(String mensaje) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFF0FDF4),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFBBF7D0)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.check_circle_outline, color: Color(0xFF16A34A), size: 18),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              mensaje,
              style: const TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w500,
                color: Color(0xFF14532D),
              ),
            ),
          ),
          IconButton(
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(),
            icon: const Icon(Icons.close, size: 14, color: Color(0xFF14532D)),
            onPressed: () => _bloc.limpiarMensajes(),
          ),
        ],
      ),
    );
  }

  Widget _construirBannerError(String mensaje) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFFEF2F2),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFFECACA)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.error_outline, color: Color(0xFFDC2626), size: 18),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              mensaje,
              style: const TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w500,
                color: Color(0xFF7F1D1D),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _construirTarjetaDictadoVoz(bool estaCargando, ComandoVozOut? comandoVoz) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFE5E5E5)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.03),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.black,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.mic, color: Colors.white, size: 16),
              ),
              const SizedBox(width: 10),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'CONSULTA Y DICTADO POR VOZ',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 1.0,
                        color: Colors.black,
                      ),
                    ),
                    Text(
                      'Dicta tu orden o escribe en lenguaje natural',
                      style: TextStyle(fontSize: 11, color: Color(0xFF777777)),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),

          // Campo de entrada
          TextField(
            controller: _comandoVozController,
            enabled: !estaCargando,
            decoration: InputDecoration(
              hintText: 'Ej: Reporte de ventas de este mes en Excel...',
              hintStyle: const TextStyle(fontSize: 12, color: Color(0xFFAAAAAA)),
              filled: true,
              fillColor: const Color(0xFFF9F9F9),
              contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: Color(0xFFE5E5E5)),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: Color(0xFFE5E5E5)),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: Colors.black, width: 1.5),
              ),
              suffixIcon: IconButton(
                icon: const Icon(Icons.send_rounded, size: 18, color: Colors.black),
                onPressed: estaCargando
                    ? null
                    : () => _procesarComando(_comandoVozController.text),
              ),
            ),
            onSubmitted: estaCargando ? null : _procesarComando,
          ),
          const SizedBox(height: 12),

          // Chips de ordenes sugeridas
          const Text(
            'Ordenes rapidas sugeridas:',
            style: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: Color(0xFF888888)),
          ),
          const SizedBox(height: 6),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: _ejemplosVoz.map((ejemplo) {
              return InkWell(
                onTap: estaCargando ? null : () => _procesarComando(ejemplo),
                borderRadius: BorderRadius.circular(16),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF5F3EF),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: const Color(0xFFE6E2D8)),
                  ),
                  child: Text(
                    ejemplo,
                    style: const TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                      color: Color(0xFF444444),
                    ),
                  ),
                ),
              );
            }).toList(),
          ),

          if (comandoVoz != null) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: const Color(0xFFFAF7F2),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: const Color(0xFFECE4D8)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.auto_awesome, color: Color(0xFFAD8C63), size: 16),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Interpretado: Modulo ${comandoVoz.modulo.toUpperCase()} | Formato ${comandoVoz.formato.toUpperCase()} | Periodo ${comandoVoz.periodo.toUpperCase()}',
                      style: const TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF5A4A32),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _construirTarjetaPrevisualizacion(
    ReportePrevisualizacionDto? prev,
    bool estaCargando,
  ) {
    final total = prev?.totalRegistros ?? 0;
    final fin = prev?.resumenFinanciero;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFE5E5E5)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'PREVISUALIZACION DE DATOS',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 1.0,
                  color: Colors.black,
                ),
              ),
              if (prev != null)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: const Color(0xFFEFF6FF),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    prev.formato.toUpperCase(),
                    style: const TextStyle(
                      fontSize: 9,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF1D4ED8),
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 12),

          // Metricas
          Row(
            children: [
              Expanded(
                child: Container(
                  padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 10),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF8FAFC),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFFE2E8F0)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'REGISTROS',
                        style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: Color(0xFF64748B)),
                      ),
                      const SizedBox(height: 4),
                      estaCargando
                          ? const SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : Text(
                              '$total',
                              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.black),
                            ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 10),
              if (fin != null && fin.containsKey('monto_total_bob'))
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 10),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF8FAFC),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0xFFE2E8F0)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'TOTAL FACTURADO',
                          style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: Color(0xFF64748B)),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Bs ${(fin['monto_total_bob'] as num).toStringAsFixed(2)}',
                          style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                ),
              if (fin != null && fin.containsKey('unidades_en_stock'))
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 10),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF8FAFC),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0xFFE2E8F0)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'STOCK TOTAL',
                          style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: Color(0xFF64748B)),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '${fin['unidades_en_stock']} prendas',
                          style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
                        ),
                      ],
                    ),
                  ),
                ),
            ],
          ),

          if (prev != null && prev.nombreArchivoSugerido.isNotEmpty) ...[
            const SizedBox(height: 10),
            Row(
              children: [
                const Icon(Icons.file_present_outlined, size: 14, color: Color(0xFF64748B)),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    prev.nombreArchivoSugerido,
                    style: const TextStyle(fontSize: 10, color: Color(0xFF64748B), fontFamily: 'monospace'),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Widget _construirPanelFiltros(ReporteFiltrosDto filtros, bool estaCargando) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFE5E5E5)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'CONFIGURACION DEL REPORTE',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w800,
              letterSpacing: 1.0,
              color: Colors.black,
            ),
          ),
          const SizedBox(height: 14),

          // 1. Selector de Modulo
          const Text('1. Modulo de Informacion', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
          const SizedBox(height: 6),
          _construirSelectorChips(
            opciones: const [
              {'valor': 'ventas', 'etiqueta': 'Ventas'},
              {'valor': 'reservas', 'etiqueta': 'Reservas'},
              {'valor': 'inventario', 'etiqueta': 'Inventario'},
              {'valor': 'bitacora', 'etiqueta': 'Bitacora'},
            ],
            valorActual: filtros.modulo,
            alSeleccionar: (v) => _bloc.actualizarFiltros(token: widget.token, modulo: v),
            deshabilitado: estaCargando,
          ),
          const SizedBox(height: 14),

          // 2. Selector de Formato
          const Text('2. Formato del Archivo', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
          const SizedBox(height: 6),
          _construirSelectorChips(
            opciones: const [
              {'valor': 'excel', 'etiqueta': 'Excel (.xlsx)'},
              {'valor': 'pdf', 'etiqueta': 'PDF (.pdf)'},
              {'valor': 'csv', 'etiqueta': 'CSV (.csv)'},
            ],
            valorActual: filtros.formato,
            alSeleccionar: (v) => _bloc.actualizarFiltros(token: widget.token, formato: v),
            deshabilitado: estaCargando,
          ),
          const SizedBox(height: 14),

          // 3. Selector de Periodo
          const Text('3. Rango Temporal', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
          const SizedBox(height: 6),
          _construirSelectorChips(
            opciones: const [
              {'valor': 'hoy', 'etiqueta': 'Hoy'},
              {'valor': 'ayer', 'etiqueta': 'Ayer'},
              {'valor': 'esta_semana', 'etiqueta': 'Esta Semana'},
              {'valor': 'este_mes', 'etiqueta': 'Este Mes'},
              {'valor': 'anio_actual', 'etiqueta': 'Anual'},
            ],
            valorActual: filtros.periodo,
            alSeleccionar: (v) => _bloc.actualizarFiltros(token: widget.token, periodo: v),
            deshabilitado: estaCargando,
          ),
          const SizedBox(height: 14),

          // 4. Selector de Sucursal
          const Text('4. Alcance Territorial (Sucursal)', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
          const SizedBox(height: 6),
          _construirDropdownSucursales(filtros, estaCargando),
        ],
      ),
    );
  }

  Widget _construirSelectorChips({
    required List<Map<String, String>> opciones,
    required String valorActual,
    required ValueChanged<String> alSeleccionar,
    required bool deshabilitado,
  }) {
    return Wrap(
      spacing: 6,
      runSpacing: 6,
      children: opciones.map((op) {
        final activo = op['valor'] == valorActual;
        return InkWell(
          onTap: deshabilitado ? null : () => alSeleccionar(op['valor']!),
          borderRadius: BorderRadius.circular(10),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
            decoration: BoxDecoration(
              color: activo ? Colors.black : const Color(0xFFF6F6F6),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: activo ? Colors.black : const Color(0xFFE2E2E2)),
            ),
            child: Text(
              op['etiqueta']!,
              style: TextStyle(
                fontSize: 11,
                fontWeight: activo ? FontWeight.bold : FontWeight.w500,
                color: activo ? Colors.white : const Color(0xFF333333),
              ),
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _construirDropdownSucursales(ReporteFiltrosDto filtros, bool deshabilitado) {
    final sucursales = _bloc.sucursales;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12),
      decoration: BoxDecoration(
        color: const Color(0xFFF9F9F9),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFE5E5E5)),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<int?>(
          isExpanded: true,
          value: filtros.idSucursal,
          hint: const Text('Consolidado Todas las Sucursales', style: TextStyle(fontSize: 12)),
          items: [
            const DropdownMenuItem<int?>(
              value: null,
              child: Text(
                'Consolidado Todas las Sucursales',
                style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
              ),
            ),
            ...sucursales.map(
              (suc) => DropdownMenuItem<int?>(
                value: suc.idSucursal,
                child: Text(
                  suc.nombre,
                  style: const TextStyle(fontSize: 12),
                ),
              ),
            ),
          ],
          onChanged: deshabilitado
              ? null
              : (val) {
                  _bloc.actualizarFiltros(
                    token: widget.token,
                    idSucursal: val,
                    resetSucursal: val == null,
                  );
                },
        ),
      ),
    );
  }

  Widget _construirBotonExportacion(bool deshabilitado) {
    return SizedBox(
      width: double.infinity,
      height: 52,
      child: ElevatedButton(
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.black,
          foregroundColor: Colors.white,
          elevation: 2,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        ),
        onPressed: deshabilitado ? null : () => _bloc.exportarReporte(widget.token),
        child: deshabilitado
            ? const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                  ),
                  SizedBox(width: 10),
                  Text(
                    'GENERANDO REPORTE...',
                    style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1.0),
                  ),
                ],
              )
            : const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.download, size: 18, color: Color(0xFFAD8C63)),
                  SizedBox(width: 8),
                  Text(
                    'EXPORTAR REPORTE BINARIO',
                    style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1.0),
                  ),
                ],
              ),
      ),
    );
  }
}
