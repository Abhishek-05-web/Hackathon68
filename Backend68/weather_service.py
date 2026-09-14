import re
from collections import Counter
from datetime import datetime, timedelta

import requests

try:
    from ollama import Client
except ImportError:
    Client = None


# ============================================================
# CONFIG
# ============================================================

DEBUG = False
OLLAMA_MODEL = "qwen3:4b-instruct"


def debug_log(label, value):
    if DEBUG:
        print(f"\n--- DEBUG [{label}] ---")
        print(value)
        print("-----------------------\n")


# ============================================================
# OLLAMA
# ============================================================

def ask_llm(prompt):
    if Client is None:
        raise RuntimeError(
            "Ollama Python package is not installed."
        )

    client = Client()

    try:
        response = client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            think=False,
            options={
                "temperature": 0.2,
                "num_ctx": 2048,
                "num_predict": 180
            }
        )

    except TypeError:

        response = client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt + "\n/no_think"
                }
            ],
            options={
                "temperature": 0.2,
                "num_ctx": 2048,
                "num_predict": 180
            }
        )

    content = response["message"]["content"]

    # Remove think block if model produces one
    content = re.sub(
        r"<think>.*?</think>",
        "",
        content,
        flags=re.S | re.I
    ).strip()

    debug_log("Final LLM output", content)

    return content


# ============================================================
# LANGUAGE DETECTION
# ============================================================

def detect_language(query):

    # Hindi Unicode
    if re.search(r"[\u0900-\u097F]", query):
        return "hi"

    q = query.lower()

    hinglish_words = [
        "kal",
        "aaj",
        "parso",
        "mausam",
        "kaisa",
        "kaisi",
        "rahega",
        "rahegi",
        "hoga",
        "hogi",
        "barish",
        "baarish",
        "subah",
        "dopahar",
        "shaam",
        "raat",
        "jana",
        "jaana",
        "chahiye"
    ]

    if any(word in q for word in hinglish_words):
        return "hinglish"

    return "en"


# ============================================================
# TIME UNDERSTANDING
# ============================================================

def python_time_reference(query):

    q = query.lower().strip()

    # Day after tomorrow
    if any(
        word in q
        for word in [
            "day after tomorrow",
            "parso",
            "parson",
            "परसों"
        ]
    ):
        return "day_after_tomorrow"

    # Tomorrow
    if any(
        word in q
        for word in [
            "tomorrow",
            "kal",
            "कल"
        ]
    ):

        if any(
            word in q
            for word in ["morning", "subah", "सुबह"]
        ):
            return "tomorrow_morning"

        if any(
            word in q
            for word in ["afternoon", "dopahar", "दोपहर"]
        ):
            return "tomorrow_afternoon"

        if any(
            word in q
            for word in ["evening", "shaam", "शाम"]
        ):
            return "tomorrow_evening"

        if any(
            word in q
            for word in ["night", "raat", "रात"]
        ):
            return "tomorrow_tonight"

        return "tomorrow"

    # Today
    if any(
        word in q
        for word in [
            "today",
            "aaj",
            "आज"
        ]
    ):

        if any(
            word in q
            for word in ["morning", "subah", "सुबह"]
        ):
            return "this_morning"

        if any(
            word in q
            for word in ["afternoon", "dopahar", "दोपहर"]
        ):
            return "this_afternoon"

        if any(
            word in q
            for word in ["evening", "shaam", "शाम"]
        ):
            return "this_evening"

        if any(
            word in q
            for word in ["night", "raat", "रात"]
        ):
            return "tonight"

        return "today"

    if "tonight" in q:
        return "tonight"

    if (
        "right now" in q
        or re.search(r"\bnow\b", q)
        or "abhi" in q
        or "अभी" in q
    ):
        return "now"

    # Default
    return "today"


def time_window_for_reference(reference):

    return {
        "this_morning": (6, 12),
        "this_afternoon": (12, 18),
        "this_evening": (18, 24),
        "tonight": (18, 24),

        "tomorrow_morning": (6, 12),
        "tomorrow_afternoon": (12, 18),
        "tomorrow_evening": (18, 24),
        "tomorrow_tonight": (18, 24)

    }.get(reference)


# ============================================================
# EXPLICIT DATE
# ============================================================

