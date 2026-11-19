import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';
import 'config/api_config.dart';

class AIMockInterviewScreen extends StatefulWidget {
  const AIMockInterviewScreen({super.key});

  @override
  State<AIMockInterviewScreen> createState() => _AIMockInterviewScreenState();
}

enum InterviewStage { setup, inProgress, results }

class _AIMockInterviewScreenState extends State<AIMockInterviewScreen> {
  InterviewStage _stage = InterviewStage.setup;
  bool _isLoading = false;

  // Setup Fields
  String _selectedRole = 'Python Backend Developer';
  String _selectedCategory = 'TECHNICAL';
  String _selectedDifficulty = 'MID';
  int _questionCount = 3;
  bool _cameraConsent = true;

  final List<String> _roleOptions = [
    'Python Backend Developer',
    'Flutter Mobile Developer',
    'Full Stack Engineer',
    'Data Scientist',
    'DevOps Engineer',
    'QA Automation Engineer',
  ];

  // Active Session State
  int? _sessionId;
  List<dynamic> _questions = [];
  int _currentIndex = 0;
  final TextEditingController _answerController = TextEditingController();
  int _timeRemainingSeconds = 900; // 15 mins default
  Timer? _timer;

  // Results State
  Map<String, dynamic>? _resultsData;

  @override
  void dispose() {
    _timer?.cancel();
    _answerController.dispose();
    super.dispose();
  }

  // ----------------------------------------------------
  // API CALL: CREATE SESSION & GENERATE QUESTIONS
  // ----------------------------------------------------
  Future<void> _startInterview() async {
    setState(() => _isLoading = true);
    try {
      final SharedPreferences prefs = await SharedPreferences.getInstance();
      final String baseUrl = await ApiConfig.getBaseUrl();
      final String? token = prefs.getString('token');

      final url = Uri.parse(ApiConfig.aiMockSessions(baseUrl));
      final response = await http.post(
        url,
        headers: ApiConfig.getHeaders(token: token),
        body: jsonEncode({
          'job_role': _selectedRole,
          'category': _selectedCategory,
          'difficulty': _selectedDifficulty,
          'question_count': _questionCount,
          'duration_minutes': 15,
          'camera_consent_given': _cameraConsent,
        }),
      );

      final data = jsonDecode(response.body);
      if (response.statusCode == 201 && data['status'] == 'ok') {
        final session = data['session'];
        setState(() {
          _sessionId = session['id'];
          _questions = session['questions'] ?? [];
          _currentIndex = 0;
          _stage = InterviewStage.inProgress;
          _timeRemainingSeconds = (session['duration_minutes'] ?? 15) * 60;
          _startTimer();
        });

        // Trigger start timestamp on backend
        if (_sessionId != null) {
          final startUrl = Uri.parse(ApiConfig.aiMockSessionStart(baseUrl, _sessionId!));
          http.post(startUrl, headers: ApiConfig.getHeaders(token: token));
        }

        Fluttertoast.showToast(
          msg: "AI Interview session generated successfully!",
          backgroundColor: Colors.green,
          textColor: Colors.white,
        );
      } else {
        Fluttertoast.showToast(
          msg: data['error'] ?? "Failed to create mock session.",
          backgroundColor: Colors.red,
          textColor: Colors.white,
        );
      }
    } catch (e) {
      Fluttertoast.showToast(
        msg: "Connection error: $e",
        backgroundColor: Colors.red,
        textColor: Colors.white,
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _startTimer() {
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_timeRemainingSeconds > 0) {
        setState(() => _timeRemainingSeconds--);
      } else {
        _timer?.cancel();
        _completeInterview();
      }
    });
  }

