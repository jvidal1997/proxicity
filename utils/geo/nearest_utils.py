"""
Nearest Neighbor Utilities for Apartments, Cities, and Landmarks
================================================================

This module provides helper functions to efficiently compute distances between
apartments, city centers, and landmarks using BallTree nearest-neighbor queries.
It includes caching mechanisms to avoid rebuilding BallTrees for repeated runs
and integrates with pandas for vectorized operations.

Key Functions
-------------
- `_get_cache_path(cache_dir, key)`
  Generates a safe file path for caching a BallTree, creating the directory if needed.

- `build_or_load_balltree(coords_list, cache_dir=None, cache_key=None)`
  Builds a BallTree from coordinates or loads it from a cached file if available.

- `_compute_city_tree(city_centers, cache_dir)`
  Filters valid city coordinates and returns a BallTree for city centers and the set of valid keys.

- `_compute_landmark_trees(landmarks_by_city, cache_dir)`
  Filters valid landmark coordinates for each city and returns a dict of BallTrees and their coordinate arrays/names.

- `append_apartments_with_nearest(df, city_centers, landmarks_by_city, cache_dir=None)`
  Adds nearest city center and landmark distances (in miles) to a DataFrame of apartments.
  Returns a new DataFrame with additional columns:
    - `nearest_city_center_miles`
    - `nearest_landmark_miles`
    - `nearest_landmark_name`

Notes
-----
- Distances are computed using haversine metric via BallTree.
- Coordinates must be validated with `_validate_coords` before building trees.
- Dependencies: `numpy`, `pandas`, `tqdm`, `joblib`, and the `geo.nearest` module.
- BallTrees are cached using pickle files to `cache_dir` for performance.
"""
import os
import re
import numpy as np
import joblib
from tqdm import tqdm
import pandas as pd
from utils.geo.nearest import _validate_coords, build_balltree, query_balltree


def _get_cache_path(cache_dir: str, key: str) -> str:
    """
    Generates a safe file path for caching a BallTree. Creates the directory if it does not exist.
    Replaces invalid characters in the key with underscores.
    :param cache_dir: Directory to cache BallTree data for.
    :param key: str | None by default.
    :return: Path to the cached BallTree file.
    """
    os.makedirs(cache_dir, exist_ok=True)
    safe_key = re.sub(r"[^\w\-]", "_", key)
    return os.path.join(cache_dir, f"{safe_key}_tree.pkl")


def build_or_load_balltree(coords_list: list, cache_dir: str = None, cache_key: str = None):
    """
    Build a BallTree for the given coordinates or load it from cache.
    Returns: tree, np.array of coordinates
    """
    coords = np.array(coords_list, dtype=float)
    path = None

    if cache_dir and cache_key:
        path = _get_cache_path(cache_dir, cache_key)
        if os.path.exists(path):
            tree = joblib.load(path)
            return tree, coords

    tree, coords_array = build_balltree(coords)

    if path:
        joblib.dump(tree, path)

    return tree, coords_array


def _compute_city_tree(city_centers, cache_dir):
    """
    Filters city centers to keep only valid coordinates and builds or loads a BallTree for nearest-neighbor queries.
    Returns the BallTree and a set of city keys with valid coordinates.
    :param city_centers: DataFrame of city centers.
    :param cache_dir: Directory to cache BallTree data for.
    :return: BallTree and a set of city keys with valid coordinates.
    """
    city_keys, city_coords = [], []
    for key, coords in city_centers.items():
        if coords and _validate_coords((coords['lat'], coords['lon'])):
            city_keys.append(key)
            city_coords.append([coords['lat'], coords['lon']])
    tree, _ = build_or_load_balltree(city_coords, cache_dir, "city_centers") if city_coords else (None, None)
    return tree, set(city_keys)


def _compute_landmark_trees(landmarks_by_city, cache_dir):
    """
    Filters landmarks by city to include only valid coordinates, builds or loads a BallTree for each city, and returns
    dictionaries mapping city keys to BallTrees and to coordinate/name data for valid landmarks.
    :param landmarks_by_city: DataFrame of landmarks by city.
    :param cache_dir: Directory to cache BallTree data for.
    :return: BallTree and a set of city keys with valid coordinates.
    """
    landmark_trees, landmark_coords = {}, {}
    for city_key, lms in landmarks_by_city.items():
        valid_coords, valid_names = [], []
        for lm in lms:
            lat, lon = lm.get('lat'), lm.get('lon')
            if _validate_coords((lat, lon)):
                valid_coords.append([lat, lon])
                valid_names.append(lm.get('name'))
        if valid_coords:
            tree, coords_array = build_or_load_balltree(valid_coords, cache_dir, city_key)
            landmark_trees[city_key] = tree
            landmark_coords[city_key] = (coords_array, valid_names)
        else:
            landmark_trees[city_key] = None
            landmark_coords[city_key] = (None, None)
    return landmark_trees, landmark_coords


def append_apartments_with_nearest(df: pd.DataFrame, city_centers: dict, landmarks_by_city: dict, cache_dir: str = None) -> pd.DataFrame:
    """
    Computes nearest city center and landmark distances for each apartment in the DataFrame.
    Returns a new DataFrame with additional columns: nearest_city_center_miles, nearest_landmark_miles, nearest_landmark_name.
    :param df: DataFrame containing apartment coordinates.
    :param city_centers: Dictionary of city centers.
    :param landmarks_by_city: Dictionary of landmark coordinates.
    :param cache_dir: Directory to cache BallTree data for.
    :return: New DataFrame with additional columns:
        - `nearest_city_center_miles`
        - `nearest_landmark_miles`
        - `nearest_landmark_name`
    """
    df = df.copy()
    city_tree, city_keys = _compute_city_tree(city_centers, cache_dir)
    landmark_trees, landmark_coords = _compute_landmark_trees(landmarks_by_city, cache_dir)

    city_dists, landmark_dists, landmark_names = [], [], []

    print("Computing nearest distances for apartments...")
    for row in tqdm(df.itertuples(index=False), total=len(df), desc="Nearest distances", colour="green"):
        apt_lat, apt_lon = row.latitude, row.longitude
        city_key = f"{row.cityname}, {row.state}"

        # --- City Center Distance ---
        if city_tree and city_key in city_keys:
            dist_city, _ = query_balltree(city_tree, [apt_lat, apt_lon])
            city_dists.append(dist_city)
        else:
            city_dists.append(np.nan)

        # --- Landmark Distance ---
        lm_tree = landmark_trees.get(city_key)
        lm_coords_array, lm_names = landmark_coords.get(city_key) or (None, None)
        if lm_tree is not None and lm_coords_array is not None and len(lm_coords_array) > 0:
            dist_landmark, idx2 = query_balltree(lm_tree, [apt_lat, apt_lon])
            landmark_dists.append(dist_landmark)
            landmark_names.append(lm_names[idx2] if lm_names else None)
        else:
            landmark_dists.append(np.nan)
            landmark_names.append(None)

    # Assign results to DataFrame
    df['nearest_city_center_miles'] = city_dists
    df['nearest_landmark_miles'] = landmark_dists
    df['nearest_landmark_name'] = landmark_names

    return df
