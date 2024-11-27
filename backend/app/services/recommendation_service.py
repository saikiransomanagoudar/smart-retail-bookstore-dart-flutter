import logging
import os
import random
import json
from fastapi import HTTPException
from sqlalchemy.orm import Session
from backend.app.models.user import get_user_preferences
from backend.app.services.graphql_service import graphql_service
from typing import List, Dict, Optional
import re
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
import asyncio
from datetime import datetime, timedelta

dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))
load_dotenv(dotenv_path)
openai_api_key = os.getenv("OPENAI_API_KEY")
llm = OpenAI(api_key=openai_api_key, temperature=0.7)

def normalize_title(title: str) -> str:
    return re.split(r':|–|-', title)[-1].strip()

def generate_random_price() -> float:
    return round(random.uniform(9.99, 29.99), 2)

def safe_float(value: any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

async def get_books(query: str = "", limit: int = 10) -> List[Dict]:
    """Get books using a basic query."""
    query = """
    query GetBooks($limit: Int!) {
        books(limit: $limit, order_by: {id: desc}) {
            id
            title
            release_year
            release_date
            images {
                url
            }
            image {
                url
            }
            rating
            pages
            description
        }
    }
    """
    try:
        result = await graphql_service.execute_query(query, {"limit": limit})
        return result.get("books", [])
    except Exception as e:
        logging.error(f"Error fetching books: {str(e)}")
        return []

def process_book(book: Dict, author: str = None) -> Dict:
    """Process a book dict into the required format."""
    image_url = None
    if book.get("images") and len(book["images"]) > 0:
        image_url = book["images"][0].get("url")
    elif book.get("image"):
        image_url = book["image"].get("url")

    return {
        "id": str(book.get("id", "")),
        "title": book.get("title", "Unknown Title"),
        "release_year": book.get("release_year"),
        "release_date": book.get("release_date"),
        "image_url": image_url,
        "rating": safe_float(book.get("rating")),
        "pages": book.get("pages"),
        "author": author or "Unknown Author",
        "price": generate_random_price(),
        "description": book.get("description", "No description available")
    }

def generate_llm_recommendations(preferences: dict) -> List[Dict]:
    favorite_books = preferences.get("favorite_books", [])
    favorite_authors = preferences.get("favorite_authors", [])
    preferred_genres = preferences.get("preferred_genres", [])

    prompt_template = PromptTemplate(
        input_variables=["favorite_books", "favorite_authors", "preferred_genres"],
        template="""You are a book recommendation system. Based on these preferences:
        - Favorite Books: {favorite_books}
        - Favorite Authors: {favorite_authors}
        - Preferred Genres: {preferred_genres}

        Return ONLY a valid JSON object containing 8 book recommendations in exactly this format:
        {{
            "recommendations": [
                {{
                    "title": "Example Title",
                    "author": "Author Name"
                }},
            ]
        }}

        Important rules:
        1. Return EXACTLY 8 recommendations
        2. Ensure complete, properly formatted JSON
        3. No additional text or explanations
        4. All brackets and braces must be properly closed"""
    )

    max_retries = 3
    for attempt in range(max_retries):
        try:
            generated_response = llm.invoke(
                prompt_template.format(
                    favorite_books=", ".join(favorite_books) if favorite_books else "various books",
                    favorite_authors=", ".join(favorite_authors) if favorite_authors else "various authors",
                    preferred_genres=", ".join(preferred_genres) if preferred_genres else "various genres"
                )
            )

            cleaned_response = generated_response.strip()
            recommendations_data = json.loads(cleaned_response)
            recommendations = recommendations_data.get("recommendations", [])

            validated_recommendations = []
            for rec in recommendations:
                if all(key in rec for key in ["title", "author"]):
                    cleaned_rec = {
                        "title": rec["title"].strip(),
                        "author": rec["author"].strip()
                    }
                    validated_recommendations.append(cleaned_rec)

            if len(validated_recommendations) == 8:
                return validated_recommendations

            print(f"Attempt {attempt + 1}: Got {len(validated_recommendations)} recommendations instead of 8. Retrying...")
            continue

        except json.JSONDecodeError as e:
            print(f"Attempt {attempt + 1}: JSON parsing error: {e}")
            print(f"Raw response: {cleaned_response}")
            continue
        except Exception as e:
            print(f"Attempt {attempt + 1}: Unexpected error: {e}")
            continue

    raise HTTPException(
        status_code=500,
        detail="Unable to generate valid recommendations after multiple attempts"
    )

async def get_trending_books() -> List[Dict]:
    """Get trending books."""
    try:
        books = await get_books(limit=10)
        processed_books = [process_book(book) for book in books if book]
        return processed_books
    except Exception as e:
        logging.error(f"Error fetching trending books: {str(e)}")
        return []

async def get_recommendations(user_id: str, db: Session) -> List[Dict]:
    """Get personalized book recommendations for a user."""
    try:
        user_preferences = await get_user_preferences(user_id, db)
        if not user_preferences:
            logging.info("No user preferences found, falling back to trending books")
            return await get_trending_books()

        recommended_books = generate_llm_recommendations(user_preferences)
        if not recommended_books:
            logging.info("No LLM recommendations, falling back to trending books")
            return await get_trending_books()

        processed_books = []
        for book in recommended_books:
            try:
                normalized_title = normalize_title(book['title'])
                book_details = await graphql_service.get_book_details_by_titles(normalized_title)
                
                if book_details:
                    processed_book = process_book(book_details[0], book['author'])
                    processed_books.append(processed_book)
                else:
                    logging.warning(f"No match found for book: {book['title']}")
            except Exception as e:
                logging.error(f"Error processing book {book.get('title', 'Unknown')}: {str(e)}")
                continue

        if not processed_books:
            return await get_trending_books()

        return processed_books

    except Exception as e:
        logging.error(f"Error in get_recommendations: {str(e)}")
        return await get_trending_books()