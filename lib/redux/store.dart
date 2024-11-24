import 'package:flutter/material.dart';

class Store with ChangeNotifier {
  // Example state management code
  String _example = "Hello, Flutter!";
  String get example => _example;

  void updateExample(String newExample) {
    _example = newExample;
    notifyListeners();
  }
}
