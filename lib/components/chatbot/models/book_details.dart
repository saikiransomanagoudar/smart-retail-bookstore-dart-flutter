class BookDetails {
  final String id;
  final String title;
  final String releaseYear;
  final String imageUrl;
  final double? rating; 
  final int pages;
  final String reasonForRecommendation;
  final double price;

  BookDetails({
    required this.id,
    required this.title,
    required this.releaseYear,
    required this.imageUrl,
    this.rating, 
    required this.pages,
    required this.price,
    required this.reasonForRecommendation,
  });

  factory BookDetails.fromJson(Map<String, dynamic> json) {
  return BookDetails(
    id: json['id']?.toString() ?? '',
    title: json['title'] ?? 'Unknown Title',
    releaseYear: json['release_year']?.toString() ?? 'N/A',
    imageUrl: json['image_url'] ?? 'https://via.placeholder.com/150',
    rating: (json['rating'] != null) ? double.tryParse(json['rating'].toString()) ?? 0.0 : 0.0,
    pages: int.tryParse(json['pages']?.toString() ?? '0') ?? 0,
    price: double.tryParse((json['Price'] ?? '0').toString()) ?? 0.0, // Ensure a non-null String is passed
    reasonForRecommendation: json['ReasonForRecommendation'] ?? 'No recommendation reason provided.',
  );
}

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'release_year': releaseYear,
      'image_url': imageUrl,
      'rating': rating,
      'pages': pages,
      'price': price,
      'reason_for_recommendation': reasonForRecommendation,
    };
  }
}
