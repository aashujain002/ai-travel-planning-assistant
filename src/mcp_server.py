from datetime import date, datetime, timedelta
import json
import math
import re
from zoneinfo import ZoneInfo

import httpx
from mcp.server.mcpserver import MCPServer


server = MCPServer("Singapore Travel Tools")
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
FRANKFURTER_LATEST_URL = "https://api.frankfurter.dev/v1/latest"
SINGAPORE_LATITUDE = 1.3521
SINGAPORE_LONGITUDE = 103.8198
SINGAPORE_TIMEZONE = "Asia/Singapore"
OPEN_METEO_MAX_FORECAST_DAYS = 16
CURRENCY_CODE_PATTERN = re.compile(r"^[A-Za-z]{3}$")
ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

WMO_WEATHER_DESCRIPTIONS = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


@server.tool()
def get_weather(location: str, start_date: str, end_date: str) -> str:
    """Get a Singapore weather forecast for an explicit ISO date range."""
    if location.strip().casefold() != "singapore":
        return "Weather is currently supported only for Singapore."

    if not isinstance(start_date, str) or not ISO_DATE_PATTERN.fullmatch(start_date):
        return "Invalid start date. Use the YYYY-MM-DD format."
    if not isinstance(end_date, str) or not ISO_DATE_PATTERN.fullmatch(end_date):
        return "Invalid end date. Use the YYYY-MM-DD format."

    try:
        requested_start_date = date.fromisoformat(start_date)
        requested_end_date = date.fromisoformat(end_date)
    except ValueError:
        return "Invalid date. Use a valid YYYY-MM-DD date."

    if requested_start_date > requested_end_date:
        return "Invalid date range. The start date must be on or before the end date."

    forecast_start_date = datetime.now(ZoneInfo(SINGAPORE_TIMEZONE)).date()
    forecast_end_date = forecast_start_date + timedelta(
        days=OPEN_METEO_MAX_FORECAST_DAYS - 1
    )
    if (
        requested_start_date < forecast_start_date
        or requested_end_date > forecast_end_date
    ):
        return (
            "Requested dates are outside the Open-Meteo forecast range. "
            f"Available dates: {forecast_start_date} to {forecast_end_date}."
        )

    requested_dates = [
        (requested_start_date + timedelta(days=offset)).isoformat()
        for offset in range((requested_end_date - requested_start_date).days + 1)
    ]
    try:
        response = httpx.get(
            OPEN_METEO_FORECAST_URL,
            params={
                "latitude": SINGAPORE_LATITUDE,
                "longitude": SINGAPORE_LONGITUDE,
                "daily": (
                    "temperature_2m_max,temperature_2m_min,"
                    "precipitation_probability_max,weather_code"
                ),
                "temperature_unit": "celsius",
                "timezone": SINGAPORE_TIMEZONE,
                "start_date": start_date,
                "end_date": end_date,
            },
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as error:
        return f"Unable to retrieve the Singapore weather forecast from Open-Meteo: {error}"

    try:
        payload = response.json()
    except json.JSONDecodeError:
        return "Open-Meteo returned an invalid weather response."

    if not isinstance(payload, dict):
        return "Open-Meteo returned an invalid weather response."

    daily = payload.get("daily")
    if not isinstance(daily, dict):
        return "Open-Meteo did not return daily weather forecast data."

    dates = daily.get("time")
    minimum_temperatures = daily.get("temperature_2m_min")
    maximum_temperatures = daily.get("temperature_2m_max")
    precipitation_probabilities = daily.get("precipitation_probability_max")
    weather_codes = daily.get("weather_code")
    forecasts = (
        dates,
        minimum_temperatures,
        maximum_temperatures,
        precipitation_probabilities,
        weather_codes,
    )
    if (
        not all(isinstance(forecast, list) for forecast in forecasts)
        or dates != requested_dates
        or any(len(forecast) != len(requested_dates) for forecast in forecasts)
    ):
        return "Open-Meteo returned incomplete daily weather forecast data."

    forecast_lines = ["Singapore weather forecast:"]
    for forecast_date, minimum, maximum, precipitation_probability, weather_code in zip(
        dates,
        minimum_temperatures,
        maximum_temperatures,
        precipitation_probabilities,
        weather_codes,
        strict=True,
    ):
        weather = WMO_WEATHER_DESCRIPTIONS.get(
            weather_code, f"Open-Meteo weather code {weather_code}"
        )
        forecast_lines.extend(
            [
                "",
                str(forecast_date),
                f"Temperature: {minimum}-{maximum} C",
                f"Weather: {weather}",
                f"Precipitation probability: {precipitation_probability}%",
            ]
        )

    return "\n".join(forecast_lines)


@server.tool()
def get_currency_rate(
    amount: float,
    from_currency: str,
    to_currency: str,
) -> str:
    """Convert an amount using the latest Frankfurter exchange rate."""
    if (
        isinstance(amount, bool)
        or not isinstance(amount, (int, float))
        or not math.isfinite(amount)
        or amount <= 0
    ):
        return "Invalid amount. Provide a positive finite amount."

    if not isinstance(from_currency, str) or not CURRENCY_CODE_PATTERN.fullmatch(
        from_currency.strip()
    ):
        return "Invalid source currency code. Use a three-letter ISO currency code."
    if not isinstance(to_currency, str) or not CURRENCY_CODE_PATTERN.fullmatch(
        to_currency.strip()
    ):
        return "Invalid target currency code. Use a three-letter ISO currency code."

    source_currency = from_currency.strip().upper()
    target_currency = to_currency.strip().upper()
    try:
        response = httpx.get(
            FRANKFURTER_LATEST_URL,
            params={"base": source_currency, "symbols": target_currency},
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as error:
        return (
            f"Unable to retrieve the current {source_currency} to {target_currency} "
            f"exchange rate from Frankfurter: {error}"
        )

    try:
        payload = response.json()
    except json.JSONDecodeError:
        return "Frankfurter returned an invalid currency response."

    if not isinstance(payload, dict):
        return "Frankfurter returned an invalid currency response."

    rates = payload.get("rates")
    if not isinstance(rates, dict):
        return "Frankfurter did not return exchange rate data."

    exchange_rate = rates.get(target_currency)
    if (
        isinstance(exchange_rate, bool)
        or not isinstance(exchange_rate, (int, float))
        or not math.isfinite(exchange_rate)
        or exchange_rate <= 0
    ):
        return (
            f"Frankfurter did not return a valid exchange rate for {target_currency}."
        )

    rate_date = payload.get("date")
    if not isinstance(rate_date, str) or not rate_date.strip():
        return "Frankfurter did not return the exchange rate date."

    converted_amount = amount * exchange_rate
    return "\n".join(
        [
            "Currency conversion:",
            f"{amount:g} {source_currency} = {converted_amount:.2f} {target_currency}",
            (
                f"Exchange rate: 1 {source_currency} = "
                f"{exchange_rate:.6g} {target_currency}"
            ),
            f"Rate date: {rate_date}",
            "Source: Frankfurter",
        ]
    )


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
