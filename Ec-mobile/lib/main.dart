import 'package:flutter/material.dart';
import 'api_config.dart';
import 'api_service.dart';

void main() {
  runApp(const EcMobileApp());
}

class EcMobileApp extends StatelessWidget {
  const EcMobileApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Ecommerce Mobile',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF4F46E5), // Indigo primario del Monorepo
          brightness: Brightness.light,
        ),
      ),
      home: const HealthCheckScreen(),
    );
  }
}

class HealthCheckScreen extends StatefulWidget {
  const HealthCheckScreen({super.key});

  @override
  State<HealthCheckScreen> createState() => _HealthCheckScreenState();
}

class _HealthCheckScreenState extends State<HealthCheckScreen> {
  final ApiService _apiService = ApiService();
  final TextEditingController _urlController = TextEditingController();

  HealthStatus? _healthStatus;
  bool _isLoading = false;
  String? _errorMessage;
  String _lastChecked = '';

  @override
  void initState() {
    super.initState();
    _urlController.text = ApiConfig.baseUrl;
    // Realizar la primera consulta automáticamente al iniciar
    _fetchHealthStatus();
  }

  @override
  void dispose() {
    _apiService.dispose();
    _urlController.dispose();
    super.dispose();
  }

  Future<void> _fetchHealthStatus() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final result = await _apiService.checkHealth(
        customBaseUrl: _urlController.text.trim().isNotEmpty
            ? _urlController.text.trim()
            : null,
      );

      final now = DateTime.now();
      final timeStr =
          '${now.hour.toString().padLeft(2, '0')}:${now.minute.toString().padLeft(2, '0')}:${now.second.toString().padLeft(2, '0')}';

