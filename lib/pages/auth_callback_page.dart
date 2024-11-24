// lib/pages/auth_callback_page.dart
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class AuthCallbackPage extends StatefulWidget {
  final VoidCallback onComplete;

  const AuthCallbackPage({Key? key, required this.onComplete}) : super(key: key);

  @override
  _AuthCallbackPageState createState() => _AuthCallbackPageState();
}

class _AuthCallbackPageState extends State<AuthCallbackPage> {
  @override
  void initState() {
    super.initState();
    _handleCallback();
  }

  Future<void> _handleCallback() async {
    try {
      // Add a small delay to ensure the state is captured
      await Future.delayed(const Duration(milliseconds: 500));
      
      // Get the current context and check if mounted
      if (!mounted) return;
      
      // Complete the authentication flow
      widget.onComplete();
      
    } catch (e) {
      print('Error in auth callback: $e');
      if (!mounted) return;
      context.go('/login'); // Redirect to login on error
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Colors.blue, Colors.green, Colors.teal],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: const Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CircularProgressIndicator(
                color: Colors.white,
              ),
              SizedBox(height: 16),
              Text(
                'Completing authentication...',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}