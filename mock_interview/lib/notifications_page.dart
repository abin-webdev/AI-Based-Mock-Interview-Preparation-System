import 'package:flutter/material.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'config/api_config.dart';
import 'services/api_client.dart';

class NotificationsPage extends StatefulWidget {
  const NotificationsPage({super.key});

  @override
  State<NotificationsPage> createState() => _NotificationsPageState();
}

class _NotificationsPageState extends State<NotificationsPage> {
  final ApiClient _apiClient = ApiClient();
  bool _isLoading = false;
  List<dynamic> _notifications = [];

  @override
  void initState() {
    super.initState();
    _fetchNotifications();
  }

  Future<void> _fetchNotifications() async {
    setState(() => _isLoading = true);
    try {
      final baseUrl = await ApiConfig.getBaseUrl();
      final url = ApiConfig.notifications(baseUrl);
      final res = await _apiClient.get(url);
      if (res is Map && res.containsKey('results')) {
        setState(() => _notifications = res['results'] ?? []);
      } else if (res is List) {
        setState(() => _notifications = res);
      }
    } catch (e) {
      Fluttertoast.showToast(msg: "Error loading notifications: $e");
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _markAsRead(int notificationId, int index) async {
    try {
      final baseUrl = await ApiConfig.getBaseUrl();
      final url = ApiConfig.notificationMarkRead(baseUrl, notificationId);
      await _apiClient.post(url);
      setState(() {
        if (index < _notifications.length) {
          _notifications[index]['is_read'] = true;
        }
      });
    } catch (_) {}
  }

  Future<void> _markAllAsRead() async {
    setState(() => _isLoading = true);
    try {
      final baseUrl = await ApiConfig.getBaseUrl();
      final url = ApiConfig.notificationMarkAllRead(baseUrl);
      await _apiClient.post(url);
      Fluttertoast.showToast(msg: "All notifications marked as read.", backgroundColor: Colors.green);
      _fetchNotifications();
    } catch (e) {
      Fluttertoast.showToast(msg: "Failed: $e");
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    const primaryColor = Color(0xFF1E3A8A);

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        title: const Text("Notifications"),
        backgroundColor: primaryColor,
        foregroundColor: Colors.white,
        actions: [
          if (_notifications.isNotEmpty)
            TextButton.icon(
              onPressed: _markAllAsRead,
              icon: const Icon(Icons.done_all, color: Colors.white, size: 18),
              label: const Text("Mark All Read", style: TextStyle(color: Colors.white, fontSize: 13)),
            ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _fetchNotifications,
              child: _notifications.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.notifications_none, size: 64, color: Colors.grey[400]),
                          const SizedBox(height: 12),
                          const Text("No notifications yet.", style: TextStyle(fontSize: 16, color: Colors.grey)),
                        ],
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.all(16),
                      itemCount: _notifications.length,
                      itemBuilder: (context, index) {
                        final notif = _notifications[index];
                        final bool isRead = notif['is_read'] ?? false;

                        return Card(
                          margin: const EdgeInsets.only(bottom: 12),
                          elevation: isRead ? 0.5 : 2,
                          color: isRead ? Colors.white : const Color(0xFFEFF6FF),
                          shape: RoundedRectangleBorder(
                            side: BorderSide(
                              color: isRead ? Colors.grey[300]! : Colors.blue[300]!,
                              width: 1,
                            ),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: ListTile(
                            onTap: isRead ? null : () => _markAsRead(notif['id'], index),
                            leading: CircleAvatar(
                              backgroundColor: isRead ? Colors.grey[200] : Colors.blue[100],
                              child: Icon(
                                isRead ? Icons.notifications_none : Icons.notifications_active,
                                color: isRead ? Colors.grey : Colors.blue[800],
                              ),
                            ),
                            title: Text(
                              notif['title'] ?? 'Notification',
                              style: TextStyle(
                                fontWeight: isRead ? FontWeight.normal : FontWeight.bold,
                                fontSize: 15,
                              ),
                            ),
                            subtitle: Padding(
                              padding: const EdgeInsets.only(top: 4),
                              child: Text(
                                notif['message'] ?? '',
                                style: TextStyle(fontSize: 13, color: Colors.grey[700]),
                              ),
                            ),
                            trailing: isRead
                                ? null
                                : Container(
                                    width: 10,
                                    height: 10,
                                    decoration: const BoxDecoration(
                                      shape: BoxShape.circle,
                                      color: Colors.blue,
                                    ),
                                  ),
                          ),
                        );
                      },
                    ),
            ),
    );
  }
}
