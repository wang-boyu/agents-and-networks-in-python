from typing import Tuple

import numpy as np


def get_coord_matrix(x_min: float, x_max: float, y_min: float, y_max: float) -> np.ndarray:
    return np.array([[x_min, y_min, 1.0],
                     [x_min, y_max, 1.0],
                     [x_max, y_min, 1.0],
                     [x_max, y_max, 1.0]])


def get_affine_transform(from_coord: np.ndarray, to_coord: np.ndarray) -> \
        Tuple[float, float, float, float, float, float]:
    A, res, rank, s = np.linalg.lstsq(from_coord, to_coord)

    np.testing.assert_array_almost_equal(res, np.zeros_like(res), decimal=15)
    np.testing.assert_array_almost_equal(A[:, 2], np.array([0.0, 0.0, 1.0]), decimal=15)

    # A.T = [[a, b, x_off],
    #        [d, e, y_off],
    #        [0, 0,  1  ]]
    # affine transform = [a, b, d, e, x_off, y_off]
    # For details, refer to https://geopandas.org/en/stable/docs/reference/api/geopandas.GeoSeries.affine_transform.html
    return A.T[0, 0], A.T[0, 1], A.T[1, 0], A.T[1, 1], A.T[0, 2], A.T[1, 2]
