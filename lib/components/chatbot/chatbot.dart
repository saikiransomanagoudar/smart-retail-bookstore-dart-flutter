import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;

import 'models/message.dart';
import 'models/book_details.dart';
import 'models/cart_item.dart';

import 'widgets/cart_summary.dart';
import 'widgets/order_form.dart';
import 'widgets/book_card.dart';

import 'utils/form_controllers.dart';

class Chatbot extends StatefulWidget {
  const Chatbot({Key? key}) : super(key: key);

  @override
  _ChatbotState createState() => _ChatbotState();
}

class _ChatbotState extends State<Chatbot> {
  final ScrollController _scrollController = ScrollController();
  bool isOpen = false;
  List<ChatMessage> messages = [];
  final TextEditingController _inputController = TextEditingController();
  bool isLoading = false;

  List<CartItem> cartItems = [];
  bool showOrderForm = false;
  final _formKey = GlobalKey<FormState>();
  final Map<String, TextEditingController> _controllers = OrderFormControllers.controllers;

  // Add cart total calculation
  double get cartTotal => cartItems.fold(
        0,
        (sum, item) => sum + (item.price * item.quantity),
      );

  void debugLog(String message) {
    print('ChatBot Debug: $message');
  }

  void addMessage(String content, String sender, [String type = 'text']) {
    setState(() {
      messages.add(ChatMessage(content: content, sender: sender, type: type));
    });
    _scrollController.animateTo(
      _scrollController.position.maxScrollExtent,
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeOut,
    );
  }

  Widget buildCartSummaryWidget() {
    return buildCartSummary(
      cartItems,
      cartTotal,
      showOrderForm,
      (value) => setState(() => showOrderForm = value),
    );
  }

  Widget buildOrderFormWidget() {
    return buildOrderForm(
      _formKey,
      _controllers,
      cartItems,
      showOrderForm,
      (value) => setState(() => showOrderForm = value),
      addMessage,
    );
  }

  Widget buildBookCardWidget(BookDetails book) {
    return buildBookCard(
      book,
      (b) => addToCart(b),
    );
  }


