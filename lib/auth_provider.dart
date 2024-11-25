import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class AuthProvider extends ChangeNotifier {
  bool _isSignedIn = false;
  String? _accessToken;
  String? _userId;
  String? _email;

  bool get isSignedIn => _isSignedIn;
  String? get accessToken => _accessToken;
  String? get userId => _userId;
  String? get email => _email;

  // Load authentication state from SharedPreferences
  Future<void> loadAuthState() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    _isSignedIn = prefs.getBool('isSignedIn') ?? false;
    _accessToken = prefs.getString('accessToken');
    _userId = prefs.getString('userId');
    _email = prefs.getString('email');
    notifyListeners();
  }

  // Save authentication state to SharedPreferences
  Future<void> signIn(String accessToken, String userId, String email) async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    await prefs.setBool('isSignedIn', true);
    await prefs.setString('accessToken', accessToken);
    await prefs.setString('userId', userId);
    await prefs.setString('email', email);
    _isSignedIn = true;
    _accessToken = accessToken;
    _userId = userId;
    _email = email;
    notifyListeners();
  }

  // Clear authentication state from SharedPreferences
  Future<void> signOut() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    await prefs.clear();
    _isSignedIn = false;
    _accessToken = null;
    _userId = null;
    _email = null;
    notifyListeners();
  }
}
