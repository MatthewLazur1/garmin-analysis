# OpenWeatherMap API Response Variables Documentation

This document provides a comprehensive breakdown of all variables available in the OpenWeatherMap API response JSON structure.

## Overview

The OpenWeatherMap API returns weather data in a structured JSON format. Each response contains multiple nested objects with various weather parameters, location data, and system information.

## Root Level Variables

| Variable | Type | Description | Example Value |
|----------|------|-------------|---------------|
| `coord` | Object | Geographic coordinates of the location | `{'lon': -74.006, 'lat': 40.7128}` |
| `weather` | Array | Weather conditions array | `[{'id': 800, 'main': 'Clear', 'description': 'clear sky', 'icon': '01n'}]` |
| `base` | String | Internal parameter | `"stations"` |
| `main` | Object | Main weather parameters | Temperature, pressure, humidity data |
| `visibility` | Integer | Visibility in meters | `10000` |
| `wind` | Object | Wind information | Speed, direction, gusts |
| `clouds` | Object | Cloud coverage information | `{'all': 0}` |
| `dt` | Integer | Time of data calculation (Unix timestamp) | `1759273677` |
| `sys` | Object | System information | Sunrise, sunset, country, etc. |
| `timezone` | Integer | Timezone shift in seconds from UTC | `-14400` |
| `id` | Integer | City ID | `5128581` |
| `name` | String | City name | `"New York"` |
| `cod` | Integer | HTTP response code | `200` |

## Detailed Variable Breakdown

### 1. Coordinates Object (`coord`)

| Variable | Type | Description | Units | Example |
|----------|------|-------------|-------|---------|
| `lon` | Float | Longitude | Degrees | `-74.006` |
| `lat` | Float | Latitude | Degrees | `40.7128` |

### 2. Weather Array (`weather`)

Each element in the weather array contains:

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `id` | Integer | Weather condition ID | `800` |
| `main` | String | Group of weather parameters | `"Clear"` |
| `description` | String | Weather condition description | `"clear sky"` |
| `icon` | String | Weather icon ID | `"01n"` |

**Common Weather Condition IDs:**
- `800`: Clear sky
- `801`: Few clouds
- `802`: Scattered clouds
- `803`: Broken clouds
- `804`: Overcast clouds
- `300-321`: Drizzle
- `500-531`: Rain
- `600-622`: Snow
- `700-781`: Atmosphere (mist, fog, etc.)
- `800`: Clear
- `900-906`: Extreme weather

### 3. Main Weather Parameters (`main`)

| Variable | Type | Description | Units | Example |
|----------|------|-------------|-------|---------|
| `temp` | Float | Temperature | Kelvin (or specified unit) | `75.94` |
| `feels_like` | Float | Human perception of weather | Kelvin (or specified unit) | `75.58` |
| `temp_min` | Float | Minimum temperature | Kelvin (or specified unit) | `72.57` |
| `temp_max` | Float | Maximum temperature | Kelvin (or specified unit) | `77.22` |
| `pressure` | Integer | Atmospheric pressure | hPa | `1016` |
| `humidity` | Integer | Humidity percentage | % | `50` |
| `sea_level` | Integer | Atmospheric pressure at sea level | hPa | `1016` |
| `grnd_level` | Integer | Atmospheric pressure at ground level | hPa | `1015` |

### 4. Wind Information (`wind`)

| Variable | Type | Description | Units | Example |
|----------|------|-------------|-------|---------|
| `speed` | Float | Wind speed | m/s (or specified unit) | `10` |
| `deg` | Integer | Wind direction | Degrees (meteorological) | `23` |
| `gust` | Float | Wind gust speed | m/s (or specified unit) | `14` |

**Wind Direction Reference:**
- `0°` or `360°`: North
- `90°`: East
- `180°`: South
- `270°`: West

### 5. Cloud Coverage (`clouds`)

| Variable | Type | Description | Units | Example |
|----------|------|-------------|-------|---------|
| `all` | Integer | Cloudiness percentage | % | `0` |

### 6. System Information (`sys`)

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `type` | Integer | Internal parameter | `1` |
| `id` | Integer | Internal parameter | `4610` |
| `country` | String | Country code (ISO 3166-1 alpha-2) | `"US"` |
| `sunrise` | Integer | Sunrise time (Unix timestamp) | `1759229497` |
| `sunset` | Integer | Sunset time (Unix timestamp) | `1759272006` |

### 7. Additional Parameters

| Variable | Type | Description | Units | Example |
|----------|------|-------------|-------|---------|
| `visibility` | Integer | Visibility distance | Meters | `10000` |
| `dt` | Integer | Time of data calculation | Unix timestamp | `1759273677` |
| `timezone` | Integer | Timezone shift from UTC | Seconds | `-14400` |
| `id` | Integer | City ID | - | `5128581` |
| `name` | String | City name | - | `"New York"` |
| `cod` | Integer | HTTP response code | - | `200` |

## Data Types and Units

### Temperature Units
- **Default**: Kelvin
- **Imperial**: Fahrenheit (when `units=imperial`)
- **Metric**: Celsius (when `units=metric`)

### Pressure Units
- **Default**: hPa (hectopascals)
- **Imperial**: inHg (inches of mercury)
- **Metric**: hPa (hectopascals)

### Wind Speed Units
- **Default**: m/s (meters per second)
- **Imperial**: mph (miles per hour)
- **Metric**: m/s (meters per second)

### Distance Units
- **Default**: Meters
- **Imperial**: Miles
- **Metric**: Meters

## Common API Response Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `400` | Bad request |
| `401` | Unauthorized (invalid API key) |
| `404` | Not found |
| `429` | Too many requests (rate limit exceeded) |
| `500` | Internal server error |

## Usage Examples

### Accessing Temperature
```python
temperature = weather_data['main']['temp']
feels_like = weather_data['main']['feels_like']
```

### Accessing Weather Description
```python
weather_description = weather_data['weather'][0]['description']
weather_icon = weather_data['weather'][0]['icon']
```

### Accessing Wind Information
```python
wind_speed = weather_data['wind']['speed']
wind_direction = weather_data['wind']['deg']
wind_gust = weather_data['wind']['gust']
```

### Converting Unix Timestamps
```python
import datetime

# Convert Unix timestamp to readable date
sunrise_time = datetime.datetime.fromtimestamp(weather_data['sys']['sunrise'])
sunset_time = datetime.datetime.fromtimestamp(weather_data['sys']['sunset'])
```

## Notes

1. **Array Structure**: The `weather` field is an array, but typically contains only one element. Access it with `weather[0]`.

2. **Units**: Units depend on the `units` parameter in the API request:
   - `standard`: Kelvin, hPa, m/s
   - `metric`: Celsius, hPa, m/s
   - `imperial`: Fahrenheit, inHg, mph

3. **Timezone**: The `timezone` field represents the shift in seconds from UTC. Negative values indicate time zones west of UTC.

4. **Visibility**: Maximum visibility is typically 10,000 meters (10 km).

5. **Pressure**: Sea level pressure is usually higher than ground level pressure due to altitude effects.

## Error Handling

Always check the `cod` field before processing data:
```python
if weather_data['cod'] == 200:
    # Process weather data
    temperature = weather_data['main']['temp']
else:
    # Handle error
    print(f"Error: {weather_data.get('message', 'Unknown error')}")
```
