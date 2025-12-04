from api.city_center import CityCentersClient
from api.landmarks import LandmarksClient
from settings.Settings import settings


def create_clients():
    city_client = CityCentersClient(
        settings.CITY_CENTER_CACHE_FILE,
        settings.NOMINATIM_REQUEST_DELAY,
        settings.NOMINATIM_MAX_RETRIES,
        settings.NOMINATIM_BACKOFF_FACTOR
    )
    landmark_client = LandmarksClient(
        cache_file=settings.LANDMARKS_CACHE_FILE,
        endpoints=settings.OVERPASS_ENDPOINTS,
        request_delay=settings.OVERPASS_REQUEST_DELAY,
        max_retries=settings.OVERPASS_MAX_RETRIES,
        backoff_factor=settings.OVERPASS_BACKOFF_FACTOR,
    )
    return city_client, landmark_client