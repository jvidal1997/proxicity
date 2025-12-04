import os
import json
import time
import requests
from tqdm import tqdm
from settings.Settings import settings

class CityCentersClient:
    def __init__(self, cache_file="cache/city_centers_cache.json", request_delay=1.1, max_retries=3, backoff_factor=2):
        self.cache_file = cache_file
        self.request_delay = request_delay
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.cache = {}
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r") as f:
                self.cache = json.load(f)

    def _save_cache(self):
        with open(self.cache_file, "w") as f:
            json.dump(self.cache, f)

    def fetch_city_center(self, city: str, state: str) -> dict | None:
        key = f"{city}, {state}"
        if key in self.cache:
            return self.cache[key]

        params = {"q": f"{city}, {state}, USA", "format": "json", "limit": 1, "addressdetails": 0}
        headers = {"User-Agent": f"{settings.PROJECT_TITLE} ({settings.EMAIL})"}

        data = {}
        for attempt in range(1, self.max_retries + 1):
            try:
                time.sleep(self.request_delay)
                response = requests.get(settings.NOMINATIM_API, params=params, headers=headers, timeout=20)
                response.raise_for_status()
                data = response.json()
                break
            except requests.RequestException as _:
                if attempt < self.max_retries:
                    time.sleep(self.request_delay * (self.backoff_factor ** (attempt-1)))
                else:
                    self.cache[key] = None
                    self._save_cache()
                    return None

        if not data:
            self.cache[key] = None
        else:
            self.cache[key] = {"lat": float(data[0]["lat"]), "lon": float(data[0]["lon"])}
        self._save_cache()
        return self.cache[key]

    def generate_all_city_centers(self, df):
        centers = {}
        unique_pairs = df[['cityname', 'state']].drop_duplicates().values
        for city, state in tqdm(unique_pairs, desc="Fetching city centers"):
            centers[f"{city}, {state}"] = self.fetch_city_center(city, state)
        return centers

    def get_cache(self):
        return self.cache
