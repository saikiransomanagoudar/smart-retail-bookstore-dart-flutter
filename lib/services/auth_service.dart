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

      if (response.statusCode == 200 || response.statusCode == 201) {
        final data = json.decode(response.body);

        if (data['success'] == true) {
          return {
            'success': true,
            'message': data['message'],
          };
        } else {
          return {
            'success': false,
            'message': data['message'],
          };
        }
      } else {
        final error = json.decode(response.body);
        return {
          'success': false,
          'message': error['message'] ?? 'Registration failed',
        };
      }
    } catch (e) {
      return {
        'success': false,
        'message': 'An error occurred during registration',
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
        return {
          'success': true,
          'token': responseData['access_token'],
          'message': 'Login successful',
        };
      } else {
        return {
          'success': false,
          'message': responseData['detail'] ?? 'Login failed',
        };
      }
    } catch (e) {
      return {
        'success': false,
        'message': 'An error occurred: $e',
      };
    }
  }
}
