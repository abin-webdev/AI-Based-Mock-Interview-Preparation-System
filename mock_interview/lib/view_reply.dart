import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'config/api_config.dart';

void main() {
  runApp(const cstd_viewComplaints());
}

class cstd_viewComplaints extends StatelessWidget {
  const cstd_viewComplaints({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(
      debugShowCheckedModeBanner: false,
      home: cstd_viewComplaintsPage(title: 'Complaint Replies'),
    );
  }
}

class cstd_viewComplaintsPage extends StatefulWidget {
  const cstd_viewComplaintsPage({super.key, required this.title});
  final String title;

  @override
  State<cstd_viewComplaintsPage> createState() => cstd_viewComplaintsPageState();
}

class cstd_viewComplaintsPageState extends State<cstd_viewComplaintsPage> {
  List<Map<String, dynamic>> users = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    viewUsers();
  }

  Future<void> viewUsers() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final SharedPreferences sh = await SharedPreferences.getInstance();
      final String baseUrl = await ApiConfig.getBaseUrl();
      final String sid = sh.getString('lid') ?? sh.getString('user_id') ?? '';

      final String apiUrl = ApiConfig.legacyUserViewReply(baseUrl);
      final response = await http.post(
        Uri.parse(apiUrl),
        body: {'lid': sid},
      ).timeout(const Duration(seconds: 20));

      final jsonData = json.decode(response.body);

      if (jsonData['status'] == 'ok' && jsonData['key'] != null) {
        List<Map<String, dynamic>> tempList = [];
        for (var item in jsonData['key']) {
          tempList.add({
            'id': item['id'].toString(),
            'replay': item['reply']?.toString() ?? 'Pending admin reply',
            'complaint': item['complaint']?.toString() ?? '',
            'date': item['date']?.toString() ?? '',
          });
        }
        setState(() {
          users = tempList;
          _isLoading = false;
        });
      } else {
        setState(() {
          users = [];
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = "Error fetching replies: $e";
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.title),
        centerTitle: true,
        backgroundColor: Colors.deepPurple,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: viewUsers,
          ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.redAccent),
              const SizedBox(height: 12),
              Text(
                _error!,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.grey),
              ),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: viewUsers,
                icon: const Icon(Icons.refresh),
                label: const Text("Retry"),
              ),
            ],
          ),
        ),
      );
    }

    if (users.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.mark_chat_unread_outlined, size: 64, color: Colors.grey.shade400),
              const SizedBox(height: 16),
              const Text(
                "No Complaints Yet",
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Text(
                "You haven't submitted any complaints or inquiries yet.",
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: viewUsers,
                child: const Text("Refresh"),
              ),
            ],
          ),
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: viewUsers,
      child: ListView.builder(
        padding: const EdgeInsets.all(12),
        itemCount: users.length,
        itemBuilder: (context, index) {
          final user = users[index];
          final bool hasReply = user['replay'] != null &&
              user['replay'].toString().trim().isNotEmpty &&
              user['replay'].toString().toLowerCase() != 'pending' &&
              user['replay'].toString().toLowerCase() != 'pending admin reply';

          return Card(
            margin: const EdgeInsets.only(bottom: 12),
            elevation: 3,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.report_problem_outlined, size: 18, color: Colors.orange.shade800),
                          const SizedBox(width: 6),
                          const Text(
                            "Complaint",
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                          ),
                        ],
                      ),
                      Text(
                        user['date'],
                        style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    user['complaint'],
                    style: const TextStyle(fontSize: 15, color: Colors.black87),
                  ),
                  const Divider(height: 24),
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(
                        hasReply ? Icons.check_circle_outline : Icons.hourglass_top,
                        size: 18,
                        color: hasReply ? Colors.green : Colors.orange,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              hasReply ? "Administrator Reply:" : "Status:",
                              style: TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.bold,
                                color: hasReply ? Colors.green.shade800 : Colors.orange.shade800,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              user['replay'],
                              style: TextStyle(
                                fontSize: 14,
                                fontStyle: hasReply ? FontStyle.normal : FontStyle.italic,
                                color: hasReply ? Colors.black87 : Colors.grey.shade700,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
