from mesa import Model
from mesa_geo import GeoAgent
from shapely.geometry import Point


class Driveway(GeoAgent):
    unique_id: int
    model: Model
    shape: Point

    def __init__(self, unique_id, model, shape) -> None:
        super().__init__(unique_id, model, shape)


class LakeAndRiver(GeoAgent):
    unique_id: int
    model: Model
    shape: Point

    def __init__(self, unique_id, model, shape) -> None:
        super().__init__(unique_id, model, shape)


class Walkway(GeoAgent):
    unique_id: int
    model: Model
    shape: Point

    def __init__(self, unique_id, model, shape) -> None:
        super().__init__(unique_id, model, shape)
