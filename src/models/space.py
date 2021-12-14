from __future__ import annotations
from typing import Set

from mesa.space import Coordinate, FloatCoordinate


class Vertex:
    unique_id: int
    pos: FloatCoordinate
    neighbors: Set[Vertex]  # agent set of neighboring vertices
    is_entrance: bool  # if it is an entrance to a building
    delete_test: bool  # used to delete in test
    # the following variables are used and renewed in each path-selection
    dist: int  # distance from original point to here
    done: bool  # 1 if has calculated the shortest path through this point, 0 otherwise
    last_node: Vertex  # last node to this point in shortest path

    def __init__(self, unique_id: int, pos: FloatCoordinate) -> None:
        self.unique_id = unique_id
        self.pos = pos
        self.neighbors = set()
        self.is_entrance = False
        self.delete_test = False
        self.dist = 0
        self.done = False
        self.last_node = None

    def __repr__(self) -> str:
        return f"Vertex(unique_id={self.unique_id}, pos={self.pos}, is_entrance={self.is_entrance})"


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
        return f"BuildingCentroid(unique_id={self.unique_id}, pos={self.pos}, function={self.function}," \
               f"entrance={self.entrance})"
