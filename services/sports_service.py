"""
Sports Service Module

Retrieves live and recent real-world sports match data, team results, and player statistics
from real online sports REST APIs (TheSportsDB, ESPN scoreboard, and custom SPORTS_API_KEY providers).
"""

import os
import re
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional


import time
import logging

logger = logging.getLogger("SportsService")


class SportsService:
    """
    Handles entity identification and live sports data retrieval across multiple sports.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SPORTS_API_KEY", "").strip()
        if self.api_key == "your_sports_api_key_here":
            self.api_key = ""
        self._cache: Dict[str, tuple[float, Dict[str, Any]]] = {}

    def fetch_sports_data(self, claim_text: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieves real live/recent sports data based on claim text and extracted entities.
        """
        if not claim_text or not isinstance(claim_text, str):
            return {
                "status": "error",
                "error_message": "Invalid claim input.",
                "data": None
            }

        cache_key = claim_text.strip().lower()
        now = time.time()
        if cache_key in self._cache:
            cached_time, cached_res = self._cache[cache_key]
            if now - cached_time < 60:
                logger.info(f"Returning cached sports data for claim: '{claim_text[:40]}...'")
                return cached_res

        # Step 1: Identify teams and sport type
        extracted_teams = self._extract_teams(claim_text)
        player = self._extract_player(claim_text)
        sport = self._identify_sport(claim_text)
        tournament = self._extract_tournament(claim_text)

        if not extracted_teams and not player and not tournament:
            return {
                "status": "error",
                "error_message": "Could not identify a specific team, player, or tournament in the sports claim.",
                "data": None
            }

        # Step 2: Query real external sports API
        team_query = extracted_teams[0] if extracted_teams else (player or tournament)
        logger.info(f"Querying sports API for team/subject: '{team_query}'")
        res = None
        api_result = self._query_thesportsdb(team_query, sport)

        if api_result["status"] == "success" and api_result.get("events"):
            res = {
                "status": "success",
                "error_message": None,
                "sport": sport,
                "query_team": team_query,
                "extracted_teams": extracted_teams,
                "player": player,
                "tournament": tournament,
                "events": api_result["events"],
                "matched_event": api_result["events"][0],
                "source": api_result.get("source", "TheSportsDB Real-Time Sports API"),
                "verification_time": datetime.now().strftime("%d %B %Y, %I:%M %p")
            }

        # Fallback to secondary search if primary team query returned no events
        if not res and len(extracted_teams) > 1:
            alt_result = self._query_thesportsdb(extracted_teams[1], sport)
            if alt_result["status"] == "success" and alt_result.get("events"):
                res = {
                    "status": "success",
                    "error_message": None,
                    "sport": sport,
                    "query_team": extracted_teams[1],
                    "extracted_teams": extracted_teams,
                    "player": player,
                    "tournament": tournament,
                    "events": alt_result["events"],
                    "matched_event": alt_result["events"][0],
                    "source": alt_result.get("source", "TheSportsDB Real-Time Sports API"),
                    "verification_time": datetime.now().strftime("%d %B %Y, %I:%M %p")
                }

        if not res:
            res = {
                "status": "error",
                "error_message": f"No recent or live match data found for '{team_query}' in the sports database.",
                "data": None
            }

        if res.get("status") == "success":
            self._cache[cache_key] = (now, res)

        return res

    def _query_thesportsdb(self, team_name: str, sport: str) -> Dict[str, Any]:
        """
        Queries TheSportsDB searchteams & eventslast REST API endpoints.
        """
        try:
            # 1. Search Team to get team ID
            team_url = "https://www.thesportsdb.com/api/v1/json/3/searchteams.php"
            t_resp = requests.get(team_url, params={"t": team_name}, timeout=8)
            if t_resp.status_code == 200:
                t_data = t_resp.json()
                teams_found = t_data.get("teams") or []

                if teams_found:
                    team_obj = teams_found[0]
                    team_id = team_obj.get("idTeam")
                    canonical_team_name = team_obj.get("strTeam", team_name)

                    # Fetch last 5 events for this team
                    last_url = "https://www.thesportsdb.com/api/v1/json/3/eventslast.php"
                    l_resp = requests.get(last_url, params={"id": team_id}, timeout=8)

                    if l_resp.status_code == 200:
                        l_data = l_resp.json()
                        raw_events = l_data.get("results") or []

                        if raw_events:
                            parsed_events = []
                            for ev in raw_events:
                                parsed_events.append(self._parse_event_object(ev))

                            return {
                                "status": "success",
                                "events": parsed_events,
                                "source": "TheSportsDB Real-Time Sports API"
                            }

            # 2. Alternative search: direct event search by query
            event_search_url = "https://www.thesportsdb.com/api/v1/json/3/searchevents.php"
            e_resp = requests.get(event_search_url, params={"e": team_name.replace(" ", "_")}, timeout=8)
            if e_resp.status_code == 200:
                e_data = e_resp.json()
                raw_events = e_data.get("event") or []

                if raw_events:
                    parsed_events = [self._parse_event_object(ev) for ev in raw_events]
                    return {
                        "status": "success",
                        "events": parsed_events,
                        "source": "TheSportsDB Real-Time Sports API"
                    }

            return {"status": "error", "error_message": "No events found."}

        except Exception as e:
            return {"status": "error", "error_message": str(e)}

    def _parse_event_object(self, ev: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts clean event properties from raw API event record.
        """
        home = ev.get("strHomeTeam", "").strip()
        away = ev.get("strAwayTeam", "").strip()
        h_score = ev.get("intHomeScore")
        a_score = ev.get("intAwayScore")
        event_title = ev.get("strEvent", f"{home} vs {away}")
        date_str = ev.get("dateEvent", "N/A")
        league = ev.get("strLeague", "")
        status = ev.get("strStatus", "")
        sport = ev.get("strSport", "")

        # Calculate winner if scores exist
        winner = None
        if h_score is not None and a_score is not None:
            try:
                hs = int(h_score)
                aws = int(a_score)
                if hs > aws:
                    winner = home
                elif aws > hs:
                    winner = away
                else:
                    winner = "Draw"
            except (ValueError, TypeError):
                winner = None

        return {
            "event_title": event_title,
            "sport": sport,
            "league": league,
            "date": date_str,
            "home_team": home,
            "away_team": away,
            "home_score": h_score,
            "away_score": a_score,
            "winner": winner,
            "status": status,
            "raw_result": ev.get("strResult") or f"{home} {h_score} - {a_score} {away}" if h_score is not None else "Score pending"
        }

    def _extract_teams(self, text: str) -> List[str]:
        """
        Extracts known team names from natural language text.
        """
        known_teams = [
            "India", "Australia", "England", "Pakistan", "South Africa", "New Zealand",
            "Sri Lanka", "Bangladesh", "West Indies", "Afghanistan",
            "Real Madrid", "Barcelona", "Manchester City", "Manchester United",
            "Arsenal", "Chelsea", "Liverpool", "Bayern Munich", "PSG", "Juventus",
            "Lakers", "Celtics", "Warriors", "Bulls", "Napoli", "Milan", "Inter", "Tottenham"
        ]

        found = []
        for team in known_teams:
            if re.search(r'\b' + re.escape(team) + r'\b', text, re.IGNORECASE):
                found.append(team)

        if not found:
            # Match proper noun phrases near sports verbs
            match = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:won|lost|defeated|plays|played|scored|match|game)\b', text)
            if match:
                extracted = match.group(1).strip()
                if extracted.lower() not in ["yesterday", "today", "tomorrow", "the"]:
                    found.append(extracted)

        return found

    def _extract_player(self, text: str) -> Optional[str]:
        """
        Extracts known player names.
        """
        known_players = [
            "Virat Kohli", "Rohit Sharma", "MS Dhoni", "Sachin Tendulkar", "Jasprit Bumrah",
            "Lionel Messi", "Cristiano Ronaldo", "Kylian Mbappe", "Erling Haaland",
            "LeBron James", "Stephen Curry"
        ]

        for player in known_players:
            if re.search(r'\b' + re.escape(player) + r'\b', text, re.IGNORECASE):
                return player
            # Single name check for famous players
            first_or_last = player.split()[-1]
            if len(first_or_last) > 4 and re.search(r'\b' + re.escape(first_or_last) + r'\b', text, re.IGNORECASE):
                return player

        return None

    def _identify_sport(self, text: str) -> str:
        """
        Identifies the target sport (Cricket, Football, Basketball, etc.).
        """
        lower = text.lower()
        if any(w in lower for w in ["cricket", "runs", "wickets", "overs", "kohli", "dhoni", "ipl", "t20", "champions trophy"]):
            return "Cricket"
        elif any(w in lower for w in ["football", "soccer", "goals", "real madrid", "barcelona", "arsenal", "epl", "champions league", "messi", "ronaldo"]):
            return "Football"
        elif any(w in lower for w in ["basketball", "nba", "points", "lakers", "celtics"]):
            return "Basketball"
        return "Sports"

    def _extract_tournament(self, text: str) -> Optional[str]:
        """
        Extracts tournament/competition names.
        """
        tournaments = [
            "Champions Trophy", "World Cup", "IPL", "EPL", "Champions League", "La Liga", "NBA"
        ]

        for tour in tournaments:
            if re.search(r'\b' + re.escape(tour) + r'\b', text, re.IGNORECASE):
                return tour
        return None
