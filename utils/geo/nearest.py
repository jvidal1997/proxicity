"""
BallTree Utility Functions for Geographic Coordinates
=====================================================

This module provides helper functions for working with latitude/longitude
coordinates using a BallTree data structure for fast nearest-neighbor queries.

Functions
---------
- `_validate_coords(coords)`
  Validates a coordinate pair, ensuring it is not None or NaN.

- `build_balltree(coords_list)`
  Constructs a BallTree from a list of [latitude, longitude] pairs.
  Returns both the BallTree (with coordinates in radians) and the original array in degrees.

- `query_balltree(tree, point)`
  Queries the nearest neighbor for a given point in the BallTree.
  Returns the distance in miles and the index of the closest point, or (np.nan, None)
  if the tree is None.

Notes
-----
- Distances are computed using the haversine metric.
- The module depends on `numpy` and `scikit-learn` for BallTree operations.
- Earth radius in miles is read from `Settings.ENV["EARTH_RADIUS_MILES"]`.
"""
import numpy as np
from numpy.typing import ArrayLike
from sklearn.neighbors import BallTree
from Settings import ENV as PROPERTY


def _validate_coords(coords: tuple[float, float] | None) -> bool:
    """
    Validates that the coordinates are within the allowed range.
    :param coords: Coordinates to validate.
    :return: True if the coordinates are within the allowed range.
    """
    if coords is None:
        return False
    lat, lon = coords
    return not (lat is None or lon is None or np.isnan(lat) or np.isnan(lon))


def build_balltree(coords_list: ArrayLike) -> tuple[BallTree, np.ndarray]:
    """
    Builds a BallTree for fast nearest-neighbor queries from a list of [lat, lon] pairs.
    Returns the BallTree (coordinates in radians) and the original coordinates array in degrees.
    :param coords_list: List of [lat, lon] pairs.
    :return: BallTree (coordinates in radians) and the original coordinates array in degrees.
    """
    coords = np.array(coords_list, dtype=float)
    tree = BallTree(np.radians(coords), metric="haversine")
    return tree, coords


def query_balltree(tree, point) -> tuple[float, None] | tuple[float, int]:
    """
    Queries a BallTree for a point and returns the coordinates in degrees.
    :param tree: BallTree (coordinates in radians) and the original coordinates array in degrees.
    :param point: Point to query.
    :return: Coordinates in degrees.
    """
    if tree is None:
        return np.nan, None

    dist, idx = tree.query(np.radians([point]), k=1)
    return float(dist[0][0] * PROPERTY["EARTH_RADIUS_MILES"]), int(idx[0][0])
