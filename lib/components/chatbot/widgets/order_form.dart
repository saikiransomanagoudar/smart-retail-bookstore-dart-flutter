import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../models/cart_item.dart';
import '../utils/form_controllers.dart';

Widget buildOrderForm(
  GlobalKey<FormState> formKey,
  Map<String, TextEditingController> controllers,
  List<CartItem> cartItems,
  bool showOrderForm,
  Function(bool) setShowOrderForm,
  Function(String, String, String) addMessage,
) {
  return Expanded(
    child: SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Order Details',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: controllers['name'],
                decoration: const InputDecoration(
                  labelText: 'Full Name',
                  border: OutlineInputBorder(),
                ),
                validator: (value) =>
                    value?.isEmpty ?? true ? 'Please enter your name' : null,
              ),
              const SizedBox(height: 16),
              const Text(
                'Shipping Address',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              ...['street', 'city', 'state', 'zip_code'].map((field) => Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: TextFormField(
                      controller: controllers[field],
                      decoration: InputDecoration(
                        labelText: field
                            .split('_')
                            .map((word) =>
                                word[0].toUpperCase() + word.substring(1))
                            .join(' '),
                        border: const OutlineInputBorder(),
                      ),
                      validator: (value) =>
                          value?.isEmpty ?? true ? 'This field is required' : null,
                    ),
                  )),
              const SizedBox(height: 16),
              const Text(
                'Payment Information',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              TextFormField(
                controller: controllers['cardNumber'],
                decoration: const InputDecoration(
                  labelText: 'Card Number',
                  border: OutlineInputBorder(),
                ),
                validator: (value) => value?.length != 16
                    ? 'Please enter a valid 16-digit card number'
                    : null,
                keyboardType: TextInputType.number,
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      controller: controllers['expiryDate'],
                      decoration: const InputDecoration(
                        labelText: 'MM/YY',
                        border: OutlineInputBorder(),
                      ),
                      validator: (value) => !RegExp(r'^\d\d/\d\d$')
                              .hasMatch(value ?? '')
                          ? 'Use MM/YY format'
                          : null,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: TextFormField(
                      controller: controllers['cvv'],
                      decoration: const InputDecoration(
                        labelText: 'CVV',
                        border: OutlineInputBorder(),
                      ),
                      validator: (value) =>
                          value?.length != 3 ? 'Enter 3-digit CVV' : null,
                      keyboardType: TextInputType.number,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  TextButton(
                    onPressed: () => setShowOrderForm(false),
                    child: const Text('Cancel'),
                  ),
                  ElevatedButton(
                    onPressed: () {
                      if (formKey.currentState?.validate() ?? false) {
                        submitOrder(
                          cartItems,
                          controllers,
                          setShowOrderForm,
                          addMessage,
                        );
                      }
                    },
                    child: const Text('Submit Order'),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    ),
  );
}

Future<void> submitOrder(
  List<CartItem> cartItems,
  Map<String, TextEditingController> controllers,
  Function(bool) setShowOrderForm,
  Function(String, String, String) addMessage,
) async {
  final orderData = {
    'user_id': '1',
    'address': {
      'street': controllers['street']?.text,
      'city': controllers['city']?.text,
      'state': controllers['state']?.text,
      'zip_code': controllers['zip_code']?.text,
    },
    'cardNumber': controllers['cardNumber']?.text,
    'expiryDate': controllers['expiryDate']?.text,
    'cvv': controllers['cvv']?.text,
  };

  try {
    final response = await http.post(
      Uri.parse('http://localhost:64535/place-order'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'order_data': cartItems
            .map((item) => {
                  'id': item.id,
                  'title': item.title,
                  'price': item.price,
                  'quantity': item.quantity,
                })
            .toList(),
        'user_details': orderData,
      }),
    );

    if (response.statusCode == 200) {
      setShowOrderForm(false);
      addMessage('Order placed successfully! Order ID-4321', 'bot', 'order_confirmation');
    } else {
      addMessage('Order placed successfully! Order ID-4321.', 'bot', 'error');
    }
  } catch (e) {
    addMessage('Error placing order: $e', 'bot', 'error');
  }
}
