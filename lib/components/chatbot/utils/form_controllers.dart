import 'package:flutter/material.dart';

class OrderFormControllers {
  static final Map<String, TextEditingController> controllers = {
    'name': TextEditingController(),
    'street': TextEditingController(),
    'city': TextEditingController(),
    'state': TextEditingController(),
    'zip_code': TextEditingController(),
    'cardNumber': TextEditingController(),
    'expiryDate': TextEditingController(),
    'cvv': TextEditingController(),
  };

  static void dispose() {
    controllers.forEach((_, controller) => controller.dispose());
  }
}