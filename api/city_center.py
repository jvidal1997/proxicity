import os
import json
import time
import requests
from tqdm import tqdm
from Settings import ENV as PROPERTY
from devtools.multithread_logger import AsyncFileLogger  # Single async file logger

class CityCentersClient:
    """
    Client to fetch and cache city center coordinates from an API.
    Uses AsyncFileLogger to log events in real-time without blocking tqdm loops.
    """

    def __init__(self, cache_file="cache/city_centers_cache.json",
                 request_delay=1.1, max_retries=3, backoff_factor=2):
        self.cache_file = cache_file
        self.request_delay = request_delay
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.cache = {}

        # Ensure cache directory exists
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)

        # Initialize async file logger
        self.logger = AsyncFileLogger()
        self.logger.info("CityCentersClient initialized")

        self._load_cache()

    # ------------------------------
    # Cache Handling
    # ------------------------------
    def _load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r", encoding="utf-8") as f:
                self.cache = json.load(f)
            self.logger.info(f"Loaded cache from {self.cache_file}")

    def _save_cache(self):
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.cache, f)
        self.logger.info(f"Saved cache to {self.cache_file}")

    # ------------------------------
    # API Fetch
    # ------------------------------
    def fetch_city_center(self, city: str, state: str) -> dict | None:
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
        self.logger.info(f"Caching coordinates: {key} -> {self.cache[key]}")
        self._save_cache()
        return self.cache[key]

    # ------------------------------
    # Bulk generation
    # ------------------------------
    def generate_all_city_centers(self, df):
        centers = {}
        unique_pairs = df[['cityname', 'state']].drop_duplicates().values

        # tqdm loop with async logging
        for city, state in tqdm(unique_pairs, desc="Fetching city centers", colour="green"):
            centers[f"{city}, {state}"] = self.fetch_city_center(city, state)
        self.logger.info("Finished generating all city centers")
        return centers

    # ------------------------------
    # Access cache externally
    # ------------------------------
    def get_cache(self):
        return self.cache
