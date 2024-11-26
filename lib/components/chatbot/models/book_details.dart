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
  });

  factory BookDetails.fromJson(Map<String, dynamic> json) {
    return BookDetails(
      id: json['id']?.toString() ?? '',
      title: json['title'] ?? 'Unknown Title',
      releaseYear: json['release_year']?.toString() ?? 'N/A',
      releaseDate: json['release_date'] ?? 'N/A',
      imageUrl: json['image_url'] ?? 'https://via.placeholder.com/150',
      rating: double.tryParse(json['rating']?.toString() ?? '0') ?? 0,
      pages: int.tryParse(json['pages']?.toString() ?? '0') ?? 0,
      author: json['author'] ?? 'Unknown Author',
      price: double.tryParse(json['price']?.toString() ?? '0') ?? 0,
    );
  }
}