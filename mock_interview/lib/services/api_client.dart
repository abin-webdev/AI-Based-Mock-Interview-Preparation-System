import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../config/api_config.dart';

class ApiException implements Exception {
  final int statusCode;
  final String message;
  final dynamic details;

  ApiException(this.statusCode, this.message, [this.details]);

  @override
  String toString() => message;
}

class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;
  ApiClient._internal();

  final http.Client _httpClient = http.Client();

  // ----------------------------------------------------
  // TOKEN STORAGE HELPERS
  // ----------------------------------------------------
  static const String _keyAccess = 'token';
  static const String _keyRefresh = 'refresh_token';
  static const String _keyRole = 'user_role';
  static const String _keyUserId = 'lid';
  static const String _keyUserEmail = 'user_email';
  static const String _keyUserName = 'user_name';

  Future<void> saveAuthSession({
    required String access,
    required String refresh,
    required String role,
    required String userId,
    String? email,
    String? name,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyAccess, access);
    await prefs.setString(_keyRefresh, refresh);
    await prefs.setString(_keyRole, role.toUpperCase());
    await prefs.setString(_keyUserId, userId);
    if (email != null) await prefs.setString(_keyUserEmail, email);
    if (name != null) await prefs.setString(_keyUserName, name);

    // Populate legacy keys so existing screens function seamlessly
    final String baseUrl = await ApiConfig.getBaseUrl();
    await prefs.setString('url', '$baseUrl/myapp');
    await prefs.setString('img_url', baseUrl);
    await prefs.setString('lid', userId);
    if (email != null) await prefs.setString('email', email);
    if (name != null) await prefs.setString('name', name);
  }

  Future<String?> getAccessToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_keyAccess);
  }

  Future<String?> getRefreshToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_keyRefresh);
  }

  Future<String?> getUserRole() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_keyRole);
  }

  Future<String?> getUserId() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_keyUserId);
  }

  Future<String?> getUserName() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_keyUserName);
  }

  Future<void> clearAuthSession() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_keyAccess);
    await prefs.remove(_keyRefresh);
    await prefs.remove(_keyRole);
    await prefs.remove(_keyUserId);
    await prefs.remove(_keyUserEmail);
    await prefs.remove(_keyUserName);
  }

  // ----------------------------------------------------
  // AUTOMATIC TOKEN REFRESH
  // ----------------------------------------------------
  Future<bool> _tryRefreshToken() async {
    try {
      final refresh = await getRefreshToken();
      if (refresh == null || refresh.isEmpty) return false;

      final baseUrl = await ApiConfig.getBaseUrl();
      final url = Uri.parse(ApiConfig.tokenRefresh(baseUrl));

      final response = await _httpClient.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'refresh': refresh}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final newAccess = data['access']?.toString();
        if (newAccess != null && newAccess.isNotEmpty) {
          final prefs = await SharedPreferences.getInstance();
          await prefs.setString(_keyAccess, newAccess);
          return true;
        }
      }
    } catch (_) {}
    return false;
  }

  // ----------------------------------------------------
  // CORE HTTP METHODS
  // ----------------------------------------------------
  Future<dynamic> get(String url, {bool requiresAuth = true}) async {
    return _sendWithRetry('GET', url, requiresAuth: requiresAuth);
  }

  Future<dynamic> post(String url, {dynamic body, bool requiresAuth = true}) async {
    return _sendWithRetry('POST', url, body: body, requiresAuth: requiresAuth);
  }

  Future<dynamic> put(String url, {dynamic body, bool requiresAuth = true}) async {
    return _sendWithRetry('PUT', url, body: body, requiresAuth: requiresAuth);
  }

  Future<dynamic> delete(String url, {bool requiresAuth = true}) async {
    return _sendWithRetry('DELETE', url, requiresAuth: requiresAuth);
  }

  Future<dynamic> _sendWithRetry(
    String method,
    String url, {
    dynamic body,
    bool requiresAuth = true,
    bool isRetry = false,
  }) async {
    final uri = Uri.parse(url);
    final token = requiresAuth ? await getAccessToken() : null;
    final headers = ApiConfig.getHeaders(token: token);

    http.Response response;
    try {
      final payload = body != null ? jsonEncode(body) : null;
      switch (method) {
        case 'GET':
          response = await _httpClient.get(uri, headers: headers).timeout(const Duration(seconds: 30));
          break;
        case 'POST':
          response = await _httpClient.post(uri, headers: headers, body: payload).timeout(const Duration(seconds: 30));
          break;
        case 'PUT':
          response = await _httpClient.put(uri, headers: headers, body: payload).timeout(const Duration(seconds: 30));
          break;
        case 'DELETE':
          response = await _httpClient.delete(uri, headers: headers).timeout(const Duration(seconds: 30));
          break;
        default:
          throw ApiException(400, 'Unsupported HTTP method: $method');
      }
    } on TimeoutException {
      throw ApiException(504, 'Connection timed out. Render may be waking up from cold start, please retry.');
    } on SocketException catch (e) {
      throw ApiException(0, 'Network connection failed: ${e.message}');
    } catch (e) {
      throw ApiException(0, 'Request failed: $e');
    }

    // Handle token expiration & retry
    if (response.statusCode == 401 && requiresAuth && !isRetry) {
      final refreshed = await _tryRefreshToken();
      if (refreshed) {
        return _sendWithRetry(method, url, body: body, requiresAuth: true, isRetry: true);
      } else {
        await clearAuthSession();
        throw ApiException(401, 'Your session has expired. Please log in again.');
      }
    }

    return _processResponse(response);
  }

  // ----------------------------------------------------
  // MULTIPART UPLOAD
  // ----------------------------------------------------
  Future<dynamic> multipartRequest(
    String url, {
    required String method,
    Map<String, String>? fields,
    Map<String, File>? files,
    bool requiresAuth = true,
  }) async {
    final uri = Uri.parse(url);
    final token = requiresAuth ? await getAccessToken() : null;

    final request = http.MultipartRequest(method, uri);
    if (token != null && token.isNotEmpty) {
      request.headers['Authorization'] = 'Bearer $token';
    }

    if (fields != null) {
      request.fields.addAll(fields);
    }

    if (files != null) {
      for (final entry in files.entries) {
        if (await entry.value.exists()) {
          request.files.add(
            await http.MultipartFile.fromPath(entry.key, entry.value.path),
          );
        }
      }
    }

    try {
      final streamedResponse = await request.send().timeout(const Duration(seconds: 45));
      final response = await http.Response.fromStream(streamedResponse);
      return _processResponse(response);
    } on TimeoutException {
      throw ApiException(504, 'File upload timed out. Please verify your connection.');
    } catch (e) {
      throw ApiException(0, 'Upload error: $e');
    }
  }

  // ----------------------------------------------------
  // RESPONSE PROCESSING & ERROR EXTRACTION
  // ----------------------------------------------------
  dynamic _processResponse(http.Response response) {
    dynamic decoded;
    try {
      decoded = jsonDecode(utf8.decode(response.bodyBytes));
    } catch (_) {
      decoded = response.body;
    }

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return decoded;
    }

    // Extract user-friendly error message
    String errorMessage = 'Request failed with status ${response.statusCode}';
    if (decoded is Map) {
      if (decoded.containsKey('detail')) {
        errorMessage = decoded['detail'].toString();
      } else if (decoded.containsKey('message')) {
        errorMessage = decoded['message'].toString();
      } else if (decoded.containsKey('error')) {
        errorMessage = decoded['error'].toString();
      } else {
        // Collect field validation errors
        final errorList = <String>[];
        decoded.forEach((key, value) {
          if (value is List) {
            errorList.add('$key: ${value.join(", ")}');
          } else {
            errorList.add('$key: $value');
          }
        });
        if (errorList.isNotEmpty) {
          errorMessage = errorList.join('\n');
        }
      }
    } else if (decoded is String && decoded.isNotEmpty) {
      errorMessage = decoded;
    }

    throw ApiException(response.statusCode, errorMessage, decoded);
  }
}
