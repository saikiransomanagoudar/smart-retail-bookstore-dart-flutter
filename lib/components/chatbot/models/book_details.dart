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
    print('Parsing BookDetails from JSON: $json');

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
      releaseDate: json['publishedDate'] ?? 'N/A',
      imageUrl: json['coverImage'] ?? 'https://via.placeholder.com/150',
      rating: json['rating'] != null ? double.tryParse(json['rating'].toString()) ?? 0.0 : 0.0,
      pages: json['pages'] != null ? int.tryParse(json['pages'].toString()) ?? 0 : 0,
      author: json['author'] ?? 'Unknown Author',
      price: json['price'] != null ? double.tryParse(json['price'].toString()) ?? 0.0 : 0.0,
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