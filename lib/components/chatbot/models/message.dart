class ChatMessage {
  final String content;
  final String sender;
  final String type;

  ChatMessage({
    required this.content,
    required this.sender,
    this.type = 'text',
  });

  Map<String, dynamic> toJson() => {
    'content': content,
    'sender': sender,
    'type': type,
  };

  factory ChatMessage.fromJson(Map<String, dynamic> json) => ChatMessage(
    content: json['content'],
    sender: json['sender'],
    type: json['type'] ?? 'text',
  );
}