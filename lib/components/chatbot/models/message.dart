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