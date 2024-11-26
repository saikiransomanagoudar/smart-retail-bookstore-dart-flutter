import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;

import 'models/message.dart';
import 'models/book_details.dart' as book_details;

import 'models/cart_item.dart';
import 'widgets/book_card.dart';
import 'widgets/cart_summary.dart';
import 'widgets/order_form.dart';

import 'utils/form_controllers.dart';

class ChatMessage {
  final String content;
  final String sender;
  final String type;

  ChatMessage({
    required this.content,
    required this.sender,
    this.type = 'text',
  });
}

class Book {
  final String title;
  final String pages;
  final String releaseYear;
  final String price;
  final String reasonForRecommendation;
  final String imageUrl;

  Book({
    required this.title,
    required this.pages,
    required this.releaseYear,
    required this.price,
    required this.reasonForRecommendation,
    required this.imageUrl,
  });

  factory Book.fromJson(Map<String, dynamic> json) {
    return Book(
      title: json['title'] ?? 'Untitled',
      pages: json['pages']?.toString() ?? 'N/A',
      releaseYear: json['release_year']?.toString() ?? 'N/A',
      price: json['Price']?.toString() ?? 'N/A',
      reasonForRecommendation: json['ReasonForRecommendation'] ?? 'No recommendation reason provided.',
      imageUrl: json['image_url'] ?? 'https://via.placeholder.com/100x150?text=No+Image',
    );
  }
}

class Chatbot extends StatefulWidget {
  const Chatbot({Key? key}) : super(key: key);

  @override
  _ChatbotState createState() => _ChatbotState();
}

