import 'package:flutter/material.dart';
import '../components/navbar.dart';
import 'package:go_router/go_router.dart';



class HomePage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(60.0),
        child: Container(
          color: const Color(0xFF181818),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              // Logo Section
              GestureDetector(
                onTap: () {
                  print('Logo clicked');
                },
                child: Row(
                  children: [
                    Image.network(
                      "https://cdn-icons-png.flaticon.com/128/10433/10433049.png",
                      height: 40,
                    ),
                    const SizedBox(width: 8),
                    const Text(
                      "BookStore",
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                  ],
                ),
              ),

              // Auth Section (Sign In and Sign Up Buttons)
              Row(
                children: [
                  TextButton(
                    onPressed: () {
                      context.go('/login'); // Navigate to Login
                    },
                    child: const Text(
                      "Sign In",
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  ElevatedButton(
                    onPressed: () {
                      context.go('/signup'); // Navigate to Sign Up
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blueAccent,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    child: const Text(
                      "Sign Up",
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
      body: Stack(
        children: [
          // Background Gradient
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [Color(0xFF1E3A8A), Color(0xFF10B981), Color(0xFF14B8A6)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
            ),
          ),
          // Main Content
          SingleChildScrollView(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 24.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 50),
                  // Hero Section
                  Text(
                    "Discover Your Next Great Read",
                    style: TextStyle(
                      fontSize: 40,
                      fontWeight: FontWeight.bold,
                      color: Colors.yellow[100],
                    ),
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    "Experience personalized book recommendations powered by AI. "
                    "Find your perfect match from thousands of titles.",
                    style: TextStyle(
                      fontSize: 18,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 32),
                  // Discover Button
                  ElevatedButton(
                    onPressed: () {
                      print('Button pressed');
                      try {
                        context.go('/login');
                        print('Navigation initiated');
                      } catch (e) {
                        print('Navigation error: $e');
                      }
                    },
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                      backgroundColor: Colors.yellow[300],
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(30.0),
                      ),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: const [
                        Text(
                          "Start Your Journey",
                          style: TextStyle(fontSize: 16, color: Colors.black),
                        ),
                        SizedBox(width: 8),
                        Icon(Icons.chevron_right, size: 20, color: Colors.black),
                      ],
                    ),
                  ),
                  const SizedBox(height: 32),
                  // Features Section
                  GridView(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      mainAxisSpacing: 16,
                      crossAxisSpacing: 16,
                    ),
                  ),
                  const SizedBox(height: 50),
                  // Hero Image
                  Center(
                    child: Stack(
                      alignment: Alignment.center,
                      children: [
                        Container(
                          width: 500,
                          height: 500,
                          decoration: BoxDecoration(
                            color: Colors.yellow[200]!.withOpacity(0.2),
                            shape: BoxShape.circle,
                          ),
                        ),
                        Image.asset(
                          'assets/images/hero.png',
                          width: 300, 
                          height: 300,
                          fit: BoxFit.cover,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class FeatureCard extends StatelessWidget {
  final String iconPath;
  final String title;
  final String description;

  const FeatureCard({
    required this.iconPath,
    required this.title,
    required this.description,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.9),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFE5E7EB)),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Image.asset(
            iconPath,
            width: 40,
            height: 40,
          ),
          const SizedBox(height: 16),
          Text(
            title,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.black,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            description,
            style: const TextStyle(
              fontSize: 14,
              color: Colors.grey,
            ),
          ),
        ],
      ),
    );
  }
}
