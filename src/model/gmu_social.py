import uuid
from typing import Dict
from functools import partial

import geopandas as gpd
import numpy as np
import pandas as pd
from mesa import Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

from src.agent.vertex import Vertex
from src.agent.commuter import Commuter
from src.space.vertex_grid import VertexGrid
from src.space.commuter_grid import CommuterGrid
from src.space.building_centroid import BuildingCentroid
from src.space.utils import get_coord_matrix, get_affine_transform, get_rounded_coordinate


def get_time(model) -> pd.Timedelta:
    return pd.Timedelta(days=model.day, hours=model.hour, minutes=model.minute)


def get_num_commuters_by_status(model, status: str) -> int:
    commuters = [commuter for commuter in model.schedule.agents if commuter.status == status]
    return len(commuters)


def get_total_friendships_by_type(model, friendship_type: str) -> int:
    if friendship_type == "home":
        num_friendships = [commuter.num_home_friends for commuter in model.schedule.agents]
    elif friendship_type == "work":
        num_friendships = [commuter.num_work_friends for commuter in model.schedule.agents]
    else:
        raise ValueError(f"Unsupported friendship type: {friendship_type}. Must be home or work.")
    return sum(num_friendships)


class GmuSocial(Model):
    running: bool
    schedule: RandomActivation
    current_id: int
    gmu_buildings: gpd.geodataframe.GeoDataFrame
    gmu_walkway: gpd.geodataframe.GeoDataFrame
    world_size: gpd.geodataframe.GeoDataFrame
    grid_width: int
    grid_height: int
    vertex_grid: VertexGrid
    commuter_grid: CommuterGrid
    got_to_destination: int  # count the total number of arrivals
    num_commuters: int
    day: int
    hour: int
    minute: int
    datacollector: DataCollector

    def __init__(self, gmu_buildings_file: str, gmu_walkway_file: str, world_size_file: str,
                 grid_width: int = 80, grid_height: int = 40,
                 num_commuters: int = 109, commuter_min_friends: int = 5, commuter_max_friends: int = 10,
                 commuter_happiness_increase: float = 0.5, commuter_happiness_decrease: float = 0.5,
                 speed: float = 5.0, chance_new_friend: float = 5.0) -> None:
        super().__init__()
        self.schedule = RandomActivation(self)
        self.gmu_buildings = gpd.read_file(gmu_buildings_file).set_index("Id")
        self.gmu_walkway = gpd.read_file(gmu_walkway_file).set_index("Id")
        self.world_size = gpd.read_file(world_size_file).set_index("Id")
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.num_commuters = num_commuters

        Commuter.MIN_FRIENDS = commuter_min_friends
        Commuter.MAX_FRIENDS = commuter_max_friends
        Commuter.HAPPINESS_INCREASE = commuter_happiness_increase
        Commuter.HAPPINESS_DECREASE = commuter_happiness_decrease
        Commuter.SPEED = speed
        Commuter.CHANCE_NEW_FRIEND = chance_new_friend

        self.vertex_grid = VertexGrid(width=grid_width, height=grid_height, torus=False)
        self.commuter_grid = CommuterGrid(width=grid_width, height=grid_height, torus=False)

        self.__setup()
        self.datacollector = DataCollector(model_reporters={
            "time": get_time,
            "status_home": partial(get_num_commuters_by_status, status="home"),
            "status_work": partial(get_num_commuters_by_status, status="work"),
            "status_traveling": partial(get_num_commuters_by_status, status="transport"),
            "friendship_home": partial(get_total_friendships_by_type, friendship_type="home"),
            "friendship_work": partial(get_total_friendships_by_type, friendship_type="work")
        })

    def __setup(self) -> None:
        self.gmu_buildings["centroid"] = self.gmu_buildings["geometry"].centroid
        # following the netlogo model, fill na with 0.0
        self.gmu_buildings["function"].fillna(0.0, inplace=True)
        self.__affine_transform()
        self.__create_building_centroids()
        self.__create_vertices()
        self.__set_building_entrance()
        self.got_to_destination = 0
        self.__create_commuters()
        self.day = 0
        self.hour = 6
        self.minute = 0

    # TODO: move to CommuterGrid and VertexGrid classes
    def __affine_transform(self) -> None:
        world_envelope_df = pd.DataFrame([(x, y) for x, y in zip(*self.world_size.envelope[0].exterior.coords.xy)],
                                         columns=["x", "y"])
        assert len(world_envelope_df) == 5
        # first and last points are the same in the envelope polygon
        np.testing.assert_array_equal(world_envelope_df.iloc[0].values, world_envelope_df.iloc[-1].values)
        # remove last point which is redundant
        world_envelope_df = world_envelope_df[:-1]

        world_envelope_coord = get_coord_matrix(x_min=world_envelope_df["x"].min(),
                                                x_max=world_envelope_df["x"].max(),
                                                y_min=world_envelope_df["y"].min(),
                                                y_max=world_envelope_df["y"].max())
        netlogo_world_coord = get_coord_matrix(x_min=0, x_max=self.grid_width - 1, y_min=0, y_max=self.grid_height - 1)
        affine_transform = get_affine_transform(from_coord=world_envelope_coord, to_coord=netlogo_world_coord)
        self.gmu_buildings["centroid_transformed"] = self.gmu_buildings["centroid"].affine_transform(affine_transform)
        self.gmu_walkway["geometry_transformed"] = self.gmu_walkway["geometry"].affine_transform(affine_transform)

    # TODO: move to CommuterGrid class
    def __create_building_centroids(self) -> None:
        homes, works, other_buildings = [], [], []
        for index, row in self.gmu_buildings.iterrows():
            transformed_coordinate = row["centroid_transformed"].x, row["centroid_transformed"].y
            centroid = BuildingCentroid(unique_id=index,
                                        function=int(row["function"]),
                                        pos=get_rounded_coordinate(transformed_coordinate))
            if centroid.function == 0:
                other_buildings.append(centroid)
            elif centroid.function == 1:
                works.append(centroid)
            elif centroid.function == 2:
                homes.append(centroid)
        self.commuter_grid.other_buildings = tuple(other_buildings)
        self.commuter_grid.works = tuple(works)
        self.commuter_grid.homes = tuple(homes)

    # TODO: move to VertexGrid class
    def __create_vertices(self) -> None:
        for _, row in self.gmu_walkway.iterrows():
            for point in row["geometry_transformed"].coords:
                rounded_point = get_rounded_coordinate(point)
                if self.vertex_grid.is_cell_empty(rounded_point):
                    vertex = Vertex(unique_id=uuid.uuid4().int, model=self, float_pos=point)
                    self.vertex_grid.place_agent(vertex, rounded_point)
        self.vertex_grid.delete_not_connected()

    def __set_building_entrance(self) -> None:
        for building in (*self.commuter_grid.homes, *self.commuter_grid.works, *self.commuter_grid.other_buildings):
            nearest_vertex = self.vertex_grid.get_nearest_vertex(building.pos)
            nearest_vertex.is_entrance = True
            self.vertex_grid.update_agent(nearest_vertex, nearest_vertex.pos)
            building.entrance = nearest_vertex

    def __create_commuters(self) -> None:
        for _ in range(self.num_commuters):
            commuter = Commuter(unique_id=uuid.uuid4().int, model=self)
            commuter.my_home = self.commuter_grid.get_random_home()
            commuter.my_work = self.commuter_grid.get_random_work()
            commuter.status = "home"
            self.commuter_grid.place_agent(commuter, commuter.my_home.pos)
            self.commuter_grid.update_home_counter(old_home_pos=None, new_home_pos=commuter.my_home.pos)
            self.schedule.add(commuter)

    def step(self) -> None:
        self.datacollector.collect(self)
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
