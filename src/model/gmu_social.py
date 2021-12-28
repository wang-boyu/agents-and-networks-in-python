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
import shapely

from src.agent.gmu_building import GmuBuilding


class GmuSocial(Model):
    running: bool
    current_id: int
    gmu_walkway: gpd.geodataframe.GeoDataFrame
    world_size: gpd.geodataframe.GeoDataFrame
    grid: GeoSpace
    MAP_COORDS = [38.830417362141866, -77.3073675720387]

    def __init__(self, gmu_buildings_file: str, gmu_walkway_file: str, world_size_file: str) -> None:
        super().__init__()
        self.grid = GeoSpace()
        self.__load_buildings_from_file(gmu_buildings_file)
        self.gmu_walkway = gpd.read_file(gmu_walkway_file).set_index("Id").set_crs("epsg:2283", allow_override=True)
        self.world_size = gpd.read_file(world_size_file).set_index("Id").set_crs("epsg:2283", allow_override=True)

    def __load_buildings_from_file(self, gmu_buildings_file: str) -> None:
        buildings_df = gpd.read_file(gmu_buildings_file).fillna(0.0).rename(columns={"NAME": "name"})
        buildings_df = buildings_df.set_index("Id").set_crs("epsg:2283", allow_override=True)
        buildings_df["centroid"] = [(x, y) for x, y in zip(buildings_df.centroid.x, buildings_df.centroid.y)]
        agent_creator = AgentCreator(GmuBuilding, {"model": self})
        buildings = agent_creator.from_GeoDataFrame(buildings_df)
        self.grid.add_agents(buildings)
