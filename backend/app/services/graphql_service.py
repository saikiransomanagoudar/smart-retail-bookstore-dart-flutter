from typing import List, Dict
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from backend.app.core.config import settings
import asyncio

class GraphQLService:
    def __init__(self, token: str):
        self.token = token
        self.url = settings.HARDCOVER_API_URL
        self._lock = asyncio.Lock()

    async def execute_query(self, query: str, variables: Dict = None) -> Dict:
        async with self._lock:
            try:
                transport = AIOHTTPTransport(
                    url=self.url,
                    headers={"Authorization": self.token}
                )
                async with Client(
                    transport=transport,
                    fetch_schema_from_transport=False
                ) as session:
                    print(f"Executing query: {query}")
                    print(f"Variables: {variables}")
                    result = await session.execute(gql(query), variable_values=variables)
                    print(f"Query result: {result}")
                    return result
            except Exception as e:
                print(f"GraphQL query failed: {str(e)}")
                return {}

    async def get_trending_books_ids(self) -> List[Dict]:
        """Get trending books with full details."""
        query = """
        query GetTrendingBooks {
            books_trending(from: "2010-01-01", limit: 10) {
                ids
            }
        }
        """
        try:
            result = await self.execute_query(query)
            return result.get("books_trending", {}).get("ids", [])
        except Exception as e:
            print(f"Error fetching trending books: {str(e)}")
            return []

    async def get_book_details_by_ids(self, book_ids: List[int]) -> List[Dict]:
        """Get book details by IDs."""
        query = """
        query GetBooksByIds($ids: [Int!]!) {
            books(where: {id: {_in: $ids}}, distinct_on: title) {
                id
                title
                release_year
                release_date
                images(limit: 1, where: {url: {_is_null: false}}) {
                    url
                }
                image {
                    url
                }
                rating
                pages
                description
                headline
            }
        }
        """
        variables = {"ids": book_ids}
        try:
            result = await self.execute_query(query, variables)
            return result.get("books", [])
        except Exception as e:
            print(f"Error fetching book details: {str(e)}")
            return []

    async def get_book_details_by_titles(self, title: str) -> List[Dict]:
        """Get book details by title."""
        query = """
        query GetBooksByTitle($title: String!) {
            books(where: {title: {_ilike: $title}}, limit: 1) {
                id
                title
                release_year
                release_date
                images(limit: 1, where: {url: {_is_null: false}}) {
                    url
                }
                image {
                    url
                }
                rating
                pages
                description
                headline
            }
        }
        """
        variables = {"title": f"%{title}%"}
        try:
            result = await self.execute_query(query, variables)
            return result.get("books", [])
        except Exception as e:
            print(f"Error fetching book details: {str(e)}")
            return []

    def transform_books(self, books: List[Dict]) -> List[Dict]:
        transformed_books = []
        for book in books:
            image_url = None
            if book.get("images") and len(book["images"]) > 0:
                image_url = book["images"][0].get("url")
            elif book.get("image"):
                image_url = book["image"].get("url")

            transformed_book = {
                "id": str(book.get("id", "")),
                "title": book.get("title", "Unknown Title"),
                "release_year": book.get("release_year"),
                "release_date": book.get("release_date"),
                "image_url": image_url,
                "rating": float(book.get("rating", 0)),
                "pages": book.get("pages"),
                "price": float(book.get("price", 9.99)),
                "description": book.get("description", ""),
                "headline": book.get("headline", "")
            }
            transformed_books.append(transformed_book)
        return transformed_books

graphql_service = GraphQLService(settings.HARDCOVER_API_TOKEN)