import 'package:flutter/material.dart';
import 'package:carousel_slider/carousel_slider.dart';
import 'package:provider/provider.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../auth_provider.dart';
import 'package:go_router/go_router.dart';
import 'package:flip_card/flip_card.dart';
import '../components/chatbot/chatbot.dart';

class DashboardPage extends StatefulWidget {
  @override
  _DashboardPageState createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  bool loadingPopular = true;
  bool loadingRecommended = true;
  List<dynamic> popularBooks = [];
  List<dynamic> recommendedBooks = [];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      if (!authProvider.isSignedIn) {
        context.go('/login');
      } else {
        fetchPopularBooks();
        fetchRecommendedBooks();
      }
    });
  }

  Future<void> fetchPopularBooks() async {
    try {
        setState(() {
        loadingPopular = true;
        });

        final response = await http.get(
        Uri.parse('http://localhost:8000/api/recommendations/trending-books'),
        );

        if (response.statusCode == 200) {
        final data = json.decode(response.body);
        print('Popular Books Response: $data');
        setState(() {
            popularBooks = data;
            loadingPopular = false;
        });
        } else {
        print("Error fetching popular books: ${response.statusCode}");
        }
    } catch (e) {
        print("Error fetching popular books: $e");
    }
  }

  Future<void> fetchRecommendedBooks() async {
    final authProvider = Provider.of<AuthProvider>(context, listen: false);
    if (authProvider.userId == null) {
      setState(() {
        loadingRecommended = false;
      });
      return;
    }

    try {
      setState(() {
        loadingRecommended = true;
      });

      final response = await http.post(
        Uri.parse(
            'http://localhost:8000/api/recommendations/initial-recommendations'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({"userId": authProvider.userId}),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          recommendedBooks = data;
          loadingRecommended = false;
        });
      } else {
        print("Error fetching recommendations: ${response.statusCode}");
      }
    } catch (e) {
      print("Error fetching recommendations: $e");
    }
  }