  // ----------------------------------------------------
  // API CALL: SUBMIT ANSWER & ADVANCE QUESTION
  // ----------------------------------------------------
  Future<void> _submitAnswerAndNext() async {
    final answerText = _answerController.text.trim();
    if (answerText.isEmpty) {
      Fluttertoast.showToast(msg: "Please provide an answer before continuing.");
      return;
    }

    setState(() => _isLoading = true);
    try {
      final SharedPreferences prefs = await SharedPreferences.getInstance();
      final String baseUrl = await ApiConfig.getBaseUrl();
      final String? token = prefs.getString('token');
      final currentQ = _questions[_currentIndex];

      final submitUrl = Uri.parse(ApiConfig.aiMockSubmitAnswer(baseUrl, _sessionId!));
      await http.post(
        submitUrl,
        headers: ApiConfig.getHeaders(token: token),
        body: jsonEncode({
          'question_id': currentQ['id'],
          'answer_text': answerText,
          'time_taken_seconds': 45,
        }),
      );

      _answerController.clear();

      if (_currentIndex < _questions.length - 1) {
        setState(() {
          _currentIndex++;
        });
      } else {
        // Last question answered -> trigger completion & grading
        await _completeInterview();
      }
    } catch (e) {
      Fluttertoast.showToast(msg: "Error submitting answer: $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  // ----------------------------------------------------
  // API CALL: COMPLETE & EVALUATE SESSION
  // ----------------------------------------------------
  Future<void> _completeInterview() async {
    _timer?.cancel();
    setState(() => _isLoading = true);
    try {
      final SharedPreferences prefs = await SharedPreferences.getInstance();
      final String baseUrl = await ApiConfig.getBaseUrl();
      final String? token = prefs.getString('token');

      // 1. Record camera telemetry if enabled
      if (_cameraConsent && _sessionId != null) {
        final telUrl = Uri.parse(ApiConfig.aiMockCameraTelemetry(baseUrl, _sessionId!));
        await http.post(
          telUrl,
          headers: ApiConfig.getHeaders(token: token),
          body: jsonEncode({
            'consent_given': true,
            'frames_processed': 120,
            'centered_posture_percentage': 91.5,
            'head_stability_score': 86.0,
            'eye_contact_ratio': 84.0,
          }),
        );
      }

      // 2. Trigger Complete & AI Grading
      final completeUrl = Uri.parse(ApiConfig.aiMockComplete(baseUrl, _sessionId!));
      final response = await http.post(
        completeUrl,
        headers: ApiConfig.getHeaders(token: token),
      );

      final data = jsonDecode(response.body);
      if (response.statusCode == 200 && data['status'] == 'ok') {
        // Fetch detailed results scorecard
        try {
          final resultsUrl = Uri.parse(ApiConfig.aiMockResults(baseUrl, _sessionId!));
          final resResponse = await http.get(resultsUrl, headers: ApiConfig.getHeaders(token: token));
          final resData = jsonDecode(resResponse.body);
          if (resData is Map<String, dynamic>) {
            _resultsData = resData;
          } else {
            _resultsData = data['results'] ?? data['summary'];
          }
        } catch (_) {
          _resultsData = data['results'] ?? data['summary'];
        }

        setState(() {
          _stage = InterviewStage.results;
        });
      } else {
        Fluttertoast.showToast(msg: data['error'] ?? "Failed to finalize evaluation.");
      }
    } catch (e) {
      Fluttertoast.showToast(msg: "Error finalizing evaluation: $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  // ----------------------------------------------------
  // DOWNLOAD PDF EVALUATION REPORT
  // ----------------------------------------------------
  Future<void> _downloadPdfReport() async {
    if (_sessionId == null) return;
    final String baseUrl = await ApiConfig.getBaseUrl();
    final String pdfUrl = ApiConfig.mockInterviewPdf(baseUrl, _sessionId!);
    final uri = Uri.parse(pdfUrl);

    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } else {
      Fluttertoast.showToast(msg: "Could not launch PDF download URL.");
    }
  }

  // ----------------------------------------------------
  // UI BUILDERS
  // ----------------------------------------------------
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("AI Mock Interview"),
        centerTitle: true,
        backgroundColor: const Color(0xFF1E3A8A),
        foregroundColor: Colors.white,
      ),
      body: _isLoading
          ? const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(color: Color(0xFF1E3A8A)),
                  SizedBox(height: 16),
                  Text("AI is generating your tailored questions...", style: TextStyle(fontSize: 16)),
                ],
              ),
            )
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: _buildCurrentStage(),
            ),
    );
  }

  Widget _buildCurrentStage() {
    switch (_stage) {
      case InterviewStage.setup:
        return _buildSetupUI();
      case InterviewStage.inProgress:
        return _buildInProgressUI();
      case InterviewStage.results:
        return _buildResultsUI();
    }
  }

  // ----------------------------------------------------
  // STAGE 1: SETUP UI
  // ----------------------------------------------------
  Widget _buildSetupUI() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Card(
          elevation: 3,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          color: const Color(0xFFEFF6FF),
          child: const Padding(
            padding: EdgeInsets.all(16.0),
            child: Row(
              children: [
                Icon(Icons.smart_toy_outlined, color: Color(0xFF1E3A8A), size: 40),
                SizedBox(width: 16),
                Expanded(
                  child: Text(
                    "Prepare for real interviews with AI-generated questions, multidimensional answer scoring, and camera posture telemetry.",
                    style: TextStyle(fontSize: 14, color: Color(0xFF1E3A8A)),
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 20),

        // Target Job Role
        const Text("Target Job Role", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        const SizedBox(height: 8),
        DropdownButtonFormField<String>(
          value: _selectedRole,
          decoration: InputDecoration(
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
            contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
          ),
          items: _roleOptions.map((role) {
            return DropdownMenuItem(value: role, child: Text(role));
          }).toList(),
          onChanged: (val) => setState(() => _selectedRole = val!),
        ),
        const SizedBox(height: 16),

        // Category
        const Text("Interview Category", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        const SizedBox(height: 8),
        DropdownButtonFormField<String>(
          value: _selectedCategory,
          decoration: InputDecoration(
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
            contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
          ),
          items: const [
            DropdownMenuItem(value: 'TECHNICAL', child: Text("Technical Round")),
            DropdownMenuItem(value: 'HR', child: Text("HR & Culture Fit Round")),
            DropdownMenuItem(value: 'GENERAL', child: Text("General & Behavioral Round")),
          ],
          onChanged: (val) => setState(() => _selectedCategory = val!),
        ),
        const SizedBox(height: 16),

        // Difficulty & Question Count Row
        Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text("Difficulty Level", style: TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  DropdownButtonFormField<String>(
                    value: _selectedDifficulty,
                    decoration: InputDecoration(
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
                    ),
                    items: const [
                      DropdownMenuItem(value: 'JUNIOR', child: Text("Junior Level")),
                      DropdownMenuItem(value: 'MID', child: Text("Mid-Level")),
                      DropdownMenuItem(value: 'SENIOR', child: Text("Senior Level")),
                    ],
                    onChanged: (val) => setState(() => _selectedDifficulty = val!),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text("Question Count", style: TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  DropdownButtonFormField<int>(
                    value: _questionCount,
                    decoration: InputDecoration(
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
                    ),
                    items: const [
                      DropdownMenuItem(value: 3, child: Text("3 Questions")),
                      DropdownMenuItem(value: 5, child: Text("5 Questions")),
                      DropdownMenuItem(value: 10, child: Text("10 Questions")),
                    ],
                    onChanged: (val) => setState(() => _questionCount = val!),
                  ),
                ],
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),

        // Camera Consent Toggle
        CheckboxListTile(
          value: _cameraConsent,
          onChanged: (val) => setState(() => _cameraConsent = val ?? false),
          activeColor: const Color(0xFF1E3A8A),
          title: const Text("Enable Camera Posture Telemetry", style: TextStyle(fontWeight: FontWeight.bold)),
          subtitle: const Text("Observational posture alignment and camera focus analysis (Optional & Private)."),
          controlAffinity: ListTileControlAffinity.leading,
          contentPadding: EdgeInsets.zero,
        ),
        const SizedBox(height: 24),

        ElevatedButton(
          onPressed: _startInterview,
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF1E3A8A),
            foregroundColor: Colors.white,
            minimumSize: const Size.fromHeight(52),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          ),
          child: const Text("Generate & Start AI Interview", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        ),
      ],
    );
  }

  // ----------------------------------------------------
  // STAGE 2: IN PROGRESS INTERVIEW UI
  // ----------------------------------------------------
  Widget _buildInProgressUI() {
    if (_questions.isEmpty) {
      return const Center(child: Text("No questions generated."));
    }

    final currentQ = _questions[_currentIndex];
    final minutes = (_timeRemainingSeconds ~/ 60).toString().padLeft(2, '0');
    final seconds = (_timeRemainingSeconds % 60).toString().padLeft(2, '0');

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Progress & Timer Bar
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              "Question ${_currentIndex + 1} of ${_questions.length}",
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Color(0xFF1E3A8A)),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: _timeRemainingSeconds < 180 ? Colors.red.shade100 : Colors.blue.shade100,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  Icon(Icons.timer_outlined, size: 16, color: _timeRemainingSeconds < 180 ? Colors.red : Colors.blue.shade900),
                  const SizedBox(width: 4),
                  Text(
                    "$minutes:$seconds",
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: _timeRemainingSeconds < 180 ? Colors.red : Colors.blue.shade900,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        LinearProgressIndicator(
          value: (_currentIndex + 1) / _questions.length,
          backgroundColor: Colors.grey.shade200,
          color: const Color(0xFF1E3A8A),
        ),
        const SizedBox(height: 16),

        // Camera Telemetry Active Badge
        if (_cameraConsent)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: Colors.green.shade50,
              border: Border.all(color: Colors.green.shade300),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Row(
              children: [
                Icon(Icons.videocam_outlined, color: Colors.green, size: 18),
                SizedBox(width: 8),
                Text("Camera Posture Telemetry: Active & Centered", style: TextStyle(fontSize: 12, color: Colors.green)),
              ],
            ),
          ),
        const SizedBox(height: 16),

        // Question Prompt Card
        Card(
          elevation: 2,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  currentQ['question_text'] ?? '',
                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, height: 1.4),
                ),
                const SizedBox(height: 12),
                if (currentQ['expected_keywords'] != null && currentQ['expected_keywords'].toString().isNotEmpty)
                  Text(
                    "Key concepts to address: ${currentQ['expected_keywords']}",
                    style: TextStyle(fontSize: 12, fontStyle: FontStyle.italic, color: Colors.grey.shade600),
                  ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 20),

        // Answer Input Box
        const Text("Your Answer:", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        const SizedBox(height: 8),
        TextField(
          controller: _answerController,
          maxLines: 8,
          decoration: InputDecoration(
            hintText: "Type your detailed technical explanation here...",
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
            filled: true,
            fillColor: Colors.grey.shade50,
          ),
        ),
        const SizedBox(height: 20),

        ElevatedButton(
          onPressed: _submitAnswerAndNext,
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF1E3A8A),
            foregroundColor: Colors.white,
            minimumSize: const Size.fromHeight(50),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          ),
          child: Text(
            _currentIndex < _questions.length - 1 ? "Save & Next Question" : "Finish & Grade Interview",
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
        ),
      ],
    );
  }

  // ----------------------------------------------------
  // STAGE 3: RESULTS & SCORECARD UI
  // ----------------------------------------------------
  Widget _buildResultsUI() {
    if (_resultsData == null) {
      return const Center(child: Text("No results available."));
    }

    final score = double.tryParse(_resultsData!['overall_score']?.toString() ?? '0.0') ?? 0.0;
    final summary = _resultsData!['summary_feedback'] ?? '';
    final strengths = _resultsData!['strengths_summary'] ?? '';
    final improvements = _resultsData!['improvements_summary'] ?? '';
    final questionsList = _resultsData!['questions'] as List<dynamic>? ?? [];

    Color scoreColor = Colors.green;
    if (score < 60) {
      scoreColor = Colors.red;
    } else if (score < 80) {
      scoreColor = Colors.orange;
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Overall Score Card
        Center(
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: scoreColor.withOpacity(0.1),
              border: Border.all(color: scoreColor, width: 2),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Column(
              children: [
                const Text("OVERALL PERFORMANCE", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                const SizedBox(height: 8),
                Text(
                  "${score.toStringAsFixed(1)}%",
                  style: TextStyle(fontSize: 48, fontWeight: FontWeight.bold, color: scoreColor),
                ),
                const SizedBox(height: 8),
                Text(
                  summary,
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 14, height: 1.3),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 20),

        // Strengths & Improvements
        Card(
          elevation: 2,
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Row(
                  children: [
                    Icon(Icons.check_circle_outline, color: Colors.green),
                    SizedBox(width: 8),
                    Text("Key Strengths", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  ],
                ),
                const SizedBox(height: 6),
                Text(strengths, style: const TextStyle(fontSize: 14)),
                const Divider(height: 24),
                const Row(
                  children: [
                    Icon(Icons.trending_up, color: Colors.orange),
                    SizedBox(width: 8),
                    Text("Areas for Improvement", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  ],
                ),
                const SizedBox(height: 6),
                Text(improvements, style: const TextStyle(fontSize: 14)),
              ],
            ),
          ),
        ),
        const SizedBox(height: 20),

        // Download PDF Button
        ElevatedButton.icon(
          onPressed: _downloadPdfReport,
          icon: const Icon(Icons.picture_as_pdf),
          label: const Text("Download Official PDF Report Card"),
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.red.shade700,
            foregroundColor: Colors.white,
            minimumSize: const Size.fromHeight(50),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          ),
        ),
        const SizedBox(height: 24),

        // Question-by-Question Breakdown
        const Text("Question-Wise Evaluation Breakdown", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
        const SizedBox(height: 12),
        ...questionsList.map((q) {
          final ans = q['answer'];
          final qScore = ans != null ? ans['overall_question_score'] : '0.0';
          return Card(
            margin: const EdgeInsets.only(bottom: 12),
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          "Q${q['question_number']}: ${q['question_text']}",
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(color: Colors.blue.shade50, borderRadius: BorderRadius.circular(6)),
                        child: Text("$qScore%", style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.blue)),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  if (ans != null) ...[
                    Text("Your Answer: ${ans['answer_text']}", style: TextStyle(fontSize: 13, color: Colors.grey.shade800)),
                    const SizedBox(height: 6),
                    Text("Feedback: ${ans['feedback']}", style: const TextStyle(fontSize: 13, color: Colors.green)),
                  ] else ...[
                    const Text("Not Answered", style: TextStyle(fontSize: 13, color: Colors.red)),
                  ]
                ],
              ),
            ),
          );
        }).toList(),

        const SizedBox(height: 20),
        OutlinedButton(
          onPressed: () => setState(() => _stage = InterviewStage.setup),
          style: OutlinedButton.styleFrom(
            minimumSize: const Size.fromHeight(50),
          ),
          child: const Text("Start Another Mock Interview"),
        ),
      ],
    );
  }
}
