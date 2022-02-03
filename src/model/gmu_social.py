import uuid
from functools import partial
import random

import geopandas as gpd
import numpy as np
import pandas as pd
from mesa import Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from mesa_geo.geoagent import GeoAgent, AgentCreator
from mesa_geo import GeoSpace
from shapely.geometry import Point

from src.agent.gmu_building import GmuBuilding
from src.agent.road_vertex import RoadVertex
from src.space.vertex_space import VertexSpace
from src.space.gmu_campus import GmuCampus
from src.agent.commuter import Commuter
from src.logger import logger


class GmuSocial(Model):
    running: bool
    schedule: RandomActivation
    current_id: int
    grid: GmuCampus
    vertex_grid: VertexSpace
    world_size: gpd.geodataframe.GeoDataFrame
    MAP_COORDS = [38.830417362141866, -77.3073675720387]
    got_to_destination: int  # count the total number of arrivals
    num_commuters: int
    day: int
    hour: int
    minute: int

    def __init__(self, gmu_buildings_file: str, gmu_walkway_file: str, world_file: str,
                 num_commuters, commuter_min_friends=5, commuter_max_friends=10, commuter_happiness_increase=0.5,
                 commuter_happiness_decrease=0.5, speed=500.0, chance_new_friend=5.0,
                 crs="epsg:3857", show_walkway=False) -> None:
        super().__init__()
        self.schedule = RandomActivation(self)
        self.show_walkway = show_walkway
        self.grid = GmuCampus(crs=crs)
        self.vertex_grid = VertexSpace(crs=crs)
        self.world = gpd.read_file(world_file).set_index("Id").set_crs("epsg:2283", allow_override=True).to_crs(crs)
        self.num_commuters = num_commuters

        Commuter.MIN_FRIENDS = commuter_min_friends
        Commuter.MAX_FRIENDS = commuter_max_friends
        Commuter.HAPPINESS_INCREASE = commuter_happiness_increase
        Commuter.HAPPINESS_DECREASE = commuter_happiness_decrease
        Commuter.SPEED = speed
        Commuter.CHANCE_NEW_FRIEND = chance_new_friend

        self.__load_buildings_from_file(gmu_buildings_file, crs=crs)
        self.__load_road_vertices_from_file(gmu_walkway_file, crs=crs)
        self.__set_building_entrance()
        self.got_to_destination = 0
        self.__create_commuters()
        self.day = 0
        self.hour = 5
        self.minute = 55

    def __create_commuters(self) -> None:
        for _ in range(self.num_commuters):
            random_home = self.grid.get_random_home()
            random_work = self.grid.get_random_work()
            commuter = Commuter(unique_id=uuid.uuid4().int, model=self, shape=Point(random_home.centroid))
            commuter.my_home_id = random_home.unique_id
            commuter.my_home_pos = random_home.centroid
            commuter.my_work_id = random_work.unique_id
            commuter.my_work_pos = random_work.centroid
            commuter.status = "home"
            self.grid.add_commuter(commuter)
            self.grid.update_home_counter(old_home_pos=None, new_home_pos=commuter.my_home_pos)
            self.schedule.add(commuter)

    def __load_buildings_from_file(self, gmu_buildings_file: str, crs: str) -> None:
        buildings_df = gpd.read_file(gmu_buildings_file).fillna(0.0).rename(columns={"NAME": "name"})
        buildings_df = buildings_df.set_index("Id").set_crs("epsg:2283", allow_override=True).to_crs(crs)
        buildings_df["centroid"] = [(x, y) for x, y in zip(buildings_df.centroid.x, buildings_df.centroid.y)]
        building_creator = AgentCreator(GmuBuilding, {"model": self}, crs=crs)
        buildings = building_creator.from_GeoDataFrame(buildings_df)
        self.grid.add_buildings(buildings)

    def __load_road_vertices_from_file(self, gmu_walkway_file: str, crs: str) -> None:
        walkway_df = gpd.read_file(gmu_walkway_file).set_index("Id").set_crs("epsg:2283",
                                                                             allow_override=True).to_crs(crs)
        vertex_set = set()
        for _, row in walkway_df.iterrows():
            for point in row["geometry"].coords:
                vertex_set.add(point)
        vertex_dict = {uuid.uuid4().int: Point(vertex) for vertex in vertex_set}
        vertex_df = gpd.GeoDataFrame.from_dict(vertex_dict,
                                               orient="index").rename(columns={0: "geometry"}).set_crs(crs)
        vertex_creator = AgentCreator(RoadVertex, {"model": self}, crs=crs)
        vertices = vertex_creator.from_GeoDataFrame(vertex_df)
        self.vertex_grid.add_agents(vertices)
        self.vertex_grid.delete_not_connected()
        if self.show_walkway:
            self.grid.add_agents(self.vertex_grid.agents)

    def __set_building_entrance(self) -> None:
        for building in (*self.grid.homes, *self.grid.works, *self.grid.other_buildings):
            nearest_vertex = self.vertex_grid.get_nearest_vertex(building.centroid)
            nearest_vertex.is_entrance = True
            building.entrance_pos = nearest_vertex.shape.x, nearest_vertex.shape.y
            building.entrance_id = nearest_vertex.unique_id

    def step(self) -> None:
        # self.datacollector.collect(self)
        self.__update_clock()
        self.schedule.step()

    def __update_clock(self) -> None:
        self.minute += 5
        if self.minute == 60:
            if self.hour == 23:
                self.hour = 0
                self.day += 1
            else:
                self.hour += 1
            self.minute = 0
