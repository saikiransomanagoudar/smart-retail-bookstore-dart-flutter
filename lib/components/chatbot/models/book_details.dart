class BookDetails {
  final String id;
  final String title;
  final String releaseYear;
  final String releaseDate;
  final String imageUrl;
  final double rating;
  final int pages;
  final String author;
  final double price;
  final String reasonForRecommendation;

  BookDetails({
    required this.id,
    required this.title,
    required this.releaseYear,
    required this.releaseDate,
    required this.imageUrl,
    required this.rating,
    required this.pages,
    required this.author,
    required this.price,
    required this.reasonForRecommendation,
  });

  factory BookDetails.fromJson(Map<String, dynamic> json) {
    print('Parsing BookDetails from JSON: $json'); // Keep this debug line
    
    // Extract year from publishedDate if available
    String releaseYear = 'N/A';
    if (json['publishedDate'] != null) {
      try {
        final date = DateTime.parse(json['publishedDate']);
        releaseYear = date.year.toString();
      } catch (e) {
        print('Error parsing date: $e');
      }
    }

    return BookDetails(
      id: json['id']?.toString() ?? '',
      title: json['title'] ?? 'Unknown Title',
      releaseYear: releaseYear,
      releaseDate: json['publishedDate'] ?? 'N/A', // Changed from release_date
      imageUrl: json['coverImage'] ?? 'https://via.placeholder.com/150', // Changed from image_url
      rating: double.tryParse(json['averageRating']?.toString() ?? '0') ?? 0, // Changed from rating
      pages: int.tryParse(json['pageCount']?.toString() ?? '0') ?? 0, // Changed from pages
      author: json['author'] ?? 'Unknown Author',
      price: 9.99, // Set default price since it's not in the API response
      reasonForRecommendation: json['ReasonForRecommendation'] ?? 'No recommendation reason provided.',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'release_year': releaseYear,
      'release_date': releaseDate,
      'image_url': imageUrl,
      'rating': rating,
      'pages': pages,
      'author': author,
      'price': price,
      'ReasonForRecommendation': reasonForRecommendation,
    };
  }
}