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
                    headers={"Authorization": f"{self.token}"}
                )
                async with Client(
                        transport=transport,
                        fetch_schema_from_transport=True
                ) as session:
                    result = await session.execute(gql(query), variable_values=variables)
                    return result
            except Exception as e:
                print(f"An error occurred while executing GraphQL query: {str(e)}")
                return {}

    def extract_author_from_dto(self, book: Dict) -> None:
        dto = book.get("dto")
        if dto and isinstance(dto, dict):
            author = dto.get("author")
            if author:
                book["author"] = author
            else:
                book["author"] = "Unknown Author"
        else:
            book["author"] = "Unknown Author"

    async def get_trending_books_ids(self) -> List[int]:
        query = """
        query GetTrendingBooks {
            books_trending(from: "2010-01-01", limit: 10, offset: 10) {
                ids
            }
        }
        """
        result = await self.execute_query(query)
        return result.get("books_trending", {}).get("ids", [])

    async def get_book_details_by_ids(self, book_ids: List[int]) -> List[Dict]:
        query = """
        query MyQuery($ids: [Int!]!) {
            books(where: {id: {_in: $ids}}, distinct_on: title) {
                id
                title
                release_year
                release_date
                images(limit: 1, where: {url: {_is_null: false}}) {
                    url
                }
                rating
                pages
                description
            }
        }
        """
        variables = {"ids": book_ids}
        result = await self.execute_query(query, variables)
        return result.get("books", [])

    async def get_book_details_by_titles(self, title: str) -> List[Dict]:

        query = """
        query MyQuery($title: String!) {
            books(where: {title: {_ilike: $title}, image_id: {_is_null: false}}) {
                id
                title
                release_year
                release_date
                rating
                pages
                images(limit: 1, where: {url: {_is_null: false}}) {
                  url
                }
                image {
                  url
                }
                description
                headline
            }
        }
        """
        variables = {"title": title}
        result = await self.execute_query(query, variables)
        books = result.get("books", [])

        for book in books:
            self.extract_author_from_dto(book)
        return books

    async def get_book_details_by_title_chatbot(self, title: str) -> List[Dict]:
        query = """
        query MyQuery($title: String!) {
            books(where: {title: {_ilike: $title, _is_null: false}}, limit: 1) {
                title
                release_year
                pages
                images(limit: 1, where: {url: {_is_null: false}}) {
                  url
                }
                image{
                  url
                }
            }
        }
        """
        variables = {"title": title}
        result = await self.execute_query(query, variables)
        books = result.get("books", [])

        for book in books:
            self.extract_author_from_dto(book)
        return books


graphql_service = GraphQLService(settings.HARDCOVER_API_TOKEN)