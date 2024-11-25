import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/user.dart';

class AuthService {
  static String get baseUrl {
    return 'http://localhost:8000/api';
  }

  // Sign Up
  static Future<Map<String, dynamic>> signUp(String email, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/signup'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'email': email,
          'password': password,
        }),
      );

      final data = json.decode(response.body);

      if (response.statusCode == 200) {
        // Handle successful registration
        return {
          'success': true,
          'access_token': data['access_token'],
          'user': data['user'],
          'message': 'Registration successful',
        };
      } else {
        // Handle failure
        return {
          'success': false,
          'message': data['detail'] ?? 'Registration failed',
        };
      }
    } catch (e) {
      return {
        'success': false,
        'message': 'An error occurred during registration: $e',
      };
    }
  }


  // Sign In
  static Future<Map<String, dynamic>> signIn(String email, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'email': email,
          'password': password,
        }),
      );

      final responseData = json.decode(response.body);

      if (response.statusCode == 200 && responseData['success'] == true) {
        // Successful login
        return {
          'success': true,
          'access_token': responseData['access_token'],
          'user': responseData['user'],
          'message': responseData['message'] ?? 'Login successful',
        };
      } else {
        // Failed login
        return {
          'success': false,
          'message': responseData['message'] ?? responseData['detail'] ?? 'Login failed',
        };
      }
    } catch (e) {
      // Handle unexpected errors
      return {
        'success': false,
        'message': 'An error occurred during login: $e',
      };
    }
  }


  // Save preferences
  static Future<void> savePreferences(String userId, Map<String, dynamic> preferences) async {
    final response = await http.post(
      Uri.parse('$baseUrl/recommendations/preferences'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'user_id': userId,
        ...preferences,
      }),
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to save preferences');
    }
  }

  static Future<void> initRecommendations(int userId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/recommendations/initial-recommendations'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'userId': userId}),
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to initialize recommendations');
    }
  }
}
