# geo/nearest_utils.py
import os
import re
import numpy as np
import joblib
from tqdm import tqdm
import pandas as pd
from geo.nearest import _validate_coords, build_balltree, query_balltree


def _get_cache_path(cache_dir: str, key: str) -> str:
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
    city_keys, city_coords = [], []
    for key, coords in city_centers.items():
        if coords and _validate_coords((coords['lat'], coords['lon'])):
            city_keys.append(key)
            city_coords.append([coords['lat'], coords['lon']])
    tree, _ = build_or_load_balltree(city_coords, cache_dir, "city_centers") if city_coords else (None, None)
    return tree, set(city_keys)


def _compute_landmark_trees(landmarks_by_city, cache_dir):
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
    Add nearest city center and landmark distances to apartment DataFrame.
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
