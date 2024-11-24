import logging
import os
import random
import json
from fastapi import HTTPException
from sqlalchemy.orm import Session  # Changed from requests.Session
from backend.app.models.user import get_user_preferences
from backend.app.services.graphql_service import graphql_service
from typing import List, Dict
import re
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI

dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))
load_dotenv(dotenv_path)
openai_api_key = os.getenv("OPENAI_API_KEY")
llm = OpenAI(api_key=openai_api_key, temperature=0.7)

def normalize_title(title: str) -> str:
    return re.split(r':|–|-', title)[-1].strip()

def generate_random_price():
    return round(random.uniform(9.99, 29.99), 2)  # Changed range to match prompt


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

            # Clean up the response
            cleaned_response = generated_response.strip()

            # Parse the JSON
            recommendations_data = json.loads(cleaned_response)
            recommendations = recommendations_data.get("recommendations", [])

            # Validate recommendations
            validated_recommendations = []
            for rec in recommendations:
                if all(key in rec for key in ["title", "author"]):  # Only check for title and author
                    cleaned_rec = {
                        "title": rec["title"].strip(),
                        "author": rec["author"].strip()
                    }
                    validated_recommendations.append(cleaned_rec)

            # If we have exactly 8 valid recommendations, return them
            if len(validated_recommendations) == 8:
                return validated_recommendations

            # If we don't have exactly 8, retry
            print(f"Attempt {attempt + 1}: Got {len(validated_recommendations)} recommendations instead of 8. Retrying...")
            continue

        except json.JSONDecodeError as e:
            print(f"Attempt {attempt + 1}: JSON parsing error: {e}")
            print(f"Raw response: {cleaned_response}")
            continue
        except Exception as e:
            print(f"Attempt {attempt + 1}: Unexpected error: {e}")
            continue

    # If we've exhausted all retries, raise an exception
    raise HTTPException(
        status_code=500,
        detail="Unable to generate valid recommendations after multiple attempts. Please try again."
    )

async def get_recommendations(user_id: str, db: Session) -> List[Dict]:
    user_preferences = await get_user_preferences(user_id, db)

    if not user_preferences:
        raise HTTPException(
            status_code=404,
            detail="User preferences not found. Please complete preferences setup."
        )

    recommended_books = generate_llm_recommendations(user_preferences)

    if not recommended_books:
        raise HTTPException(
            status_code=404,
            detail="Could not generate recommendations. Please try again."
        )

    processed_books = []
    for book in recommended_books:
        normalized_title = normalize_title(book['title'])
        book_details = await graphql_service.get_book_details_by_titles(normalized_title)
        if book_details:
            b = book_details[0]
            processed_book = {
                "title": b["title"],
                "release_year": b.get("release_year"),
                "image_url": b["images"][0]["url"] if b.get("images") else (
                    b["image"]["url"] if b.get("image") else None),
                "rating": b.get("rating"),
                "pages": b.get("pages"),
                "author": book["author"],
                "price": generate_random_price(),
                "description": b.get("description"),
                "headline": b.get("headline")
            }
            processed_books.append(processed_book)
        else:
            logging.warning(f"No match found for book: {book['title']}")

    return processed_books


async def get_trending_books() -> List[Dict]:  # Renamed for clarity
    trending_ids = await graphql_service.get_trending_books_ids()

    if not trending_ids:
        raise HTTPException(
            status_code=404,
            detail="No trending books found"
        )

    trending_books = await graphql_service.get_book_details_by_ids(trending_ids)

    if not trending_books:
        raise HTTPException(
            status_code=404,
            detail="Could not fetch trending books details"
        )

    processed_books = []
    for book in trending_books:
        processed_book = {
            "id": book["id"],
            "title": book["title"],
            "release_year": book.get("release_year"),
            "release_date": book.get("release_date"),
            "image_url": book["images"][0]["url"] if book.get("images") else (book["image"]["url"] if book.get("image") else None),
            "rating": book.get("rating"),
            "pages": book.get("pages"),
            "description": book.get("description", "No description available."),
            "price": generate_random_price()
        }
        processed_books.append(processed_book)

    return processed_books