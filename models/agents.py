from __future__ import annotations
from typing import Tuple, Set

from mesa import Agent, Model


class Vertex(Agent):
    unique_id: int
    model: Model
    pos: Tuple[float, float]
    neighbors: Set[Vertex]  # agent set of neighboring vertices
    is_entrance: bool  # if it is an entrance to a building
    delete_test: bool  # used to delete in test
    # the following variables are used and renewed in each path-selection
    dist: int  # distance from original point to here
    done: bool  # 1 if has calculated the shortest path through this point, 0 otherwise
    last_node: Vertex  # last node to this point in shortest path

    def __init__(self, unique_id: int, model: Model, pos: Tuple[float, float]) -> None:
        super().__init__(unique_id, model)
        self.pos = pos

    def step(self) -> None:
        pass

    def advance(self) -> None:
        pass


class BuildingCentroid(Agent):
    """
    Equivalent to a NetLogo patch with centroid? = True.
    Implemented as an Agent due to the lack of patches-owned properties in Mesa.
    """
    unique_id: int  # an ID that represents the building
    model: Model
    pos: Tuple[int, int]
    entrance: Vertex  # nearest vertex on road
    function: int  # 1 for work, 2 for home, 0 for neither

    def __init__(self, unique_id: int, model: Model, pos: Tuple[int, int]) -> None:
        super().__init__(unique_id, model)
        self.pos = pos

    def step(self) -> None:
        pass

    def advance(self) -> None:
        pass


class Commuter(Agent):
    unique_id: int  # commuter_id, used to link commuters and nodes
    model: Model
    my_node: Vertex  # where he begins his trip
    destination: Vertex  # the destination he wants to arrive at
    destination_entrance: Vertex  # the entrance of the destination on the road
    my_path: Set[Vertex]  # a set containing nodes to visit in the shortest path
    step_in_path: int  # the number of step taking in the walk
    last_stop: Vertex  # last destination
    my_home: BuildingCentroid  # home location
    my_work: BuildingCentroid  # work location
    start_time_h: int  # time to start going to work, hour and minute
    start_time_m: int
    end_time_h: int  # time to leave work, hour and minute
    end_time_m: int
    home_friends: Set[Commuter]  # set of friends at home
    work_friends: Set[Commuter]  # set of friends at work
    num_friends: int  # number of friends
    status: str  # work, home, or transport
    testing: bool  # a temp variable used in identifying friends
    happiness_home: int
    happiness_work: int

    def __init__(self, unique_id: int, model: Model) -> None:
        super().__init__(unique_id, model)

    def step(self) -> None:
        pass

    def advance(self) -> None:
        pass
