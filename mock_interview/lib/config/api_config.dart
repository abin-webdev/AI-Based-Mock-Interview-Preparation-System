import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ApiConfig {
  // ----------------------------------------------------
  // BASE HOSTS
  // ----------------------------------------------------
  // Deployed Live Production Backend on Render:
  static const String productionBaseUrl = 'https://ai-mock-interview-backend-nklz.onrender.com';

  // ----------------------------------------------------
  // INITIALIZER FOR PRODUCTION STARTUP
  // ----------------------------------------------------
  static Future<void> initializeDefaultProduction() async {
    final SharedPreferences prefs = await SharedPreferences.getInstance();
    final String? configuredUrl = prefs.getString('base_api_url') ?? prefs.getString('url');
    final bool isInvalid = configuredUrl == null ||
        configuredUrl.isEmpty ||
        (kIsWeb && (configuredUrl.contains('localhost') ||
                    configuredUrl.contains('127.0.0.1') ||
                    configuredUrl.startsWith('http://192.') ||
                    configuredUrl.startsWith('http://10.')));

    if (isInvalid) {
      await prefs.setString('base_api_url', productionBaseUrl);
      await prefs.setString('url', '$productionBaseUrl/myapp');
      await prefs.setString('img_url', productionBaseUrl);
    }
  }

  // ----------------------------------------------------
  // DYNAMIC URL RESOLVER
  // ----------------------------------------------------
  static Future<String> getBaseUrl() async {
    final SharedPreferences prefs = await SharedPreferences.getInstance();
    final String? configuredUrl = prefs.getString('base_api_url') ?? prefs.getString('url');
    if (configuredUrl != null && configuredUrl.isNotEmpty) {
      String clean = configuredUrl.trim();
      // Remove trailing slash if present
      if (clean.endsWith('/')) {
        clean = clean.substring(0, clean.length - 1);
      }
      // Strip legacy /myapp suffix if saved previously
      if (clean.endsWith('/myapp')) {
        clean = clean.substring(0, clean.length - 6);
      }
      // On web release, prevent unencrypted http/localhost requests
      if (kIsWeb && (clean.contains('localhost') || clean.startsWith('http://'))) {
        return productionBaseUrl;
      }
      if (clean.startsWith('http://') || clean.startsWith('https://')) {
        return clean;
      }
    }
    return productionBaseUrl;
  }

  static Future<String> getMediaUrl(String? relativePath) async {
    if (relativePath == null || relativePath.isEmpty) return '';
    if (relativePath.startsWith('http://') || relativePath.startsWith('https://')) {
      return relativePath;
    }
    final String base = await getBaseUrl();
    final String cleanPath = relativePath.startsWith('/') ? relativePath.substring(1) : relativePath;
    return '$base/$cleanPath';
  }

  // ----------------------------------------------------
  // RESTFUL API (v1) ENDPOINTS
  // ----------------------------------------------------
  // Auth
  static String tokenObtain(String base) => '$base/api/v1/auth/token/';
  static String tokenRefresh(String base) => '$base/api/v1/auth/token/refresh/';
  static String registerCandidate(String base) => '$base/api/v1/auth/register/candidate/';
  static String registerCompany(String base) => '$base/api/v1/auth/register/company/';
  static String currentUser(String base) => '$base/api/v1/auth/me/';
  static String changePassword(String base) => '$base/api/v1/auth/change-password/';
  static String logout(String base) => '$base/api/v1/auth/logout/';

  // Candidate Portal
  static String candidateDashboard(String base) => '$base/api/v1/candidates/dashboard/';
  static String candidateProfile(String base) => '$base/api/v1/candidates/profile/';
  static String candidatePhoto(String base) => '$base/api/v1/candidates/profile/photo/';
  static String candidateResume(String base) => '$base/api/v1/candidates/profile/resume/';

  // Company Portal
  static String companyDashboard(String base) => '$base/api/v1/companies/dashboard/';
  static String companyProfile(String base) => '$base/api/v1/companies/profile/';
  static String companyVacancies(String base) => '$base/api/v1/companies/vacancies/';
  static String companyVacancyDetail(String base, int id) => '$base/api/v1/companies/vacancies/$id/';
  static String companyVacancyApplications(String base, int vacancyId) => '$base/api/v1/companies/vacancies/$vacancyId/applications/';
  static String companyApplications(String base) => '$base/api/v1/companies/applications/';
  static String companyApplicationStatus(String base, int applicationId) => '$base/api/v1/companies/applications/$applicationId/status/';

  // Public Vacancies & Candidate Applications
  static String vacancies(String base) => '$base/api/v1/vacancies/';
  static String vacancyDetail(String base, int id) => '$base/api/v1/vacancies/$id/';
  static String vacancyApply(String base, int id) => '$base/api/v1/vacancies/$id/apply/';
  static String myApplications(String base) => '$base/api/v1/applications/';
  static String applicationDetail(String base, int id) => '$base/api/v1/applications/$id/';
  static String applicationWithdraw(String base, int id) => '$base/api/v1/applications/$id/withdraw/';

  // AI Mock Interviews
  static String aiMockSessions(String base) => '$base/api/v1/ai-interviews/sessions/';
  static String aiMockSessionDetail(String base, int id) => '$base/api/v1/ai-interviews/sessions/$id/';
  static String aiMockSessionStart(String base, int id) => '$base/api/v1/ai-interviews/sessions/$id/start/';
  static String aiMockSessionQuestions(String base, int id) => '$base/api/v1/ai-interviews/sessions/$id/questions/';
  static String aiMockSubmitAnswer(String base, int id) => '$base/api/v1/ai-interviews/sessions/$id/submit-answer/';
  static String aiMockComplete(String base, int id) => '$base/api/v1/ai-interviews/sessions/$id/complete/';
  static String aiMockCameraTelemetry(String base, int id) => '$base/api/v1/ai-interviews/sessions/$id/camera-telemetry/';
  static String aiMockResults(String base, int id) => '$base/api/v1/ai-interviews/sessions/$id/results/';

  // Reports
  static String mockInterviewPdf(String base, int id) => '$base/api/v1/reports/mock-interviews/$id/pdf/';

  // Feedback & Complaints
  static String feedback(String base) => '$base/api/v1/feedback/';
  static String complaints(String base) => '$base/api/v1/complaints/';
  static String complaintDetail(String base, int id) => '$base/api/v1/complaints/$id/';

  // Notifications
  static String notifications(String base) => '$base/api/v1/notifications/';
  static String notificationMarkRead(String base, int id) => '$base/api/v1/notifications/$id/read/';
  static String notificationMarkAllRead(String base) => '$base/api/v1/notifications/mark-all-read/';

  // ----------------------------------------------------
  // LEGACY FLUTTER ENDPOINTS (/myapp/...)
  // ----------------------------------------------------
  static String legacyUserLogin(String base) => '$base/myapp/User_login/';
  static String legacyUserRegistration(String base) => '$base/myapp/user_registration/';
  static String legacyUserProfile(String base) => '$base/myapp/user_profile/';
  static String legacyUserProfileViewForEdit(String base) => '$base/myapp/user_profileviewforedit/';
  static String legacyUserEditProfile(String base) => '$base/myapp/user_edit_profile/';
  static String legacyCompanyDropdown(String base) => '$base/myapp/companytocomplaint/';
  static String legacyReviewCompany(String base) => '$base/myapp/review_company/';
  static String legacyViewVacancy(String base) => '$base/myapp/user_view_vacancy/';
  static String legacyApplyVacancy(String base) => '$base/myapp/user_apply_vacancy/';
  static String legacyViewAppliedVacancy(String base) => '$base/myapp/view_applied_vacancy/';
  static String legacyUserViewTest(String base) => '$base/myapp/user_view_test/';
  static String legacySendFeedback(String base) => '$base/myapp/send_feedback/';
  static String legacySendComplaint(String base) => '$base/myapp/send_complaint/';
  static String legacyUserViewReply(String base) => '$base/myapp/user_viewreply/';

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