  Future<void> sendMessage(String message) async {
    setState(() {
      isLoading = true;
    });

    debugLog('Sending message: $message');

    try {
      // Convert current messages to format backend expects
      final messageHistory = messages.map((msg) => {
        'content': json.encode({
          'original_message': msg.content,
          'type': msg.type,
          'metadata': {}
        }),
        'role': msg.sender
      }).toList();

      final response = await http.post(
        Uri.parse('http://localhost:8000/api/chatbot/chat'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'message': message,
          'messages': messageHistory  // Include conversation history
        }),
      );

      debugLog('Response status code: ${response.statusCode}');
      debugLog('Response body: ${response.body}');

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        debugLog('Decoded data: $data');
        handleBotResponse(data);
      }
    } catch (e) {
      debugLog('Error communicating with chatbot: $e');
      addMessage(
        "I'm sorry, I'm having trouble processing your request. Please try again later.",
        "bot",
      );
    } finally {
      setState(() {
        isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!isOpen) {
      return Align(
        alignment: Alignment.bottomRight,
        child: Padding(
          padding: const EdgeInsets.only(right: 16, bottom: 16),
          child: FloatingActionButton(
            onPressed: () {
            setState(() {
              isOpen = true;
              // Add the greeting message when chatbot is opened
              if (messages.isEmpty) {
                addMessage(
                  "Welcome! I'm BookWorm, your personal book assistant. How can I help you today?",
                  'bot',
                );
              }
            });
          },
            child: const FaIcon(FontAwesomeIcons.robot),
            backgroundColor: Colors.blue,
          ),
        ),
      );
    }

    return Align(
      alignment: Alignment.bottomRight,
      child: Padding(
        padding: const EdgeInsets.only(right: 16, bottom: 16),
        child: Container(
          width: 400,
          height: 600,
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            boxShadow: [
              const BoxShadow(
                color: Colors.black26,
                blurRadius: 10,
                offset: Offset(0, 2),
              ),
            ],
          ),
          child: Column(
            children: [
              // Chat header
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: const BoxDecoration(
                  color: Colors.blue,
                  borderRadius: BorderRadius.vertical(top: Radius.circular(12)),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const FaIcon(FontAwesomeIcons.robot, color: Colors.white),
                    const Text(
                      'BookWorm',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.close, color: Colors.white),
                      onPressed: () => setState(() => isOpen = false),
                    ),
                  ],
                ),
              ),
              // Messages area
              Expanded(
                child: ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.all(16),
                  itemCount: messages.length,
                  itemBuilder: (context, index) {
                    final msg = messages[index];
                    if (msg.type == 'book_recommendation') {
                      try {
                        final bookData = json.decode(msg.content) as Map<String, dynamic>;
                        final book = BookDetails.fromJson(bookData);
                        return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          child: buildBookCardWidget(book),
                        );
                      } catch (e) {
                        debugLog('Error rendering book card: $e');
                        return const Text('Error displaying book details.');
                      }
                    }
                    return Align(
                      alignment: msg.sender == 'user'
                          ? Alignment.centerRight
                          : Alignment.centerLeft,
                      child: Container(
                        margin: const EdgeInsets.symmetric(vertical: 4),
                        padding: const EdgeInsets.all(12),
                        constraints: BoxConstraints(
                          maxWidth: MediaQuery.of(context).size.width * 0.7,
                        ),
                        decoration: BoxDecoration(
                          color: msg.sender == 'user'
                              ? Colors.blue.shade100
                              : Colors.grey.shade100,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          msg.content,
                          style: const TextStyle(fontSize: 14),
                        ),
                      ),
                    );
                  },
                ),
              ),
              // Cart summary if items in cart
              if (cartItems.isNotEmpty && !showOrderForm) buildCartSummaryWidget(),
              // Order form if showing
              if (showOrderForm) buildOrderFormWidget(),
              // Input area
              Container(
                padding: const EdgeInsets.all(8.0),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: const BorderRadius.vertical(bottom: Radius.circular(12)),
                  boxShadow: const [
                    BoxShadow(
                      color: Colors.black12,
                      blurRadius: 4,
                      offset: Offset(0, -2),
                    ),
                  ],
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _inputController,
                        decoration: InputDecoration(
                          hintText: 'Type your message...',
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(24),
                            borderSide: BorderSide.none,
                          ),
                          filled: true,
                          fillColor: Colors.grey.shade100,
                          contentPadding: const EdgeInsets.symmetric(
                            horizontal: 16,
                            vertical: 8,
                          ),
                        ),
                        onSubmitted: (value) {
                          if (value.trim().isNotEmpty) {
                            addMessage(value, 'user');
                            sendMessage(value);
                            _inputController.clear();
                          }
                        },
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      decoration: const BoxDecoration(
                        color: Colors.blue,
                        shape: BoxShape.circle,
                      ),
                      child: IconButton(
                        icon: isLoading
                            ? const SizedBox(
                                width: 24,
                                height: 24,
                                child: CircularProgressIndicator(
                                  color: Colors.white,
                                  strokeWidth: 2,
                                ),
                              )
                            : const Icon(Icons.send, color: Colors.white),
                        onPressed: isLoading
                            ? null
                            : () {
                                if (_inputController.text.trim().isNotEmpty) {
                                  final message = _inputController.text;
                                  _inputController.clear();
                                  addMessage(message, 'user');
                                  sendMessage(message);
                                }
                              },
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void addToCart(BookDetails book) {
    setState(() {
      final existingItem = cartItems.firstWhere(
        (item) => item.id == book.id,
        orElse: () => CartItem(
          id: book.id,
          title: book.title,
          price: book.price,
          imageUrl: book.imageUrl,
        ),
      );

      if (cartItems.contains(existingItem)) {
        existingItem.quantity++;
      } else {
        cartItems.add(existingItem);
      }

      addMessage(
        'Added "${book.title}" to cart. Current quantity: ${existingItem.quantity}',
        'bot',
        'cart_update',
      );
    });
  }

  void handleBotResponse(Map<String, dynamic> data) {
    final type = data['type'];
    final response = data['response'];

    switch (type) {
      case 'greeting':
      case 'clarification':
      case 'question':
      case 'order_question':
      case 'general':
      case 'order':
      case 'order_query':
      case 'error':
        if (response is String) addMessage(response, 'bot');
        break;

      case 'recommendation':
        if (response is List) {
          addMessage('Here are some book recommendations for you:', 'bot');
          for (var bookJson in response) {
            final book = BookDetails.fromJson(bookJson);
            setState(() {
              messages.add(ChatMessage(
                content: json.encode(book),
                sender: 'bot',
                type: 'book_recommendation',
              ));
            });
          }
        } else {
          addMessage(
            "I received a recommendation response, but I couldn't parse it. Please try again.",
            'bot',
          );
        }
        break;


      case 'order_confirmation':
        if (response is Map<String, dynamic>) {
          addMessage(
            '''Order Confirmation:
Order ID: ${response['order_id']}
Total Cost: \$${response['total_cost']}
Order Date: ${response['order_placed_on']}
Expected Delivery: ${response['expected_delivery']}
${response['message']}''',
            'bot',
            'order_confirmation',
          );
        }
        break;

      case 'order_info':
        if (response is Map<String, dynamic>) {
          final status = response['status'] ?? 'Processing';
          final deliveryDate = response['expected_delivery'] ?? 'Not available';

          addMessage(
            '''Order Details:
Order ID: ${response['order_id']}
Status: $status
Expected Delivery: $deliveryDate
Total Cost: \$${response['total_cost']}''',
            'bot',
            'order_info',
          );

          if (response['items'] is List) {
            addMessage('Order Items:', 'bot');
            for (var item in response['items']) {
              addMessage(
                '- ${item['title']} (Qty: ${item['quantity']}) - \$${item['price']}',
                'bot',
                'order_item',
              );
            }
          }
        }
        break;

      case 'system':
        addMessage(response, 'bot', 'system');
        break;

      default:
        if (response is String) {
          addMessage(response, 'bot');
        } else {
          addMessage(
            "I received your message but I'm not sure how to display the response. Can you try rephrasing your request?",
            'bot',
          );
        }
    }

    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  void dispose() {
    _inputController.dispose();
    _scrollController.dispose();
    OrderFormControllers.dispose();
    super.dispose();
  }
}