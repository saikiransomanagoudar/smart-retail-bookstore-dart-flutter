# google_books_service.py
import requests

class GoogleBooksAPIClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/books/v1"

    def search_books(self, query):
        url = f"{self.base_url}/volumes?q={query}&key={self.api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error fetching books: {response.status_code}")

    def get_book_details(self, book_id):
        url = f"{self.base_url}/volumes/{book_id}?key={self.api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error fetching book details: {response.status_code}")