"""
City Centers Client
===================

This module provides the `CityCentersClient` class, a utility for fetching,
caching, and managing geographic center coordinates for U.S. cities via a
Nominatim-compatible API. It is designed for batch data workflows and integrates
non-blocking asynchronous file logging to avoid interrupting progress displays
such as tqdm loops.

Key Features
------------
- **API-backed coordinate lookup**
  Retrieves latitude/longitude pairs for (city, state) combinations using
  a configurable Nominatim API endpoint defined in `Settings.ENV`.

- **Persistent caching**
  Results are stored in a JSON cache file on disk to minimize redundant API
  requests. Cached entries are automatically reused on future runs.

- **Robust request handling**
  Includes retry logic, exponential backoff, and a delay between requests to
  respect rate limits and mitigate transient network failures.

- **Asynchronous file logging**
  Uses `AsyncFileLogger` to record events (initialization, cache loads/saves,
  retries, errors, etc.) without blocking or interfering with tqdm progress
  bars.

- **Bulk generation support**
  Capable of iterating over large sets of (city, state) pairs, commonly sourced
  from a pandas DataFrame, and producing a complete mapping of all resolved
  coordinates.

Usage Overview
--------------
Typical usage involves instantiating a client, fetching individual city centers,
or generating a full dataset:

    client = CityCentersClient()
    coords = client.fetch_city_center("Baltimore", "MD")

For vectorized workflows:

    centers = client.generate_all_city_centers(df)

Configuration
-------------
`CityCentersClient` accepts several parameters for request behavior:

- `cache_file`     : Path to the JSON cache file. Automatically created if missing.
- `request_delay`  : Base delay between API calls.
- `max_retries`    : Number of retry attempts on request failure.
- `backoff_factor` : Multiplier for exponential backoff between retries.

The cache can also be accessed directly via `get_cache()`.

Dependencies
------------
- `requests` for API calls
- `tqdm` for progress bars
- `AsyncFileLogger` for non-blocking log writes
- `Settings.ENV` for environment-configured API URL and user email

"""

import os
import json
import time
import requests
from tqdm import tqdm
from Settings import ENV as PROPERTY
from utils.devtools.multithread_logger import AsyncFileLogger  # Single async file logger


class CityCentersClient:
    """
    Client to fetch and cache city center coordinates from an API.
    Uses AsyncFileLogger to log events in real-time without blocking tqdm loops.
    """

    def __init__(self, cache_file="cache/city_centers_cache.json",
                 request_delay=1.1, max_retries=3, backoff_factor=2):
        """
        Initializes a CityCentersClient instance.
        :param cache_file: a filepath to desired cache file
        :param request_delay: Base delay between API calls
        :param max_retries: Number of retry attempts on request failure.
        :param backoff_factor: Multiplier for exponential backoff between retries.
        """
        self.cache_file = cache_file
        self.request_delay = request_delay
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.cache = {}

        # Ensure cache directory exists
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)

        # Initialize async file logger
        self.logger = AsyncFileLogger()

        # Load cache
        self._load_cache()
        self.logger.info("CityCentersClient initialized")

    def _load_cache(self):
        """
        Loads cached city center coordinates from the cache file if it exists, logging the outcome.
        """
        self.logger.info("Loading cache...")
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r", encoding="utf-8") as f:
                self.cache = json.load(f)
            if len(self.cache) == 0:
                self.logger.info("Cache is empty.")
            else:
                self.logger.info(f"Cache loaded successfully: {len(self.cache)} entries.")
        else:
            self.logger.info("Cache not found.")

    def _save_cache(self):
        """
        Saves the current in-memory cache to the cache file, logging success.
        """
        self.logger.info("Saving to cache...")
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.cache, f)
        self.logger.info("Cache saved successfully")

    def fetch_city_center(self, city: str, state: str) -> dict | None:
        """
        Fetches latitude and longitude for a given city and state, using a cache to avoid redundant API calls.
        Updates the cache and returns a dictionary with 'lat' and 'lon', or None if unavailable.
        :param city: Name of the city.
        :param state: Two-letter state abbreviation.
        :return: Dictionary with 'lat' and 'lon' or None.
        """
        key = f"{city}, {state}"
        if key in self.cache:
            return self.cache[key]

        params = {"q": f"{city}, {state}, USA", "format": "json", "limit": 1, "addressdetails": 0}
        headers = {"User-Agent": f"COMSC 230: Final Project ({PROPERTY['EMAIL']})"}

        data = {}
        for attempt in range(1, self.max_retries + 1):
            try:
                time.sleep(self.request_delay)
                response = requests.get(PROPERTY["NOMINATIM_API"], params=params, headers=headers, timeout=20)
                response.raise_for_status()
                data = response.json()
                break
            except requests.RequestException:
                if attempt < self.max_retries:
                    backoff_time = self.request_delay * (self.backoff_factor ** (attempt - 1))
                    self.logger.info(f"Retrying {key} in {backoff_time:.1f}s (attempt {attempt})")
                    time.sleep(backoff_time)
                else:
                    self.logger.error(f"Failed to fetch city center for {key} after {self.max_retries} attempts")
                    self.cache[key] = None
                    self._save_cache()
                    return None

        if not data:
            self.cache[key] = None
        else:
            coordinates = {"lat": float(data[0]["lat"]), "lon": float(data[0]["lon"])}
            self.cache[key] = coordinates
        self.logger.info(f"Caching city center coordinates: {key} -> {self.cache[key]}")
        self._save_cache()
        self.logger.info(f"Cache saved successfully: {key} -> {self.cache[key]}")
        return self.cache[key]

    def generate_all_city_centers(self, df):
        """
        Iterates over unique city-state pairs in a DataFrame, fetching and caching coordinates for each city.
        Returns a dictionary mapping "City, State" to coordinates.
        :param df: DataFrame with unique city-state pairs.
        :return: Dictionary mapping "City, State" to coordinates.
        """
        centers = {}
        unique_pairs = df[['cityname', 'state']].drop_duplicates().values

        # tqdm loop with async logging
        for city, state in tqdm(unique_pairs, desc="Fetching city centers", colour="green"):
            centers[f"{city}, {state}"] = self.fetch_city_center(city, state)
        self.logger.info(f"Fetched landmarks for {len(centers)} cities successfully.")
        return centers

    def get_cache(self):
        """
        Returns the current in-memory cache dictionary of all fetched city centers.
        :return:
        """
        return self.cache
