import 'package:flutter/material.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'models/message.dart';
import 'models/book_details.dart';
import 'models/cart_item.dart';
import 'package:file_picker/file_picker.dart';

import 'widgets/cart_summary.dart';
import 'widgets/order_form.dart';
import 'widgets/book_card.dart';

import 'utils/form_controllers.dart';
import 'package:provider/provider.dart';
import '../../auth_provider.dart';

class Chatbot extends StatefulWidget {
  final String? userId;
  const Chatbot({Key? key, this.userId,}) : super(key: key);

  @override
  _ChatbotState createState() => _ChatbotState();
}

class _ChatbotState extends State<Chatbot> {
  final ScrollController _scrollController = ScrollController();
  bool isOpen = false;
  List<ChatMessage> messages = [];
  final TextEditingController _inputController = TextEditingController();
  bool isLoading = false;
  String? _selectedImage;

  List<CartItem> cartItems = [];
  bool showOrderForm = false;
  final _formKey = GlobalKey<FormState>();
  final Map<String, TextEditingController> _controllers = OrderFormControllers.controllers;

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
    _scrollToBottom();
  }

  void _scrollToBottom() {
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
      context,
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

  Future<void> _pickImage() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.image,
        allowMultiple: false,
      );

      if (result != null) {
        final bytes = result.files.first.bytes;
        if (bytes != null) {
          setState(() {
            _selectedImage = base64Encode(bytes);
            // Add image preview message
            messages.add(ChatMessage(
              content: 'Selected image for analysis',
              sender: 'user',
              type: 'image',
              imageData: _selectedImage,
            ));
          });
          _scrollToBottom();
        }
      }
    } catch (e) {
      debugLog('Error picking image: $e');
    }
  }

  Future<void> sendMessage(String message) async {
    setState(() {
      isLoading = true;
    });

    debugLog('Sending message: $message');

    try {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final userId = authProvider.userId;

      // Create a properly structured message
      final messageContent = {
        "type": _selectedImage != null ? "image" : "text",
        "content": message,
        "metadata": {
          "image": _selectedImage,
          "timestamp": DateTime.now().toIso8601String(),
        }
      };

      final messageHistory = messages.map((msg) => {
        'content': msg.content,
        'type': msg.type,
        'sender': msg.sender,
      }).toList();

      // Create the request body
      final requestBody = {
        'message': json.encode(messageContent),
        'messages': messageHistory,
        'metadata': {
          'user_id': userId,
          'image': _selectedImage,
        },
        'type': _selectedImage != null ? 'image' : 'text',
        'original_message': message,
      };

      debugLog('Sending request body: ${json.encode(requestBody)}');

      final response = await http.post(
        Uri.parse('http://localhost:8000/api/chatbot/chat'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode(requestBody),
      );

      debugLog('Response status code: ${response.statusCode}');
      debugLog('Response body: ${response.body}');

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        debugLog('Decoded data: $data');
        handleBotResponse(data);
        // Clear the selected image after sending
        setState(() {
          _selectedImage = null;
        });
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

  void handleBotResponse(Map<String, dynamic> data) {
  debugLog('Processing bot response: ${json.encode(data)}');

  final type = data['type'];
  final response = data['response'];

  // Helper function to clean text
  String cleanText(String text) {
    return text
        .replaceAll('â€™', "'")
        .replaceAll('â€œ', '"')
        .replaceAll('â€', '"')
        .replaceAll('donâ€™t', "don't");
  }

  switch (type) {
    case 'recommendation':
      if (response is Map<String, dynamic>) {
        // Display the recommendation message
        if (response['message'] != null) {
          addMessage(cleanText(response['message']), 'bot');
        }

        // Process the list of books
        if (response['books'] is List) {
          final books = response['books'] as List<dynamic>;
          debugLog('Processing ${books.length} book recommendations');

          for (var bookJson in books) {
            try {
              debugLog('Processing book: ${json.encode(bookJson)}');

              // Clean text fields in book data
              if (bookJson is Map<String, dynamic>) {
                bookJson['description'] = cleanText(bookJson['description'] ?? '');
                bookJson['title'] = cleanText(bookJson['title'] ?? '');
                bookJson['ReasonForRecommendation'] =
                    cleanText(bookJson['ReasonForRecommendation'] ?? '');
              }

              // Render the book card
              final book = BookDetails.fromJson(bookJson);
              setState(() {
                messages.add(ChatMessage(
                  content: json.encode(bookJson),
                  sender: 'bot',
                  type: 'book_recommendation',
                ));
              });
            } catch (e) {
              debugLog('Error processing book: $e');
            }
          }
        }
      }
      break;

    case 'damage_assessment':
      if (response is Map<String, dynamic> && response.containsKey('message')) {
        addMessage(response['message'], 'bot', 'damage_assessment');
      }
      break;

    case 'question':
      if (response is Map<String, dynamic> && response.containsKey('message')) {
        addMessage(response['message'], 'bot', type);
      } else if (response is String) {
        addMessage(response, 'bot', type);
      }
      break;

    case 'clarification':
      if (response is Map<String, dynamic> && response.containsKey('message')) {
        addMessage(response['message'], 'bot', type);
      } else if (response is String) {
        addMessage(response, 'bot', type);
      }
      break;

    case 'error':
      if (response is Map<String, dynamic> && response['message'] != null) {
        addMessage(cleanText(response['message']), 'bot', type);
      } else if (response is String) {
        addMessage(cleanText(response), 'bot', type);
      }
      break;

    case 'order_response':
      if (response is Map<String, dynamic>) {
        final message = response['message'] as String?;
        final orderDetails = response['order_details'];

        if (orderDetails is List) {
          // Format multiple orders
          final formattedOrders = orderDetails.map((order) => '''
    Order ID: ${order['order_id']}
    Title: ${order['title']}
    Price: \$${order['price'].toStringAsFixed(2)}
    Quantity: ${order['total_quantity']}
    Purchase Date: ${order['purchase_date']}
    Expected Delivery: ${order['expected_delivery']}
    ''').join('\n-------------------\n');

          addMessage(
            '${message ?? "Your Orders:"}\n\n$formattedOrders',
            'bot',
            'order_response'
          );
        } else if (orderDetails is Map<String, dynamic>) {
          // Format single order
          final order = orderDetails;
          final formattedOrder = '''
    Order ID: ${order['order_id']}
    Title: ${order['title']}
    Price: \$${order['price'].toStringAsFixed(2)}
    Quantity: ${order['total_quantity']}
    Purchase Date: ${order['purchase_date']}
    Expected Delivery: ${order['expected_delivery']}
    ''';

          addMessage(
            '${message ?? "Order Details:"}\n\n$formattedOrder',
            'bot',
            'order_response'
          );
        }
      }
      break;

    case 'greeting':
    case 'question':
    case 'general':
      if (response is String) {
        addMessage(cleanText(response), 'bot', type);
      }
      break;

    case 'order_confirmation':
      if (response is Map<String, dynamic>) {
        final message = cleanText('''Order Confirmation:
Order ID: ${response['order_id']}
Total Cost: \$${response['total_cost']}
Order Date: ${response['order_placed_on']}
Expected Delivery: ${response['expected_delivery']}
${response['message']}''');
        addMessage(message, 'bot', 'order_confirmation');
      }
      break;

    default:
      debugLog('Unhandled response type: $type');
      if (response is String) {
        addMessage(cleanText(response), 'bot', 'text');
      } else if (response is Map<String, dynamic> && response.containsKey('message')) {
        addMessage(response['message'], 'bot', 'text');
      } else {
        addMessage(
          cleanText(
              "I received your message but I'm not sure how to display the response. Can you try rephrasing your request?"),
          'bot',
          'error',
        );
      }
  }
  _scrollToBottom();
}


  Widget buildMessageBubble(ChatMessage msg) {
    if (msg.type == 'book_recommendation') {
      try {
        debugLog('Rendering book card from: ${msg.content}');
        final bookData = json.decode(msg.content) as Map<String, dynamic>;
        final book = BookDetails.fromJson(bookData);
        return Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: buildBookCardWidget(book),
        );
      } catch (e) {
        debugLog('Error rendering book card: $e');
        return Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.red.shade50,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              'Error displaying book details: $e',
              style: TextStyle(color: Colors.red),
            ),
          ),
        );
      }
    }

    if (msg.type == 'image' && msg.imageData != null) {
      return Align(
        alignment: msg.sender == 'user' ? Alignment.centerRight : Alignment.centerLeft,
        child: Container(
          margin: const EdgeInsets.symmetric(vertical: 4),
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: msg.sender == 'user' ? Colors.blue.shade100 : Colors.grey.shade100,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(msg.content),
              const SizedBox(height: 8),
              ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: Image.memory(
                  base64Decode(msg.imageData!),
                  height: 150,
                  width: 200,
                  fit: BoxFit.cover,
                ),
              ),
            ],
          ),
        ),
      );
    }

    // Handle bot messages
    if (msg.sender == 'bot') {
      String displayText = '';
      
      try {
        Map<String, dynamic> contentMap;
        
        // Parse content if it's a string
        if (msg.content is String) {
          contentMap = json.decode(msg.content as String);
        } else if (msg.content is Map) {
          contentMap = Map<String, dynamic>.from(msg.content as Map);
        } else {
          throw FormatException('Invalid message content format');
        }

        // Extract message from response
        if (contentMap.containsKey('response')) {
          final responseData = contentMap['response'];
          if (responseData is Map<String, dynamic> && responseData.containsKey('message')) {
            displayText = responseData['message'].toString();
          } else if (responseData is String) {
            displayText = responseData;
          }
        } else {
          displayText = contentMap.toString();
        }
      } catch (e) {
        debugPrint('Error parsing message content: $e');
        displayText = msg.content.toString();
      }

      return Align(
        alignment: Alignment.centerLeft,
        child: Container(
          margin: const EdgeInsets.symmetric(vertical: 4),
          padding: const EdgeInsets.all(12),
          constraints: BoxConstraints(
            maxWidth: MediaQuery.of(context).size.width * 0.7,
          ),
          decoration: BoxDecoration(
            color: Colors.grey.shade100,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(
            displayText,
            style: const TextStyle(fontSize: 14),
          ),
        ),
      );
    }

    // Default user message bubble
    return Align(
      alignment: msg.sender == 'user' ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        padding: const EdgeInsets.all(12),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.7,
        ),
        decoration: BoxDecoration(
          color: msg.sender == 'user' ? Colors.blue.shade100 : Colors.grey.shade100,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Text(
          msg.content,
          style: const TextStyle(fontSize: 14),
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
                if (messages.isEmpty) {
                  addMessage(
                    "Welcome! I'm BookWorm, your personal book assistant. How can I help you today?",
                    'bot',
                    'greeting'
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
              Expanded(
                child: ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.all(16),
                  itemCount: messages.length,
                  itemBuilder: (context, index) => buildMessageBubble(messages[index]),
                ),
              ),
              if (cartItems.isNotEmpty && !showOrderForm) buildCartSummaryWidget(),
              if (showOrderForm) buildOrderFormWidget(),
              Container(
                padding: const EdgeInsets.all(8.0),
                decoration: const BoxDecoration(
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
                    IconButton(
                      icon: const Icon(Icons.attach_file),
                      onPressed: _pickImage,
                      tooltip: 'Upload image for fraud/damage analysis',
                    ),
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

  @override
  void dispose() {
    _inputController.dispose();
    _scrollController.dispose();
    OrderFormControllers.dispose();
    super.dispose();
  }
}