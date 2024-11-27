from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
import json
import logging
import random
import re
from backend.app.services.graphql_service import graphql_service

logger = logging.getLogger(__name__)

class RecommendationAgent:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.7, model="gpt-4o-mini")
        self.setup_prompts()

    def setup_prompts(self):
        """Initialize recommendation prompts."""
        # Initial recommendation prompt for general requests
        self.general_prompt = PromptTemplate(
            input_variables=["query_type"],
            template="""You are a book recommendation system. Generate {query_type} book recommendations.

            Return ONLY a valid JSON object containing 5 book recommendations in exactly this format:
            {{
                "recommendations": [
                    {{
                        "title": "Example Title",
                        "author": "Author Name",
                        "reason": "Specific reason for recommendation"
                    }}
                ]
            }}

            Important rules:
            1. Return EXACTLY 5 recommendations
            2. Ensure complete, properly formatted JSON
            3. No additional text or explanations
            4. Include varied genres and styles
            5. Mix of contemporary and classic titles"""
        )

        # Specific recommendation prompt for user preferences
        self.preference_prompt = PromptTemplate(
            input_variables=["conversation_history", "current_message"],
            template="""You are a book recommendation system. Based on this conversation:
            Previous messages: {conversation_history}
            Current message: {current_message}

            Return ONLY a valid JSON object containing 5 book recommendations in exactly this format:
            {{
                "recommendations": [
                    {{
                        "title": "Example Title",
                        "author": "Author Name",
                        "reason": "Specific reason why this matches their interests"
                    }}
                ]
            }}

            If you need more information, return:
            {{
                "question": "Your specific question about their preferences"
            }}

            Important rules:
            1. Return EXACTLY 5 recommendations if providing books
            2. Ensure complete, properly formatted JSON
            3. No additional text or explanations
            4. Only ask a question if absolutely necessary"""
        )

    def normalize_title(self, title: str) -> str:
        """Normalize book titles by removing subtitles."""
        return re.split(r':|–|-', title)[-1].strip()

    def generate_random_price(self) -> float:
        """Generate a random price for books."""
        return round(random.uniform(9.99, 29.99), 2)

    async def _get_book_details_by_title(self, title: str) -> List[Dict[str, Any]]:
        """Fetch book details using GraphQL query by title."""
        query = """
        query GetBookByTitle($title: String!) {
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
            result = await graphql_service.execute_query(query, variables)
            books = result.get("books", [])
            
            if not books:
                return []

            processed_books = []
            for book in books:
                # Get the image URL with proper fallback
                image_url = None
                if book.get("images") and book["images"]:
                    image_url = book["images"][0].get("url")
                if not image_url and book.get("image"):
                    image_url = book["image"].get("url")
                if not image_url:
                    image_url = "https://via.placeholder.com/150"

                # Convert all numeric values to strings and handle None values
                processed_book = {
                    "id": str(book.get("id", "")),
                    "title": book.get("title", "Unknown Title"),
                    "release_year": str(book.get("release_year", "")),
                    "release_date": str(book.get("release_date", "")),
                    "image_url": image_url,
                    "rating": str(book.get("rating", "0.0")),
                    "pages": str(book.get("pages", "0")),
                    "description": book.get("description", "No description available."),
                    "price": str(self.generate_random_price())
                }
                processed_books.append(processed_book)

            return processed_books

        except Exception as e:
            logger.error(f"Error fetching book details for title '{title}': {str(e)}")
            return []

    async def _fetch_book_metadata(self, recommendations: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Fetch and process book metadata with better error handling."""
        final_recommendations = []
        seen_titles = set()

        for rec in recommendations:
            try:
                if rec['title'] in seen_titles:
                    continue

                books = await self._get_book_details_by_title(rec['title'])
                
                if books:
                    book = books[0]  # Use first match
                    processed_book = {
                        "id": book.get("id", str(len(final_recommendations) + 1)),
                        "title": rec['title'],
                        "author": rec['author'],
                        "coverImage": book.get("image_url", "https://via.placeholder.com/150"),
                        "rating": book.get("rating", "0.0"),
                        "pages": book.get("pages", "0"),
                        "description": book.get("description", "A recommended book based on your interests."),
                        "publishedDate": book.get("release_year", ""),  # Ensure this is a string
                        "price": str(self.generate_random_price()),
                        "ReasonForRecommendation": rec.get('reason', 'A recommended book based on your interests.')
                    }
                else:
                    # Fallback for books not found
                    processed_book = {
                        "id": str(len(final_recommendations) + 1),
                        "title": rec['title'],
                        "author": rec['author'],
                        "coverImage": "https://via.placeholder.com/150",
                        "rating": "0.0",
                        "pages": "0",
                        "description": "A recommended book based on your interests.",
                        "publishedDate": "",  # Empty string instead of None
                        "price": str(self.generate_random_price()),
                        "ReasonForRecommendation": rec.get('reason', 'A recommended book based on your interests.')
                    }

                final_recommendations.append(processed_book)
                seen_titles.add(rec['title'])

            except Exception as e:
                logger.error(f"Error processing book metadata for '{rec['title']}': {str(e)}")
                continue

        return final_recommendations
        
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process recommendation requests."""
        try:
            messages = state.get("messages", [])
            if not messages:
                return {
                    "type": "error",
                    "response": "No message found to process"
                }

            current_message = messages[-1].content.strip()
            is_initial_request = current_message.lower() in [
                "recommend some books", "recommend books", "book recommendations"
            ]

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if is_initial_request:
                        # Generate general recommendations
                        response = await self.llm.ainvoke(
                            self.general_prompt.format(query_type="diverse")
                        )
                        response_text = response.content  # Extract content from AIMessage
                    else:
                        # Generate specific recommendations based on conversation
                        conversation_history = "\n".join(
                            msg.content for msg in messages[-3:-1]
                        ) if len(messages) > 1 else ""
                        
                        response = await self.llm.ainvoke(
                            self.preference_prompt.format(
                                conversation_history=conversation_history,
                                current_message=current_message
                            )
                        )
                        response_text = response.content  # Extract content from AIMessage

                    # Parse response
                    parsed_response = json.loads(response_text.strip())

                    if "recommendations" in parsed_response:
                        recommendations = parsed_response["recommendations"]
                        if len(recommendations) == 5:  # Verify we got exactly 5 recommendations
                            final_recommendations = await self._fetch_book_metadata(recommendations)
                            
                            if final_recommendations:
                                return {
                                    "type": "recommendation",
                                    "response": {
                                        "message": "Based on your interests, here are some books you might enjoy:",
                                        "books": final_recommendations
                                    }
                                }

                    elif "question" in parsed_response:
                        return {
                            "type": "clarification",
                            "response": {
                                "message": parsed_response["question"],
                                "needs_clarification": True
                            }
                        }

                except json.JSONDecodeError as e:
                    logger.error(f"Attempt {attempt + 1}: JSON parsing error: {e}")
                    logger.error(f"Raw response: {response_text}")
                    continue
                except Exception as e:
                    logger.error(f"Attempt {attempt + 1}: Error processing recommendations: {e}")
                    continue

            # If we've exhausted all retries
            return {
                "type": "error",
                "response": "I'm having trouble generating recommendations. Please try again."
            }

        except Exception as e:
            logger.error(f"Error in recommendation processing: {str(e)}")
            return {
                "type": "error",
                "response": "An error occurred while processing your request. Please try again."
            }