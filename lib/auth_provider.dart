import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class AuthProvider extends ChangeNotifier {
  bool _isSignedIn = false;
  String? _userId; // User ID is now a string

  bool get isSignedIn => _isSignedIn;
  String? get userId => _userId;

  /// Load authentication state from SharedPreferences
  Future<void> loadAuthState() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    _isSignedIn = prefs.getBool('isSignedIn') ?? false;
    _userId = prefs.getString('userId');
    notifyListeners();
  }

  /// Sign in the user and store the userId
  Future<void> signIn(String userId) async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    await prefs.setBool('isSignedIn', true);
    await prefs.setString('userId', userId); // Save userId as a string
    _isSignedIn = true;
    _userId = userId;
    notifyListeners();
  }

  /// Sign out the user and clear authentication data
  Future<void> signOut() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    await prefs.setBool('isSignedIn', false);
    await prefs.remove('userId'); // Remove userId
    _isSignedIn = false;
    _userId = null;
    notifyListeners();
  }
}
