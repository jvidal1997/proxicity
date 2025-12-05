import os
import json
import time
import random
import requests
from tqdm import tqdm
from Settings import ENV as PROPERTY

class LandmarksClient:
    def __init__(
        self,
        cache_file="cache/landmarks_cache.json",
        endpoints=None,
        request_delay=1.1,
        max_retries=3,
        backoff_factor=2,
    ):
        self.cache_file = cache_file
        self.endpoints = endpoints
        self.request_delay = request_delay
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

        self.cache = {}
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        self._load_cache()

        # Track last request time for enforced rate limit
        self._last_request_time = 0

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r") as f:
                self.cache = json.load(f)

    def _save_cache(self):
        with open(self.cache_file, "w") as f:
            json.dump(self.cache, f, indent=2)

    def _respect_rate_limit(self):
        """Ensures no request is made faster than request_delay seconds."""
        now = time.time()
        elapsed = now - self._last_request_time

        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)

        self._last_request_time = time.time()

    def fetch_landmarks(self, city: str, state: str):
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
                    delay = self.request_delay * (self.backoff_factor ** (attempt - 1))
                    time.sleep(delay)
                else:
                    self.cache[key] = []
                    self._save_cache()
                    return []

        # Parse OSM nodes
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

        self.cache[key] = landmarks
        self._save_cache()
        return landmarks

    def fetch_landmarks_for_cities(self, city_state_pairs):
        results = {}

        for city, state in tqdm(city_state_pairs, desc="Fetching landmarks", colour="green"):
            results[f"{city}, {state}"] = self.fetch_landmarks(city, state)

        return results

    def get_cache(self):
        return self.cache
