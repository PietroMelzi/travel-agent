import logging
import os
from pathlib import Path
from typing import List, Optional
from serpapi import GoogleSearch
import pandas as pd

log = logging.getLogger(__name__)

AIRPORTS_CSV = Path(__file__).resolve().parent / "airports.csv"


def find_iata_codes(city: str) -> List[str]:
    """
    Find IATA codes for a city

    Args:
        city: The city to find IATA codes for

    Returns:
        List of IATA codes for airports in the given city.

    Raises:
        FileNotFoundError: If the airports CSV file is missing.
    """
    if not city or not str(city).strip():
        log.warning("find_iata_codes called with empty city")
        return []

    try:
        df = pd.read_csv(AIRPORTS_CSV)
    except FileNotFoundError:
        log.error("Airports file not found: %s", AIRPORTS_CSV)
        raise
    except Exception as e:
        log.exception("Error reading airports file: %s", e)
        raise

    mask = df["City"].str.contains(city, case=False, na=False, regex=False)
    codes = df.loc[mask, "IATA"].dropna().unique().tolist()
    log.info("find_iata_codes(%s) -> %s", city, codes)
    return codes


def get_location_kgmid(city: str) -> Optional[str]:
    """
    Look up a city via SearchAPI Google Flights location search and return
    the kgmid of the first matching location.
    """
    if not city or not str(city).strip():
        log.warning("get_location_kgmid called with empty city")
        return None

    api_key = os.getenv("SERP_API_KEY")
    if not api_key:
        log.error("SERP_API_KEY environment variable is not set")
        return "Flight search is not configured: missing SERP_API_KEY. Please set it in your environment."


    params = {
        "engine": "google_flights_autocomplete",
        "q": city.strip(),
        "api_key": api_key,
    }
    log.info("get_location_kgmid: q=%s", city.strip())

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
    except Exception as e:
        log.exception("Google Flights API error: %s", e)
        return f"Error while searching for flights: {e!s}. Please try again later."

    locations = results.get("suggestions") or []
    kgmid = locations[0].get("id") if locations else None
    log.info("get_location_kgmid(%s) -> %s", city, kgmid)
    return kgmid
