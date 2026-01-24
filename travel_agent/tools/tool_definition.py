import logging
import os

from agents import function_tool
from serpapi import GoogleSearch

from travel_agent.tools.utils import get_location_kgmid

log = logging.getLogger(__name__)


@function_tool
def find_flights(departure: str, arrival: str, departure_date: str, return_date: str) -> str:
    """
    Find flights to a destination

    Args:
        departure: The origin of the flight
        arrival: The destination of the flight
        departure_date: The departure date of the flight
        return_date: The return date of the flight
    """
    log.info(
        "find_flights: departure=%s, arrival=%s, departure_date=%s, return_date=%s",
        departure, arrival, departure_date, return_date,
    )
    departure_id = get_location_kgmid(departure)
    arrival_id = get_location_kgmid(arrival)
    log.info("Location kgmids: departure=%s, arrival=%s", departure_id, arrival_id)

    if not departure_id:
        log.warning("No location found for departure city: %s", departure)
        return f"No location found for departure city: {departure}. Please check the city name."
    if not arrival_id:
        log.warning("No location found for arrival city: %s", arrival)
        return f"No location found for arrival city: {arrival}. Please check the city name."

    api_key = os.getenv("SERP_API_KEY")
    if not api_key:
        log.error("SERP_API_KEY environment variable is not set")
        return "Flight search is not configured: missing SERP_API_KEY. Please set it in your environment."

    params = {
        "engine": "google_flights",
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "currency": "EUR",
        "type": "1",
        "outbound_date": departure_date,
        "return_date": return_date,
        "api_key": api_key,
        "deep_search": True
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        log.info("Google Flights API response received")
        return results
    except Exception as e:
        log.exception("Google Flights API error: %s", e)
        return f"Error while searching for flights: {e!s}. Please try again later."


@function_tool
def find_hotels(destination: str, check_in_date: str, check_out_date: str) -> str:
    """
    Find hotels in a destination

    Args:
        destination: The destination of the hotel
        check_in_date: The check-in date of the hotel
        check_out_date: The check-out date of the hotel
    """
    return f"Found hotels in {destination} for {check_in_date} to {check_out_date}."


map_tool_name_to_function = {
    "find_flights": find_flights,
    "find_hotels": find_hotels,
}