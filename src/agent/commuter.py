from __future__ import annotations
from typing import Set

import numpy as np
from mesa import Agent, Model
from mesa.space import Coordinate

from src.agent.vertex import Vertex
from src.space.building_centroid import BuildingCentroid


class Commuter(Agent):
    unique_id: int  # commuter_id, used to link commuters and nodes
    model: Model
    pos: Coordinate
    my_node: Vertex  # where he begins his trip
    destination: BuildingCentroid  # the destination he wants to arrive at
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
    num_home_friends: int  # number of friends at home
    num_work_friends: int  # number of friends at work
    status: str  # work, home, or transport
    testing: bool  # a temp variable used in identifying friends
    happiness_home: int
    happiness_work: int

    def __init__(self, unique_id: int, model: Model) -> None:
        super().__init__(unique_id, model)
        self.destination = None
        self.last_stop = None
        self.start_time_h = np.random.normal(6.5, 1)
        while self.start_time_h < 6 or self.start_time_h > 9:
            self.start_time_h = np.random.normal(6.5, 1)
        self.start_time_m = np.random.randint(0, 12) * 5
        self.end_time_h = self.start_time_h + 8  # will work for 8 hours
        self.end_time_m = self.start_time_m
        self.happiness_work = 100
        self.happiness_home = 100
        self.num_home_friends = 0
        self.num_work_friends = 0

    def __repr__(self) -> str:
        return f"Commuter(unique_id={self.unique_id}, pos={self.pos}, status={self.status}, " \
               f"num_home_friends={self.num_home_friends}, num_work_friends={self.num_work_friends})"

    def step(self) -> None:
        pass

    def advance(self) -> None:
        raise NotImplementedError