class _ChatbotState extends State<Chatbot> {
  bool isOpen = false;
  List<ChatMessage> messages = [];
  final TextEditingController _inputController = TextEditingController();
  bool isLoading = false;
  Map<String, dynamic> cart = {};
  bool isOrderProcessing = false;
  bool isOrderComplete = false;
  String? tempMessage;
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (messages.isEmpty) {
        setState(() {
          messages.add(
            ChatMessage(
              content: "Welcome! I'm BookWorm, your virtual assistant. I'm here to help you browse and find the perfect book for your collection. Ready to start exploring?",
              sender: "bot",
            ),
          );
        });
      }
    });
  }

  void debugLog(String message) {
    print('ChatBot Debug: $message');
  }

  // Update your sendMessage method
  Future<void> sendMessage(String message) async {
    setState(() {
      isLoading = true;
    });

    debugLog('Sending message: $message');

    try {
      final response = await http.post(
        Uri.parse('http://localhost:8000/api/chatbot/chat'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'message': message}),
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

  void addMessage(String content, String sender, [String type = 'text']) {
    setState(() {
      messages.add(ChatMessage(
        content: content,
        sender: sender,
        type: type,
      ));
    });
    
    Future.delayed(Duration(milliseconds: 100), () {
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    });
  }

  void handleBotResponse(Map<String, dynamic> data) {
    String type = data['type'];
    dynamic response = data['response'];
    
    print('Received response - Type: $type, Content: $response'); // Debug log

    switch (type) {
      case 'greeting':
      case 'clarification':
      case 'question':
      case 'order_question':
      case 'general':
      case 'order':
      case 'order_query':
      case 'error':
        // Handle text responses
        if (response is String) {
          addMessage(response, 'bot');
        }
        break;

      case 'recommendation':
        if (response is List) {
          // Handle book recommendations
          addMessage('Here are some book recommendations for you:', 'bot');
          for (var book in response) {
            try {
              Book bookObj = Book.fromJson(book);
              addMessage(
                '''Title: ${bookObj.title}
Price: \$${bookObj.price}
Reason: ${bookObj.reasonForRecommendation}''',
                'bot',
                'recommendation'
              );
            } catch (e) {
              print('Error parsing book: $e');
            }
          }
          addMessage('Would you like more recommendations or have questions about these books?', 'bot');
        } else if (response is String) {
          addMessage(response, 'bot');
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
            'order_confirmation'
          );
        } else if (response is String) {
          addMessage(response, 'bot');
        }
        break;

      case 'order_info':
        if (response is Map<String, dynamic>) {
          String status = response['status'] ?? 'Processing';
          String deliveryDate = response['expected_delivery'] ?? 'Not available';
          
          addMessage(
            '''Order Details:
Order ID: ${response['order_id']}
Status: $status
Expected Delivery: $deliveryDate
Total Cost: \$${response['total_cost']}''',
            'bot',
            'order_info'
          );
          
          if (response['items'] != null && response['items'] is List) {
            addMessage('Order Items:', 'bot');
            for (var item in response['items']) {
              addMessage(
                '- ${item['title']} (Qty: ${item['quantity']}) - \$${item['price']}',
                'bot',
                'order_item'
              );
            }
          }
        } else if (response is String) {
          addMessage(response, 'bot');
        }
        break;

      case 'system':
        // Handle system messages
        addMessage(response, 'bot', 'system');
        break;

      default:
        // Handle any unrecognized response types
        if (response is String) {
          addMessage(response, 'bot');
        } else {
          addMessage("I received your message but I'm not sure how to display the response. Can you try rephrasing your request?", 'bot');
        }
    }

    // Auto-scroll to the bottom after adding new messages
    Future.delayed(Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
}

Widget buildMessageContent(ChatMessage msg, BuildContext context) {
  switch (msg.type) {
    case 'recommendation':
    case 'order_info':
    case 'order_confirmation':
      return Container(
        padding: EdgeInsets.all(8),
        decoration: BoxDecoration(
          border: Border.all(color: Colors.blue.shade200),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Text(
          msg.content,
          style: TextStyle(fontSize: 14),
        ),
      );
    
    case 'order_item':
      return Container(
        padding: EdgeInsets.symmetric(vertical: 4, horizontal: 8),
        margin: EdgeInsets.only(left: 16),
        decoration: BoxDecoration(
          color: Colors.grey.shade50,
          border: Border.all(color: Colors.grey.shade200),
          borderRadius: BorderRadius.circular(4),
        ),
        child: Text(
          msg.content,
          style: TextStyle(fontSize: 13),
        ),
      );
    
    case 'system':
      return Container(
        padding: EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: Colors.yellow.shade50,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Text(
          msg.content,
          style: TextStyle(
            fontSize: 14,
            fontStyle: FontStyle.italic,
          ),
        ),
      );
    
    default:
      return Text(
        msg.content,
        style: TextStyle(fontSize: 14),
      );
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
            onPressed: () => setState(() => isOpen = true),
            child: FaIcon(FontAwesomeIcons.robot),
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
              BoxShadow(
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
                decoration: BoxDecoration(
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
                    debugLog('Building message at index $index: ${msg.content}');
                    
                    return Padding(
                      padding: EdgeInsets.only(
                        left: msg.sender == 'user' ? 50.0 : 0.0,
                        right: msg.sender == 'user' ? 0.0 : 50.0,
                        bottom: 8.0,
                      ),
                      child: Align(
                        alignment: msg.sender == 'user' 
                            ? Alignment.centerRight 
                            : Alignment.centerLeft,
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                          decoration: BoxDecoration(
                            color: msg.sender == 'user' 
                                ? Colors.blue.shade100 
                                : Colors.grey.shade100,
                            borderRadius: BorderRadius.circular(12),
                            border: msg.type == 'error' 
                                ? Border.all(color: Colors.red.shade200)
                                : null,
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                msg.content,
                                style: TextStyle(
                                  color: msg.type == 'error' 
                                      ? Colors.red.shade700
                                      : Colors.black87,
                                  fontSize: 14,
                                ),
                              ),
                              if (msg.type == 'recommendation' || msg.type == 'order_query')
                                Padding(
                                  padding: const EdgeInsets.only(top: 4),
                                  child: Text(
                                    msg.type.replaceAll('_', ' ').toUpperCase(),
                                    style: TextStyle(
                                      color: Colors.grey.shade600,
                                      fontSize: 10,
                                      fontWeight: FontWeight.w500,
                                    ),
                                  ),
                                ),
                            ],
                          ),
                        ),
                      ),
                    );
                  },
                ),
              ),      
              // Input area
              Container(
                padding: const EdgeInsets.all(8.0),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.vertical(bottom: Radius.circular(12)),
                  boxShadow: [
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
                          contentPadding: EdgeInsets.symmetric(
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
                      decoration: BoxDecoration(
                        color: Colors.blue,
                        shape: BoxShape.circle,
                      ),
                      child: IconButton(
                        icon: isLoading
                            ? SizedBox(
                                width: 24,
                                height: 24,
                                child: CircularProgressIndicator(
                                  color: Colors.white,
                                  strokeWidth: 2,
                                ),
                              )
                            : Icon(Icons.send, color: Colors.white),
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

  @override
  void dispose() {
    _inputController.dispose();
    _scrollController.dispose();
    super.dispose();
  }
}