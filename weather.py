from datetime import date, datetime, timedelta, UTC
from httpx import AsyncClient
from fastapi import HTTPException

from db import connect_db
from place import search_place_by_coordinates

OPENMETEO_URL = "https://api.open-meteo.com/v1/forecast"
WEATHER_LABELS = {
    0: "Clear",
    1: "Mostly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Freezing fog",
    51: "Drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    56: "Freezing drizzle",
    57: "Heavy freezing drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    66: "Freezing rain",
    67: "Heavy freezing rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Light rain showers",
    81: "Rain showers",
    82: "Heavy rain showers",
    85: "Light snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorms",
    96: "Thunderstorms with hail",
    97: "Strong thunderstorms",
    99: "Thunderstorms with heavy hail",
}


def check_unit(unit: str):
    if unit not in ("C", "F"):
        raise HTTPException(status_code=422, detail="Unit should either be C or F.")

def celsius_to_fahrenheit(celsius):
    """Convert Celsius to Fahrenheit."""
    return (celsius * 9/5) + 32


def temps_celsius_to_fahrenheit(result):
    """Convert all temperatures in a request result from Celsius into Fahrenheit."""
    for temp in result["temps"]:
        temp["min_t"] = celsius_to_fahrenheit(temp["min_t"])
        temp["max_t"] = celsius_to_fahrenheit(temp["max_t"])
    return result


def to_utc(time: datetime):
    """Convert a datetime object to UTC time for easy comparison."""
    if time.tzinfo is None or time.utcoffset() is None:
        raise ValueError("Datetime must include a time zone.")
    return time.astimezone(UTC)

def _to_sql_ts(time: datetime):
    """Convert a datetime object in UTC time to the sql timestamp format."""
    return time.replace(tzinfo=None).isoformat(sep=" ")

def check_dates(date_start, date_end):
    """Check that the input date is within the date required by forecast API."""
    today = datetime.now().date()
    start = today - timedelta(days=91)
    end = today + timedelta(days=14)
    if not start <= date_start <= date_end <= end:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid dates. Choose ordered start date after {start} and end date before {end}, inclusive."
        )


async def query_temperature(lat, lon, date_start, date_end):
    """Query Open-Meteo forecast API for range temperature."""
    async with AsyncClient(timeout=10.0) as client:
        response = await client.request(
            "GET",
            OPENMETEO_URL,
            params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": date_start,
                "end_date": date_end,
                "daily": "temperature_2m_min,temperature_2m_max",
                "timezone": "auto",
                "temperature_unit": "celsius",
            }
        )
        if not response.is_success:
            raise HTTPException(status_code=502, detail="Error in forecast API.")

    # Get the max and min temp each day.
    daily = response.json()["daily"]
    temps = [
        {"date": date, "min_t": min_t, "max_t": max_t}
        for date, min_t, max_t in zip(
            daily["time"],
            daily["temperature_2m_min"],
            daily["temperature_2m_max"],
            strict=True,
        )
    ]
    if not temps:
        raise HTTPException(status_code=502, detail="No matching temperature record found.")
    return temps


async def query_current(lat: float, lon: float):
    """Query Open-Meteo forecast API for current weather."""
    async with AsyncClient(timeout=10.0) as client:
        response = await client.get(
            OPENMETEO_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": ("temperature_2m,weather_code"),
                "temperature_unit": "celsius",
                "timezone": "auto",
            },
        )
        response.raise_for_status()

    data = response.json()
    current = data["current"]

    return {
        "curr_t": current["temperature_2m"],
        "weather": WEATHER_LABELS.get(current["weather_code"], "Unknown"),
    }


async def write_current(lat, lon, city, state, country, curr_t, weather):
    """Save the current weather search result into the DB."""
    conn = connect_db()
    try:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO Current_Requests (lat, lon, city, state, country, curr_t, weather)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                RETURNING request_id
                """, (lat, lon, city, state, country, curr_t, weather)
            )
            request_id = cursor.fetchone()["request_id"]
    finally:
        conn.close()
    return request_id


async def get_save_current(lat: float, lon: float):
    """
    Get the temperature in the given dates, search for the city of the location,
    save results in DB, and return.
    """
    # Get the weather.
    result = await query_current(lat, lon)

    # Search for the city, state, and country name.
    city, state, country = await search_place_by_coordinates(lat, lon)

    # Save and return.
    try:
        request_id = await write_current(lat, lon, city, state, country, result["curr_t"], result["weather"])
    except Exception:
        raise HTTPException(status_code=500, detail="Internal DB Error.")
    return {
        "request_id": request_id,
        "city": city,
        "state": state,
        "curr_t": result["curr_t"],
        "weather": result["weather"]
    }


async def write_temperature(lat, lon, date_start, date_end, city, state, country, temps):
    """Save the temperature search result into the DB."""
    conn = connect_db()
    try:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO Temperature_Requests (lat, lon, date_start, date_end, city, state, country)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                RETURNING request_id
                """, (lat, lon, date_start, date_end, city, state, country)
            )
            request_id = cursor.fetchone()["request_id"]
            conn.executemany(
                """
                INSERT INTO Temperatures (request_id, date, min_t, max_t)
                VALUES (?, ?, ?, ?)
                """,
                ((request_id, temp["date"], temp["min_t"], temp["max_t"]) for temp in temps)
            )
    finally:
        conn.close()
    return request_id


