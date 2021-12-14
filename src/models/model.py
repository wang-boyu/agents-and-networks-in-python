from typing import Set, List
import uuid

import geopandas as gpd
import numpy as np
import pandas as pd
from mesa import Model
from mesa.time import RandomActivation

from src.data.utils import get_coord_matrix, get_affine_transform
from src.models.space import BuildingCentroid, Vertex


class GmuSocial(Model):
    running: bool
    schedule: RandomActivation
    current_id: int
    gmu_buildings: gpd.geodataframe.GeoDataFrame
    gmu_walkway: gpd.geodataframe.GeoDataFrame
    world_size: gpd.geodataframe.GeoDataFrame
    grid_width: int
    grid_height: int
    homes: Set[BuildingCentroid]
    works: Set[BuildingCentroid]
    other_buildings: Set[BuildingCentroid]
    vertices: List[List[Vertex]]
    got_to_destination: int  # count the total number of arrivals
    hour: int
    minute: int

    def __init__(self, gmu_buildings_file: str, gmu_walkway_file: str, world_size_file: str,
                 grid_width: int = 80, grid_height: int = 40) -> None:
        super().__init__()
        self.schedule = RandomActivation(self)
        self.gmu_buildings = gpd.read_file(gmu_buildings_file).set_index("Id")
        self.gmu_walkway = gpd.read_file(gmu_walkway_file).set_index("Id")
        self.world_size = gpd.read_file(world_size_file).set_index("Id")
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.homes = set()
        self.works = set()
        self.other_buildings = set()
        self.vertices = []

        self.__setup()

    def __setup(self) -> None:
        self.gmu_buildings["centroid"] = self.gmu_buildings["geometry"].centroid
        # following the netlogo model, fill na with 0.0
        self.gmu_buildings["function"].fillna(0.0, inplace=True)
        self.__affine_transform()
        self.__create_building_centroids()
        self.__create_vertices()

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

    def __create_building_centroids(self) -> None:
        for index, row in self.gmu_buildings.iterrows():
            centroid = BuildingCentroid(unique_id=index,
                                        function=int(row["function"]),
                                        pos=(round(row["centroid_transformed"].x),
                                             round(row["centroid_transformed"].y)))
            if centroid.function == 0:
                self.other_buildings.add(centroid)
            elif centroid.function == 1:
                self.works.add(centroid)
            elif centroid.function == 2:
                self.homes.add(centroid)

    def __create_vertices(self) -> None:
        list_of_vertex_list = []
        vertex_position_set = set()
        for _, row in self.gmu_walkway.iterrows():
            vertices = []
            for point in row["geometry_transformed"].coords:
                rounded_point = (round(point[0]), round(point[1]))
                if rounded_point not in vertex_position_set:
                    vertex_position_set.add(rounded_point)
                    vertex = Vertex(unique_id=uuid.uuid4().int, pos=point)
                    vertices.append(vertex)
            list_of_vertex_list.append(vertices)
        # TODO: delete not connected. Probably need to use grid space to find neighbours.
        self.vertices = list_of_vertex_list

    def step(self) -> None:
        pass
