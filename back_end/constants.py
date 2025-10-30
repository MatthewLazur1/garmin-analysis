REGRESSION_START_DATE_YEAR = 2024
REGRESSION_START_DATE_MONTH = 1
REGRESSION_START_DATE_DAY = 1

# Default weather location (lat/lon)
DEFAULT_LATITUDE = 35.7796
DEFAULT_LONGITUDE = -78.6382

# Elevation gain assumption (feet per mile)
ELEVATION_FT_PER_MILE = 50.0

# Target average HR by workout type
HR_TARGETS = {
    'Easy': 140,
    'Steady': 155,
    'Workout': 175,
    'Rest': None,  # Do not predict on Rest
}
