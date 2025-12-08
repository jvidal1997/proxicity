"""
Landmarks Client
================

This module defines the `LandmarksClient`, a high-level utility for querying,
caching, and managing points of interest (“landmarks”) from OpenStreetMap’s
Overpass API for U.S. cities. It is designed for reliable batch processing and
uses asynchronous file logging to ensure that diagnostic output does not
interfere with tqdm progress bars or slow down long-running data pipelines.

Overview
--------
The client accepts (city, state) pairs and returns lists of landmarks within the
administrative boundary of that city. Landmarks are derived from OSM elements
associated with tags such as **tourism**, **amenity**, **historic**, and
**leisure**.

The class supports persistent caching, rate limiting between requests,
exponential backoff retry logic, and the ability to distribute POST requests
across multiple Overpass API endpoints.

Key Features
------------
- **Overpass API integration**
  Automatically constructs and submits Overpass QL queries to retrieve
  point-of-interest elements for a given city/state region.

- **Persistent JSON caching**
  Results are written to a JSON cache file, reducing redundant calls and enabling
  fast repeated runs. Cached results are automatically reused whenever possible.

- **Rate-limit enforcement**
  Ensures that API calls never occur more frequently than `request_delay`
  seconds, even across retries. This prevents needless 429/timeout errors when
  working with strict Overpass servers.

- **Robust retry and backoff**
  Implements multiple retry attempts with exponential backoff, improving
  stability against intermittent server failures.

- **Asynchronous file logging**
  Uses `AsyncFileLogger` to produce non-blocking, thread-safe logs without
  slowing down tqdm progress bars.

- **Bulk landmark retrieval**
  Provides a helper method for iterating through large batches of (city, state)
  pairs and building a complete dataset of landmark lists.

Configuration
-------------
`LandmarksClient` supports flexible initialization:

- `cache_file`     : Path to the JSON cache file. Automatically created if needed.
- `endpoints`      : A list of Overpass API endpoint URLs to randomly distribute
                      requests across.
- `request_delay`  : Minimum delay between requests (rate-limit control).
- `max_retries`    : Number of retry attempts per request.
- `backoff_factor` : Exponential multiplier applied to retry delays.

Workflow Example
----------------
Basic usage:

    client = LandmarksClient(endpoints=["https://overpass-api.de/api/interpreter"])
    landmarks = client.fetch_landmarks("Baltimore", "MD")

Batch usage:

    city_state_pairs = [("Baltimore", "MD"), ("Denver", "CO")]
    all_landmarks = client.fetch_landmarks_for_cities(city_state_pairs)

Dependencies
------------
- `requests` for HTTP operations
- `tqdm` for progress displays
- `AsyncFileLogger` for concurrent, non-blocking log output
- `Settings.ENV` for user-agent metadata and environment configuration

"""
import os
import json
import time
import random
import requests
from tqdm import tqdm
from Settings import ENV as PROPERTY
from utils.devtools.multithread_logger import AsyncFileLogger


