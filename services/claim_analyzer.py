"""
Claim Analyzer Service Module

Provides domain classification and structured entity extraction for natural language claims.
Supported Categories: weather, sports, movies, science, news, unknown.

Designed with a modular architecture so rule-based engine can be augmented or swapped
with ML/LLM models in future iterations.
"""

import re
from typing import Dict, Any, List, Optional


class ClaimAnalyzer:
    """
    Analyzes natural language claims to determine category, location, subject,
    date/time, key metrics, and extracted keywords.
    """

    def __init__(self):
        # Category Keyword Lexicons
        self.category_keywords = {
            "weather": [
                "temperature", "temp", "rain", "raining", "rainy", "degree", "degrees",
                "°c", "°f", "celsius", "fahrenheit", "weather", "sunny", "cloudy",
                "forecast", "wind", "humidity", "snow", "storm", "climate", "hot", "cold", "weather in"
            ],
            "sports": [
                "match", "game", "won", "lost", "scored", "runs", "goals", "wicket", "wickets",
                "cricket", "football", "soccer", "basketball", "tennis", "tournament",
                "cup", "championship", "nba", "ipl", "epl", "barcelona", "real madrid",
                "kohli", "virat", "messi", "ronaldo", "player", "team", "stadium",
                "latest match", "last game", "yesterday's match", "defeated"
            ],
            "movies": [
                "movie", "film", "released", "release", "directed", "director",
                "actor", "actress", "acted", "cast", "starring", "box office",
                "cinema", "interstellar", "avatar", "forrest gump", "inception", "titanic",
                "the dark knight", "dark knight", "nolan", "christopher nolan", "tom hanks",
                "sequel", "rating", "rated", "imdb", "released in", "directed by"
            ],
            "science": [
                "speed of light", "revolves", "revolve", "orbit", "freeze", "freezes",
                "boil", "boils", "gravity", "planet", "solar system", "atom",
                "molecule", "element", "celsius", "pressure", "atmospheric",
                "dna", "quantum", "physics", "chemistry", "biology", "space",
                "light speed", "km/s", "galaxy", "moon", "sun", "earth", "satellite", "star", "nasa", "exoplanet",
                "natural satellite", "fourth planet", "4th planet", "largest planet", "revolves around"
            ],
            "news": [
                "minister", "prime minister", "president", "government", "policy",
                "election", "announced", "announcement", "parliament", "official",
                "statement", "tax", "treaty", "economy", "governor", "law", "bill"
            ]
        }

        # Known Locations List for fast reference
        self.known_locations = [
            "vijayawada", "hyderabad", "mumbai", "delhi", "bengaluru", "chennai",
            "kolkata", "london", "new york", "paris", "tokyo", "sydney", "washington",
            "barcelona", "madrid", "beijing", "berlin", "rome"
        ]

    def analyze(self, claim: str) -> Dict[str, Any]:
        """
        Main entry point to analyze a natural language claim string.
        """
        # Input validation
        if not isinstance(claim, str) or not claim.strip():
            return {
                "category": "unknown",
                "location": None,
                "subject": None,
                "date": None,
                "keywords": [],
                "claim_text": claim if isinstance(claim, str) else ""
            }

        cleaned_claim = claim.strip()
        lower_claim = cleaned_claim.lower()

        # Step 1: Detect Category
        category = self._detect_category(lower_claim)

        # Step 2: Extract Entities (Location, Date, Subject, Keywords)
        location = self._extract_location(cleaned_claim, lower_claim)
        date = self._extract_date(lower_claim)
        subject = self._extract_subject(lower_claim, category)
        keywords = self._extract_keywords(lower_claim)

        return {
            "category": category,
            "location": location,
            "subject": subject,
            "date": date,
            "keywords": keywords,
            "claim_text": cleaned_claim
        }

    def _detect_category(self, lower_claim: str) -> str:
        """
        Scores input text against keyword lexicons to determine category.
        """
        category_scores: Dict[str, int] = {cat: 0 for cat in self.category_keywords}

        # Multi-word phrase matches get higher weight
        for cat, keywords in self.category_keywords.items():
            for kw in keywords:
                if " " in kw and kw in lower_claim:
                    category_scores[cat] += 3
                elif re.search(r'\b' + re.escape(kw) + r'\b', lower_claim):
                    category_scores[cat] += 1

        # Direct domain-specific regex indicators
        if re.search(r'\b\d+\s*(degrees?|°c|°f)\b', lower_claim):
            category_scores["weather"] += 2
        if re.search(r'\b(won|lost|scored|match|runs|goals|wickets)\b', lower_claim):
            category_scores["sports"] += 2
        if re.search(r'\b(released in|directed by|starred in|acted in)\b', lower_claim):
            category_scores["movies"] += 2
        if re.search(r'\b(speed of light|freezes at|revolves around|discovered a new planet|natural satellite|is a star|solar system|largest planet)\b', lower_claim):
            category_scores["science"] += 3
        if re.search(r'\b(announced|prime minister|president|government|policy)\b', lower_claim):
            category_scores["news"] += 2

        # Find highest scoring category
        max_score = 0
        best_category = "unknown"

        for cat, score in category_scores.items():
            if score > max_score:
                max_score = score
                best_category = cat

        return best_category if max_score > 0 else "unknown"

    def _extract_location(self, original_claim: str, lower_claim: str) -> Optional[str]:
        """
        Extracts location from text using prepositions, capitalized words, or known cities.
        """
        # 1. Match prepositions followed by proper nouns: "in Vijayawada", "at London"
        match = re.search(r'\b(?:in|at|for|near)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', original_claim)
        if match:
            extracted = match.group(1).strip()
            # Ignore common non-location capitalized words if any
            if extracted.lower() not in ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december", "today", "yesterday"]:
                return extracted

        # 2. Check known city list in lower claim
        for city in self.known_locations:
            if re.search(r'\b' + re.escape(city) + r'\b', lower_claim):
                return city.title()

        return None

    def _extract_date(self, lower_claim: str) -> Optional[str]:
        """
        Extracts temporal expressions (e.g., today, yesterday, 2024, 2025).
        """
        # Check relative dates
        for rel_date in ["today", "yesterday", "tomorrow", "latest", "recent"]:
            if re.search(r'\b' + rel_date + r'\b', lower_claim):
                return rel_date

        # Check 4-digit years (1900-2099)
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', lower_claim)
        if year_match:
            return year_match.group(1)

        return None

    def _extract_subject(self, lower_claim: str, category: str) -> Optional[str]:
        """
        Extracts the main topic/subject of the claim based on category.
        """
        if category == "weather":
            if "temperature" in lower_claim or "temp" in lower_claim or "degree" in lower_claim:
                return "temperature"
            elif "rain" in lower_claim or "raining" in lower_claim:
                return "rain"
            elif "snow" in lower_claim:
                return "snow"
            return "weather condition"

        elif category == "sports":
            if "cricket" in lower_claim:
                return "cricket match"
            elif "football" in lower_claim or "soccer" in lower_claim:
                return "football match"
            elif "runs" in lower_claim or "scored" in lower_claim:
                return "score / statistics"
            elif "won" in lower_claim or "lost" in lower_claim:
                return "match result"
            return "sports event"

        elif category == "movies":
            if "released" in lower_claim or "release" in lower_claim:
                return "release date"
            elif "directed" in lower_claim or "director" in lower_claim:
                return "director"
            elif "acted" in lower_claim or "cast" in lower_claim or "starring" in lower_claim:
                return "cast"
            return "movie detail"

        elif category == "science":
            if "speed of light" in lower_claim:
                return "speed of light"
            elif "freeze" in lower_claim or "freezes" in lower_claim:
                return "freezing point"
            elif "revolves" in lower_claim or "orbit" in lower_claim:
                return "planetary motion"
            elif "planet" in lower_claim or "nasa" in lower_claim:
                return "astronomy discovery"
            return "scientific fact"

        elif category == "news":
            if "policy" in lower_claim:
                return "government policy"
            elif "election" in lower_claim:
                return "election"
            elif "announced" in lower_claim:
                return "official announcement"
            return "news event"

        return None

    def _extract_keywords(self, lower_claim: str) -> List[str]:
        """
        Extracts meaningful tokens (removing stop words and punctuation).
        """
        stop_words = {
            "a", "an", "the", "is", "was", "are", "were", "in", "at", "on", "of", "to",
            "for", "with", "by", "about", "against", "into", "through", "during", "before",
            "after", "above", "below", "from", "up", "down", "in", "out", "on", "off", "over",
            "under", "again", "further", "then", "once", "here", "there", "when", "where",
            "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some",
            "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
            "s", "t", "can", "will", "just", "don", "should", "now", "did", "does", "do"
        }

        # Tokenize by word characters
        words = re.findall(r'\b[a-zA-Z0-9°]+\b', lower_claim)
        keywords = [w for w in words if w not in stop_words and len(w) > 1]
        return keywords


# Standalone utility function wrapper for clean caller access
def analyze_claim(claim: str) -> Dict[str, Any]:
    """
    Functional wrapper around ClaimAnalyzer.analyze(claim).
    """
    analyzer = ClaimAnalyzer()
    return analyzer.analyze(claim)