Widget buildFlipCardFront(dynamic book) {
  return Container(
    width: 180,
    child: Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
      ),
      elevation: 3,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(8),
        child: Stack(
          children: [
            Positioned.fill(
              child: Container(
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.red, width: 2),
                ),
              ),
            ),
            // Book Image
            Image.network(
              book['image_url'] ?? 'https://via.placeholder.com/150',
              width: double.infinity,
              height: double.infinity,
              fit: BoxFit.cover,
              errorBuilder: (context, error, stackTrace) {
                return Container(
                  color: Colors.grey[300],
                  child: Icon(Icons.broken_image, size: 60),
                );
              },
            ),
            // Gradient Overlay
            Positioned.fill(
              child: Container(
                color: Colors.black.withOpacity(0.2), // Debug: Semi-transparent overlay
              ),
            ),
            // Title and Rating
            Positioned(
              bottom: 8,
              left: 8,
              right: 8,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    book['title'] ?? 'Untitled',
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                  if ((book['rating'] ?? 0) > 0) ...[
                    SizedBox(height: 4),
                    Row(
                      children: [
                        Icon(Icons.star, color: Colors.amber, size: 12),
                        SizedBox(width: 4),
                        Text(
                          (book['rating'] ?? 0).toStringAsFixed(1),
                          style: TextStyle(color: Colors.white, fontSize: 10),
                        ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
            // Price Tag
            Positioned(
              top: 8,
              right: 8,
              child: Container(
                padding: EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.9),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  '\$${(book['price'] ?? 0).toStringAsFixed(2)}',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    ),
  );
}


@override
  Widget buildBookCard(dynamic book) {
  return Container(
    width: 180,
    child: Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
      ),
      elevation: 3,
      child: SizedBox(
        height: 240,
        child: Stack(
          children: [
            // Book Image
            ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: Image.network(
                    book['image_url'] ?? 'https://via.placeholder.com/150',
                    width: double.infinity,
                    height: 240,
                    fit: BoxFit.cover,
                    errorBuilder: (context, error, stackTrace) {
                    print("Image failed to load: ${book['image_url']}");
                    return Container(
                        color: Colors.grey[300],
                        child: Icon(Icons.broken_image, size: 60), // Fallback icon
                    );
                },
              ),
            ),
            Positioned.fill(
              child: Container(
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(8),
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [
                      Colors.transparent, // Fully transparent at the top
                      Colors.black.withOpacity(0.4), // Lighter opacity at the bottom
                    ],
                  ),
                ),
              ),
            ),
            // Title and Rating
            Positioned(
              bottom: 8,
              left: 8,
              right: 8,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    book['title'] ?? 'Untitled',
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                  if ((book['rating'] ?? 0) > 0) ...[
                    SizedBox(height: 4),
                    Row(
                      children: [
                        Icon(Icons.star, color: Colors.amber, size: 12),
                        SizedBox(width: 4),
                        Text(
                          (book['rating'] ?? 0).toStringAsFixed(1),
                          style: TextStyle(color: Colors.white, fontSize: 10),
                        ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
            // Price Tag
            Positioned(
              top: 8,
              right: 8,
              child: Container(
                padding: EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.9),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  '\$${(book['price'] ?? 0).toStringAsFixed(2)}',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 10,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    ),
  );
}


@override
  Widget buildFlipCard(dynamic book) {
  return FlipCard(
    front: buildFlipCardFront(book),
    back: Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        boxShadow: [
          BoxShadow(
            color: Colors.black26,
            blurRadius: 6,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              book['title'] ?? 'Untitled',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 16,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            SizedBox(height: 8),
            Text(
              book['author'] ?? 'Unknown Author',
              style: TextStyle(
                color: Colors.grey[600],
                fontSize: 14,
                overflow: TextOverflow.ellipsis,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            SizedBox(height: 8),
            Row(
              children: [
                Icon(Icons.star, color: Colors.amber, size: 14),
                SizedBox(width: 4),
                Text(
                  (book['rating'] ?? 0).toStringAsFixed(1),
                  style: TextStyle(color: Colors.orange, fontSize: 14),
                ),
              ],
            ),
            SizedBox(height: 12),
            Expanded(
              child: SingleChildScrollView(
                child: Text(
                  book['description'] ?? 'No description available.',
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.grey[800],
                    height: 1.5,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    ),
  );
}


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Dashboard"),
        backgroundColor: Colors.blueAccent,
      ),
      body: Stack(
        children: [
            SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                "Popular Books",
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 16),
              CarouselSlider(
                items: loadingPopular
                    ? List.generate(
                        6,
                        (index) => Container(
                          width: 180,
                          margin: const EdgeInsets.symmetric(horizontal: 8),
                          decoration: BoxDecoration(
                            color: Colors.grey[300],
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                      )
                    : popularBooks.map((book) => buildBookCard(book)).toList(),
                options: CarouselOptions(
                  height: 240,
                  aspectRatio: 0.7,
                  enlargeCenterPage: true,
                  enableInfiniteScroll: true,
                  autoPlay: true,
                  autoPlayInterval: const Duration(seconds: 3),
                  viewportFraction: 0.5,
                ),
              ),
              SizedBox(height: 24),
              Consumer<AuthProvider>(
                builder: (context, authProvider, _) {
                  if (!authProvider.isSignedIn) {
                    return const SizedBox.shrink();
                  }
                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        "Recommended for You",
                        style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                      ),
                      SizedBox(height: 16),
                      GridView.builder(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        gridDelegate:
                            const SliverGridDelegateWithFixedCrossAxisCount(
                          crossAxisCount: 4,
                          childAspectRatio: 0.8,
                          crossAxisSpacing: 8,
                          mainAxisSpacing: 8,
                        ),
                        itemCount:
                            loadingRecommended ? 8 : recommendedBooks.length,
                        itemBuilder: (context, index) {
                          if (loadingRecommended) {
                            return Container(
                              decoration: BoxDecoration(
                                color: Colors.grey[300],
                                borderRadius: BorderRadius.circular(8),
                              ),
                            );
                          }
                          return buildFlipCard(recommendedBooks[index]);
                        },
                      ),
                    ],
                  );
                },
              ),
            ],
          ),
        ),
      ),
      Positioned(
          right: 16,
          bottom: 16,
          child: Chatbot(),
        ),
        ],
      ),
    );
  }
}
