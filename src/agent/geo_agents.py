from mesa import Model
from mesa_geo import GeoAgent
from shapely.geometry import Point


class Driveway(GeoAgent):
    unique_id: int
    model: Model
    geometry: Point

    def __init__(self, unique_id, model, geometry) -> None:
        super().__init__(unique_id, model, geometry)


class LakeAndRiver(GeoAgent):
    unique_id: int
    model: Model
    geometry: Point

    def __init__(self, unique_id, model, geometry) -> None:
        super().__init__(unique_id, model, geometry)


class Walkway(GeoAgent):
    unique_id: int
    model: Model
    geometry: Point

    def __init__(self, unique_id, model, geometry) -> None:
        super().__init__(unique_id, model, geometry)
