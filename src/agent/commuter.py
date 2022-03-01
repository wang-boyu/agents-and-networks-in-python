from __future__ import annotations

import random
from typing import List

import numpy as np
from mesa import Model
from mesa.space import FloatCoordinate
from mesa_geo.geoagent import GeoAgent
from shapely.geometry import Point

from src.agent.building import Building


class Commuter(GeoAgent):
    unique_id: int  # commuter_id, used to link commuters and nodes
    model: Model
    shape: Point
    origin_id: int  # where he begins his trip
    origin_pos: FloatCoordinate
    origin_name: str
    origin_entrance_pos: FloatCoordinate
    destination_id: int  # the destination he wants to arrive at
    destination_pos: FloatCoordinate
    destination_name: str
    destination_entrance_pos: FloatCoordinate
    my_path: List[FloatCoordinate]  # a set containing nodes to visit in the shortest path
    step_in_path: int  # the number of step taking in the walk
    my_home_id: int
    my_home_pos: FloatCoordinate  # home location
    my_home_name: str
    my_work_id: int
    my_work_pos: FloatCoordinate  # work location
    my_work_name: str
    start_time_h: int  # time to start going to work, hour and minute
    start_time_m: int
    end_time_h: int  # time to leave work, hour and minute
    end_time_m: int
    work_friends_id: List[int]  # set of friends at work
    status: str  # work, home, or transport
    testing: bool  # a temp variable used in identifying friends
    happiness_home: float
    happiness_work: float
    MIN_FRIENDS: int
    MAX_FRIENDS: int
    HAPPINESS_INCREASE: float
    HAPPINESS_DECREASE: float
    SPEED: float
    CHANCE_NEW_FRIEND: float  # percent chance to make a new friend every 5 min

    def __init__(self, unique_id, model, shape) -> None:
        super().__init__(unique_id, model, shape)
        self.my_home_pos = None
        self.start_time_h = round(np.random.normal(6.5, 1))
        while self.start_time_h < 6 or self.start_time_h > 9:
            self.start_time_h = round(np.random.normal(6.5, 1))
        self.start_time_m = np.random.randint(0, 12) * 5
        self.end_time_h = self.start_time_h + 8  # will work for 8 hours
        self.end_time_m = self.start_time_m
        self.happiness_work = 100.0
        self.happiness_home = 100.0
        self.work_friends_id = []
        self.testing = False

    def __repr__(self) -> str:
        return f"Commuter(unique_id={self.unique_id}, shape={self.shape}, status={self.status}, " \
               f"num_home_friends={self.num_home_friends}, num_work_friends={len(self.work_friends_id)})"

    @property
    def num_home_friends(self) -> int:
        return self.model.grid.home_counter[self.my_home_pos]

    @property
    def num_work_friends(self) -> int:
        return len(self.work_friends_id)

    def set_home(self, new_home: Building) -> None:
        old_home_pos = self.my_home_pos
        self.my_home_id = new_home.unique_id
        self.my_home_pos = new_home.centroid
        self.my_home_name = new_home.name
        self.happiness_home = 100.0
        self.model.grid.update_home_counter(old_home_pos=old_home_pos, new_home_pos=self.my_home_pos)

    def set_work(self, new_work: Building) -> None:
        self.my_work_id = new_work.unique_id
        self.my_work_pos = new_work.centroid
        self.my_work_name = new_work.name
        self.work_friends_id = []
        self.happiness_work = 100.0

    def step(self) -> None:
        self.__check_happiness()
        self.__prepare_to_move()
        self.__move()
        self.__make_friends_at_work()

    def __check_happiness(self) -> None:
        if self.status == "work":
            if len(self.work_friends_id) > self.MAX_FRIENDS:
                self.happiness_work -= self.HAPPINESS_DECREASE * (len(self.work_friends_id) - self.MAX_FRIENDS)
            else:
                if len(self.work_friends_id) < self.MIN_FRIENDS:
                    self.happiness_work -= self.HAPPINESS_DECREASE * (self.MIN_FRIENDS - len(self.work_friends_id))
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
            self.__set_origin(self.model.grid.get_building_by_id(self.my_home_id))
            self.model.grid.move_commuter(self, pos=self.origin_pos)
            self.__set_destination(self.model.grid.get_building_by_id(self.my_work_id))
            self.__path_select()
            self.status = "transport"
        # start going home
        elif self.status == "work" and self.model.hour == self.end_time_h and self.model.minute == self.end_time_m:
            self.__set_origin(self.model.grid.get_building_by_id(self.my_work_id))
            self.model.grid.move_commuter(self, pos=self.origin_pos)
            self.__set_destination(self.model.grid.get_building_by_id(self.my_home_id))
            self.__path_select()
            self.status = "transport"

    def __set_origin(self, origin: Building) -> None:
        self.origin_id = origin.unique_id
        self.origin_pos = origin.centroid
        self.origin_name = origin.name
        self.origin_entrance_pos = origin.entrance_pos

    def __set_destination(self, destination: Building) -> None:
        self.destination_id = destination.unique_id
        self.destination_pos = destination.centroid
        self.destination_name = destination.name
        self.destination_entrance_pos = destination.entrance_pos

    def __move(self) -> None:
        if self.status == "transport":
            if self.step_in_path < len(self.my_path):
                next_position = self.my_path[self.step_in_path]
                self.model.grid.move_commuter(self, next_position)
                self.step_in_path += 1
            else:
                self.model.grid.move_commuter(self, self.destination_entrance_pos)
                if self.destination_id == self.my_work_id:
                    self.status = "work"
                elif self.destination_id == self.my_home_id:
                    self.status = "home"
                self.model.got_to_destination += 1

    def advance(self) -> None:
        raise NotImplementedError

    def __relocate_home(self) -> None:
        old_home_id = self.my_home_id
        while True:
            new_home = self.model.grid.get_random_home()
            if new_home.unique_id != old_home_id:
                break
        self.set_home(new_home)

    def __relocate_work(self) -> None:
        old_work_id = self.my_work_id
        while True:
            new_work = self.model.grid.get_random_work()
            if new_work.unique_id != old_work_id:
                break
        self.set_work(new_work)

    def __path_select(self) -> None:
        self.step_in_path = 0
        if (cached_path := self.model.walkway.get_cached_path(source=self.origin_entrance_pos,
                                                              target=self.destination_entrance_pos)) \
                is not None:
            self.my_path = cached_path
        else:
            self.my_path = self.model.walkway.get_shortest_path(source=self.origin_entrance_pos,
                                                                target=self.destination_entrance_pos)
            self.model.walkway.cache_path(source=self.origin_entrance_pos,
                                          target=self.destination_entrance_pos,
                                          path=self.my_path)

    def __make_friends_at_work(self) -> None:
        if self.status == "work":
            for work_friend_id in self.work_friends_id:
                self.model.grid.get_commuter_by_id(work_friend_id).testing = True
            commuters_to_check = [c for c in self.model.grid.get_commuters_by_pos((self.shape.x, self.shape.y))
                                  if not c.testing]
            if commuters_to_check and np.random.uniform(0.0, 100.0) < self.CHANCE_NEW_FRIEND:
                target_friend = random.choice(commuters_to_check)
                target_friend.work_friends_id.append(self.unique_id)
                self.work_friends_id.append(target_friend.unique_id)
            for work_friend_id in self.work_friends_id:
                self.model.grid.get_commuter_by_id(work_friend_id).testing = False
