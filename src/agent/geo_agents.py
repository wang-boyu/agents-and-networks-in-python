from mesa import Model
from mesa_geo import GeoAgent
from shapely.geometry import Point
import pyproj

class Driveway(GeoAgent):
    unique_id: int
    model: Model
    geometry: Point
    crs: pyproj.CRS

    def __init__(self, unique_id, model, geometry, crs) -> None:
        super().__init__(unique_id, model, geometry, crs)


class LakeAndRiver(GeoAgent):
    unique_id: int
    model: Model
    geometry: Point
    crs: pyproj.CRS

    def __init__(self, unique_id, model, geometry, crs) -> None:
        super().__init__(unique_id, model, geometry, crs)


class Walkway(GeoAgent):
    unique_id: int
    model: Model
    geometry: Point
    crs: pyproj.CRS

    def __init__(self, unique_id, model, geometry, crs) -> None:
        super().__init__(unique_id, model, geometry, crs)
