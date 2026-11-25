from datetime import date, datetime, UTC
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse, Response
import csv
from io import StringIO

from place import search_place_by_city, google_maps_url
from weather import (get_save_temperature, celsius_to_fahrenheit, temps_celsius_to_fahrenheit, check_unit,
                     read_temperatures_wide, to_utc, check_dates, read_results_temperature,
                     update_temperature, delete_temperature, read_result_temperature,
                     get_save_current, read_results_current, read_result_current, update_current, delete_current)


async def handle_get_search_places(city: str):
    """Get all places' lat and lon with matching names."""
    # Check for empty input
    city = city.strip()
    if len(city) < 1:
        raise HTTPException(status_code=422, detail="Please enter a non-empty city.")

    # Search for top-5 matching places and return their names, lats and lons in a dictionary.
    try:
        places = await search_place_by_city(city, 5)
    except Exception:
        raise HTTPException(status_code=502, detail="Error with Geocoding API.")
    return places


async def handle_post_current(unit: str, request: Request):
    """Get the current weather and save it."""
    try:
        args = await request.json()
    except ValueError:
        raise HTTPException(400, "Request body must be valid JSON.")
    if not isinstance(args, dict):
        raise HTTPException(400, "Request body must be valid JSON.")

    # Parse the arguments.
    try:
        lat = float(args["lat"])
        lon = float(args["lon"])
    except Exception:
        raise HTTPException(422, "Please provide valid latitude and longitude.")

    # Check for latitude and longitude.
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise HTTPException(422, "Invalid coordinates. Latitude is between -90 and 90. Longitude is betweem -180 and 180.")

    # Check for unit
    check_unit(unit)

    result = await get_save_current(lat, lon)
    if unit == 'F':
        result["curr_t"] = celsius_to_fahrenheit(result["curr_t"])
    map = google_maps_url(lat, lon)
    return result | {"unit": unit, "map": map}


async def handle_post_temperature(unit: str, request: Request):
    """Get the temperature within given dates and save them."""
    try:
        args = await request.json()
    except ValueError:
        raise HTTPException(400, "Request body must be valid JSON.")
    if not isinstance(args, dict):
        raise HTTPException(400, "Request body must be valid JSON.")

    # Parse the arguments.
    try:
        lat = float(args["lat"])
        lon = float(args["lon"])
        date_start = date.fromisoformat(args["date_start"])
        date_end = date.fromisoformat(args["date_end"])
    except Exception:
        raise HTTPException(422, "Please provide valid latitude, longitude, start date, and end date.")

    # Check for latitude and longitude.
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise HTTPException(422, "Invalid coordinates. Latitude is between -90 and 90. Longitude is betweem -180 and 180.")

    check_dates(date_start, date_end)
    check_unit(unit)

    result = await get_save_temperature(lat, lon, date_start, date_end)
    if unit == 'F':
        result = temps_celsius_to_fahrenheit(result)
    map = google_maps_url(lat, lon)
    return result | {"unit": unit, "map": map}


async def handle_get_current(request_id: int, unit: str):
    """Get one temperature request by ID."""
    if unit not in ('C', 'F'):
        raise HTTPException(422, "Invalid unit. Unit must be either C or F.")

    # Get the results and convert the units.
    result = await read_result_current(request_id)
    if unit == 'F':
        result["curr_t"] = celsius_to_fahrenheit(result["curr_t"])
    map = google_maps_url(result["lat"], result["lon"])
    return result | {"unit": unit, "map": map}


async def handle_get_temperature(request_id: int, unit: str):
    """Get one temperature request by ID."""
    check_unit(unit)

    # Get the results and convert the units.
    result = await read_result_temperature(request_id)
    if unit == 'F':
        result = temps_celsius_to_fahrenheit(result)
    map = google_maps_url(result["lat"], result["lon"])
    return result | {"unit": unit, "map": map}


