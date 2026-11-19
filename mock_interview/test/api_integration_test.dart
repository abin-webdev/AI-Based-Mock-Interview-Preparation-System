import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:mock_interview/config/api_config.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class _RealHttpOverrides extends HttpOverrides {
  @override
  HttpClient createHttpClient(SecurityContext? context) {
    return super.createHttpClient(context)
      ..badCertificateCallback = (cert, host, port) => true;
  }
}

void main() {
  setUpAll(() {
    HttpOverrides.global = _RealHttpOverrides();
  });

  tearDownAll(() {
    HttpOverrides.global = null;
  });

  group('ApiConfig & Endpoint Generation Tests', () {
    test('Production Base URL is correctly configured to deployed Render backend', () {
      expect(ApiConfig.productionBaseUrl, 'https://ai-mock-interview-backend-nklz.onrender.com');
    });

    test('Endpoint generator functions produce valid HTTPS URLs', () {
      const base = 'https://ai-mock-interview-backend-nklz.onrender.com';
      expect(ApiConfig.tokenObtain(base), '$base/api/v1/auth/token/');
      expect(ApiConfig.tokenRefresh(base), '$base/api/v1/auth/token/refresh/');
      expect(ApiConfig.registerCandidate(base), '$base/api/v1/auth/register/candidate/');
      expect(ApiConfig.registerCompany(base), '$base/api/v1/auth/register/company/');
      expect(ApiConfig.vacancies(base), '$base/api/v1/vacancies/');
      expect(ApiConfig.aiMockSessions(base), '$base/api/v1/ai-interviews/sessions/');
      expect(ApiConfig.notifications(base), '$base/api/v1/notifications/');
    });

    test('Legacy compatibility endpoints produce correct /myapp/ URLs', () {
      const base = 'https://ai-mock-interview-backend-nklz.onrender.com';
      expect(ApiConfig.legacyUserLogin(base), '$base/myapp/User_login/');
      expect(ApiConfig.legacyUserRegistration(base), '$base/myapp/user_registration/');
      expect(ApiConfig.legacyViewVacancy(base), '$base/myapp/user_view_vacancy/');
      expect(ApiConfig.legacyApplyVacancy(base), '$base/myapp/user_apply_vacancy/');
      expect(ApiConfig.legacyViewAppliedVacancy(base), '$base/myapp/view_applied_vacancy/');
      expect(ApiConfig.legacySendFeedback(base), '$base/myapp/send_feedback/');
      expect(ApiConfig.legacySendComplaint(base), '$base/myapp/send_complaint/');
      expect(ApiConfig.legacyUserViewReply(base), '$base/myapp/user_viewreply/');
    });

    test('Header generator produces valid JSON and bearer headers', () {
      final headersNoAuth = ApiConfig.getHeaders();
      expect(headersNoAuth['Content-Type'], 'application/json');
      expect(headersNoAuth.containsKey('Authorization'), false);

      final headersWithAuth = ApiConfig.getHeaders(token: 'test_token_123');
      expect(headersWithAuth['Authorization'], 'Bearer test_token_123');
    });
  });

  group('Live Production Backend Integration Verification', () {
    test('Live backend is alive and accessible', () async {
      final response = await http.get(
        Uri.parse('https://ai-mock-interview-backend-nklz.onrender.com/api/v1/vacancies/'),
      ).timeout(const Duration(seconds: 45));
      expect(response.statusCode, 200);
      final decoded = json.decode(response.body);
      expect(decoded, isA<Map<String, dynamic>>());
      expect(decoded.containsKey('results'), true);
    }, timeout: const Timeout(Duration(seconds: 60)));

    test('Candidate registration validation correctly handles mismatched passwords', () async {
      final response = await http.post(
        Uri.parse('https://ai-mock-interview-backend-nklz.onrender.com/api/v1/auth/register/candidate/'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'email': 'invalid_test_pwd@example.com',
          'password': 'Password123!',
          'confirm_password': 'MismatchedPassword999!',
        }),
      ).timeout(const Duration(seconds: 45));
      expect(response.statusCode, 400);
    }, timeout: const Timeout(Duration(seconds: 60)));
  });
}
