from __future__ import annotations

import random
from typing import List, Set

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
    my_path: List[Vertex]  # a set containing nodes to visit in the shortest path
    step_in_path: int  # the number of step taking in the walk
    last_stop: Vertex  # last destination
    my_home: BuildingCentroid  # home location
    my_work: BuildingCentroid  # work location
    start_time_h: int  # time to start going to work, hour and minute
    start_time_m: int
    end_time_h: int  # time to leave work, hour and minute
    end_time_m: int
    work_friends: Set[Commuter]  # set of friends at work
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

    def __init__(self, unique_id: int, model: Model) -> None:
        super().__init__(unique_id, model)
        self.destination = None
        self.last_stop = None
        self.start_time_h = round(np.random.normal(6.5, 1))
        while self.start_time_h < 6 or self.start_time_h > 9:
            self.start_time_h = round(np.random.normal(6.5, 1))
        self.start_time_m = np.random.randint(0, 12) * 5
        self.end_time_h = self.start_time_h + 8  # will work for 8 hours
        self.end_time_m = self.start_time_m
        self.happiness_work = 100.0
        self.happiness_home = 100.0
        self.work_friends = set()
        self.testing = False

    def __repr__(self) -> str:
        return f"Commuter(unique_id={self.unique_id}, pos={self.pos}, status={self.status}, " \
               f"num_home_friends={self.num_home_friends}, num_work_friends={len(self.work_friends)})"

    @property
    def num_home_friends(self) -> int:
        return self.model.commuter_grid.home_counter[self.my_home.pos]

    @property
    def num_work_friends(self) -> int:
        return len(self.work_friends)

    def step(self) -> None:
        self.__check_happiness()
        self.__prepare_to_move()
        self.__move()
        self.__make_friends_at_work()

    def __check_happiness(self) -> None:
        if self.status == "work":
            if len(self.work_friends) > self.MAX_FRIENDS:
                self.happiness_work -= self.HAPPINESS_DECREASE * (len(self.work_friends) - self.MAX_FRIENDS)
            else:
                if len(self.work_friends) < self.MIN_FRIENDS:
                    self.happiness_work -= self.HAPPINESS_DECREASE * (self.MIN_FRIENDS - len(self.work_friends))
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
        if self.status == "transport":
            if self.model.vertex_grid.get_distance(self.pos, self.destination_entrance.float_pos) > 0.5:
                next_node = self.my_path[self.step_in_path]
                dist_1 = self.model.vertex_grid.get_distance(self.pos, next_node.float_pos)
                remain = self.SPEED
                while remain > dist_1 and self.step_in_path < len(self.my_path):
                    self.model.commuter_grid.place_agent(self, next_node.pos)
                    self.step_in_path += 1
                    remain -= dist_1
                    if self.step_in_path < len(self.my_path):
                        next_node = self.my_path[self.step_in_path]
                    else:
                        remain = 0.0
                        self.model.commuter_grid.place_agent(self, self.destination_entrance.pos)
                        if self.destination == self.my_work:
                            self.status = "work"
                        elif self.destination == self.my_home:
                            self.status = "home"
                        self.model.got_to_destination += 1
                    dist_1 = self.model.vertex_grid.get_distance(self.pos, next_node.float_pos)
            else:
                self.model.commuter_grid.place_agent(self, self.destination_entrance.pos)
                if self.destination == self.my_work:
                    self.status = "work"
                elif self.destination == self.my_home:
                    self.status = "home"
                self.model.got_to_destination += 1

    def advance(self) -> None:
        raise NotImplementedError

    def __relocate_home(self) -> None:
        old_home = self.my_home
        while (new_home := self.model.commuter_grid.get_random_home()) == old_home:
            continue
        self.my_home = new_home
        self.happiness_home = 100.0
        self.model.commuter_grid.update_home_counter(old_home_pos=old_home.pos, new_home_pos=self.my_home.pos)

    def __relocate_work(self) -> None:
        old_work = self.my_work
        while (new_work := self.model.commuter_grid.get_random_work()) == old_work:
            continue
        self.my_work = new_work
        self.work_friends = set()
        self.happiness_work = 100.0

    def __path_select(self) -> None:
        # TODO: cache each path select result in self.model.vertex_grid
        self.my_path = []
        self.step_in_path = 0
        undone_vertices_id = set()
        for vertex in self.model.vertex_grid:
            if vertex is not None:
                vertex.dist = 99999
                vertex.done = 0
                vertex.last_node = None
                undone_vertices_id.add(vertex.unique_id)
        self.my_node.dist = 0

        while undone_vertices_id:
            for vertex in self.model.vertex_grid:
                if vertex is not None and vertex.dist < 99999 and vertex.done == 0:
                    for neighbor in self.model.vertex_grid.get_neighbors(vertex.pos, moore=True, radius=3):
                        distance = self.model.vertex_grid.get_distance(vertex.float_pos, neighbor.float_pos)
                        dist_0 = distance + vertex.dist
                        if neighbor.dist > dist_0:
                            neighbor.dist = dist_0
                            neighbor.done = 0
                            neighbor.last_node = vertex
                            undone_vertices_id.add(neighbor.unique_id)
                    vertex.done = 1
                    undone_vertices_id.remove(vertex.unique_id)
        x = self.destination_entrance
        while x != self.my_node:
            self.my_path.append(x)
            x = x.last_node
        self.my_path.reverse()

    def __make_friends_at_work(self) -> None:
        if self.status == "work":
            for work_friend in self.work_friends:
                work_friend.testing = True
            commuters_to_check = [commuter for commuter in self.model.commuter_grid[self.pos] if not commuter.testing]
            if commuters_to_check and np.random.uniform(0.0, 100.0) < self.CHANCE_NEW_FRIEND:
                target_friend = random.choice(commuters_to_check)
                target_friend.work_friends.add(self)
                self.work_friends.add(target_friend)
            for work_friend in self.work_friends:
                work_friend.testing = False
