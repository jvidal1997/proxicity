from api.city_center import CityCentersClient
from api.landmarks import LandmarksClient
from Settings import ENV as PROPERTY


def create_clients():
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