async def handle_get_currents(unit: str, time: str | None = None, count: int | None = None):
    """Get the most recent [count] results from current requests before [time]."""
    # Check for time.
    try:
        if time is not None:
            time = to_utc(datetime.fromisoformat(time))
        else:
            time = datetime.now(UTC)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid time. Please use ISO format with timezone.")
    # Count must be positive int.
    if count is not None and count < 1:
        raise HTTPException(status_code=422, detail="Count should be a positive integer.")
    check_unit(unit)

    # Get the results and convert the units.
    results = await read_results_current(time, count)
    if unit == 'F':
        for result in results:
            result["curr_t"] = celsius_to_fahrenheit(result["curr_t"])
            result |= {"unit": unit}
    return results


async def handle_get_temperatures(unit: str, time: str | None = None, count: int | None = None):
    """Get the most recent [count] results from temperature requests before [time]."""
    # Check for time.
    try:
        if time is not None:
            time = to_utc(datetime.fromisoformat(time))
        else:
            time = datetime.now(UTC)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid time. Please use ISO format with timezone.")
    # Count must be positive int.
    if count is not None and count < 1:
        raise HTTPException(status_code=422, detail="Count should be a positive integer.")
    check_unit(unit)

    # Get the results and convert the units.
    results = await read_results_temperature(time, count)
    if unit == 'F':
        results = [temps_celsius_to_fahrenheit(result) | {"unit": unit} for result in results]
    return results


async def handle_patch_current(request_id: int, unit: str):
    """Update a current request using new timestamp."""
    check_unit(unit)

    # Update the DB, get the result and convert the units.
    result = await update_current(request_id)
    if unit == 'F':
        result["curr_t"] = celsius_to_fahrenheit(result["curr_t"])
    return result | {"unit": unit}


async def handle_patch_temperature(request_id: int, unit: str, request: Request):
    """Update a temperature request using new start and end date."""
    try:
        args = await request.json()
    except ValueError:
        raise HTTPException(400, "Request body must be valid JSON.")
    if not isinstance(args, dict):
        raise HTTPException(400, "Request body must be valid JSON.")

    # Check dates.
    try:
        date_start = date.fromisoformat(args["date_start"])
        date_end = date.fromisoformat(args["date_end"])
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid date format.")
    check_dates(date_start, date_end)
    check_unit(unit)

    # Update the DB, get the result and convert the units.
    result = await update_temperature(request_id, date_start, date_end)
    if unit == 'F':
        result = temps_celsius_to_fahrenheit(result)
    return result | {"unit": unit}


async def handle_delete_current(request_id: int):
    """Delete a current request."""
    await delete_current(request_id)


async def handle_delete_temperature(request_id: int):
    """Delete a temperature request and matching temperatures."""
    await delete_temperature(request_id)


async def handle_export_json(unit: str):
    """Export all weather information in json format."""
    check_unit(unit)

    results = {}
    results["current"] = await handle_get_currents(unit)
    results["temperature"] = await handle_get_temperatures(unit)
    return JSONResponse(
        content={"unit": unit, "weather_requests": [results]},
        headers={"Content-Disposition": 'attachment; filename="weather_requests.json"'},
    )


def _csv_download(rows, fields, temperature_fields, unit, filename):
    """Export the fetched dictionary into csv."""
    # Write into StringIO in memory.
    check_unit(unit)
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields)
    # Write the haeder.
    writer.writeheader()

    # Result rows.
    for result in rows:
        row = result | {"unit": "Fahrenheit" if unit == "F" else "Celsius"}
        # Unit conversion on fields regarding temperature.
        if unit == "F":
            for field in temperature_fields:
                row[field] = celsius_to_fahrenheit(row[field])
        writer.writerow(row)

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def handle_export_csv_temperature(unit: str):
    rows = await read_temperatures_wide()
    return _csv_download(
        rows,
        fields=(
            "request ID", "latitude", "longitude", "date start", "date end",
            "timestamp", "city", "state", "country", "date",
            "min temperature", "max temperature", "unit"
        ),
        temperature_fields=("min temperature", "max temperature"),
        unit=unit,
        filename="temperature_requests.csv",
    )


async def handle_export_csv_current(unit: str):
    rows = await read_results_current(datetime.now(UTC), None)
    return _csv_download(
        rows,
        fields=(
            "request_id", "lat", "lon", "ts", "city", "state", "country",
            "curr_t", "weather", "unit"
        ),
        temperature_fields=("curr_t",),
        unit=unit,
        filename="current_weather_requests.csv",
    )