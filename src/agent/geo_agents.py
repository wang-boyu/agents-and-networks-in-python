from mesa import Model
from mesa_geo import GeoAgent
from shapely.geometry import Point


class GmuDriveway(GeoAgent):
    unique_id: int
    model: Model
    shape: Point

    def __init__(self, unique_id, model, shape) -> None:
        super().__init__(unique_id, model, shape)


class GmuLakeAndRiver(GeoAgent):
    unique_id: int
    model: Model
    shape: Point

    def __init__(self, unique_id, model, shape) -> None:
        super().__init__(unique_id, model, shape)


class GmuWalkway(GeoAgent):
    unique_id: int
    model: Model
    shape: Point

    def __init__(self, unique_id, model, shape) -> None:
        super().__init__(unique_id, model, shape)
