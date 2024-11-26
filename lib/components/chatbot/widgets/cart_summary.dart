import 'package:flutter/material.dart';
import '../models/cart_item.dart';

Widget buildCartSummary(List<CartItem> cartItems,
  double cartTotal,
  bool showOrderForm,
  Function(bool) setShowOrderForm,) {
  if (cartItems.isEmpty) return SizedBox.shrink();

  return Container(
    margin: EdgeInsets.symmetric(vertical: 8),
    padding: EdgeInsets.all(12),
    decoration: BoxDecoration(
      color: Colors.blue.shade50,
      borderRadius: BorderRadius.circular(8),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Shopping Cart',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            fontSize: 16,
          ),
        ),
        SizedBox(height: 8),
        ...cartItems.map((item) => Padding(
          padding: EdgeInsets.symmetric(vertical: 4),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  '${item.title} (x${item.quantity})',
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              Text('\$${(item.price * item.quantity).toStringAsFixed(2)}'),
            ],
          ),
        )),
        Divider(),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Total:',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            Text(
              '\$${cartTotal.toStringAsFixed(2)}',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
          ],
        ),
        SizedBox(height: 12),
        Center(
          child: ElevatedButton(
            onPressed: () => setShowOrderForm(true),
            child: Text('Place Order'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.green,
              foregroundColor: Colors.white,
              padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
            ),
          ),
        ),
      ],
    ),
  );
}