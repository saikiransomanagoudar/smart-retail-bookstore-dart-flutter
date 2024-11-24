import 'dart:convert';
import 'dart:developer';
import 'package:http/http.dart' as http;
import 'package:flutter_dotenv/flutter_dotenv.dart';

class ClerkService {
  final String publishableKey = dotenv.env['CLERK_PUBLISHABLE_KEY'] ?? '';

  Future<Map<String, dynamic>> _postRequest(String endpoint, Map<String, dynamic> body) async {
    if (publishableKey.isEmpty) {
      throw Exception('Publishable key is missing. Check your .env.local file.');
    }

    log('Request to Clerk API: $endpoint');
    final response = await http.post(
      Uri.parse('https://api.clerk.dev/v1/$endpoint'),
      headers: {
        'Authorization': 'Bearer $publishableKey',
        'Content-Type': 'application/json',
      },
      body: jsonEncode(body),
    );

    log('Response: ${response.body}');
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      final error = jsonDecode(response.body);
      throw Exception('Error: ${error['message'] ?? response.body}');
    }
  }

  Future<Map<String, dynamic>?> signIn(String email, String password) {
    return _postRequest('sign_in_attempts', {
      'email_address': email,
      'password': password,
    });
  }

  Future<Map<String, dynamic>?> signUp(String email, String password) {
    return _postRequest('sign_up_attempts', {
      'email_address': email,
      'password': password,
    });
  }
}
