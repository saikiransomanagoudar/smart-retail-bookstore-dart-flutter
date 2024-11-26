import logging
import os
import random
import json
from fastapi import HTTPException
from sqlalchemy.orm import Session
from backend.app.models.user import get_user_preferences
from backend.app.services.google_books_service import GoogleBooksAPIClient
from typing import List, Dict
import re
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from urllib.parse import urlparse, parse_qs

dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))
load_dotenv(dotenv_path)
openai_api_key = os.getenv("OPENAI_API_KEY")
google_books_api_key = os.getenv("GOOGLE_BOOKS_API_KEY")
llm = OpenAI(api_key=openai_api_key, temperature=0.7)
google_books_api = GoogleBooksAPIClient(api_key=google_books_api_key)

def normalize_title(title: str) -> str:
    return re.split(r':|–|-', title)[-1].strip()

def generate_random_price():
    return round(random.uniform(9.99, 29.99), 2)

async def get_book_description(book_id: str) -> str:
    try:
        book_details = google_books_api.get_book_details(book_id)
        if book_details and "volumeInfo" in book_details:
            return book_details["volumeInfo"].get("description", "No description available.")
    except Exception as e:
        logging.error(f"Error fetching book description for book_id={book_id}: {e}")
    return "No description available."

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

def clean_description(text: str) -> str:
    if not text:
        return "No description available."
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Replace special characters and unknown unicode
    text = text.encode('ascii', 'ignore').decode('ascii')
    # Remove multiple spaces
    text = ' '.join(text.split())
    return text

def process_image_url(url: str) -> str:
    if not url:
        return None
    try:
        # Extract book ID from the URL
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        book_id = query_params.get('id', [None])[0]
        if book_id:
            # Return a simpler URL format
            return f'https://books.google.com/books/publisher/content/images/frontcover/{book_id}?fife=w400-h600'
        return url
    except Exception as e:
        print(f"Error processing image URL: {e}")
        return url

async def get_recommendations(user_id: str, db: Session) -> List[Dict]:
    try:
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
            try:
                normalized_title = normalize_title(book['title'])
                search_results = google_books_api.search_books(f"{normalized_title} {book['author']}")
                
                if search_results and "items" in search_results:
                    book_info = search_results["items"][0]
                    book_id = book_info["id"]
                    volume_info = book_info.get("volumeInfo", {})
                    
                    # Process the image URL
                    image_url = volume_info.get("imageLinks", {}).get("thumbnail")
                    processed_image_url = process_image_url(image_url) if image_url else None
                    
                    processed_book = {
                        "id": book_id,
                        "title": volume_info.get("title", book["title"]),
                        "release_year": int(volume_info.get("publishedDate", "0")[:4]) if volume_info.get("publishedDate") else None,
                        "release_date": volume_info.get("publishedDate"),
                        "image_url": processed_image_url,
                        "rating": volume_info.get("averageRating"),
                        "pages": volume_info.get("pageCount"),
                        "genres": volume_info.get("categories"),
                        "description": clean_description(volume_info.get("description", "No description available.")),
                        "price": generate_random_price(),
                        "author": volume_info.get("authors", [book["author"]])[0]
                    }
                    processed_books.append(processed_book)
                    print(f"Successfully processed book: {book['title']} with image URL: {processed_image_url}")
            except Exception as e:
                print(f"Error processing book {book['title']}: {str(e)}")
                continue

        return processed_books
    except Exception as e:
        print(f"Error in get_recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_trending_books() -> List[Dict]:
    search_results = google_books_api.search_books("subject:fiction&orderBy=newest")
    trending_books = []
    if search_results and "items" in search_results:
        for item in search_results["items"]:
            book_details = item["volumeInfo"]
            book_id = item["id"]
            book_description = await get_book_description(book_id)
            trending_book = {
                "id": book_id,
                "title": book_details.get("title"),
                "release_year": int(book_details.get("publishedDate", "0")[:4]) if book_details.get("publishedDate") else None,
                "release_date": book_details.get("publishedDate"),
                "image_url": book_details.get("imageLinks", {}).get("thumbnail"),
                "rating": book_details.get("averageRating"),
                "pages": book_details.get("pageCount"),
                "genres": book_details.get("categories"),
                "description": book_description,
                "price": generate_random_price()
            }
            trending_books.append(trending_book)
    return trending_books