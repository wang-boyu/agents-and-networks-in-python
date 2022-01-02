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


class GmuSocial(Model):
    running: bool
    current_id: int
    grid: GmuCampus
    vertex_grid: VertexSpace
    world_size: gpd.geodataframe.GeoDataFrame
    MAP_COORDS = [38.830417362141866, -77.3073675720387]

    def __init__(self, gmu_buildings_file: str, gmu_walkway_file: str, world_file: str,
                 crs="epsg:3857", show_walkway=False) -> None:
        super().__init__()
        self.show_walkway = show_walkway
        self.grid = GmuCampus(crs=crs)
        self.vertex_grid = VertexSpace(crs=crs)
        self.__load_buildings_from_file(gmu_buildings_file, crs=crs)
        self.__load_road_vertices_from_file(gmu_walkway_file, crs=crs)
        self.__set_building_entrance()
        self.world = gpd.read_file(world_file).set_index("Id").set_crs("epsg:2283", allow_override=True).to_crs(crs)

    def __load_buildings_from_file(self, gmu_buildings_file: str, crs: str) -> None:
        buildings_df = gpd.read_file(gmu_buildings_file).fillna(0.0).rename(columns={"NAME": "name"})
        buildings_df = buildings_df.set_index("Id").set_crs("epsg:2283", allow_override=True).to_crs(crs)
        buildings_df["centroid"] = [(x, y) for x, y in zip(buildings_df.centroid.x, buildings_df.centroid.y)]
        building_creator = AgentCreator(GmuBuilding, {"model": self}, crs=crs)
        buildings = building_creator.from_GeoDataFrame(buildings_df)
        self.grid.add_agents(buildings)

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
        # TODO
        pass
