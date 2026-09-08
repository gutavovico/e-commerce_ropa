import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:ec_mobile/api_service.dart';

void main() {
  group('ApiService & HealthStatus Tests', () {
    test('HealthStatus.fromJson maps json fields correctly', () {
      const raw = '{"status":"online","service":"Ec-backend","timestamp":"2026-09-08T12:00:00Z"}';
      final json = jsonDecode(raw) as Map<String, dynamic>;
      final status = HealthStatus.fromJson(json, raw);

      expect(status.status, 'online');
      expect(status.isOnline, isTrue);
      expect(status.service, 'Ec-backend');
      expect(status.timestamp, '2026-09-08T12:00:00Z');
      expect(status.rawJson, raw);
    });

    test('ApiService.checkHealth returns HealthStatus when response is 200', () async {
      final mockClient = MockClient((request) async {
        if (request.url.path == '/api/v1/health') {
          return http.Response(
            '{"status":"online","service":"Ec-backend"}',
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        return http.Response('Not Found', 404);
      });

      final apiService = ApiService(client: mockClient);
      final result = await apiService.checkHealth(customBaseUrl: 'http://127.0.0.1:8000');

      expect(result.status, 'online');
      expect(result.isOnline, isTrue);
      expect(result.service, 'Ec-backend');
    });

    test('ApiService.checkHealth throws when HTTP status is not 200', () async {
      final mockClient = MockClient((request) async {
        return http.Response('Server Error', 500);
      });

      final apiService = ApiService(client: mockClient);

      expect(
        () => apiService.checkHealth(customBaseUrl: 'http://127.0.0.1:8000'),
        throwsA(isA<Exception>()),
      );
    });
  });
}
