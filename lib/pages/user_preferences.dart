import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../auth_provider.dart';

class UserPreferencesPage extends StatefulWidget {
  @override
  _UserPreferencesPageState createState() => _UserPreferencesPageState();
}

class _UserPreferencesPageState extends State<UserPreferencesPage> {
  bool isSubmitting = false;

  Map<String, dynamic> formData = {
    "favorite_books": [],
    "favorite_authors": [],
    "preferred_genres": [],
    "themes_of_interest": [],
    "reading_level": "intermediate",
  };

  // Predefined lists
  final List<String> popularBooks = [
    "The Great Gatsby",
    "1984",
    "Pride and Prejudice",
    "To Kill a Mockingbird",
    "The Hobbit",
    "Harry Potter",
    "The Da Vinci Code",
    "The Alchemist",
    "The Catcher in the Rye",
    "Lord of the Rings",
    "The Hunger Games",
    "The Shining"
  ];

  final List<String> popularAuthors = [
    "J.K. Rowling",
    "Stephen King",
    "Jane Austen",
    "George R.R. Martin",
    "Agatha Christie",
    "Dan Brown",
    "Ernest Hemingway",
    "Mark Twain",
    "Charles Dickens",
    "Virginia Woolf",
    "George Orwell",
    "Paulo Coelho"
  ];

  final List<String> genres = [
    "Fiction",
    "Mystery",
    "Thriller",
    "Romance",
    "Science Fiction",
    "Fantasy",
    "Horror",
    "Historical Fiction",
    "Literary Fiction",
    "Young Adult",
    "Children's",
    "Biography"
  ];

  final List<String> themes = [
    "Adventure",
    "Love",
    "Family",
    "Friendship",
    "Coming of Age",
    "Good vs Evil",
    "Survival",
    "Redemption",
    "Identity",
    "Justice",
    "Power",
    "Nature"
  ];

  final List<Map<String, String>> readingLevels = [
    {"value": "beginner", "label": "Beginner"},
    {"value": "intermediate", "label": "Intermediate"},
    {"value": "advanced", "label": "Advanced"},
  ];

  void handleArraySelect(String field, String value) {
    setState(() {
      if (formData[field]!.contains(value)) {
        formData[field]!.remove(value);
      } else {
        formData[field]!.add(value);
      }
    });
  }

    Future<void> handleSubmit() async {
        setState(() {
            isSubmitting = true;
        });

        final authProvider = Provider.of<AuthProvider>(context, listen: false);
        final userId = authProvider.userId;

        try {
            if (authProvider.userId == null) {
            throw Exception("User ID is null. Ensure the user is signed in.");
            }

            print("Submitting preferences for user_id: ${authProvider.userId}");

            final response = await http.post(
            Uri.parse("http://localhost:8000/api/recommendations/preferences"),
            headers: {
                'Content-Type': 'application/json',
            },
            body: json.encode({
                "user_id": authProvider.userId,
                ...formData,
            }),
            );

            if (response.statusCode == 200) {
            Navigator.pushNamed(context, "/dashboard");
            } else {
            print("Error response: ${response.body}");
            throw Exception("Error saving preferences");
            }
        } catch (error) {
            print("Error saving preferences: $error");
        } finally {
            setState(() {
            isSubmitting = false;
            });
        }
    }



  Widget buildSelectableButton(String value, bool selected, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 4, vertical: 4),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: selected ? Colors.indigo[100] : Colors.white,
          border: Border.all(
            color: selected ? Colors.indigo : Colors.grey,
            width: 1,
          ),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Text(
          value,
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: selected ? Colors.indigo : Colors.black,
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFF4A148C), Color(0xFF7C4DFF)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: Column(
          children: [
            Expanded(
              child: SingleChildScrollView(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SizedBox(height: 50),
                      const Text(
                        "Welcome to BookStore!",
                        style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Colors.white),
                      ),
                      const SizedBox(height: 16),
                      const Text(
                        "Help us personalize your reading experience",
                        style: TextStyle(fontSize: 18, color: Colors.white),
                      ),
                      const SizedBox(height: 24),
                      // Favorite Books
                      buildSection("Select Your Favorite Books", popularBooks, "favorite_books"),
                      // Favorite Authors
                      buildSection("Select Your Favorite Authors", popularAuthors, "favorite_authors"),
                      // Preferred Genres
                      buildSection("Select Your Preferred Genres", genres, "preferred_genres"),
                      // Themes of Interest
                      buildSection("Select Themes That Interest You", themes, "themes_of_interest"),
                      // Reading Level
                      const Text(
                        "Select Your Reading Level",
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: readingLevels.map((level) {
                          return Expanded(
                            child: GestureDetector(
                              onTap: () {
                                setState(() {
                                  formData["reading_level"] = level["value"]!;
                                });
                              },
                              child: Container(
                                padding: const EdgeInsets.all(12.0),
                                margin: const EdgeInsets.symmetric(horizontal: 4.0),
                                decoration: BoxDecoration(
                                  color: formData["reading_level"] == level["value"]
                                      ? Colors.indigo
                                      : Colors.white,
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(color: Colors.indigo),
                                ),
                                child: Text(
                                  level["label"]!,
                                  textAlign: TextAlign.center,
                                  style: TextStyle(
                                    color: formData["reading_level"] == level["value"]
                                        ? Colors.white
                                        : Colors.black,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),
                            ),
                          );
                        }).toList(),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            Container(
              padding: const EdgeInsets.all(16.0),
              decoration: BoxDecoration(
                color: Colors.indigo[600],
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.2),
                    blurRadius: 8,
                    offset: const Offset(0, -2),
                  ),
                ],
              ),
              child: Center(
                child: ElevatedButton(
                  onPressed: isSubmitting ? null : handleSubmit,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blueAccent,
                    padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: isSubmitting
                      ? const CircularProgressIndicator(color: Colors.white)
                      : const Text(
                          "Continue to Dashboard",
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                        ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget buildSection(String title, List<String> items, String field) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 24),
        Text(
          title,
          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: items.map((item) {
            return buildSelectableButton(
              item,
              formData[field]!.contains(item),
              () => handleArraySelect(field, item),
            );
          }).toList(),
        ),
      ],
    );
  }
}
