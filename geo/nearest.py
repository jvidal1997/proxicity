import numpy as np
from numpy.typing import ArrayLike
from sklearn.neighbors import BallTree

EARTH_RADIUS_MILES = 3958.8


def _validate_coords(coords: tuple[float, float] | None) -> bool:
    """Ensure coordinates are valid numbers."""
    if coords is None:
        return False
    lat, lon = coords
    return not (lat is None or lon is None or np.isnan(lat) or np.isnan(lon))


def build_balltree(coords_list: ArrayLike) -> tuple[BallTree, np.ndarray]:
    """
    Build a BallTree from a list of [lat, lon] pairs.

    Returns
    -------
    tree : BallTree
        BallTree object with coordinates in radians.
    coords_array : np.ndarray
        Original coordinates array in degrees.
    """
    coords = np.array(coords_list, dtype=float)
    tree = BallTree(np.radians(coords), metric="haversine")
    return tree, coords


def query_balltree(tree, point) -> tuple[float, None] | tuple[float, int]:
    """
    Query the nearest neighbor from a BallTree.

    Parameters
    ----------
    tree : BallTree or None
        Pre-built BallTree object with coordinates in radians.
    point : list or tuple
        [latitude, longitude] of the query point in degrees.

    Returns
    -------
    dist_miles : float
        Distance to the nearest neighbor in miles (np.nan if tree is None).
    idx : int or None
        Index of the nearest neighbor in the original dataset.
    """
    if tree is None:
        return np.nan, None

    dist, idx = tree.query(np.radians([point]), k=1)
    return float(dist[0][0] * EARTH_RADIUS_MILES), int(idx[0][0])
