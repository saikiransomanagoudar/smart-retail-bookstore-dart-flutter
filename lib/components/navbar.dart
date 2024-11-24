import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../auth_provider.dart';

class Navbar extends StatelessWidget {
  const Navbar({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final authProvider = Provider.of<AuthProvider>(context);

    return Container(
      color: const Color(0xFF181818), // Dark navbar background
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          // Logo Section
          GestureDetector(
            onTap: () {
              context.go('/'); // Navigate to home
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

          // Spacer to align the Auth Section to the right
          const Spacer(),

          // Auth Section
          Row(
            children: [
              if (!authProvider.isSignedIn) ...[
                TextButton(
                  onPressed: () {
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
                const SizedBox(width: 8),
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
              ] else ...[
                ElevatedButton(
                  onPressed: () async {
                    await authProvider.signOut();
                    context.go('/login'); // Redirect to login after sign out
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.redAccent,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  child: const Text(
                    "Sign Out",
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }
}

// SearchBar Component
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
    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
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
            ConstrainedBox(
              constraints: const BoxConstraints(
                maxHeight: 200, // Limit the height of the dropdown
              ),
              child: Container(
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
                child: ListView.builder(
                  shrinkWrap: true,
                  itemCount: filteredBooks.length,
                  itemBuilder: (context, index) {
                    final book = filteredBooks[index];
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
                          if (index < filteredBooks.length - 1)
                            const Divider(color: Colors.grey),
                        ],
                      ),
                    );
                  },
                ),
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

// Dropdown Menu Widget
class DropdownMenu extends StatelessWidget {
  final VoidCallback resetSearch;

  const DropdownMenu({required this.resetSearch});

  @override
  Widget build(BuildContext context) {
    final authProvider = Provider.of<AuthProvider>(context);

    return Container(
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
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ListTile(
            title: const Text("Profile Settings"),
            onTap: () {
              resetSearch();
              context.go('/profile');
            },
          ),
          ListTile(
            title: const Text("My Orders"),
            onTap: () {
              resetSearch();
              context.go('/orders');
            },
          ),
          ListTile(
            title: const Text("Sign Out"),
            onTap: () async {
              resetSearch();
              await authProvider.signOut();
              context.go('/login');
            },
          ),
        ],
      ),
    );
  }
}
