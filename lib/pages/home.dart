import 'package:flutter/material.dart';
import '../components/navbar.dart';
import 'package:go_router/go_router.dart';



class HomePage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // Display the Navbar at the top
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(60.0), // Set height for the Navbar
        child: Navbar(),
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
                      context.go('/login');
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
                    // children: [
                    //   FeatureCard(
                    //     iconPath: 'assets/images/vast_library.png',
                    //     title: "Vast Library",
                    //     description: "Access thousands of books across all genres.",
                    //   ),
                    //   FeatureCard(
                    //     iconPath: 'assets/images/smart_recommendations.png',
                    //     title: "Smart Recommendations",
                    //     description: "AI-powered suggestions based on your preferences.",
                    //   ),
                    // ],
                  ),
                  const SizedBox(height: 50),
                  // Hero Image
                  Center(
                    child: Stack(
                      alignment: Alignment.center,
                      children: [
                        Container(
                          width: 300,
                          height: 300,
                          decoration: BoxDecoration(
                            color: Colors.yellow[100]!.withOpacity(0.2),
                            shape: BoxShape.circle,
                          ),
                        ),
                        // Image.asset(
                        //   'assets/images/hero_image.png',
                        //   width: 250,
                        //   height: 250,
                        // ),
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