class LandmarksClient:
    """
        Fetches and caches landmark data for U.S. cities using the Overpass API.

        Handles rate limiting, retries with exponential backoff, and persistent
        JSON caching to support large batch queries. Uses an asynchronous logger
        to record events without blocking tqdm progress bars.
    """
    def __init__(
        self,
        cache_file="cache/landmarks_cache.json",
        endpoints=None,
        request_delay=1.1,
        max_retries=3,
        backoff_factor=2,
    ):
        """
        Initializes the client, sets up caching, asynchronous logging, and rate-limiting.
        Prepares the class for fetching landmarks.
        :param cache_file: Path to the cache file. Automatically created if needed.
        :param endpoints: List of Overpass API endpoint URLs to randomly distribute
        :param request_delay: Minimum delay between requests (rate-limit control).
        :param max_retries: Number of retry attempts per request.
        :param backoff_factor: Exponential multiplier applied to retry delays.
        """
        self.cache_file = cache_file
        self.endpoints = endpoints
        self.request_delay = request_delay
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

        # Ensure cache directory exists
        self.cache = {}
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)

        # Initialize async file logger
        self.logger = AsyncFileLogger()

        # Load cache
        self._load_cache()

        # Track last request time for enforced rate limit
        self._last_request_time = 0
        self.logger.info("LandmarksClient initialized")

    def _load_cache(self):
        """
        Loads the cache from the cache file if it exists.
        Logs the number of entries or notes if the cache is empty or missing.
        """
        self.logger.info("Loading cache...")
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r") as f:
                self.cache = json.load(f)
            if len(self.cache) == 0:
                self.logger.info("Cache is empty.")
            else:
                self.logger.info(f"Cache loaded successfully: {len(self.cache)} entries.")
        else:
            self.logger.info("Cache not found.")

    def _save_cache(self):
        """
        Saves the current in-memory cache to the cache file. Logs the operation and success status.
        """
        self.logger.info("Saving cache...")
        with open(self.cache_file, "w") as f:
            json.dump(self.cache, f, indent=2)
        self.logger.info("Cache saved successfully")

    def _respect_rate_limit(self):
        """Ensures no request is made faster than request_delay seconds."""
        now = time.time()
        elapsed = now - self._last_request_time

        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)

        self._last_request_time = time.time()

    def fetch_landmarks(self, city: str, state: str):
        """
        Fetches landmarks for a given city and state using the Overpass API.
        Applies rate limiting, retries with exponential backoff, caches results, and returns a list of landmarks
        (each a dict with name, lat, lon).
        :param city: the city to fetch landmarks for
        :param state: the state to fetch landmarks for
        :return: a list of dicts with name, latitude (lat), longitude (lon) key-value pairs
        """
        key = f"{city}, {state}"

        # Return cached
        if key in self.cache:
            return self.cache[key]

        # Overpass Query
        query = f"""
        [out:json][timeout:25];
        area["ISO3166-2"="US-{state}"]->.stateArea;
        area["name"="{city}"]["boundary"="administrative"](area.stateArea)->.cityArea;
        (
          node["tourism"](area.cityArea);
          node["amenity"](area.cityArea);
          node["historic"](area.cityArea);
          node["leisure"](area.cityArea);
        );
        out center;
        """

        headers = {"User-Agent": f"COMSC 230: Final Project ({PROPERTY["EMAIL"]})"}
        data = []

        # Retry logic
        for attempt in range(1, self.max_retries + 1):
            try:
                # Enforce rate limit on EVERY request attempt
                self._respect_rate_limit()
                self.logger.info(f"Attempting to fetch landmarks for {key}...")
                response = requests.post(
                    random.choice(self.endpoints),
                    data={"data": query},
                    headers=headers,
                    timeout=40,
                )
                response.raise_for_status()

                data = response.json()
                break

            except Exception as _:
                # Retry or fail
                if attempt < self.max_retries:
                    self.logger.warning(f"Failed to fetch landmarks for {key}. \nRetrying, {self.max_retries - attempt} attempts left...")
                    delay = self.request_delay * (self.backoff_factor ** (attempt - 1))
                    time.sleep(delay)
                else:
                    self.logger.error(f"Failed to fetch landmarks for {key}. No more attempts left. Saving None.")
                    self.cache[key] = []
                    self._save_cache()
                    return []

        # Parse response
        self.logger.info(f"Fetched landmarks for {key} successfully.")
        elements = data.get("elements", [])
        landmarks = [
            {
                "name": el.get("tags", {}).get("name"),
                "lat": el["lat"],
                "lon": el["lon"],
            }
            for el in elements
            if "lat" in el and "lon" in el
        ]

        # Add to cache
        self.cache[key] = landmarks

        # Save cache to file
        self.logger.info(f"Caching {len(landmarks)} landmarks to {key}...")
        self._save_cache()
        self.logger.info(f"Landmarks for {key} cached successfully")

        return landmarks

    def fetch_landmarks_for_cities(self, city_state_pairs):
        """
        Fetches landmarks for multiple city/state pairs in bulk.
        Uses tqdm to display progress, caches results, and returns a dictionary mapping "City, State" to landmark lists.
        :param city_state_pairs: a list of unique city/state pairs
        :return: a list of dicts with name, latitude (lat), longitude (lon) key-value pairs
        """
        # Initialize results
        results = {}

        # Fetch landmarks from API or cache
        self.logger.info("Fetching landmarks...")
        for city, state in tqdm(city_state_pairs, desc="Fetching landmarks", colour="green"):
            results[f"{city}, {state}"] = self.fetch_landmarks(city, state)
        self.logger.info(f"Fetched landmarks for {len(results)} cities successfully.")

        # Return results
        return results

    def get_cache(self):
        """
        Returns the current in-memory cache dictionary for inspection or export.
        :return: a dictionary mapping city/state pairs to landmarks
        """
        return self.cache
