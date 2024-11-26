// lib/components/chatbot/chatbot.dart

import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;

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

  Future<void> sendMessage(String message) async {
    setState(() {
      isLoading = true;
    });

    try {
      final response = await http.post(
        Uri.parse('http://localhost:8000/api/chatbot/chat'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'message': message}),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        handleBotResponse(data);
      }
    } catch (e) {
      print('Error communicating with chatbot: $e');
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

    switch (type) {
      case 'greeting':
      case 'clarification':
      case 'question':
      case 'order_question':
        addMessage(response, 'bot');
        break;
      case 'recommendation':
        if (response is List) {
          addMessage('Based on our conversation, here are some book recommendations for you:', 'bot');
          addMessage(json.encode(response), 'bot', 'recommendations');
          addMessage('Would you like more recommendations or have any other questions?', 'bot');
        }
        break;
      // Add other cases as needed
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
                          style: TextStyle(fontSize: 14),
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