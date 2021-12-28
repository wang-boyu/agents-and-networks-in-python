from __future__ import annotations

from mesa.space import Coordinate

from src.agent.vertex import Vertex


class BuildingCentroid:
    unique_id: int  # an ID that represents the building
    pos: Coordinate
    function: int  # 1 for work, 2 for home, 0 for neither
    entrance: Vertex  # nearest vertex on road

    def __init__(self, unique_id: int, pos: Coordinate, function: int) -> None:
        self.unique_id = unique_id
        self.pos = pos
        self.function = function
        self.entrance = None

    def __repr__(self) -> str:
        return f"BuildingCentroid(unique_id={self.unique_id}, pos={self.pos}, function={self.function}, " \
               f"entrance={self.entrance})"

    def __eq__(self, other):
        if isinstance(other, BuildingCentroid):
            return self.unique_id == other.unique_id
        return False
