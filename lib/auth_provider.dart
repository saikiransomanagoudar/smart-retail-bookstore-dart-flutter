import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class AuthProvider extends ChangeNotifier {
  bool _isSignedIn = false;

  bool get isSignedIn => _isSignedIn;

  Future<void> loadAuthState() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    _isSignedIn = prefs.getBool('isSignedIn') ?? false;
    notifyListeners();
  }

  Future<void> signIn() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    await prefs.setBool('isSignedIn', true);
    _isSignedIn = true;
    notifyListeners();
  }

  Future<void> signOut() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    await prefs.setBool('isSignedIn', false);
    _isSignedIn = false;
    notifyListeners();
  }
}
