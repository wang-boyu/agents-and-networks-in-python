from __future__ import annotations

import logging
import random
from typing import List

import numpy as np
from mesa import Model
from mesa.space import FloatCoordinate
from mesa_geo.geoagent import GeoAgent
from shapely.geometry import Point

from src.logger import logger


class Commuter(GeoAgent):
    unique_id: int  # commuter_id, used to link commuters and nodes
    model: Model
    shape: Point
    my_node_entrance_id: int  # where he begins his trip
    my_node_pos: FloatCoordinate
    my_node_id: int
    my_node_name: str
    destination_id: int  # the destination he wants to arrive at
    destination_pos: FloatCoordinate
    destination_name: str
    destination_entrance_id: int
    destination_entrance_pos: FloatCoordinate
    my_path: List[FloatCoordinate]  # a set containing nodes to visit in the shortest path
    step_in_path: int  # the number of step taking in the walk
    # last_stop: RoadVertex  # last destination
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
        # self.last_stop = None
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
            self.my_node_entrance_id = self.model.grid.get_building_by_id(self.my_home_id).entrance_id
            self.my_node_pos = self.model.grid.get_building_by_id(self.my_home_id).entrance_pos
            self.my_node_id = self.model.grid.get_building_by_id(self.my_home_id).unique_id
            self.my_node_name = self.model.grid.get_building_by_id(self.my_home_id).name
            self.model.grid.move_commuter(self, pos=self.my_node_pos)
            self.destination_id = self.my_work_id
            self.destination_pos = self.my_work_pos
            self.destination_name = self.my_work_name
            self.destination_entrance_id = self.model.grid.get_building_by_id(self.destination_id).entrance_id
            self.destination_entrance_pos = self.model.grid.get_building_by_id(self.destination_id).entrance_pos
            self.__path_select()
            self.status = "transport"
        # start going home
        elif self.status == "work" and self.model.hour == self.end_time_h and self.model.minute == self.end_time_m:
            self.my_node_entrance_id = self.model.grid.get_building_by_id(self.my_work_id).entrance_id
            self.my_node_pos = self.model.grid.get_building_by_id(self.my_work_id).entrance_pos
            self.my_node_id = self.model.grid.get_building_by_id(self.my_work_id).unique_id
            self.my_node_name = self.model.grid.get_building_by_id(self.my_work_id).name
            self.model.grid.move_commuter(self, pos=self.my_node_pos)
            self.destination_id = self.my_home_id
            self.destination_pos = self.my_home_pos
            self.destination_name = self.my_home_name
            self.destination_entrance_id = self.model.grid.get_building_by_id(self.destination_id).entrance_id
            self.destination_entrance_pos = self.model.grid.get_building_by_id(self.destination_id).entrance_pos
            self.__path_select()
            self.status = "transport"

    def __move(self) -> None:
        if self.status == "transport":
            if self.model.vertex_grid.get_distance((self.shape.x, self.shape.y), self.destination_entrance_pos) > 5:
                next_position = self.my_path[self.step_in_path]
                dist_1 = self.model.vertex_grid.get_distance((self.shape.x, self.shape.y), next_position)
                remain = self.SPEED
                while remain >= dist_1 and self.step_in_path < len(self.my_path):
                    self.model.grid.move_commuter(self, next_position)
                    self.step_in_path += 1
                    remain -= dist_1
                    if self.step_in_path < len(self.my_path):
                        next_position = self.my_path[self.step_in_path]
                    else:
                        remain = 0.0
                        self.model.grid.move_commuter(self, self.destination_entrance_pos)
                        if self.destination_id == self.my_work_id:
                            self.status = "work"
                        elif self.destination_id == self.my_home_id:
                            self.status = "home"
                        self.model.got_to_destination += 1
                    dist_1 = self.model.vertex_grid.get_distance((self.shape.x, self.shape.y), next_position)
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
        old_home_pos = self.my_home_pos
        while True:
            new_home = self.model.grid.get_random_home()
            if new_home.unique_id != old_home_id:
                break
        self.my_home_id = new_home.unique_id
        self.my_home_pos = new_home.centroid
        self.my_node_name = new_home.name
        self.happiness_home = 100.0
        self.model.grid.update_home_counter(old_home_pos=old_home_pos, new_home_pos=self.my_home_pos)

    def __relocate_work(self) -> None:
        old_work_id = self.my_work_id
        while True:
            new_work = self.model.grid.get_random_work()
            if new_work.unique_id != old_work_id:
                break
        self.my_work_id = new_work.unique_id
        self.my_work_pos = new_work.centroid
        self.my_work_name = new_work.name
        self.work_friends_id = []
        self.happiness_work = 100.0

    def __path_select(self) -> None:
        self.step_in_path = 0
        if (cached_path := self.model.vertex_grid.get_cached_path(from_building=self.my_node_name,
                                                                  to_building=self.destination_name)) \
                is not None:
            print(f"cache hit.")
            self.my_path = cached_path
        else:
            print(f"cache miss.")
            self.my_path = []
            undone_vertices_id = set()
            for vertex in self.model.vertex_grid.agents:
                if vertex is not None:
                    vertex.dist = 99999
                    vertex.done = 0
                    vertex.last_node_id = None
                    undone_vertices_id.add(vertex.unique_id)
            self.model.vertex_grid.get_vertex_by_id(self.my_node_entrance_id).dist = 0

            # previous_num_undone_vertices = 0
            while undone_vertices_id:
                # num_undone_vertices = len(undone_vertices_id)
                # if num_undone_vertices == previous_num_undone_vertices:
                #     breakpoint()
                # previous_num_undone_vertices = num_undone_vertices
                for vertex in self.model.vertex_grid.agents:
                    if vertex is not None and vertex.dist < 99999 and vertex.done == 0:
                        neighbors = self.model.vertex_grid.get_neighbors_within_distance(vertex, distance=self.SPEED)
                        num_neighbors = len(list(neighbors))
                        # print(f"number of neighbors found: {num_neighbors}")
                        for neighbor in self.model.vertex_grid.get_neighbors_within_distance(vertex,
                                                                                             distance=self.SPEED):
                            if vertex != neighbor:
                                distance = self.model.vertex_grid.distance(vertex, neighbor)
                                dist_0 = distance + vertex.dist
                                if neighbor.dist > dist_0:
                                    neighbor.dist = dist_0
                                    neighbor.done = 0
                                    neighbor.last_node_id = vertex.unique_id
                                    undone_vertices_id.add(neighbor.unique_id)
                        vertex.done = 1
                        undone_vertices_id.remove(vertex.unique_id)
            x = self.destination_entrance_id

            while x != self.my_node_entrance_id:
                x_node = self.model.vertex_grid.get_vertex_by_id(x)
                self.my_path.append((x_node.shape.x, x_node.shape.y))
                x = x_node.last_node_id
            self.my_path.reverse()
            self.model.vertex_grid.cache_path(from_building=self.my_node_name, to_building=self.destination_name,
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
