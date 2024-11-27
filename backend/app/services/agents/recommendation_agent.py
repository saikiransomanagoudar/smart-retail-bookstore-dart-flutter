from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import json
import logging
import re
from backend.app.services.graphql_service import graphql_service

logger = logging.getLogger(__name__)

class RecommendationAgent:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.7, model="gpt-4o-mini")
        self.setup_prompts()

    def setup_prompts(self):
        """Initialize recommendation prompt with tailored questions."""
        self.recommend_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a book recommendation expert. Your primary task is to recommend books based on user preferences. 

            Follow these rules:
            - Always ask follow-up questions if the user's preferences are unclear.
            - Questions you can ask include:
                - "What genres do you enjoy? (e.g., mystery, romance, science fiction)"
                - "Do you have a favorite author or a particular writing style you prefer?"
                - "Are there any themes or topics you'd like to explore? (e.g., adventure, personal growth, history)"
                - "What kind of mood or experience are you looking for in a book? (e.g., uplifting, suspenseful, thought-provoking)"
            - Wait for user input before generating recommendations if preferences are missing.

            When generating recommendations:
            - Use the following JSON format strictly:
            {{
            "recommendations": [
                {{
                    "title": "exact book title",
                    "author": "author name",
                    "reason": "brief reason for recommendation"
                }}
            ]
            }}
            - Do not include any text or explanations outside this JSON format.

            If the user's input lacks preferences, respond with a JSON object containing a `question` field to ask for more details:
            {{
            "question": "Which genres or themes do you enjoy reading about?"
            }}

            Always aim to recommend well-known books that match the user's preferences. Be concise and accurate."""),
            ("human", """{input}

            If no specific preferences were provided, generate a follow-up question in the JSON `question` format to refine your recommendations.
            """)
        ])


    def _extract_books_from_text(self, text: str) -> List[Dict[str, str]]:
        """Extract book titles and authors from unstructured LLM text response."""
        books = []
        matches = re.findall(r'\*?\*?([^*\n]+) by ([^*\n]+)\*?\*?', text)
        for title, author in matches:
            books.append({
                "title": title.strip(),
                "author": author.strip(),
                "reason": "This book matches your interests"
            })
        return books

    async def _fetch_book_metadata(self, recommendations: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Fetch detailed metadata for each recommended book."""
        final_recommendations = []
        for rec in recommendations[:5]:  # Limit to 5 books
            try:
                books = await graphql_service.get_book_details_by_titles(rec['title'])
                if books:
                    transformed_books = graphql_service.transform_books(books)
                    for book in transformed_books:
                        book['ReasonForRecommendation'] = rec.get(
                            'reason', f"This book matches your interest in {rec['title']}")
                        final_recommendations.append(book)
                        break  # Use only the first match
            except Exception as e:
                logger.error(f"Error fetching details for book '{rec['title']}': {str(e)}")
                continue
        return final_recommendations
    
    async def _schema_supports_field(self, type_name: str, field_name: str) -> bool:
        """
        Check if a specific type contains a given field in the GraphQL schema.
        Args:
            type_name (str): The GraphQL type to check.
            field_name (str): The field name to search for.
        Returns:
            bool: True if the field exists, False otherwise.
        """
        try:
            introspection_query = """
            query IntrospectionQuery {
            __schema {
                types {
                name
                fields {
                    name
                }
                }
            }
            }
            """
            result = await graphql_service.execute_query(introspection_query)
            for gql_type in result["__schema"]["types"]:
                if gql_type["name"] == type_name:
                    return any(f["name"] == field_name for f in gql_type.get("fields", []))
            return False
        except Exception as e:
            logging.error(f"Error checking schema for type '{type_name}' and field '{field_name}': {str(e)}")
            return False


    async def _fallback_to_trending_books(self) -> List[Dict[str, Any]]:
        """Fetch trending books or provide default recommendations if schema fails."""
        try:
            # Check schema support for required fields
            supports_offset = await self._schema_supports_field("books_trending", "offset")
            supports_from = await self._schema_supports_field("books_trending", "from")

            if supports_offset:
                query = """
                query GetTrendingBooks {
                books_trending(offset: 0, limit: 10) {
                    id
                    title
                    author
                }
                }
                """
            elif supports_from:
                query = """
                query GetTrendingBooks {
                books_trending(from: "2023-01-01", limit: 10) {
                    id
                    title
                    author
                }
                }
                """
            else:
                logging.warning("No suitable trending book query structure found in schema")
                # Return default static recommendations
                return self._default_recommendations()

            # Execute the query
            result = await graphql_service.execute_query(query)
            if "books_trending" not in result or not result["books_trending"]:
                logging.warning("No trending books found in GraphQL response")
                return self._default_recommendations()

            # Transform books for recommendation response
            books = result["books_trending"]
            transformed_books = graphql_service.transform_books(books)
            for book in transformed_books:
                book["ReasonForRecommendation"] = "This is a trending book you might enjoy"

            return transformed_books

        except Exception as e:
            logging.error(f"Error fetching trending books: {str(e)}")
            return self._default_recommendations()

    def _default_recommendations(self) -> List[Dict[str, Any]]:
        """Provide a static list of default recommendations."""
        logging.info("Returning static fallback recommendations")
        return [
            {"title": "To Kill a Mockingbird", "author": "Harper Lee", "ReasonForRecommendation": "A timeless classic."},
            {"title": "1984", "author": "George Orwell", "ReasonForRecommendation": "A thought-provoking dystopian novel."},
            {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "ReasonForRecommendation": "A masterpiece of the Jazz Age."},
            {"title": "Pride and Prejudice", "author": "Jane Austen", "ReasonForRecommendation": "A beloved romance novel."},
            {"title": "The Catcher in the Rye", "author": "J.D. Salinger", "ReasonForRecommendation": "A story of teenage rebellion and angst."},
        ]

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process recommendation requests and return book suggestions with metadata"""
        try:
            # Extract the last user message
            messages = state.get("messages", [])
            if not messages:
                return {
                    "type": "error",
                    "response": "No message found to process"
                }

            last_message = messages[-1].content.strip()
            if not last_message:
                return {
                    "type": "error",
                    "response": "Message content is empty"
                }

            logging.info(f"Processing message: {last_message}")

            # Invoke the LLM
            chain = self.recommend_prompt | self.llm
            try:
                llm_response = await chain.ainvoke(last_message)
                logging.debug(f"LLM response: {llm_response.content}")
            except Exception as e:
                logging.error(f"LLM invocation failed: {str(e)}")
                return {
                    "type": "error",
                    "response": "Failed to fetch recommendations from LLM"
                }

            # Parse or extract recommendations
            recommendations = []
            try:
                if isinstance(llm_response.content, str):
                    recommendations = json.loads(llm_response.content).get('recommendations', [])
                else:
                    raise ValueError("Unexpected LLM response type")
            except (json.JSONDecodeError, KeyError, ValueError):
                logging.warning("LLM response is not structured JSON, attempting text extraction")
                recommendations = self._extract_books_from_text(llm_response.content)

            if not recommendations:
                logging.warning("No recommendations extracted, attempting fallback")
                recommendations = await self._fallback_to_trending_books()

            if not recommendations:
                return {
                    "type": "error",
                    "response": "I couldn't find any books matching your preferences right now."
                }

            # Fetch metadata for each recommended book
            final_recommendations = []
            for rec in recommendations[:5]:  # Limit to 5 books
                try:
                    # Search by title in GraphQL
                    books = await graphql_service.get_book_details_by_titles(rec['title'])
                    if books:
                        # Transform the books to match frontend format
                        transformed_books = graphql_service.transform_books(books)
                        for book in transformed_books:
                            # Add the recommendation reason
                            book['ReasonForRecommendation'] = rec.get(
                                'reason',
                                f"This book matches your interest in {rec['title']}"
                            )
                            final_recommendations.append(book)
                            break  # Take only the first match for each title
                except Exception as e:
                    logging.error(f"Error fetching details for book {rec['title']}: {str(e)}")
                    continue

            if not final_recommendations:
                logging.warning("No detailed recommendations found, attempting trending fallback")
                final_recommendations = await self._fallback_to_trending_books()

            if not final_recommendations:
                return {
                    "type": "error",
                    "response": "I couldn't find any books matching your preferences right now."
                }

            return {
                "type": "recommendation",
                "response": {
                    "message": "Based on your interests, here are some books you might enjoy:",
                    "books": final_recommendations
                }
            }

        except Exception as e:
            logging.error(f"Error in recommendation processing: {str(e)}")
            return {
                "type": "error",
                "response": "I encountered an error while finding book recommendations."
            }



