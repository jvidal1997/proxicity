"""
Factory utilities for constructing geospatial API clients used throughout the
data processing pipeline.

This module initializes and returns fully configured client instances for:
    - **CityCentersClient**: Interfaces with Nominatim to retrieve city center
      coordinates, using caching and retry-aware request handling.
    - **LandmarksClient**: Interfaces with Overpass API endpoints to fetch
      landmark data for specified geographic regions, with support for
      rate limiting, retries, and multiple endpoint fallbacks.

Configuration:
    All client parameters (cache file paths, request delays, retry limits,
    backoff factors, and API endpoints) are sourced from the `ENV` dictionary
    exposed by the `Settings` module. This ensures environment-driven,
    reproducible configuration.

Function Provided:
    - `create_clients()`: Constructs and returns a tuple containing the
      `CityCentersClient` and `LandmarksClient` instances in that order.

Intended Use:
    Import and call `create_clients()` within higher-level workflows that
    require geocoding operations, including fetching city center coordinates
    and retrieving landmark information.

Dependencies:
    - api.city_center.CityCentersClient
    - api.landmarks.LandmarksClient
    - Settings.ENV
"""

from api.city_center import CityCentersClient
from api.landmarks import LandmarksClient
from Settings import ENV as PROPERTY


def create_clients():
    """
    Creates API clients for Nominatim and Overpass
    :return: Separate API clients for Nominatim and Overpass (in that order)
    """
    city_client = CityCentersClient(
        cache_file=PROPERTY["CITY_CENTER_CACHE_FILE"],
        request_delay=PROPERTY["NOMINATIM_REQUEST_DELAY"],
        max_retries=PROPERTY["NOMINATIM_MAX_RETRIES"],
        backoff_factor=PROPERTY["NOMINATIM_BACKOFF_FACTOR"]
    )

    landmark_client = LandmarksClient(
        cache_file=PROPERTY["LANDMARKS_CACHE_FILE"],
        endpoints=PROPERTY["OVERPASS_ENDPOINTS"],
        request_delay=PROPERTY["OVERPASS_REQUEST_DELAY"],
        max_retries=PROPERTY["OVERPASS_MAX_RETRIES"],
        backoff_factor=PROPERTY["OVERPASS_BACKOFF_FACTOR"],
    )

    return city_client, landmark_client