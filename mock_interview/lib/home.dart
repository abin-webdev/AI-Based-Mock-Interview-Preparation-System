
import 'package:flutter/material.dart';
import 'package:mock_interview/review_company.dart';
import 'package:mock_interview/send_complaint.dart';
import 'package:mock_interview/view_applied_vacancy.dart';
import 'package:mock_interview/view_profile.dart';
import 'package:mock_interview/view_vacancy.dart';
import 'package:mock_interview/ai_mock_interview.dart';
import 'package:mock_interview/notifications_page.dart';
import 'package:mock_interview/view_reply.dart';
import 'package:mock_interview/services/api_client.dart';

import 'login.dart';
import 'send_feedback.dart';


void main() {
  runApp(const userHome());
}

class userHome extends StatelessWidget {
  const userHome({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Home Page Demo',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      home: const userHomePAge(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class userHomePAge extends StatefulWidget {
  const userHomePAge({super.key});

  @override
  State<userHomePAge> createState() => _HomePageState();
}

class _HomePageState extends State<userHomePAge> {
  String _displayName = "Candidate";

  @override
  void initState() {
    super.initState();
    _loadUserHeader();
  }

  Future<void> _loadUserHeader() async {
    final name = await ApiClient().getUserName();
    if (name != null && name.isNotEmpty) {
      setState(() => _displayName = name);
    }
  }

  Future<void> _handleLogout() async {
    await ApiClient().clearAuthSession();
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
    return Scaffold(
      appBar: AppBar(
        title: const Text('Candidate Portal'),
        centerTitle: true,
        backgroundColor: Theme.of(context).colorScheme.primary,
        foregroundColor: Colors.white,
        elevation: 4,
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications_outlined),
            tooltip: "Notifications",
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => const NotificationsPage()),
              );
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 10),
            Text(
              'Hello, $_displayName!',
              style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              'Prepare for high-impact tech interviews with automated AI feedback.',
              style: TextStyle(fontSize: 14, color: Colors.grey[600]),
            ),
            const SizedBox(height: 25),
            ElevatedButton.icon(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const AIMockInterviewScreen()),
                );
              },
              icon: const Icon(Icons.psychology_outlined, color: Colors.white),
              label: const Text('AI Mock Interview Preparation', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              style: ElevatedButton.styleFrom(
                minimumSize: const Size.fromHeight(54),
                backgroundColor: const Color(0xFF1E3A8A),
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
            ),

            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => ViewProfile()),
                );
              },
              child: const Text('View Profile'),
              style: ElevatedButton.styleFrom(
                minimumSize: const Size.fromHeight(50),
              ),
            ),

            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => Send_complaintPage(title: '')),
                );
              },
              child: const Text('Send Complaint / Inquiry'),
              style: ElevatedButton.styleFrom(
                minimumSize: const Size.fromHeight(50),
              ),
            ),
            const SizedBox(height: 12),
            OutlinedButton(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const cstd_viewComplaintsPage(title: 'Complaint Replies')),
                );
              },
              child: const Text('View Complaint Replies'),
              style: OutlinedButton.styleFrom(
                minimumSize: const Size.fromHeight(46),
              ),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => SendFeedback()),
                );
              },
              child: const Text('Send feedback'),
              style: ElevatedButton.styleFrom(
                minimumSize: const Size.fromHeight(50),
              ),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => ViewVacancyPage(title: '',)),
                );
              },
              child: const Text('View Vacancy'),
              style: ElevatedButton.styleFrom(
                minimumSize: const Size.fromHeight(50),
              ),
            ),

                   const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => ViewAppliedVacancy()),
                );
              },
              child: const Text('View Applied Vacancy'),
              style: ElevatedButton.styleFrom(
                minimumSize: const Size.fromHeight(50),
              ),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => Sendreview( )),
                );
              },
              child: const Text('Review Company'),
              style: ElevatedButton.styleFrom(
                minimumSize: const Size.fromHeight(50),
              ),
            ),
            const SizedBox(height: 20),

            Center(
              child: TextButton.icon(
                onPressed: _handleLogout,
                icon: const Icon(Icons.logout, color: Colors.red),
                label: const Text(
                  'Log Out',
                  style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