def extract_explicit_date(query):

    q = query.lower()

    # YYYY-MM-DD
    match = re.search(
        r"\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b",
        q
    )

    if match:

        year, month, day = map(
            int,
            match.groups()
        )

        try:
            return datetime(
                year,
                month,
                day
            ).strftime("%Y-%m-%d")

        except ValueError:
            return None

    months = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }

    short_months = {
        name[:3]: number
        for name, number in months.items()
    }

    month_pattern = (
        "january|february|march|april|may|june|"
        "july|august|september|october|november|december|"
        "jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec"
    )

    # September 13
    match = re.search(
        rf"\b({month_pattern})\s+"
        r"(\d{1,2})(?:st|nd|rd|th)?"
        r"(?:,?\s+(20\d{2}))?\b",
        q
    )

    if match:

        month_name = match.group(1)

        month = (
            months.get(month_name)
            or short_months.get(month_name)
        )

        day = int(match.group(2))

        year = (
            int(match.group(3))
            if match.group(3)
            else datetime.now().year
        )

        try:
            return datetime(
                year,
                month,
                day
            ).strftime("%Y-%m-%d")

        except ValueError:
            return None

    # 13 September
    match = re.search(
        rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+"
        rf"({month_pattern})"
        r"(?:\s+(20\d{2}))?\b",
        q
    )

    if match:

        day = int(match.group(1))
        month_name = match.group(2)

        month = (
            months.get(month_name)
            or short_months.get(month_name)
        )

        year = (
            int(match.group(3))
            if match.group(3)
            else datetime.now().year
        )

        try:
            return datetime(
                year,
                month,
                day
            ).strftime("%Y-%m-%d")

        except ValueError:
            return None

    return None


# ============================================================
# QUESTION DECODER
# NO AI USED HERE
# ============================================================

def question_decoder(query):

    explicit_date = extract_explicit_date(query)

    if explicit_date:
        time_reference = "specified_date"
    else:
        time_reference = python_time_reference(query)

    return {
        "intent": "weather_query",

        "time_reference": time_reference,

        "required_data": [
            "temperature",
            "humidity",
            "precipitation",
            "wind",
            "weather_condition",
            "uv"
        ],

        "location_requirement": "current_location",

        "response_type": "direct_answer",

        "interpreted_question": query,

        "language": detect_language(query),

        "confidence": 1.0,

        "target_date": None
    }


# ============================================================
# TARGET DATE
# ============================================================

def resolve_target_date(
    query,
    time_reference,
    forecast_timezone=None,
    forecast_current_time=None
):

    explicit = extract_explicit_date(query)

    if explicit:
        return explicit

    # Use weather location local date
    if forecast_current_time:

        base = datetime.fromisoformat(
            forecast_current_time
        ).date()

    else:

        base = datetime.now().date()

    tomorrow_refs = {
        "tomorrow",
        "tomorrow_morning",
        "tomorrow_afternoon",
        "tomorrow_evening",
        "tomorrow_tonight"
    }

    if time_reference in tomorrow_refs:

        return (
            base + timedelta(days=1)
        ).isoformat()

    if time_reference == "day_after_tomorrow":

        return (
            base + timedelta(days=2)
        ).isoformat()

    return base.isoformat()


# ============================================================
# REVERSE GEOCODING
# ============================================================

def get_place_name(latitude, longitude):

    try:

        url = (
            "https://nominatim.openstreetmap.org/reverse"
        )

        params = {
            "lat": latitude,
            "lon": longitude,
            "format": "jsonv2",
            "zoom": 10
        }

        headers = {
            "User-Agent":
            "WeatherGPT-Hackathon/1.0"
        }

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=8
        )

        response.raise_for_status()

        address = response.json().get(
            "address",
            {}
        )

        return {
            "city": (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("municipality")
                or address.get("county")
            ),

            "state": address.get("state"),

            "country": address.get("country")
        }

    except Exception as error:

        debug_log(
            "Reverse geocoding error",
            error
        )

        return {
            "city": None,
            "state": None,
            "country": None
        }


# ============================================================
# WEATHER CODE
# ============================================================

def weather_code_to_text(code):

    mapping = {

        0: "Clear sky",

        1: "Mainly clear",

        2: "Partly cloudy",

        3: "Overcast",

        45: "Fog",

        48: "Depositing rime fog",

        51: "Light drizzle",

        53: "Moderate drizzle",

        55: "Dense drizzle",

        56: "Light freezing drizzle",

        57: "Dense freezing drizzle",

        61: "Light rain",

        63: "Moderate rain",

        65: "Heavy rain",

        66: "Light freezing rain",

        67: "Heavy freezing rain",

        71: "Light snow",

        73: "Moderate snow",

        75: "Heavy snow",

        77: "Snow grains",

        80: "Light rain showers",

        81: "Moderate rain showers",

        82: "Heavy rain showers",

        85: "Light snow showers",

        86: "Heavy snow showers",

        95: "Thunderstorm",

        96: "Thunderstorm with hail",

        99: "Severe thunderstorm with hail"
    }

    return mapping.get(
        code,
        "Unknown weather"
    )