async def get_save_temperature(lat: float, lon: float, date_start: date, date_end: date):
    """
    Get the temperature in the given dates, search for the city of the location,
    save results in DB, and return.
    """
    # Get the weather.
    temps = await query_temperature(lat, lon, date_start, date_end)

    # Search for the city, state, and country name.
    city, state, country = await search_place_by_coordinates(lat, lon)

    # Save and return.
    try:
        request_id = await write_temperature(lat, lon, date_start, date_end, city, state, country, temps)
    except Exception:
        raise HTTPException(status_code=500, detail="Internal DB Error.")
    return {
        "request_id": request_id,
        "city": city,
        "state": state,
        "country": country,
        "temps": temps
    }


async def read_result_temperature(request_id: int):
    """Read one temperature request record."""
    conn = connect_db()
    try:
        with conn:
            # get the lat/lon... from that request.
            cursor = conn.execute(
                """
                SELECT request_id, lat, lon, city, state, country
                FROM Temperature_Requests
                WHERE request_id = ?
                """, (request_id,)
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Request ID not found.")
            result = dict(row)
            # Get the corresponding temperature records.
            cursor = conn.execute(
                """
                SELECT date, min_t, max_t FROM Temperatures
                WHERE request_id = ?
                """, (result["request_id"],)
            )
            result["temps"] = [dict(row) for row in cursor.fetchall()]
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal DB error.")
    finally:
        conn.close()
    return result


async def read_result_current(request_id: int):
    """Read one current weather record."""
    conn = connect_db()
    try:
        with conn:
            cursor = conn.execute(
                """
                SELECT *
                FROM Current_Requests
                WHERE request_id = ?
                """, (request_id,)
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Request ID not found.")
            result = dict(row)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal DB error.")
    finally:
        conn.close()
    return result


async def read_results_temperature(time: datetime, count: int | None):
    """Return most recent [count] results from requests before [time]."""
    time = _to_sql_ts(time)
    conn = connect_db()
    try:
        with conn:
            # Default to fetching all rows before [time] if count isn't specified.
            if count:
                cursor = conn.execute(
                    """
                    SELECT * FROM Temperature_Requests
                    WHERE ts < ?
                    ORDER BY ts DESC, request_id DESC
                    LIMIT ?
                    """, (time, count)
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT * FROM Temperature_Requests
                    WHERE ts < ?
                    ORDER BY ts DESC, request_id DESC
                    """, (time,)
                )
            results = [dict(row) for row in cursor.fetchall()]
            # Fetch all dates' temperatures for each request ID.
            for result in results:
                cursor = conn.execute(
                    """
                    SELECT date, min_t, max_t FROM Temperatures
                    WHERE request_id = ?
                    """, (result["request_id"],)
                )
                result["temps"] = [dict(row) for row in cursor.fetchall()]
    except Exception:
        raise HTTPException(status_code=500, detail="Internal DB error.")
    finally:
        conn.close()
    return results


async def read_results_current(time: datetime, count: int | None):
    """Read all current weather records."""
    time = _to_sql_ts(time)
    conn = connect_db()
    try:
        with conn:
            if count:
                cursor = conn.execute(
                    """
                    SELECT *
                    FROM Current_Requests
                    WHERE ts < ?
                    ORDER BY ts DESC, request_id DESC
                    LIMIT ?
                    """, (time, count)
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT *
                    FROM Current_Requests
                    WHERE ts < ?
                    ORDER BY ts DESC, request_id DESC
                    """, (time,)
                )
            results = [dict(row) for row in cursor.fetchall()]
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal DB error.")
    finally:
        conn.close()
    return results


async def read_temperatures_wide():
    """Read all records. Each row represent a temperature record."""
    time = _to_sql_ts(datetime.now(UTC))
    conn = connect_db()
    try:
        with conn:
            cursor = conn.execute(
                """
                SELECT
                    w.request_id as `request ID`, w.lat as latitude, w.lon as longitude,
                    w.date_start as `date start`, w.date_end as `date end`, w.ts as timestamp,
                    w.city, w.state, w.country,
                    t.date, t.min_t as `min temperature`, t.max_t as `max temperature`
                FROM Temperature_Requests w, Temperatures t
                WHERE w.request_id = t.request_id
                ORDER BY w.ts DESC, w.request_id DESC, t.date ASC
                """
            )
            results = [dict(row) for row in cursor.fetchall()]
    except Exception:
        raise HTTPException(status_code=500, detail="Internal DB error.")
    finally:
        conn.close()
    return results


async def update_temperature(request_id: int, date_start: date, date_end: date):
    """Update a request with a new date range and update the timestamp."""
    conn = connect_db()
    try:
        with conn:
            # First verify the request ID and get the lat/lon from that request.
            cursor = conn.execute(
                """
                SELECT lat, lon, city, state, country
                FROM Temperature_Requests
                WHERE request_id = ?
                """, (request_id,)
            )
            request = cursor.fetchone()
            if not request:
                raise HTTPException(status_code=404, detail="Request ID not found.")

            # Query Open-Meteo with the new dates.
            temps = await query_temperature(request["lat"], request["lon"], date_start, date_end)
            # Update the request row.
            cursor = conn.execute(
                """
                UPDATE Temperature_Requests
                SET date_start = ?, date_end = ?, ts = CURRENT_TIMESTAMP
                WHERE request_id = ?
                """, (date_start, date_end, request_id)
            )
            # Check if the request is deleted during Open-Meteo query.
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Request ID not found.")
            # Upsert new temperature rows. Update existing rows to reduce delete/insert.
            conn.executemany(
                """
                INSERT INTO Temperatures (request_id, date, min_t, max_t)
                VALUES (?, ?, ?, ?)
                ON CONFLICT DO UPDATE
                SET min_t = excluded.min_t, max_t = excluded.max_t
                """, [(request_id, temp["date"], temp["min_t"], temp["max_t"]) for temp in temps]
            )
            # Delete unwanted rows.
            conn.execute(
                """
                DELETE FROM Temperatures
                WHERE request_id = ?
                    AND (date < ? OR date > ?)
                """, (request_id, date_start, date_end)
            )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal DB error.")
    finally:
        conn.close()

    # Same return as the POST API.
    return {
        "request_id": request_id,
        "city": request["city"],
        "state": request["state"],
        "country": request["country"],
        "temps": temps
    }


async def update_current(request_id: int):
    """Update a current request with the current timestamp."""
    conn = connect_db()
    try:
        with conn:
            # First verify the request ID and get the lat/lon from that request.
            cursor = conn.execute(
                """
                SELECT lat, lon, city, state, country
                FROM Current_Requests
                WHERE request_id = ?
                """, (request_id,)
            )
            request = cursor.fetchone()
            if not request:
                raise HTTPException(status_code=404, detail="Request ID not found.")

            # Query Open-Meteo with the new timestamp.
            result = await query_current(request["lat"], request["lon"])
            # Update the request row.
            cursor = conn.execute(
                """
                UPDATE Current_Requests
                SET ts = CURRENT_TIMESTAMP, curr_t = ?, weather = ?
                WHERE request_id = ?
                """, (result["curr_t"], result["weather"], request_id)
            )
            # Check if the request is deleted during Open-Meteo query.
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Request ID not found.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal DB error.")
    finally:
        conn.close()

    # Same return as the POST API.
    return {
        "request_id": request_id,
        "city": request["city"],
        "state": request["state"],
        "country": request["country"],
        "curr_t": result["curr_t"],
        "weather": result["weather"]
    } 



async def delete_temperature(request_id: int):
    """Delete a temperature request and cascade to the temperature records."""
    conn = connect_db()
    try:
        with conn:
            cursor = conn.execute(
                """
                DELETE FROM Temperature_Requests
                WHERE request_id = ?
                """, (request_id,)
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Request ID not found.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal DB error.")
    finally:
        conn.close()


async def delete_current(request_id: int):
    """Delete a current request."""
    conn = connect_db()
    try:
        with conn:
            cursor = conn.execute(
                """
                DELETE FROM Current_Requests
                WHERE request_id = ?
                """, (request_id,)
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Request ID not found.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal DB error.")
    finally:
        conn.close()