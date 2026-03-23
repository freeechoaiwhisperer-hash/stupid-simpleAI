# ============================================================
#  FreedomForge AI — modules/weather.py
#  Weather plugin — uses wttr.in (free, no API key needed)
#
#  Trigger phrases (handled by modules/__init__.py router):
#    "weather in Paris"
#    "what's the weather in London?"
#    "how hot is it in Tokyo"
#    "/weather New York"
# ============================================================

import re
import threading
from typing import Callable

MODULE_NAME = "weather"

# wttr.in returns beautifully formatted weather for any city.
# Using format=j1 gives structured JSON so we can build a clean reply.
_WTTR_URL = "https://wttr.in/{location}?format=j1"


def _format_weather(data: dict, location: str) -> str:
    """Turn the wttr.in JSON response into a readable message."""
    try:
        current = data["current_condition"][0]

        temp_c   = current.get("temp_C", "?")
        temp_f   = current.get("temp_F", "?")
        feels_c  = current.get("FeelsLikeC", "?")
        feels_f  = current.get("FeelsLikeF", "?")
        humidity = current.get("humidity", "?")
        wind_kmh = current.get("windspeedKmph", "?")
        wind_dir = current.get("winddir16Point", "?")
        vis_km   = current.get("visibility", "?")
        desc     = current["weatherDesc"][0].get("value", "?") \
                   if current.get("weatherDesc") else "?"

        # Tonight / tomorrow from the forecast
        forecast = data.get("weather", [])
        lines = [
            f"🌤  Weather for **{location.title()}**",
            "",
            f"  {desc}",
            f"  🌡  {temp_c}°C  /  {temp_f}°F  (feels like {feels_c}°C / {feels_f}°F)",
            f"  💧  Humidity: {humidity}%",
            f"  💨  Wind: {wind_kmh} km/h {wind_dir}",
            f"  👁  Visibility: {vis_km} km",
        ]

        if forecast:
            today = forecast[0]
            max_c = today.get("maxtempC", "?")
            min_c = today.get("mintempC", "?")
            max_f = today.get("maxtempF", "?")
            min_f = today.get("mintempF", "?")
            lines += [
                "",
                f"  📅  Today's range: {min_c}°C – {max_c}°C  "
                f"({min_f}°F – {max_f}°F)",
            ]

        if len(forecast) > 1:
            tomorrow = forecast[1]
            t_max_c  = tomorrow.get("maxtempC", "?")
            t_min_c  = tomorrow.get("mintempC", "?")
            t_desc   = tomorrow["hourly"][4]["weatherDesc"][0].get("value", "?") \
                       if tomorrow.get("hourly") else "?"
            lines += [
                f"  🔮  Tomorrow: {t_min_c}°C – {t_max_c}°C, {t_desc}",
            ]

        lines.append("")
        lines.append("  _Powered by wttr.in — no account needed._")

        return "\n".join(lines)

    except Exception as e:
        return (
            f"Got weather data but couldn't parse it: {e}\n"
            f"Try asking again with a more specific city name."
        )


def _extract_location(message: str) -> str:
    """Pull the location name out of the user's message."""
    msg = message.strip()

    # Explicit command: /weather <location>
    if msg.lower().startswith("/weather"):
        loc = msg[8:].strip()
        return loc if loc else ""

    # "weather in <city>" / "weather for <city>"
    m = re.search(
        r'\bweather\s+(?:in|for|at)\s+(.+)', msg, re.IGNORECASE)
    if m:
        return m.group(1).strip().rstrip("?!.")

    # "how hot / cold / warm is it in <city>"
    m = re.search(
        r'\bhow\s+(?:hot|cold|warm|cool)\s+is\s+it\s+in\s+(.+)',
        msg, re.IGNORECASE)
    if m:
        return m.group(1).strip().rstrip("?!.")

    # "temperature in <city>"
    m = re.search(
        r'\btemperature\s+in\s+(.+)', msg, re.IGNORECASE)
    if m:
        return m.group(1).strip().rstrip("?!.")

    # Fallback: take everything after the last "in"
    m = re.search(r'\bin\s+(.+)$', msg, re.IGNORECASE)
    if m:
        return m.group(1).strip().rstrip("?!.")

    return ""


def fetch_weather(
    location:  str,
    on_result: Callable[[str], None],
    on_error:  Callable[[str], None],
) -> None:
    """Fetch weather for *location* in a background thread."""

    def _fetch():
        try:
            import requests
            url = _WTTR_URL.format(location=requests.utils.quote(location))
            r   = requests.get(url, timeout=10)

            if r.status_code == 404:
                on_error(
                    f"Location not found: \"{location}\"\n"
                    f"Try a more specific name, e.g. \"Paris, France\"."
                )
                return

            r.raise_for_status()
            data = r.json()
            on_result(_format_weather(data, location))

        except Exception as e:
            on_error(
                f"Couldn't fetch weather right now.\n"
                f"Details: {e}\n\n"
                f"This feature needs an internet connection."
            )

    threading.Thread(target=_fetch, daemon=True).start()


def handle(
    message:   str,
    on_result: Callable[[str], None],
    on_error:  Callable[[str], None],
) -> None:
    """Entry point called by the module router."""
    location = _extract_location(message)

    if not location:
        on_error(
            "Please tell me which city you want weather for.\n"
            "Example: \"weather in London\" or \"/weather Tokyo\""
        )
        return

    fetch_weather(location, on_result, on_error)
