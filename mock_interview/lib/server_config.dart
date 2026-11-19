import 'package:flutter/material.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'config/api_config.dart';
import 'login.dart';

class ServerConfigPage extends StatefulWidget {
  const ServerConfigPage({super.key, required this.title});

  final String title;

  @override
  State<ServerConfigPage> createState() => _ServerConfigPageState();
}

class _ServerConfigPageState extends State<ServerConfigPage> {
  final TextEditingController _textController = TextEditingController();
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _textController.text = ApiConfig.productionBaseUrl;
    _checkSavedSession();
  }

  Future<void> _checkSavedSession() async {
    final prefs = await SharedPreferences.getInstance();
    final savedUrl = prefs.getString('base_api_url') ?? prefs.getString('url');
    if (savedUrl != null && savedUrl.isNotEmpty) {
      _textController.text = savedUrl;
    }
  }

  static const Color primaryPurple = Color(0xFF6C5CE7);
  static const Color secondaryPurple = Color(0xFF272366);
  static const Color backgroundColor = Color(0xFFF8F9FF);
  static const Color surfaceColor = Colors.white;
  static const Color textPrimary = Color(0xFF2D3436);
  static const Color textSecondary = Color(0xFF636E72);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: backgroundColor,
      appBar: AppBar(
        title: Text(widget.title),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.settings_ethernet_rounded, size: 64, color: primaryPurple),
              const SizedBox(height: 16),
              const Text(
                "Developer Server Configuration",
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: textPrimary),
              ),
              const SizedBox(height: 8),
              const Text(
                "Modify backend endpoint for local testing or debugging",
                style: TextStyle(fontSize: 14, color: textSecondary),
              ),
              const SizedBox(height: 24),
              TextField(
                controller: _textController,
                decoration: InputDecoration(
                  labelText: "Backend Host URL",
                  prefixIcon: const Icon(Icons.link),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  filled: true,
                  fillColor: surfaceColor,
                ),
              ),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: primaryPurple,
                  foregroundColor: Colors.white,
                  minimumSize: const Size.fromHeight(50),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                onPressed: _saveAndConnect,
                icon: const Icon(Icons.check_circle_outline),
                label: const Text("Save & Connect"),
              ),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size.fromHeight(50),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                onPressed: () {
                  _textController.text = ApiConfig.productionBaseUrl;
                  _saveAndConnect();
                },
                icon: const Icon(Icons.cloud_done_outlined),
                label: const Text("Reset to Production Cloud"),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _saveAndConnect() async {
    String input = _textController.text.trim();
    if (input.isEmpty) {
      input = ApiConfig.productionBaseUrl;
    }
    if (!input.startsWith('http://') && !input.startsWith('https://')) {
      input = 'http://$input:8000';
    }
    if (input.endsWith('/')) {
      input = input.substring(0, input.length - 1);
    }

    setState(() => _isLoading = true);

    try {
      SharedPreferences sh = await SharedPreferences.getInstance();
      await sh.setString('base_api_url', input);
      await sh.setString('url', '$input/myapp');
      await sh.setString('img_url', input);
      await sh.setString('img_url2', '$input/media/');

      Fluttertoast.showToast(msg: 'Server configured: $input', backgroundColor: Colors.green);

      if (mounted) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (context) => const MyLoginPage(title: 'AI Mock Interview')),
        );
      }
    } catch (e) {
      Fluttertoast.showToast(msg: 'Error: $e', backgroundColor: Colors.red);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }
}
