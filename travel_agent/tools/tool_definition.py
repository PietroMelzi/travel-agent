from agents import function_tool


@function_tool
def find_flights(origin: str, destination: str, departure_date: str, return_date: str) -> str:
    """
    Find flights to a destination

    Args:
        origin: The origin of the flight
        destination: The destination of the flight
        departure_date: The departure date of the flight
        return_date: The return date of the flight
    """
    return f"Found flights from {origin} to {destination} for {departure_date} to {return_date}."


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