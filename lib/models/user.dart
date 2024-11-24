class User {
  final int userId;
  final String email;
  final String passwordHash;
  final DateTime? createdAt;

  User({
    required this.userId,
    required this.email,
    required this.passwordHash,
    this.createdAt,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      userId: json['user_id'],
      email: json['email'],
      passwordHash: json['password_hash'],
      createdAt: json['created_at'] != null 
          ? DateTime.parse(json['created_at']) 
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'user_id': userId,
      'email': email,
      'password_hash': passwordHash,
      'created_at': createdAt?.toIso8601String(),
    };
  }
}