      if (!mounted) return;
      setState(() {
        _healthStatus = result;
        _isLoading = false;
        _lastChecked = timeStr;
      });
    } catch (e) {
      final now = DateTime.now();
      final timeStr =
          '${now.hour.toString().padLeft(2, '0')}:${now.minute.toString().padLeft(2, '0')}:${now.second.toString().padLeft(2, '0')}';

      if (!mounted) return;
      setState(() {
        _healthStatus = null;
        _isLoading = false;
        _errorMessage = e.toString().replaceFirst('Exception: ', '');
        _lastChecked = timeStr;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isOnline = _healthStatus?.isOnline ?? false;

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        title: const Text(
          'Ecommerce Mobile',
          style: TextStyle(fontWeight: FontWeight.w700),
        ),
        centerTitle: true,
        elevation: 0,
        backgroundColor: Colors.white,
        foregroundColor: const Color(0xFF0F172A),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Badge & Subtítulo
              Center(
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: const Color(0xFFE0E7FF),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: const Text(
                    'FLUTTER + FASTAPI INTEGRATION',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                      color: Color(0xFF4338CA),
                      letterSpacing: 0.8,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 12),
              const Text(
                'Comprobación de Conectividad',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.w800,
                  color: Color(0xFF0F172A),
                ),
              ),
              const SizedBox(height: 6),
              Text(
                'Consume el endpoint /api/v1/health de Ec-backend',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
              ),
              const SizedBox(height: 24),

              // Tarjeta 1: Información de Red y Entorno
              Card(
                elevation: 0,
                color: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                  side: const BorderSide(color: Color(0xFFE2E8F0)),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.router_outlined,
                              color: theme.colorScheme.primary, size: 20),
                          const SizedBox(width: 8),
                          const Text(
                            'Configuración de Red',
                            style: TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.w700,
                              color: Color(0xFF1E293B),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      _buildInfoRow('Plataforma detectada:', ApiConfig.platformName),
                      const SizedBox(height: 8),
                      _buildInfoRow('Endpoint destino:', '/api/v1/health'),
                      const SizedBox(height: 12),
                      const Divider(color: Color(0xFFF1F5F9)),
                      const SizedBox(height: 8),
                      const Text(
                        'URL Base de la API:',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: Color(0xFF64748B),
                        ),
                      ),
                      const SizedBox(height: 6),
                      TextField(
                        controller: _urlController,
                        style: const TextStyle(
                          fontSize: 13,
                          fontFamily: 'monospace',
                        ),
                        decoration: InputDecoration(
                          isDense: true,
                          hintText: 'http://10.0.2.2:8000',
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(8),
                            borderSide: const BorderSide(color: Color(0xFFCBD5E1)),
                          ),
                          suffixIcon: IconButton(
                            icon: const Icon(Icons.restore, size: 18),
                            tooltip: 'Restablecer URL por defecto',
                            onPressed: () {
                              setState(() {
                                _urlController.text = ApiConfig.baseUrl;
                              });
                            },
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Tarjeta 2: Estado de Salud del Backend
              Card(
                elevation: 0,
                color: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                  side: const BorderSide(color: Color(0xFFE2E8F0)),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text(
                            'Estado del Backend',
                            style: TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.w700,
                              color: Color(0xFF1E293B),
                            ),
                          ),
                          _buildStatusBadge(isOnline),
                        ],
                      ),
                      const SizedBox(height: 16),

                      // Contenido según estado
                      if (_isLoading) ...[
                        const Center(
                          child: Padding(
                            padding: EdgeInsets.symmetric(vertical: 24.0),
                            child: Column(
                              children: [
                                CircularProgressIndicator(),
                                SizedBox(height: 12),
                                Text(
                                  'Consultando GET /api/v1/health...',
                                  style: TextStyle(fontSize: 13, color: Colors.grey),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ] else if (_healthStatus != null) ...[
                        Container(
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(
                            color: const Color(0xFFF0FDF4),
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: const Color(0xFFBBF7D0)),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  const Icon(Icons.check_circle,
                                      color: Color(0xFF16A34A), size: 18),
                                  const SizedBox(width: 8),
                                  const Text(
                                    'RESPUESTA RECIBIDA CON ÉXITO',
                                    style: TextStyle(
                                      color: Color(0xFF15803D),
                                      fontWeight: FontWeight.w800,
                                      fontSize: 12,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 10),
                              _buildResultRow(
                                  'Status devuelto:', _healthStatus!.status,
                                  isHighlight: true),
                              if (_healthStatus!.service != null) ...[
                                const SizedBox(height: 4),
                                _buildResultRow(
                                    'Servicio:', _healthStatus!.service!),
                              ],
                              if (_healthStatus!.timestamp != null) ...[
                                const SizedBox(height: 4),
                                _buildResultRow(
                                    'Timestamp (UTC):', _healthStatus!.timestamp!),
                              ],
                              const SizedBox(height: 4),
                              _buildResultRow('Último chequeo:', _lastChecked),
                              const SizedBox(height: 10),
                              const Text(
                                'Cuerpo JSON recibido:',
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w600,
                                  color: Color(0xFF475569),
                                ),
                              ),
                              const SizedBox(height: 4),
                              Container(
                                width: double.infinity,
                                padding: const EdgeInsets.all(8),
                                decoration: BoxDecoration(
                                  color: const Color(0xFF0F172A),
                                  borderRadius: BorderRadius.circular(6),
                                ),
                                child: Text(
                                  _healthStatus!.rawJson,
                                  style: const TextStyle(
                                    fontFamily: 'monospace',
                                    fontSize: 12,
                                    color: Color(0xFF38BDF8),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ] else if (_errorMessage != null) ...[
                        Container(
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(
                            color: const Color(0xFFFEF2F2),
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: const Color(0xFFFECACA)),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Row(
                                children: [
                                  Icon(Icons.error_outline,
                                      color: Color(0xFFDC2626), size: 18),
                                  SizedBox(width: 8),
                                  Text(
                                    'SIN CONEXIÓN AL BACKEND',
                                    style: TextStyle(
                                      color: Color(0xFFB91C1C),
                                      fontWeight: FontWeight.w800,
                                      fontSize: 12,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),
                              Text(
                                _errorMessage!,
                                style: const TextStyle(
                                  fontSize: 12,
                                  color: Color(0xFF991B1B),
                                ),
                              ),
                              if (_lastChecked.isNotEmpty) ...[
                                const SizedBox(height: 6),
                                Text(
                                  'Intentado a las: $_lastChecked',
                                  style: TextStyle(
                                    fontSize: 11,
                                    color: Colors.grey.shade600,
                                  ),
                                ),
                              ],
                            ],
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Botón de acción principal
              ElevatedButton.icon(
                onPressed: _isLoading ? null : _fetchHealthStatus,
                icon: _isLoading
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Icon(Icons.refresh, color: Colors.white),
                label: Text(
                  _isLoading
                      ? 'Consultando backend...'
                      : 'Consultar Estado del Backend',
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
                  ),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF4F46E5),
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  elevation: 2,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatusBadge(bool isOnline) {
    if (_isLoading) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: const Color(0xFFFEF3C7),
          borderRadius: BorderRadius.circular(12),
        ),
        child: const Text(
          'CONSULTANDO',
          style: TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w800,
            color: Color(0xFFB45309),
          ),
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: isOnline ? const Color(0xFFDCFCE7) : const Color(0xFFFEE2E2),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        isOnline ? 'ONLINE' : 'OFFLINE',
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w800,
          color: isOnline ? const Color(0xFF15803D) : const Color(0xFFB91C1C),
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: const TextStyle(fontSize: 12, color: Color(0xFF64748B)),
        ),
        Text(
          value,
          style: const TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w600,
            color: Color(0xFF0F172A),
          ),
        ),
      ],
    );
  }

  Widget _buildResultRow(String label, String value, {bool isHighlight = false}) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: const TextStyle(fontSize: 12, color: Color(0xFF374151)),
        ),
        Text(
          value,
          style: TextStyle(
            fontSize: 12,
            fontWeight: isHighlight ? FontWeight.w800 : FontWeight.w600,
            color: isHighlight ? const Color(0xFF16A34A) : const Color(0xFF111827),
          ),
        ),
      ],
    );
  }
}
