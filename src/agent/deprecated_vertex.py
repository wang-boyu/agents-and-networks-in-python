from __future__ import annotations

from mesa import Agent, Model
from mesa.space import Coordinate, FloatCoordinate

from src.space.utils import get_rounded_coordinate


class Vertex(Agent):
    unique_id: int
    model: Model
    float_pos: FloatCoordinate
    pos: Coordinate
    is_entrance: bool  # if it is an entrance to a building
    delete_test: bool  # used to delete in test
    # the following variables are used and renewed in each path-selection
    dist: int  # distance from original point to here
    done: bool  # 1 if has calculated the shortest path through this point, 0 otherwise
    last_node: Vertex  # last node to this point in shortest path

    def __init__(self, unique_id: int, model: Model, float_pos: FloatCoordinate) -> None:
        super().__init__(unique_id, model)
        self.float_pos = float_pos
        self.pos = get_rounded_coordinate(float_pos)
        self.is_entrance = False
        self.delete_test = False
        self.dist = 0
        self.done = False
        self.last_node = None

    def __repr__(self) -> str:
        return f"Vertex(unique_id={self.unique_id}, float_pos={self.float_pos}, is_entrance={self.is_entrance}, " \
               f"dist={self.dist}, done={self.done})"

    def __eq__(self, other):
        if isinstance(other, Vertex):
            return self.unique_id == other.unique_id
        return False

    def step(self) -> None:
        pass

    def advance(self) -> None:
        raise NotImplementedError
