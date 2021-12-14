from __future__ import annotations
from typing import Set

from mesa import Agent, Model
from mesa.space import Coordinate

from src.models.space import Vertex, BuildingCentroid


class Commuter(Agent):
    unique_id: int  # commuter_id, used to link commuters and nodes
    model: Model
    pos: Coordinate
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
        raise NotImplementedError
