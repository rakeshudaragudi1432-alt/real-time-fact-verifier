"""
Movie Service Module

Retrieves real-world movie details (title, release date/year, director, cast, genre, rating, plot)
from external Movie REST APIs (OMDb / IMDb / TMDB).
Supports MOVIE_API_KEY from .env with automatic public API fallback.
"""

import os
import re
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional


import time
import logging

logger = logging.getLogger("MovieService")


class MovieService:
    """
    Handles movie identification and live metadata retrieval from external APIs.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MOVIE_API_KEY", "").strip()
        if self.api_key == "your_movie_api_key_here":
            self.api_key = ""
        self._cache: Dict[str, tuple[float, Dict[str, Any]]] = {}

    def fetch_movie_info(self, claim_text: str, entities: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Retrieves live movie information from API for a natural language claim.
        """
        if not claim_text or not isinstance(claim_text, str):
            return {
                "status": "error",
                "error_message": "Invalid claim text input.",
                "data": None
            }

        cleaned_text = claim_text.strip()
        cache_key = cleaned_text.lower()
        now = time.time()

        if cache_key in self._cache:
            cached_time, cached_res = self._cache[cache_key]
            if now - cached_time < 60:
                logger.info(f"Returning cached movie data for: '{cleaned_text[:40]}...'")
                return cached_res

        # Step 1: Extract movie title from claim
        extracted_title = self._extract_movie_title(cleaned_text)

        if not extracted_title:
            return {
                "status": "error",
                "error_message": "Could not identify a specific movie title in the claim.",
                "data": None
            }

        # Step 2: Query real Movie API
        logger.info(f"Querying OMDb/IMDb movie API for title: '{extracted_title}'")
        res = None
        api_result = self._query_omdb_api(extracted_title)

        if api_result["status"] == "success":
            res = api_result

        if not res:
            # Retry with cleaned title keywords if direct title search failed
            alt_title = re.sub(r'(?:movie|film|released in|directed by|acted in|starring)', '', extracted_title, flags=re.IGNORECASE).strip()
            if alt_title and alt_title != extracted_title:
                alt_result = self._query_omdb_api(alt_title)
                if alt_result["status"] == "success":
                    res = alt_result

        if not res:
            res = {
                "status": "error",
                "error_message": f"Movie '{extracted_title}' could not be found in live movie databases.",
                "data": None
            }

        if res.get("status") == "success":
            self._cache[cache_key] = (now, res)

        return res

    def _query_omdb_api(self, title: str) -> Dict[str, Any]:
        """
        Queries OMDb API for movie details.
        """
        # Determine API keys to attempt (configured key first, followed by public backup keys)
        keys_to_try = []
        if self.api_key:
            keys_to_try.append(self.api_key)
        keys_to_try.extend(["trilogy", "b793b6b0", "1481b7e"])

        for key in keys_to_try:
            try:
                url = "http://www.omdbapi.com/"
                params = {
                    "t": title,
                    "apikey": key,
                    "plot": "short"
                }
                resp = requests.get(url, params=params, timeout=8)
                if resp.status_code != 200:
                    continue

                data = resp.json()
                if data.get("Response") == "True":
                    # Successfully found movie
                    actors_list = [a.strip() for a in data.get("Actors", "").split(",") if a.strip()]
                    genre_list = [g.strip() for g in data.get("Genre", "").split(",") if g.strip()]

                    rating_float = None
                    try:
                        rating_float = float(data.get("imdbRating", 0))
                    except (ValueError, TypeError):
                        rating_float = None

                    return {
                        "status": "success",
                        "error_message": None,
                        "title": data.get("Title", title),
                        "year": data.get("Year", "").strip(),
                        "release_date": data.get("Released", "N/A"),
                        "director": data.get("Director", "N/A"),
                        "writers": data.get("Writer", "N/A"),
                        "actors": actors_list,
                        "actors_raw": data.get("Actors", "N/A"),
                        "genre": genre_list,
                        "genre_raw": data.get("Genre", "N/A"),
                        "rating": rating_float,
                        "rating_raw": data.get("imdbRating", "N/A"),
                        "runtime": data.get("Runtime", "N/A"),
                        "plot": data.get("Plot", "N/A"),
                        "box_office": data.get("BoxOffice", "N/A"),
                        "poster": data.get("Poster", "N/A"),
                        "source": "OMDb / IMDb REST API",
                        "verification_time": datetime.now().strftime("%d %B %Y, %I:%M %p")
                    }
                elif "Movie not found" in data.get("Error", ""):
                    # Specific API response when title isn't found
                    return {
                        "status": "error",
                        "error_message": f"Movie '{title}' was not found in the database."
                    }
            except Exception:
                continue

        return {
            "status": "error",
            "error_message": f"Unable to retrieve movie details for '{title}' due to network or API issue."
        }

    def _extract_movie_title(self, text: str) -> Optional[str]:
        """
        Extracts candidate movie title using patterns or recognized titles.
        """
        # Common title extractions
        known_titles = [
            "Interstellar", "Titanic", "Avatar 3", "Avatar", "Inception", "Forrest Gump",
            "The Dark Knight", "Oppenheimer", "Barbie", "Gladiator", "The Matrix",
            "Pulp Fiction", "The Godfather", "Fight Club", "Jurassic Park", "Avengers",
            "Star Wars", "Harry Potter", "Spider-Man", "Iron Man"
        ]

        # 1. Match known titles explicitly
        for known in known_titles:
            if re.search(r'\b' + re.escape(known) + r'\b', text, re.IGNORECASE):
                return known

        # 2. Match patterns: "movie <Title> was", "<Title> was released", "<Title> was directed"
        match1 = re.search(r'(?:movie|film)\s+([A-Za-z0-9][a-zA-Z0-9\s:-]+?)(?:\s+was|\s+is|\s+directed|\s+released|\s+starred|\s+has|$)', text, re.IGNORECASE)
        if match1:
            title = match1.group(1).strip()
            if len(title) > 1:
                return title

        match2 = re.search(r'([A-Za-z0-9][a-zA-Z0-9\s:-]+?)\s+(?:was released|released in|was directed|directed by|starred in|acted in)', text, re.IGNORECASE)
        if match2:
            title = match2.group(1).strip()
            # Remove leading articles or filler words if present
            title = re.sub(r'^(?:the|a|an)\s+(?:movie|film)?\s*', '', title, flags=re.IGNORECASE).strip()
            # Ignore common person names if captured in match2
            if title.lower() not in ["christopher nolan", "tom hanks", "james cameron", "leonardo dicaprio", "steven spielberg"]:
                return title if title else match2.group(1).strip()

        match3 = re.search(r'(?:directed|starred in|acted in)\s+([A-Za-z0-9][a-zA-Z0-9\s:-]+)', text, re.IGNORECASE)
        if match3:
            return match3.group(1).strip()

        # 3. Fallback: extract main proper noun or first few words if short statement
        clean_words = [w for w in text.split() if w.lower() not in ["was", "released", "in", "directed", "by", "is", "a", "the", "movie", "film", "directed", "starring"]]
        if clean_words:
            return " ".join(clean_words[:3])

        return None
