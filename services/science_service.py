"""
Science Service Module

Retrieves real-world scientific data and verified scientific reference information
from authoritative external APIs (Wikimedia Scientific REST API, NASA Open API, PubChem NIH API).
Supports optional NASA_API_KEY / SCIENCE_API_KEY from .env with automatic public API fallback.
"""

import os
import re
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional


import time
import logging

logger = logging.getLogger("ScienceService")


class ScienceService:
    """
    Handles scientific entity detection and live reference data retrieval from external APIs.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("NASA_API_KEY", "").strip() or os.getenv("SCIENCE_API_KEY", "").strip()
        if self.api_key in ["your_science_api_key_here", "DEMO_KEY"]:
            self.api_key = ""
        
        self.headers = {
            "User-Agent": "RealTimeFactVerifier/1.0 (contact@factverifier.org; academic verification app)"
        }
        self._cache: Dict[str, tuple[float, Dict[str, Any]]] = {}

    def fetch_science_data(self, claim_text: str, entities: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Retrieves real live scientific reference information for a natural language claim.
        """
        if not claim_text or not isinstance(claim_text, str):
            return {
                "status": "error",
                "error_message": "Invalid claim text input.",
                "data": None
            }

        cleaned_claim = claim_text.strip()
        cache_key = cleaned_claim.lower()
        now = time.time()

        if cache_key in self._cache:
            cached_time, cached_res = self._cache[cache_key]
            if now - cached_time < 60:
                logger.info(f"Returning cached science data for: '{cleaned_claim[:40]}...'")
                return cached_res

        # Step 1: Identify key scientific subjects/entities
        subject = self._extract_science_subject(cleaned_claim)

        if not subject:
            return {
                "status": "error",
                "error_message": "Could not identify a recognized scientific concept or entity in the claim.",
                "data": None
            }

        logger.info(f"Querying scientific APIs for concept/subject: '{subject}'")
        res = None

        # Step 2: Query appropriate REST API based on topic (NASA for NASA/exoplanet, Wikipedia/PubChem for general science)
        if "nasa" in cleaned_claim.lower() or "exoplanet" in cleaned_claim.lower():
            nasa_res = self._query_nasa_api(subject)
            if nasa_res["status"] == "success":
                res = nasa_res

        if not res and "water" in cleaned_claim.lower() and any(k in cleaned_claim.lower() for k in ["freeze", "freezes", "boil", "boils", "0", "100", "celsius"]):
            pubchem_res = self._query_pubchem_api("water")
            if pubchem_res["status"] == "success":
                res = pubchem_res

        if not res:
            # Query Wikimedia / Wikipedia Scientific REST API
            wiki_res = self._query_wiki_api(subject)
            if wiki_res["status"] == "success":
                res = wiki_res

        if not res:
            res = {
                "status": "error",
                "error_message": f"Unable to find reliable scientific reference data for '{subject}'.",
                "data": None
            }

        if res.get("status") == "success":
            self._cache[cache_key] = (now, res)

        return res

    def _query_wiki_api(self, topic: str) -> Dict[str, Any]:
        """
        Queries Wikipedia/Wikimedia Scientific Knowledge Base REST API.
        """
        try:
            # Format topic string for URL path
            formatted_topic = topic.replace(" ", "_")
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{formatted_topic}"
            
            resp = requests.get(url, headers=self.headers, timeout=8)
            if resp.status_code != 200:
                # Try search API if direct page path returns 404
                search_url = "https://en.wikipedia.org/w/api.php"
                params = {
                    "action": "query",
                    "list": "search",
                    "srsearch": topic,
                    "format": "json"
                }
                s_resp = requests.get(search_url, params=params, headers=self.headers, timeout=8)
                if s_resp.status_code == 200:
                    s_data = s_resp.json()
                    search_results = s_data.get("query", {}).get("search", [])
                    if search_results:
                        first_title = search_results[0]["title"].replace(" ", "_")
                        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{first_title}"
                        resp = requests.get(url, headers=self.headers, timeout=8)

            if resp.status_code == 200:
                data = resp.json()
                title = data.get("title", topic)
                extract = data.get("extract", "")
                page_url = data.get("content_urls", {}).get("desktop", {}).get("page", f"https://en.wikipedia.org/wiki/{formatted_topic}")

                return {
                    "status": "success",
                    "error_message": None,
                    "topic": topic,
                    "title": title,
                    "extract": extract,
                    "source_name": "Wikimedia Scientific Knowledge Base REST API",
                    "source_url": page_url,
                    "verification_time": datetime.now().strftime("%d %B %Y, %I:%M %p"),
                    "raw_data": data
                }

            return {"status": "error", "error_message": f"Science API query returned HTTP status {resp.status_code}."}

        except Exception as e:
            return {"status": "error", "error_message": f"Network or scientific API exception: {str(e)}"}

    def _query_nasa_api(self, query: str) -> Dict[str, Any]:
        """
        Queries NASA Open REST API (images-api.nasa.gov search catalog).
        """
        try:
            url = "https://images-api.nasa.gov/search"
            params = {"q": query}
            resp = requests.get(url, params=params, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("collection", {}).get("items", [])
                if items:
                    item_data = items[0].get("data", [{}])[0]
                    title = item_data.get("title", query)
                    description = item_data.get("description", "Official NASA Discovery Record.")

                    return {
                        "status": "success",
                        "error_message": None,
                        "topic": query,
                        "title": title,
                        "extract": description[:300] + "...",
                        "source_name": "NASA Open Science REST API Catalog",
                        "source_url": "https://api.nasa.gov",
                        "verification_time": datetime.now().strftime("%d %B %Y, %I:%M %p"),
                        "raw_data": item_data
                    }
            return {"status": "error", "error_message": "NASA API search returned no results."}
        except Exception as e:
            return {"status": "error", "error_message": str(e)}

    def _query_pubchem_api(self, compound: str) -> Dict[str, Any]:
        """
        Queries PubChem NIH Chemical & Physical Property API.
        """
        try:
            url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{compound}/description/JSON"
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                info_list = data.get("InformationList", {}).get("Information", [])
                for info in info_list:
                    if "Description" in info:
                        return {
                            "status": "success",
                            "error_message": None,
                            "topic": compound,
                            "title": "Water (Chemical Properties)",
                            "extract": info["Description"],
                            "source_name": "PubChem NIH Chemical Database API",
                            "source_url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{compound}",
                            "verification_time": datetime.now().strftime("%d %B %Y, %I:%M %p"),
                            "raw_data": info
                        }
            return {"status": "error", "error_message": "PubChem search failed."}
        except Exception as e:
            return {"status": "error", "error_message": str(e)}

    def _extract_science_subject(self, text: str) -> Optional[str]:
        """
        Extracts candidate scientific topic or entity from natural language text.
        """
        lower_text = text.lower()

        known_science_entities = [
            ("moon", "Moon"),
            ("sun", "Sun"),
            ("earth", "Earth"),
            ("jupiter", "Jupiter"),
            ("mars", "Mars"),
            ("water", "Water"),
            ("speed of light", "Speed_of_light"),
            ("exoplanet", "Exoplanet"),
            ("nasa", "NASA"),
            ("gravity", "Gravity"),
            ("atom", "Atom"),
            ("dna", "DNA")
        ]

        # 1. Match known entities directly
        for kw, canonical in known_science_entities:
            if re.search(r'\b' + re.escape(kw) + r'\b', lower_text):
                return canonical

        # 2. Extract noun phrase before or after verb
        match = re.search(r'\b(?:the|a|an)?\s*([A-Za-z0-9]+)\s+(?:is|freezes|revolves|orbits|discovered)\b', text, re.IGNORECASE)
        if match:
            extracted = match.group(1).strip()
            if extracted.lower() not in ["it", "this", "that", "there", "what", "how"]:
                return extracted.title()

        return None
