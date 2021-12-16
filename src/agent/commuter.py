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
    num_work_friends: int  # number of friends at work
    status: str  # work, home, or transport
    testing: bool  # a temp variable used in identifying friends
    happiness_home: float
    happiness_work: float
    MIN_FRIENDS: int
    MAX_FRIENDS: int
    HAPPINESS_INCREASE: float
    HAPPINESS_DECREASE: float

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
        self.happiness_work = 100.0
        self.happiness_home = 100.0
        self.num_work_friends = 0

    def __repr__(self) -> str:
        return f"Commuter(unique_id={self.unique_id}, pos={self.pos}, status={self.status}, " \
               f"num_home_friends={self.num_home_friends}, num_work_friends={self.num_work_friends})"

    @property
    def num_home_friends(self) -> int:
        return self.model.commuter_grid.home_counter[self.my_home.pos]

    def step(self) -> None:
        self.__check_happiness()
        self.__prepare_to_move()
        self.__move()
        self.__make_friends_at_work()

    def __check_happiness(self) -> None:
        if self.status == "work":
            if self.num_work_friends > self.MAX_FRIENDS:
                self.happiness_work -= self.HAPPINESS_DECREASE * (self.num_work_friends - self.MAX_FRIENDS)
            else:
                if self.num_work_friends < self.MIN_FRIENDS:
                    self.happiness_work -= self.HAPPINESS_DECREASE * (self.MIN_FRIENDS - self.num_work_friends)
                else:
                    self.happiness_work += self.HAPPINESS_INCREASE
            if self.happiness_work < 0.0:
                self.__relocate_work()
        elif self.status == "home":
            if self.num_home_friends > self.MAX_FRIENDS:
                self.happiness_home -= self.HAPPINESS_DECREASE * (self.num_home_friends - self.MAX_FRIENDS)
            else:
                if self.num_home_friends < self.MIN_FRIENDS:
                    self.happiness_home -= self.HAPPINESS_DECREASE * (self.MIN_FRIENDS - self.num_home_friends)
                else:
                    self.happiness_home += self.HAPPINESS_INCREASE
            if self.happiness_home < 0.0:
                self.__relocate_home()

    def __prepare_to_move(self) -> None:
        # start going to work
        if self.status == "home" and self.model.hour == self.start_time_h and self.model.minute == self.start_time_m:
            self.my_node = self.model.vertex_grid.get_nearest_vertex(self.pos)
            self.model.commuter_grid.place_agent(self, pos=self.my_node.pos)
            self.destination = self.my_work
            self.destination_entrance = self.destination.entrance
            self.__path_select()
            self.status = "transport"
        # start going home
        elif self.status == "work" and self.model.hour == self.end_time_h and self.model.minute == self.end_time_m:
            self.my_node = self.model.vertex_grid.get_nearest_vertex(self.pos)
            self.model.commuter_grid.place_agent(self, pos=self.my_node.pos)
            self.destination = self.my_home
            self.destination_entrance = self.destination.entrance
            self.__path_select()
            self.status = "transport"

    def __move(self) -> None:
        pass

    def advance(self) -> None:
        raise NotImplementedError

    def __relocate_home(self) -> None:
        old_home = self.my_home
        while (new_home := self.model.commuter_grid.get_random_home()) == old_home:
            continue
        self.my_home = new_home
        self.happiness_home = 100.0
        self.commuter_grid.update_home_counter(old_home_pos=old_home.pos, new_home_pos=self.my_home.pos)

    def __relocate_work(self) -> None:
        old_work = self.my_work
        while (new_work := self.model.commuter_grid.get_random_work()) == old_work:
            continue
        self.my_work = new_work
        self.num_work_friends = 0
        self.happiness_work = 100.0

    def __path_select(self) -> None:
        pass

    def __make_friends_at_work(self) -> None:
        pass
