from __future__ import annotations

import uuid
from random import randrange

from mesa.model import Model
from mesa.space import FloatCoordinate
from mesa_geo.geoagent import GeoAgent
from shapely.geometry import Polygon


class Building(GeoAgent):
    unique_id: int  # an ID that represents the building
    model: Model
    shape: Polygon
    centroid: FloatCoordinate
    name: str
    function: float  # 1.0 for work, 2.0 for home, 0.0 for neither
    entrance_pos: FloatCoordinate  # nearest vertex on road
    entrance_id: int

    def __init__(self, unique_id, model, shape) -> None:
        super().__init__(unique_id=unique_id, model=model, shape=shape)
        self.entrance = None
        self.entrance_id = None
        self.name = str(uuid.uuid4())
        self.function = randrange(3)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(unique_id={self.unique_id}, name={self.name}, function={self.function}, " \
               f"centroid={self.centroid})"

    def __eq__(self, other):
        if isinstance(other, Building):
            return self.unique_id == other.unique_id
        return False
