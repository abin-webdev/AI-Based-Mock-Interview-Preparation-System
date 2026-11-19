import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'config/api_config.dart';
import 'test_details.dart';

class ViewAppliedVacancy extends StatelessWidget {
  const ViewAppliedVacancy({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(
      debugShowCheckedModeBanner: false,
      home: ViewAppliedVacancyPage(title: 'My Applications'),
    );
  }
}

class ViewAppliedVacancyPage extends StatefulWidget {
  const ViewAppliedVacancyPage({super.key, required this.title});
  final String title;

  @override
  State<ViewAppliedVacancyPage> createState() => ViewAppliedVacancyPageState();
}

class ViewAppliedVacancyPageState extends State<ViewAppliedVacancyPage> {
  List<Map<String, dynamic>> appliedList = [];
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    viewAppliedVacancy();
  }

  Future<void> viewAppliedVacancy() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final SharedPreferences sh = await SharedPreferences.getInstance();
      final String baseUrl = await ApiConfig.getBaseUrl();
      final String lid = sh.getString('lid') ?? sh.getString('user_id') ?? '';

      final String apiUrl = ApiConfig.legacyViewAppliedVacancy(baseUrl);

      final response = await http.post(
        Uri.parse(apiUrl),
        body: {'lid': lid},
      ).timeout(const Duration(seconds: 20));

      final jsonData = json.decode(response.body);

      if (jsonData['status'] == 'ok' && jsonData['data'] != null) {
        List<Map<String, dynamic>> tempList = [];
        for (var item in jsonData['data']) {
          tempList.add({
            'id': item['id'].toString(),
            'position': item['VACCANCY']?.toString() ?? 'Job Position',
            'company': item['company']?.toString() ?? 'Company',
            'status': item['status']?.toString() ?? 'Pending',
            'date': item['date']?.toString() ?? '',
            'start': item['start']?.toString() ?? 'N/A',
            'end': item['end']?.toString() ?? 'N/A',
          });
        }
        setState(() {
          appliedList = tempList;
          _isLoading = false;
        });
      } else {
        setState(() {
          appliedList = [];
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = "Failed to load applied vacancies: $e";
        _isLoading = false;
      });
    }
  }

  Future<void> viewTest(String applicationId) async {
    try {
      final String baseUrl = await ApiConfig.getBaseUrl();
      final String apiUrl = ApiConfig.legacyUserViewTest(baseUrl);

      final response = await http.post(
        Uri.parse(apiUrl),
        body: {'candidate_id': applicationId},
      ).timeout(const Duration(seconds: 15));

      final jsonData = json.decode(response.body);

      if (jsonData['status'] == 'ok' && jsonData['data'] != null && (jsonData['data'] as List).isNotEmpty) {
        if (!mounted) return;
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => TestDetailsPage(
              testData: jsonData['data'][0],
            ),
          ),
        );
      } else {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("No test schedule assigned yet for this application.")),
        );
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error fetching test details: $e")),
      );
    }
  }

  Color getStatusColor(String status) {
    switch (status.toLowerCase()) {
      case "accepted":
      case "approved":
        return Colors.green;
      case "shortlisted":
        return Colors.blue;
      case "rejected":
        return Colors.red;
      case "reviewed":
        return Colors.deepPurple;
      case "applied":
      case "pending":
      default:
        return Colors.orange;
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
            tooltip: "Refresh Applications",
            onPressed: viewAppliedVacancy,
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

    if (_errorMessage != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.redAccent),
              const SizedBox(height: 12),
              Text(
                _errorMessage!,
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 14, color: Colors.grey),
              ),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: viewAppliedVacancy,
                icon: const Icon(Icons.refresh),
                label: const Text("Retry"),
              ),
            ],
          ),
        ),
      );
    }

    if (appliedList.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.work_history_outlined, size: 64, color: Colors.grey.shade400),
              const SizedBox(height: 16),
              const Text(
                "No Applications Yet",
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Text(
                "You haven't submitted any job applications yet. Go to Vacancies to apply!",
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: viewAppliedVacancy,
                child: const Text("Refresh"),
              ),
            ],
          ),
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: viewAppliedVacancy,
      child: ListView.builder(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        itemCount: appliedList.length,
        itemBuilder: (context, index) {
          final item = appliedList[index];
          final String status = item['status'];
          final bool isAccepted = status.toLowerCase() == "accepted" || status.toLowerCase() == "approved";

          return Card(
            margin: const EdgeInsets.symmetric(vertical: 6),
            elevation: 2,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          item['position'],
                          style: const TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 17,
                          ),
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: getStatusColor(status).withOpacity(0.12),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: getStatusColor(status).withOpacity(0.5)),
                        ),
                        child: Text(
                          status.toUpperCase(),
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                            color: getStatusColor(status),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      const Icon(Icons.business, size: 16, color: Colors.grey),
                      const SizedBox(width: 6),
                      Text(
                        item['company'],
                        style: const TextStyle(fontWeight: FontWeight.w600, color: Colors.black87),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      const Icon(Icons.calendar_today, size: 14, color: Colors.grey),
                      const SizedBox(width: 6),
                      Text(
                        "Applied: ${item['date']}",
                        style: TextStyle(fontSize: 13, color: Colors.grey.shade700),
                      ),
                    ],
                  ),
                  if (isAccepted) ...[
                    const Divider(height: 20),
                    Align(
                      alignment: Alignment.centerRight,
                      child: ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.green,
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                        ),
                        onPressed: () => viewTest(item['id']),
                        icon: const Icon(Icons.assignment_turned_in, size: 16),
                        label: const Text("View Test Details"),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
