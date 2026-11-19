import 'package:shared_preferences/shared_preferences.dart';

class ApiConfig {
  // ----------------------------------------------------
  // BASE HOSTS
  // ----------------------------------------------------
  // Local Android Emulator default: http://10.0.2.2:8000
  // Local Web / iOS default: http://127.0.0.1:8000
  // Production Render Deployment URL:
  static const String productionBaseUrl = 'https://ai-mock-interview-backend.onrender.com';
  static const String defaultLocalUrl = 'http://10.0.2.2:8000';

  // ----------------------------------------------------
  // DYNAMIC URL RESOLVER
  // ----------------------------------------------------
  static Future<String> getBaseUrl() async {
    final SharedPreferences prefs = await SharedPreferences.getInstance();
    final String? configuredUrl = prefs.getString('url');
    if (configuredUrl != null && configuredUrl.isNotEmpty) {
      // Normalize trailing slash
      return configuredUrl.endsWith('/')
          ? configuredUrl.substring(0, configuredUrl.length - 1)
          : configuredUrl;
    }
    return defaultLocalUrl;
  }

  // ----------------------------------------------------
  // LEGACY FLUTTER ENDPOINTS (/myapp/...)
  // ----------------------------------------------------
  static String userLogin(String base) => '$base/myapp/User_login/';
  static String userRegistration(String base) => '$base/myapp/user_registration/';
  static String userProfile(String base) => '$base/myapp/user_profile/';
  static String userProfileViewForEdit(String base) => '$base/myapp/user_profileviewforedit/';
  static String userEditProfile(String base) => '$base/myapp/user_edit_profile/';
  static String companyDropdown(String base) => '$base/myapp/companytocomplaint/';
  static String reviewCompany(String base) => '$base/myapp/review_company/';
  static String viewVacancy(String base) => '$base/myapp/user_view_vacancy/';
  static String applyVacancy(String base) => '$base/myapp/user_apply_vacancy/';
  static String viewAppliedVacancy(String base) => '$base/myapp/view_applied_vacancy/';
  static String userViewTest(String base) => '$base/myapp/user_view_test/';
  static String sendFeedback(String base) => '$base/myapp/send_feedback/';
  static String sendComplaint(String base) => '$base/myapp/send_complaint/';
  static String userViewReply(String base) => '$base/myapp/user_viewreply/';

  // ----------------------------------------------------
  // MODERN RESTFUL API (v1) ENDPOINTS (/api/v1/...)
  // ----------------------------------------------------
  // AI Mock Interviews
  static String aiMockSessions(String base) => '$base/api/v1/ai-interviews/sessions/';
  static String aiMockSessionDetail(String base, int id) => '$base/api/v1/ai-interviews/sessions/$id/';
  static String aiMockSessionStart(String base, int id) => '$base/api/v1/ai-interviews/sessions/$id/start/';
  static String aiMockSubmitAnswer(String base, int id) => '$base/api/v1/ai-interviews/sessions/$id/submit-answer/';
  static String aiMockComplete(String base, int id) => '$base/api/v1/ai-interviews/sessions/$id/complete/';
  static String aiMockCameraTelemetry(String base, int id) => '$base/api/v1/ai-interviews/sessions/$id/camera-telemetry/';
  static String aiMockResults(String base, int id) => '$base/api/v1/ai-interviews/sessions/$id/results/';

  // Reports
  static String mockInterviewPdf(String base, int id) => '$base/api/v1/reports/mock-interviews/$id/pdf/';

  // Notifications
  static String notifications(String base) => '$base/api/v1/notifications/';
  static String notificationMarkRead(String base, int id) => '$base/api/v1/notifications/$id/read/';

  // ----------------------------------------------------
  // AUTH HEADERS HELPER
  // ----------------------------------------------------
  static Map<String, String> getHeaders({String? token}) {
    final Map<String, String> headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (token != null && token.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }
}
