from httpx import AsyncClient
from urllib.parse import urlencode


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
GEONAME_URL = "https://secure.geonames.org/findNearbyPlaceNameJSON"
GEONAME_USERNAME = "benyirao"


async def search_place_by_city(city: str, count: int):
    """Get the cities, states, countries, lats, and lons for top-[count] matches."""
    async with AsyncClient(timeout=10.0) as client:
        response = await client.request(
            "GET",
            GEOCODING_URL,
            params={"name": city, "count": count, "language": "en"},
        )
        response.raise_for_status()

    # Filter only needed attributes. state and country are optional.
    places = response.json().get("results", [])
    return [
        {
            "place_id": place["id"],
            "city": place["name"],
            "state": place.get("admin1"),
            "country": place.get("country"),
            "lat": place["latitude"],
            "lon": place["longitude"],
        }
        for place in places
    ]


async def search_place_by_coordinates(lat: float, lon: float):
    """Get the city, state, and country names from lat and lon."""
    async with AsyncClient(timeout=10.0) as client:
        response = await client.request(
            "GET",
            GEONAME_URL,
            params={
                "lat": lat,
                "lng": lon,
                "username": GEONAME_USERNAME,
                "maxRows": 1,
            },
        )
        response.raise_for_status()

    # Return None if no city matches the coordinate.
    places = response.json().get("geonames", [])
    if not places:
        return None, None, None

    place = places[0]
    return place.get("name"), place.get("adminName1"), place.get("countryName")


def google_maps_url(lat: float, lon: float):
    """Get the URL for Google Map of the location."""
    params = urlencode({"api": 1, "query": f"{lat},{lon}"})
    return f"https://www.google.com/maps/search/?{params}"