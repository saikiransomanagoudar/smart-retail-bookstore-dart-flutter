import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class Navbar extends StatefulWidget {
  @override
  _NavbarState createState() => _NavbarState();
}

class _NavbarState extends State<Navbar> {
  bool isSignedIn = false; // Replace with actual authentication state
  String searchQuery = ""; // Search query
  List<Map<String, dynamic>> filteredBooks = []; // Filtered books for the search bar
  final List<Map<String, dynamic>> searchData = [
    {"id": 1, "title": "Book 1"},
    {"id": 2, "title": "Book 2"},
    {"id": 3, "title": "Book 3"},
  ]; // Mock data for search results

  void handleSearchChange(String query) {
    setState(() {
      searchQuery = query;
      if (query.isNotEmpty) {
        filteredBooks = searchData
            .where((book) =>
                book['title'].toLowerCase().contains(query.toLowerCase()))
            .toList();
      } else {
        filteredBooks = [];
      }
    });
  }

  void resetSearch() {
    setState(() {
      searchQuery = "";
      filteredBooks = [];
    });
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      child: Container(
        color: const Color(0xFF181818), // Dark background color for the navbar
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            // Logo Section
            GestureDetector(
              onTap: resetSearch,
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

            // Search Bar
            Expanded(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16.0),
                child: SearchBar(
                  searchQuery: searchQuery,
                  handleSearchChange: handleSearchChange,
                  filteredBooks: filteredBooks,
                  resetSearch: resetSearch,
                ),
              ),
            ),

            // Auth Section
            Row(
              children: [
                // Sign In Button
                GestureDetector(
                  onTap: () {
                    context.go('/login'); 
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
                const SizedBox(width: 16),
                // Sign Up Button
                ElevatedButton(
                  onPressed: () {
                    context.go('/signup');
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
    );
  }
}

// SearchBar Widget
class SearchBar extends StatelessWidget {
  final String searchQuery;
  final Function(String) handleSearchChange;
  final List<Map<String, dynamic>> filteredBooks;
  final VoidCallback resetSearch;

  const SearchBar({
    required this.searchQuery,
    required this.handleSearchChange,
    required this.filteredBooks,
    required this.resetSearch,
  });

  @override
  Widget build(BuildContext context) {
    return Flexible(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Search Input
          TextField(
            onChanged: handleSearchChange,
            decoration: InputDecoration(
              hintText: 'Search books...',
              filled: true,
              fillColor: Colors.white,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide.none,
              ),
              contentPadding:
                  const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              suffixIcon: const Icon(Icons.search),
            ),
          ),

          // Search Results Dropdown
          if (filteredBooks.isNotEmpty)
            Container(
              margin: const EdgeInsets.only(top: 8),
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.1),
                    blurRadius: 8,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Column(
                children: filteredBooks.map((book) {
                  return GestureDetector(
                    onTap: () {
                      resetSearch();
                      context.go('/view-book-details/${book["id"]}');
                    },
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          book["title"],
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: Colors.black,
                          ),
                        ),
                        const Divider(color: Colors.grey),
                      ],
                    ),
                  );
                }).toList(),
              ),
            ),
          if (searchQuery.isNotEmpty && filteredBooks.isEmpty)
            Container(
              margin: const EdgeInsets.only(top: 8),
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.1),
                    blurRadius: 8,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: const Text(
                "No books found",
                style: TextStyle(color: Colors.black),
              ),
            ),
        ],
      ),
    );
  }
}
