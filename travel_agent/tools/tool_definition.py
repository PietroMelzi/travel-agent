import json
import logging
import os
import requests
from typing import Tuple
from agents import function_tool
from serpapi import GoogleSearch

from travel_agent.tools.utils import get_location_kgmid

log = logging.getLogger(__name__)


@function_tool
def find_flights(departure: str, arrival: str, departure_date: str, return_date: str) -> Tuple[str, str]:
    """
    Find flights to a destination

    Args:
        departure: The origin of the flight
        arrival: The destination of the flight
        departure_date: The departure date of the flight
        return_date: The return date of the flight

    Returns:
        Tuple of (one_way_result, return_result).
        - one_way_result: Raw response from the initial Google Flights API search (outbound).
        - return_result: If the first response contains a non-empty best_flight array,
          the raw response from a follow-up search with departure_token (return leg);
          otherwise None.
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
        "outbound_date": departure_date,
        "api_key": api_key,
        "deep_search": True
    }

    if return_date:
        params = {**params, "return_date": return_date, "type": "1"}
    else:
        params = {**params, "type": "2"}

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        log.info("Google Flights API response received")

        outbound = (results.get("best_flights") or results.get("other_flights")) if isinstance(results, dict) else None
        if outbound and isinstance(outbound, list) and len(outbound) > 0:
            first = outbound[0]
            departure_token = first.get("departure_token") if isinstance(first, dict) else None
            if departure_token:
                params2 = {**params, "departure_token": departure_token}
                search2 = GoogleSearch(params2)
                second_results = search2.get_dict()
                log.info("Google Flights API follow-up response received (departure_token)")
                return_flights = (second_results.get("best_flights") or second_results.get("other_flights")) if isinstance(second_results, dict) else None
                return (outbound, return_flights)

        return (outbound, None)
    except Exception as e:
        log.exception("Google Flights API error: %s", e)
        return f"Error while searching for flights: {e!s}. Please try again later."


@function_tool
def find_hotels(city: str, country_code: str, check_in_date: str, check_out_date: str, occupancies: int = 2) -> str:
    """
    Find hotels in a destination

    Args:
        city: The city of the hotel
        country_code: The country code in ISO 2-letter format
        check_in_date: The check-in date of the hotel
        check_out_date: The check-out date of the hotel
        occupancies: The number of guests in the room

    Returns:
        JSON: {"hotels": [{"id": "<hotel_id>", "name": "<hotel_name>", "rooms": [{"name": "<room_name>", "price": <float>, "currency": "<EUR|...>"}]}]}
    """
    log.info(
        "find_hotels: city=%s, country_code=%s, check_in=%s, check_out=%s, occupancies=%s",
        city, country_code, check_in_date, check_out_date, occupancies,
    )
    api_key = os.getenv("LITE_API_KEY")
    if not api_key:
        log.error("LITE_API_KEY environment variable is not set")
        return "Hotel search is not configured: missing LITE_API_KEY. Please set it in your environment."

    url = "https://api.liteapi.travel/v3.0/hotels/rates"
    payload = {
        "occupancies": [{"adults": occupancies}],
        "currency": "EUR",
        "guestNationality": "ES",
        "checkin": check_in_date,
        "checkout": check_out_date,
        "cityName": city,
        "countryCode": country_code,
        "limit": 50,
        "maxRatesPerHotel": 5
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "X-API-Key": api_key,
    }

    response = requests.post(url, json=payload, headers=headers)
    log.info("liteAPI Hotel Rates response received for %s, %s", city, country_code)

    try:
        data = response.json()
    except Exception as e:
        log.exception("liteAPI Hotel Rates invalid JSON: %s", e)
        return f"Hotel search failed: invalid response from API. {e!s}"

    if response.status_code != 200:
        return f"Hotel search failed: API returned {response.status_code}. {data.get('message', data.get('error', ''))}"

    # Build id -> name from hotels array (same shape as a.json)
    hotels_arr = data.get("hotels") or []
    hotels_map = {
        str(h["id"]): h.get("name", "—")
        for h in hotels_arr
        if isinstance(h, dict) and h.get("id") is not None
    }

    # Reduce data[] to: hotel id, name, and per room: name, price, currency
    out = []
    for d in data.get("data") or []:
        if not isinstance(d, dict):
            continue
        hid = d.get("hotelId")
        if not hid:
            continue
        hid = str(hid)
        hname = hotels_map.get(hid, "—")
        rooms = []
        for rt in d.get("roomTypes") or []:
            if not isinstance(rt, dict):
                continue
            rates = rt.get("rates") or []
            rname = rates[0].get("name") if rates and isinstance(rates[0], dict) else "Room"
            offer = rt.get("offerRetailRate") or {}
            amount = offer.get("amount")
            if amount is None:
                continue
            currency = offer.get("currency") or "EUR"
            rooms.append({"name": rname, "price": amount, "currency": currency})
        if rooms:
            out.append({"id": hid, "name": hname, "rooms": rooms})

    return json.dumps({"hotels": out}, indent=2)


@function_tool
def find_cost_of_living(city: str, country: str) -> str:
    """
    Get cost-of-living and price data for a city.

    Args:
        city: The city to look up (e.g. "Madrid", "Tokyo").
        country: The country the city is in (e.g. "Spain", "Japan").

    Returns:
        JSON from the RapidAPI cost-of-living API (prices, categories, etc.).
    """
    url = "https://cost-of-living-and-prices.p.rapidapi.com/prices"

    querystring = {"city_name": city, "country_name": country}

    headers = {
        "x-rapidapi-key": os.getenv("RAPID_API_KEY"),
        "x-rapidapi-host": "cost-of-living-and-prices.p.rapidapi.com"
    }

    log.info("find_cost_of_living: city=%s, country=%s", city, country)
    response = requests.get(url, headers=headers, params=querystring)
    log.info("Cost-of-living API response received for %s, %s", city, country)
    return response.json()
