from api.city_center import CityCentersClient
from api.landmarks import LandmarksClient
from Settings import ENV as PROPERTY
import json

# Creating API clients
cc_client_from_json_cache = CityCentersClient()
cc_client_from_env_cache = CityCentersClient(
        cache_file=PROPERTY["CITY_CENTER_CACHE_FILE"],
        request_delay=PROPERTY["NOMINATIM_REQUEST_DELAY"],
        max_retries=PROPERTY["NOMINATIM_MAX_RETRIES"],
        backoff_factor=PROPERTY["NOMINATIM_BACKOFF_FACTOR"]
    )

ld_client_from_json_cache = LandmarksClient()
ld_client_from_env_cache  = LandmarksClient(
        cache_file=PROPERTY["LANDMARKS_CACHE_FILE"],
        endpoints=PROPERTY["OVERPASS_ENDPOINTS"],
        request_delay=PROPERTY["OVERPASS_REQUEST_DELAY"],
        max_retries=PROPERTY["OVERPASS_MAX_RETRIES"],
        backoff_factor=PROPERTY["OVERPASS_BACKOFF_FACTOR"],
    )


def print_cache_state(cc_client_from_json_cache, cc_client_from_env_cache):
    json_cache = cc_client_from_json_cache.get_cache()
    env_cache = cc_client_from_env_cache.get_cache()

    json_valid_entry_count = len(json_cache)
    env_valid_entry_count = len(env_cache)

    if json_valid_entry_count > 0 and env_valid_entry_count > 0:
        for entry in json_cache:
            if json_cache[entry] is None:
                json_valid_entry_count -= 1

        for entry in env_cache:
            if env_cache[entry] is None:
                env_valid_entry_count -= 1


    print(f"JSON Cache \n\tTotal Entries: {len(json_cache)}\n\tTotal Valid Entries: {json_valid_entry_count}/{len(json_cache)}")
    print(f"ENV Cache: \n\tTotal Entries: {len(env_cache)}\n\tTotal Valid Entries: {env_valid_entry_count}/{len(env_cache)}")


print("Validating city centers cache...")
print_cache_state(cc_client_from_json_cache, cc_client_from_env_cache)
print("-------------------------------------")
with open(PROPERTY["CITY_CENTER_CACHE_FILE"], "w", encoding="utf-8") as f:
    json.dump(cc_client_from_json_cache.get_cache(), f)
print(f"Saved cache to {PROPERTY["CITY_CENTER_CACHE_FILE"]}")
print("-------------------------------------")
print_cache_state(cc_client_from_json_cache, cc_client_from_env_cache)
print("Validation complete.")


print("Validating landmarks cache...")
print_cache_state(ld_client_from_json_cache, ld_client_from_env_cache)
print("-------------------------------------")
with open(PROPERTY["LANDMARKS_CACHE_FILE"], "w", encoding="utf-8") as f:
    json.dump(ld_client_from_json_cache.get_cache(), f)
print(f"Saved cache to {PROPERTY["CITY_CENTER_CACHE_FILE"]}")
print("-------------------------------------")
print_cache_state(ld_client_from_json_cache, ld_client_from_env_cache)
print("Validation complete.")