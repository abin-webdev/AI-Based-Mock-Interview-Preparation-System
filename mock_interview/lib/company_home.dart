import 'package:flutter/material.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:url_launcher/url_launcher.dart';
import 'config/api_config.dart';
import 'services/api_client.dart';
import 'login.dart';

class CompanyHomePage extends StatefulWidget {
  const CompanyHomePage({super.key});

  @override
  State<CompanyHomePage> createState() => _CompanyHomePageState();
}

class _CompanyHomePageState extends State<CompanyHomePage> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final ApiClient _apiClient = ApiClient();

  bool _isLoading = false;
  Map<String, dynamic>? _dashboardData;
  Map<String, dynamic>? _profileData;
  List<dynamic> _vacancies = [];
  List<dynamic> _applications = [];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _loadAllCompanyData();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadAllCompanyData() async {
    setState(() => _isLoading = true);
    try {
      final baseUrl = await ApiConfig.getBaseUrl();
      
      // Load Dashboard
      try {
        final dashRes = await _apiClient.get(ApiConfig.companyDashboard(baseUrl));
        if (dashRes is Map<String, dynamic>) {
          _dashboardData = dashRes;
        }
      } catch (_) {}

      // Load Profile
      try {
        final profRes = await _apiClient.get(ApiConfig.companyProfile(baseUrl));
        if (profRes is Map<String, dynamic>) {
          _profileData = profRes;
        }
      } catch (_) {}

      // Load Vacancies
      try {
        final vacRes = await _apiClient.get(ApiConfig.companyVacancies(baseUrl));
        if (vacRes is List) {
          _vacancies = vacRes;
        }
      } catch (_) {}

      // Load Applications
      try {
        final appRes = await _apiClient.get(ApiConfig.companyApplications(baseUrl));
        if (appRes is Map && appRes.containsKey('results')) {
          _applications = appRes['results'] ?? [];
        } else if (appRes is List) {
          _applications = appRes;
        }
      } catch (_) {}
    } catch (e) {
      Fluttertoast.showToast(msg: "Error loading company portal: $e");
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  bool get _isVerified {
    final status = _profileData?['verification_status'] ?? _dashboardData?['company']?['verification_status'];
    return status == 'APPROVED';
  }

  String get _verificationStatus {
    return _profileData?['verification_status'] ?? _dashboardData?['company']?['verification_status'] ?? 'PENDING';
  }

  // ----------------------------------------------------
  // POST NEW VACANCY
  // ----------------------------------------------------
  void _showCreateVacancyDialog() {
    if (!_isVerified) {
      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Row(
            children: [
              Icon(Icons.lock, color: Colors.amber),
              SizedBox(width: 8),
              Text("Verification Required"),
            ],
          ),
          content: Text(
            "Your company account is currently '$_verificationStatus'.\n\n"
            "Only approved and verified companies can publish job vacancies. "
            "Please wait for an administrator to approve your account.",
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("OK")),
          ],
        ),
      );
      return;
    }

    final titleController = TextEditingController();
    final descController = TextEditingController();
    final expController = TextEditingController(text: '2');
    final salaryMinController = TextEditingController(text: '60000');
    final salaryMaxController = TextEditingController(text: '90000');
    final locationController = TextEditingController(text: 'Remote');
    final skillsController = TextEditingController(text: 'Python, Django, REST APIs');
    String selectedJobType = 'FULL_TIME';

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text("Post New Job Vacancy"),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: titleController,
                  decoration: const InputDecoration(labelText: "Job Title *", border: OutlineInputBorder()),
                ),
                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  value: selectedJobType,
                  decoration: const InputDecoration(labelText: "Job Type", border: OutlineInputBorder()),
                  items: const [
                    DropdownMenuItem(value: 'FULL_TIME', child: Text("Full Time")),
                    DropdownMenuItem(value: 'PART_TIME', child: Text("Part Time")),
                    DropdownMenuItem(value: 'CONTRACT', child: Text("Contract")),
                    DropdownMenuItem(value: 'INTERNSHIP', child: Text("Internship")),
                  ],
                  onChanged: (val) => setDialogState(() => selectedJobType = val ?? 'FULL_TIME'),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: descController,
                  maxLines: 3,
                  decoration: const InputDecoration(labelText: "Description *", border: OutlineInputBorder()),
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: skillsController,
                  decoration: const InputDecoration(labelText: "Skills Required *", border: OutlineInputBorder()),
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: salaryMinController,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(labelText: "Min Salary", border: OutlineInputBorder()),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: TextField(
                        controller: salaryMaxController,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(labelText: "Max Salary", border: OutlineInputBorder()),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: locationController,
                  decoration: const InputDecoration(labelText: "Location", border: OutlineInputBorder()),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
            ElevatedButton(
              onPressed: () async {
                if (titleController.text.trim().isEmpty || descController.text.trim().isEmpty) {
                  Fluttertoast.showToast(msg: "Please fill in title and description.");
                  return;
                }
                Navigator.pop(ctx);
                setState(() => _isLoading = true);
                try {
                  final baseUrl = await ApiConfig.getBaseUrl();
                  final url = ApiConfig.companyVacancies(baseUrl);
                  final payload = {
                    'title': titleController.text.trim(),
                    'description': descController.text.trim(),
                    'job_type': selectedJobType,
                    'experience_years_required': int.tryParse(expController.text) ?? 1,
                    'salary_min': double.tryParse(salaryMinController.text) ?? 50000,
                    'salary_max': double.tryParse(salaryMaxController.text) ?? 80000,
                    'location': locationController.text.trim(),
                    'skills_required': skillsController.text.trim(),
                    'status': 'ACTIVE',
                  };
                  await _apiClient.post(url, body: payload);
                  Fluttertoast.showToast(msg: "Vacancy posted successfully!", backgroundColor: Colors.green);
                  _loadAllCompanyData();
                } catch (e) {
                  Fluttertoast.showToast(msg: "Failed to post vacancy: $e", backgroundColor: Colors.red);
                } finally {
                  if (mounted) setState(() => _isLoading = false);
                }
              },
              child: const Text("Publish Vacancy"),
            ),
          ],
        ),
      ),
    );
  }

  // ----------------------------------------------------
  // UPDATE APPLICANT STATUS
  // ----------------------------------------------------
  Future<void> _updateApplicationStatus(int applicationId, String newStatus) async {
    setState(() => _isLoading = true);
    try {
      final baseUrl = await ApiConfig.getBaseUrl();
      final url = ApiConfig.companyApplicationStatus(baseUrl, applicationId);
      await _apiClient.post(url, body: {'status': newStatus});
      Fluttertoast.showToast(msg: "Applicant status updated to $newStatus", backgroundColor: Colors.green);
      _loadAllCompanyData();
    } catch (e) {
      Fluttertoast.showToast(msg: "Failed to update status: $e", backgroundColor: Colors.red);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _handleLogout() async {
    await _apiClient.clearAuthSession();
    if (mounted) {
      Navigator.pushAndRemoveUntil(
        context,
        MaterialPageRoute(builder: (context) => const MyLoginPage(title: '')),
        (route) => false,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    const primaryColor = Color(0xFF1E3A8A);

    return Scaffold(
      backgroundColor: const Color(0xFFF1F5F9),
      appBar: AppBar(
        title: Text(_profileData?['company_name'] ?? "Company Portal"),
        backgroundColor: primaryColor,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadAllCompanyData,
            tooltip: "Refresh Data",
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: _handleLogout,
            tooltip: "Logout",
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: Colors.white,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          tabs: const [
            Tab(icon: Icon(Icons.dashboard), text: "Dashboard"),
            Tab(icon: Icon(Icons.work), text: "My Vacancies"),
            Tab(icon: Icon(Icons.people), text: "Applicants"),
          ],
        ),
      ),
      floatingActionButton: _tabController.index == 1
          ? FloatingActionButton.extended(
              onPressed: _showCreateVacancyDialog,
              backgroundColor: primaryColor,
              foregroundColor: Colors.white,
              icon: const Icon(Icons.add),
              label: const Text("Post Vacancy"),
            )
          : null,
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              controller: _tabController,
              children: [
                _buildDashboardTab(),
                _buildVacanciesTab(),
                _buildApplicantsTab(),
              ],
            ),
    );
  }

  Widget _buildDashboardTab() {
    final status = _verificationStatus;
    Color statusColor = Colors.orange;
    IconData statusIcon = Icons.hourglass_top;
    if (status == 'APPROVED') {
      statusColor = Colors.green;
      statusIcon = Icons.verified;
    } else if (status == 'REJECTED') {
      statusColor = Colors.red;
      statusIcon = Icons.cancel;
    }

    final vacData = _dashboardData?['vacancies'] ?? {};
    final appData = _dashboardData?['applications'] ?? {};

    return RefreshIndicator(
      onRefresh: _loadAllCompanyData,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Verification Banner Card
            Card(
              color: statusColor.withOpacity(0.1),
              shape: RoundedRectangleBorder(
                side: BorderSide(color: statusColor, width: 1.5),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    Icon(statusIcon, color: statusColor, size: 36),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            "Account Status: $status",
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: statusColor,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            status == 'APPROVED'
                                ? "Your company is verified. You can post job openings and review candidates."
                                : "Account is awaiting administrator verification. Publishing vacancies is disabled until verified.",
                            style: TextStyle(fontSize: 13, color: Colors.grey[800]),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Metrics Cards
            Row(
              children: [
                Expanded(
                  child: _buildMetricCard(
                    "Total Vacancies",
                    "${vacData['total'] ?? _vacancies.length}",
                    Icons.work_outline,
                    Colors.indigo,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildMetricCard(
                    "Active Vacancies",
                    "${vacData['active'] ?? _vacancies.where((v) => v['status'] == 'ACTIVE').length}",
                    Icons.check_circle_outline,
                    Colors.teal,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: _buildMetricCard(
                    "Total Applicants",
                    "${appData['total'] ?? _applications.length}",
                    Icons.groups,
                    Colors.blue,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildMetricCard(
                    "Pending Review",
                    "${appData['pending'] ?? _applications.where((a) => a['status'] == 'PENDING').length}",
                    Icons.pending_actions,
                    Colors.amber[800]!,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),

            // Company Profile Details Card
            Card(
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "Company Profile Information",
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                    const Divider(height: 20),
                    _buildInfoRow(Icons.business, "Company Name", _profileData?['company_name'] ?? 'N/A'),
                    _buildInfoRow(Icons.email, "Contact Email", _profileData?['email'] ?? 'N/A'),
                    _buildInfoRow(Icons.phone, "Phone", _profileData?['phone'] ?? 'N/A'),
                    _buildInfoRow(Icons.location_on, "Address", _profileData?['address'] ?? 'N/A'),
                    if (_profileData?['website'] != null && _profileData!['website'].toString().isNotEmpty)
                      _buildInfoRow(Icons.language, "Website", _profileData!['website'].toString()),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMetricCard(String label, String value, IconData icon, Color color) {
    return Card(
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
                Icon(icon, color: color, size: 28),
                Text(
                  value,
                  style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: color),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(label, style: const TextStyle(fontSize: 13, color: Colors.grey)),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(IconData icon, String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 20, color: Colors.indigo),
          const SizedBox(width: 10),
          SizedBox(
            width: 110,
            child: Text(label, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
          ),
          Expanded(
            child: Text(value, style: const TextStyle(fontSize: 13, color: Colors.black87)),
          ),
        ],
      ),
    );
  }

  Widget _buildVacanciesTab() {
    if (_vacancies.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.work_outline, size: 64, color: Colors.grey),
            const SizedBox(height: 12),
            const Text("No vacancies posted yet.", style: TextStyle(fontSize: 16, color: Colors.grey)),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: _showCreateVacancyDialog,
              icon: const Icon(Icons.add),
              label: const Text("Post First Vacancy"),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _vacancies.length,
      itemBuilder: (context, index) {
        final vac = _vacancies[index];
        final isActive = vac['status'] == 'ACTIVE';
        return Card(
          margin: const EdgeInsets.only(bottom: 12),
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
                        vac['title'] ?? 'Job Title',
                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                    ),
                    Chip(
                      label: Text(
                        vac['status'] ?? 'ACTIVE',
                        style: TextStyle(
                          fontSize: 11,
                          color: isActive ? Colors.green[800] : Colors.grey[700],
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      backgroundColor: isActive ? Colors.green[50] : Colors.grey[200],
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Text(
                  vac['description'] ?? '',
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(fontSize: 13, color: Colors.grey[700]),
                ),
                const SizedBox(height: 10),
                Wrap(
                  spacing: 12,
                  runSpacing: 6,
                  children: [
                    _buildBadge(Icons.location_on, vac['location'] ?? 'Remote'),
                    _buildBadge(Icons.schedule, vac['job_type'] ?? 'Full Time'),
                    if (vac['salary_min'] != null && vac['salary_max'] != null)
                      _buildBadge(Icons.payments, "\$${vac['salary_min']} - \$${vac['salary_max']}"),
                  ],
                ),
                const Divider(height: 20),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      "Skills: ${vac['skills_required'] ?? 'N/A'}",
                      style: const TextStyle(fontSize: 12, color: Colors.grey),
                    ),
                    TextButton.icon(
                      onPressed: () {
                        // Switch to Applicants tab filtered by this vacancy
                        _tabController.animateTo(2);
                      },
                      icon: const Icon(Icons.people_outline, size: 18),
                      label: const Text("View Applicants"),
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildApplicantsTab() {
    if (_applications.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.inbox, size: 64, color: Colors.grey),
            SizedBox(height: 12),
            Text("No applications received yet.", style: TextStyle(fontSize: 16, color: Colors.grey)),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _applications.length,
      itemBuilder: (context, index) {
        final app = _applications[index];
        final status = app['status'] ?? 'PENDING';
        Color statusColor = Colors.orange;
        if (status == 'SHORTLISTED') statusColor = Colors.blue;
        if (status == 'ACCEPTED') statusColor = Colors.green;
        if (status == 'REJECTED') statusColor = Colors.red;

        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      app['candidate_name'] ?? "Applicant #${app['id']}",
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                    Chip(
                      label: Text(
                        status,
                        style: TextStyle(color: statusColor, fontWeight: FontWeight.bold, fontSize: 11),
                      ),
                      backgroundColor: statusColor.withOpacity(0.1),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Text(
                  "Applied for: ${app['vacancy_title'] ?? 'Vacancy'}",
                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Colors.indigo),
                ),
                if (app['candidate_email'] != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Text("Email: ${app['candidate_email']}", style: const TextStyle(fontSize: 12, color: Colors.grey)),
                  ),
                if (app['cover_letter'] != null && app['cover_letter'].toString().isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Text("Cover Letter: \"${app['cover_letter']}\"", style: const TextStyle(fontSize: 12, fontStyle: FontStyle.italic)),
                  ),
                const Divider(height: 20),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    // Resume download
                    if (app['resume'] != null && app['resume'].toString().isNotEmpty)
                      TextButton.icon(
                        onPressed: () async {
                          final resumeUrl = await ApiConfig.getMediaUrl(app['resume']);
                          final uri = Uri.parse(resumeUrl);
                          if (await canLaunchUrl(uri)) {
                            await launchUrl(uri, mode: LaunchMode.externalApplication);
                          } else {
                            Fluttertoast.showToast(msg: "Could not open resume file.");
                          }
                        },
                        icon: const Icon(Icons.picture_as_pdf, size: 18, color: Colors.red),
                        label: const Text("View Resume"),
                      )
                    else
                      const Text("No Resume Attached", style: TextStyle(fontSize: 12, color: Colors.grey)),

                    // Status Actions
                    PopupMenuButton<String>(
                      onSelected: (newStatus) => _updateApplicationStatus(app['id'], newStatus),
                      itemBuilder: (ctx) => [
                        const PopupMenuItem(value: 'SHORTLISTED', child: Text("Mark Shortlisted")),
                        const PopupMenuItem(value: 'ACCEPTED', child: Text("Accept Applicant")),
                        const PopupMenuItem(value: 'REJECTED', child: Text("Reject Applicant")),
                      ],
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          border: Border.all(color: Colors.indigo),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text("Update Status", style: TextStyle(color: Colors.indigo, fontSize: 13, fontWeight: FontWeight.bold)),
                            Icon(Icons.arrow_drop_down, color: Colors.indigo),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildBadge(IconData icon, String text) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: Colors.grey[600]),
        const SizedBox(width: 4),
        Text(text, style: TextStyle(fontSize: 12, color: Colors.grey[700])),
      ],
    );
  }
}
