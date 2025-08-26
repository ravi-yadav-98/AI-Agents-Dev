import os
import requests
from mcp.server.fastmcp import FastMCP, Context

OPENWEATHERMAP_API_KEY = "015236b3a26f8ee64fcae06eb92dbb50"

# Initialize the FastMCP server
mcp = FastMCP("WeatherAssistant")

@mcp.tool()
# 2. Add 'async' and 'ctx: Context'
async def get_weather(location: str, ctx: Context) -> dict:
    """
    Fetches the current weather for a specified location using the OpenWeatherMap API.

    Args:
        location: The city name and optional country code (e.g., "London,uk").

    Returns:
        A dictionary containing weather information or an error message.
    """
    await ctx.info(f"Received request to get weather for '{location}'.")

    if not OPENWEATHERMAP_API_KEY or OPENWEATHERMAP_API_KEY == "YOUR_OPENWEATHERMAP_API_KEY":
        await ctx.error("Server-side error: OpenWeatherMap API key is not configured.")
        return {"error": "OpenWeatherMap API key is not configured on the server."}

    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": location,
        "appid": OPENWEATHERMAP_API_KEY,
        "units": "metric"
    }

    try:
        await ctx.debug(f"Making GET request to OpenWeatherMap API: {base_url}")
        response = requests.get(base_url, params=params)
        response.raise_for_status()

        data = response.json()
        await ctx.info("Successfully received data from weather API.")

        weather_description = data["weather"][0]["description"]
        temperature = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]
        
        await ctx.debug("Successfully parsed all weather data fields.")

        return {
            "location": data["name"],
            "weather": weather_description,
            "temperature_celsius": f"{temperature}°C",
            "feels_like_celsius": f"{feels_like}°C",
            "humidity": f"{humidity}%",
            "wind_speed_mps": f"{wind_speed} m/s"
        }

    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            await ctx.warning(f"API returned 404 Not Found for location: '{location}'.")
            return {"error": f"Could not find weather data for '{location}'. Please check the location name."}
        elif response.status_code == 401:
            await ctx.error("API authentication failed. The server's API key is likely invalid.")
            return {"error": "Authentication failed. The API key is likely invalid or inactive."}
        else:
            await ctx.error(f"An unexpected HTTP error occurred: {http_err}")
            return {"error": f"An HTTP error occurred: {http_err}"}
    except requests.exceptions.RequestException as req_err:
        await ctx.error(f"A network error occurred during API call: {req_err}")
        return {"error": f"A network error occurred: {req_err}"}
    except KeyError:
        await ctx.error("Failed to parse the weather API response due to unexpected data format.")
        return {"error": "Received unexpected data format from the weather API."}
    except Exception as e:
        await ctx.error(f"A critical unexpected error occurred in get_weather tool: {e}")
        return {"error": f"An unexpected error occurred: {e}"}

if __name__ == "__main__":
    # The server will run and listen for requests from the client over stdio
    mcp.run(transport="stdio")