# ============================================================
# FETCH WEATHER
# ============================================================

def fetch_weather(latitude, longitude):

    url = (
        "https://api.open-meteo.com/v1/forecast"
    )

    params = {

        "latitude": latitude,

        "longitude": longitude,

        "current": (
            "temperature_2m,"
            "apparent_temperature,"
            "relative_humidity_2m,"
            "wind_speed_10m,"
            "wind_direction_10m,"
            "precipitation,"
            "weather_code"
        ),

        "hourly": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "precipitation_probability,"
            "precipitation,"
            "wind_speed_10m,"
            "wind_direction_10m,"
            "weather_code"
        ),

        "daily": (
            "weather_code,"
            "temperature_2m_max,"
            "temperature_2m_min,"
            "precipitation_sum,"
            "precipitation_probability_max,"
            "wind_speed_10m_max,"
            "uv_index_max"
        ),

        "timezone": "auto",

        "forecast_days": 7
    }

    response = requests.get(
        url,
        params=params,
        timeout=12
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# NORMALIZE WEATHER
# ============================================================

def normalize_weather(data):

    current = data["current"]

    hourly = data["hourly"]

    daily = data["daily"]

    return {

        "current": {

            "time":
                current["time"],

            "temperature":
                current["temperature_2m"],

            "feels_like":
                current["apparent_temperature"],

            "humidity":
                current["relative_humidity_2m"],

            "wind_speed":
                current["wind_speed_10m"],

            "wind_direction":
                current["wind_direction_10m"],

            "precipitation":
                current["precipitation"],

            "weather_code":
                current["weather_code"],

            "condition":
                weather_code_to_text(
                    current["weather_code"]
                )
        },

        "hourly": [

            {
                "time":
                    hourly["time"][i],

                "temperature":
                    hourly["temperature_2m"][i],

                "humidity":
                    hourly[
                        "relative_humidity_2m"
                    ][i],

                "precipitation_probability":
                    hourly[
                        "precipitation_probability"
                    ][i],

                "precipitation":
                    hourly[
                        "precipitation"
                    ][i],

                "wind_speed":
                    hourly[
                        "wind_speed_10m"
                    ][i],

                "wind_direction":
                    hourly[
                        "wind_direction_10m"
                    ][i],

                "weather_code":
                    hourly[
                        "weather_code"
                    ][i],

                "condition":
                    weather_code_to_text(
                        hourly[
                            "weather_code"
                        ][i]
                    )
            }

            for i in range(
                len(hourly["time"])
            )
        ],

        "daily": [

            {
                "time":
                    daily["time"][i],

                "weather_code":
                    daily[
                        "weather_code"
                    ][i],

                "condition":
                    weather_code_to_text(
                        daily[
                            "weather_code"
                        ][i]
                    ),

                "temperature_max":
                    daily[
                        "temperature_2m_max"
                    ][i],

                "temperature_min":
                    daily[
                        "temperature_2m_min"
                    ][i],

                "precipitation":
                    daily[
                        "precipitation_sum"
                    ][i],

                "precipitation_probability":
                    daily[
                        "precipitation_probability_max"
                    ][i],

                "wind_speed_max":
                    daily[
                        "wind_speed_10m_max"
                    ][i],

                "uv_index_max":
                    daily[
                        "uv_index_max"
                    ][i]
            }

            for i in range(
                len(daily["time"])
            )
        ],

        "location": {

            "latitude":
                data["latitude"],

            "longitude":
                data["longitude"],

            "timezone":
                data["timezone"]
        },

        "source": "Open-Meteo"
    }


# ============================================================
# HOURLY SUMMARY
# ============================================================

def summarize_hours(hours):

    if not hours:
        return None

    temperatures = [
        h["temperature"]
        for h in hours
        if h.get("temperature") is not None
    ]

    rain_probabilities = [
        h["precipitation_probability"]
        for h in hours
        if h.get(
            "precipitation_probability"
        ) is not None
    ]

    precipitation = [
        h["precipitation"]
        for h in hours
        if h.get("precipitation") is not None
    ]

    winds = [
        h["wind_speed"]
        for h in hours
        if h.get("wind_speed") is not None
    ]

    weather_codes = [
        h["weather_code"]
        for h in hours
        if h.get("weather_code") is not None
    ]

    dominant_code = None

    if weather_codes:

        dominant_code = Counter(
            weather_codes
        ).most_common(1)[0][0]

    return {

        "temperature_min_c":
            round(min(temperatures), 1)
            if temperatures else None,

        "temperature_max_c":
            round(max(temperatures), 1)
            if temperatures else None,

        "max_rain_probability_pct":
            round(max(rain_probabilities))
            if rain_probabilities else 0,

        "total_precipitation_mm":
            round(sum(precipitation), 1)
            if precipitation else 0,

        "max_wind_kmh":
            round(max(winds), 1)
            if winds else 0,

        "condition":
            weather_code_to_text(
                dominant_code
            )
            if dominant_code is not None
            else None
    }


# ============================================================
# BUILD COMPACT FACTS FOR AI
# ============================================================

def build_forecast_facts(selected):

    daily = selected.get(
        "daily",
        []
    )

    hourly = selected.get(
        "hourly",
        []
    )

    day = (
        daily[0]
        if daily
        else {}
    )

    facts = {

        "temperature_min_c":
            day.get(
                "temperature_min"
            ),

        "temperature_max_c":
            day.get(
                "temperature_max"
            ),

        "condition":
            day.get(
                "condition"
            ),

        "precipitation_mm":
            day.get(
                "precipitation"
            ),

        "max_rain_probability_pct":
            day.get(
                "precipitation_probability"
            ),

        "max_wind_kmh":
            day.get(
                "wind_speed_max"
            ),

        "uv_index_max":
            day.get(
                "uv_index_max"
            )
    }

    current = selected.get(
        "current"
    )

    if current:

        facts["current"] = {

            "temperature_c":
                current.get(
                    "temperature"
                ),

            "feels_like_c":
                current.get(
                    "feels_like"
                ),

            "humidity_pct":
                current.get(
                    "humidity"
                ),

            "wind_kmh":
                current.get(
                    "wind_speed"
                ),

            "precipitation_mm":
                current.get(
                    "precipitation"
                ),

            "condition":
                current.get(
                    "condition"
                )
        }

    # Time-period summaries

    morning = [
        h
        for h in hourly
        if 6 <= int(
            h["time"][11:13]
        ) < 12
    ]

    afternoon = [
        h
        for h in hourly
        if 12 <= int(
            h["time"][11:13]
        ) < 18
    ]

    evening = [
        h
        for h in hourly
        if 18 <= int(
            h["time"][11:13]
        ) < 24
    ]

    night = [
        h
        for h in hourly
        if 0 <= int(
            h["time"][11:13]
        ) < 6
    ]

    facts["periods"] = {

        "morning":
            summarize_hours(morning),

        "afternoon":
            summarize_hours(afternoon),

        "evening":
            summarize_hours(evening),

        "night":
            summarize_hours(night)
    }

    return facts


# ============================================================
# SELECT EXACT REQUESTED DATE
# ============================================================

def select_weather_for_query(
    weather,
    target_date,
    time_reference
):

    daily = [
        day
        for day in weather["daily"]
        if day["time"] == target_date
    ]

    if not daily:

        raise ValueError(
            f"Requested date {target_date} "
            "is outside available forecast range."
        )

    hours = [
        hour
        for hour in weather["hourly"]
        if hour["time"].startswith(
            target_date
        )
    ]

    window = time_window_for_reference(
        time_reference
    )

    if window:

        start_hour, end_hour = window

        hours = [
            hour
            for hour in hours
            if (
                start_hour
                <= int(
                    hour[
                        "time"
                    ][11:13]
                )
                < end_hour
            )
        ]

    current_date = (
        weather.get(
            "current",
            {}
        )
        .get(
            "time",
            ""
        )[:10]
    )

    selected = {

        "hourly": hours,

        "daily": daily,

        "current": (
            weather.get(
                "current"
            )
            if target_date == current_date
            else None
        ),

        "location":
            dict(
                weather.get(
                    "location",
                    {}
                )
            ),

        "source":
            weather.get(
                "source"
            ),

        "requested_date":
            target_date,

        "requested_time_reference":
            time_reference
    }

    selected["facts"] = (
        build_forecast_facts(
            selected
        )
    )

    return selected


# ============================================================
# DETERMINISTIC WEATHER WARNINGS
# NO AI USED
# ============================================================

def get_warnings(data):

    warnings = []

    daily = data.get(
        "daily",
        []
    )

    hourly = data.get(
        "hourly",
        []
    )

    if not daily:

        return {
            "warnings": []
        }

    day = daily[0]

    max_temp = (
        day.get(
            "temperature_max"
        )
        or 0
    )

    max_wind = (
        day.get(
            "wind_speed_max"
        )
        or 0
    )

    daily_rain = (
        day.get(
            "precipitation"
        )
        or 0
    )

    weather_codes = [

        hour.get(
            "weather_code"
        )

        for hour in hourly

        if hour.get(
            "weather_code"
        ) is not None
    ]

    hourly_rain = [

        hour.get(
            "precipitation",
            0
        ) or 0

        for hour in hourly
    ]

    # Thunderstorm

    if any(
        code >= 95
        for code in weather_codes
    ):

        warnings.append({

            "type":
                "thunderstorm",

            "severity":
                "high",

            "reason":
                "Thunderstorm conditions "
                "are present in the forecast."
        })

    # Strong wind

    if max_wind >= 70:

        warnings.append({

            "type":
                "strong wind",

            "severity":
                "high",

            "reason":
                f"Maximum wind speed may "
                f"reach {max_wind} km/h."
        })

    elif max_wind >= 50:

        warnings.append({

            "type":
                "strong wind",

            "severity":
                "moderate",

            "reason":
                f"Maximum wind speed may "
                f"reach {max_wind} km/h."
        })

    # Heat

    if max_temp >= 45:

        warnings.append({

            "type":
                "extreme heat",

            "severity":
                "high",

            "reason":
                f"Maximum temperature may "
                f"reach {max_temp}°C."
        })

    elif max_temp >= 40:

        warnings.append({

            "type":
                "high heat",

            "severity":
                "moderate",

            "reason":
                f"Maximum temperature may "
                f"reach {max_temp}°C."
        })

    # Heavy rain based on real amount

    max_hourly_rain = max(
        hourly_rain,
        default=0
    )

    if (
        daily_rain >= 50
        or max_hourly_rain >= 10
    ):

        warnings.append({

            "type":
                "heavy rain",

            "severity":
                "high",

            "reason":
                "Significant rainfall "
                "is present in the forecast."
        })

    elif (
        daily_rain >= 25
        or max_hourly_rain >= 5
    ):

        warnings.append({

            "type":
                "heavy rain",

            "severity":
                "moderate",

            "reason":
                "Elevated rainfall "
                "is present in the forecast."
        })

    return {
        "warnings": warnings
    }


# ============================================================
# REMOVE ACCIDENTAL CALENDAR DATES
# ============================================================

_MONTH_NAMES = (
    "january|february|march|april|may|"
    "june|july|august|september|october|"
    "november|december|jan|feb|mar|apr|"
    "jun|jul|aug|sep|sept|oct|nov|dec"
)


def strip_hallucinated_dates(text):

    pattern = re.compile(

        rf"\b(?:on\s+)?"
        rf"(?:"
        rf"\d{{1,2}}(?:st|nd|rd|th)?\s+"
        rf"(?:{_MONTH_NAMES})"
        rf"|"
        rf"(?:{_MONTH_NAMES})\s+"
        rf"\d{{1,2}}(?:st|nd|rd|th)?"
        rf")"
        rf"(?:,?\s+\d{{4}})?\b",

        flags=re.I
    )

    text = pattern.sub(
        "",
        text
    )

    text = re.sub(
        r"\s{2,}",
        " ",
        text
    )

    text = re.sub(
        r"\s+([,.;])",
        r"\1",
        text
    )

    return text.strip()


# ============================================================
# FINAL AI RESPONSE
# ONLY LLM CALL IN COMPLETE PIPELINE
# ============================================================

def natural_response(
    data,
    query,
    decoded_question
):

    language_map = {

        "en":
            "English",

        "hi":
            "Hindi using Devanagari script",

        "hinglish":
            "Hinglish using Roman Hindi "
            "and simple English",

        "bn":
            "Bengali",

        "mr":
            "Marathi",

        "gu":
            "Gujarati",

        "ta":
            "Tamil",

        "te":
            "Telugu",

        "kn":
            "Kannada",

        "ml":
            "Malayalam",

        "pa":
            "Punjabi",

        "ur":
            "Urdu"
    }

    language = decoded_question.get(
        "language",
        "en"
    )

    response_language = (
        language_map.get(
            language,
            "English"
        )
    )

    location = data.get(
        "location",
        {}
    )

    location_text = ", ".join(

        part

        for part in [

            location.get("city"),

            location.get("state"),

            location.get("country")

        ]

        if part
    )

    facts = data.get(
        "facts",
        {}
    )

    warnings = data.get(
        "warnings",
        {
            "warnings": []
        }
    )

    time_reference = data.get(
        "requested_time_reference",
        "today"
    )

    prompt = f"""
You are WeatherGPT, a fast and accurate weather assistant.

USER QUESTION:
{query}

LOCATION:
{location_text}

REQUESTED TIME:
{time_reference}

VERIFIED WEATHER FACTS:
{facts}

VERIFIED WEATHER WARNINGS:
{warnings}

RESPONSE LANGUAGE:
{response_language}

STRICT RULES:

1. Answer ONLY using the verified weather facts above.

2. Never invent temperature, rain, wind, humidity, UV, weather warnings, or timing.

3. If the user asks "safe", "should I go", travel timing, college timing, outdoor plans, or similar:
   give a practical weather-based recommendation.
   Do not guarantee absolute safety.

4. Rain probability means chance of rain.
   It is NOT rainfall amount.

5. Actual precipitation amount is measured in mm.

6. If rain probability is high but precipitation amount is very low,
   say rain is possible, not that heavy rain is certain.

7. Use the morning / afternoon / evening summaries when the user asks about timing.

8. If verified warnings list is empty, do not invent any alert.

9. If the response language is Hinglish:
   use Roman Hindi + simple English.
   Do NOT use Hindi Devanagari script.

10. Keep the answer natural and conversational.

11. Maximum 3 short sentences.

12. Do not mention APIs, JSON, Python, Open-Meteo, Ollama, models, prompts, or internal processing.

13. Do not write an explicit calendar date.
   Say today, tomorrow, morning, evening, etc.

Return ONLY the final answer.
"""

    try:

        response = ask_llm(
            prompt
        )

        return strip_hallucinated_dates(
            response
        )

    except Exception as error:

        debug_log(
            "Final response error",
            error
        )

        return (
            "Weather service is temporarily "
            "unavailable."
        )


# ============================================================
# MAIN PUBLIC FUNCTION
# ============================================================

def get_weather(
    latitude,
    longitude,
    query
):

    # ----------------------------------------
    # 1. Understand query WITHOUT AI
    # ----------------------------------------

    decoded = question_decoder(
        query
    )

    # ----------------------------------------
    # 2. Get location name
    # ----------------------------------------

    location = get_place_name(
        latitude,
        longitude
    )

    debug_log(
        "Resolved location",
        {
            "latitude": latitude,
            "longitude": longitude,
            "location": location
        }
    )

    # ----------------------------------------
    # 3. Fetch real weather
    # ----------------------------------------

    raw = fetch_weather(
        latitude,
        longitude
    )

    weather = normalize_weather(
        raw
    )

    # ----------------------------------------
    # 4. Resolve exact requested date
    # ----------------------------------------

    time_reference = decoded.get(
        "time_reference",
        "today"
    )

    forecast_current_time = (
        raw
        .get(
            "current",
            {}
        )
        .get(
            "time"
        )
    )

    target_date = resolve_target_date(

        query,

        time_reference,

        raw.get(
            "timezone"
        ),

        forecast_current_time
    )

    decoded[
        "target_date"
    ] = target_date

    # ----------------------------------------
    # 5. Select only requested weather
    # ----------------------------------------

    selected = select_weather_for_query(

        weather,

        target_date,

        time_reference
    )

    # ----------------------------------------
    # 6. Attach location
    # ----------------------------------------

    selected[
        "location"
    ] = {

        "city":
            location.get(
                "city"
            ),

        "state":
            location.get(
                "state"
            ),

        "country":
            location.get(
                "country"
            ),

        "latitude":
            raw["latitude"],

        "longitude":
            raw["longitude"],

        "timezone":
            raw["timezone"]
    }

    # ----------------------------------------
    # 7. Warnings WITHOUT AI
    # ----------------------------------------

    selected[
        "warnings"
    ] = get_warnings(
        selected
    )

    # ----------------------------------------
    # Return weather data + decoded query
    # ----------------------------------------

    return (
        selected,
        decoded
    )


# ============================================================
# OPTIONAL TEST
# ============================================================

if __name__ == "__main__":

    print(
        "WeatherGPT optimized service loaded."
    )

    print(
        "LLM model:",
        OLLAMA_MODEL
    )