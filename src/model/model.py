import uuid
from functools import partial

import pandas as pd
import geopandas as gpd
from mesa import Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from mesa_geo.geoagent import AgentCreator
from shapely.geometry import Point

from src.agent.commuter import Commuter
from src.agent.geo_agents import Driveway, LakeAndRiver, Walkway
from src.agent.building import Building
from src.agent.road_vertex import RoadVertex
from src.space.campus import Campus
from src.space.vertex_space import VertexSpace


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


class AgentsAndNetworks(Model):
    running: bool
    schedule: RandomActivation
    show_walkway: bool
    show_lakes_and_rivers: bool
    current_id: int
    grid: Campus
    vertex_grid: VertexSpace
    world_size: gpd.geodataframe.GeoDataFrame
    got_to_destination: int  # count the total number of arrivals
    num_commuters: int
    day: int
    hour: int
    minute: int
    datacollector: DataCollector

    def __init__(self, campus: str, data_crs: str, buildings_file: str, walkway_file: str, lakes_file: str,
                 rivers_file: str, driveway_file: str, num_commuters, commuter_min_friends=5, commuter_max_friends=10,
                 commuter_happiness_increase=0.5, commuter_happiness_decrease=0.5, commuter_speed=200.0,
                 chance_new_friend=5.0, model_crs="epsg:3857", show_walkway=False, show_lakes_and_rivers=False,
                 show_driveway=False) \
            -> None:
        super().__init__()
        self.schedule = RandomActivation(self)
        self.show_walkway = show_walkway
        self.show_lakes_and_rivers = show_lakes_and_rivers
        self.data_crs = data_crs
        self.grid = Campus(crs=model_crs)
        self.vertex_grid = VertexSpace(crs=model_crs, campus=campus)
        self.num_commuters = num_commuters

        Commuter.MIN_FRIENDS = commuter_min_friends
        Commuter.MAX_FRIENDS = commuter_max_friends
        Commuter.HAPPINESS_INCREASE = commuter_happiness_increase
        Commuter.HAPPINESS_DECREASE = commuter_happiness_decrease
        Commuter.SPEED = commuter_speed
        Commuter.CHANCE_NEW_FRIEND = chance_new_friend

        self.__load_buildings_from_file(buildings_file, crs=model_crs, campus=campus)
        self.__load_road_vertices_from_file(walkway_file, crs=model_crs)
        self.__set_building_entrance()
        self.got_to_destination = 0
        self.__create_commuters()
        self.day = 0
        self.hour = 5
        self.minute = 55

        if show_driveway:
            self.__load_driveway_from_file(driveway_file, crs=model_crs)
        if show_lakes_and_rivers:
            self.__load_lakes_and_rivers_from_file(lakes_file, crs=model_crs)
            self.__load_lakes_and_rivers_from_file(rivers_file, crs=model_crs)

        self.datacollector = DataCollector(model_reporters={
            "time": get_time,
            "status_home": partial(get_num_commuters_by_status, status="home"),
            "status_work": partial(get_num_commuters_by_status, status="work"),
            "status_traveling": partial(get_num_commuters_by_status, status="transport"),
            "friendship_home": partial(get_total_friendships_by_type, friendship_type="home"),
            "friendship_work": partial(get_total_friendships_by_type, friendship_type="work")
        })

    def __create_commuters(self) -> None:
        for _ in range(self.num_commuters):
            random_home = self.grid.get_random_home()
            random_work = self.grid.get_random_work()
            commuter = Commuter(unique_id=uuid.uuid4().int, model=self, shape=Point(random_home.centroid))
            commuter.set_home(random_home)
            commuter.set_work(random_work)
            commuter.status = "home"
            self.grid.add_commuter(commuter)
            self.schedule.add(commuter)

    def __load_buildings_from_file(self, buildings_file: str, crs: str, campus: str) -> None:
        assert campus in ("ub", "gmu")

        buildings_df = gpd.read_file(buildings_file)
        if campus == "gmu":
            buildings_df.fillna(0.0, inplace=True)
            buildings_df.rename(columns={"NAME": "name"}, inplace=True)
        buildings_df.drop("Id", axis=1, inplace=True)
        buildings_df.index.name = "unique_id"
        buildings_df = buildings_df.set_crs(self.data_crs, allow_override=True).to_crs(crs)
        buildings_df["centroid"] = [(x, y) for x, y in zip(buildings_df.centroid.x, buildings_df.centroid.y)]
        building_creator = AgentCreator(Building, {"model": self}, crs=crs)
        buildings = building_creator.from_GeoDataFrame(buildings_df)
        self.grid.add_buildings(buildings)

    def __load_road_vertices_from_file(self, walkway_file: str, crs: str) -> None:
        walkway_df = gpd.read_file(walkway_file).set_index("Id").set_crs(self.data_crs,
                                                                         allow_override=True).to_crs(crs)
        if self.show_walkway:
            walkway_creator = AgentCreator(Walkway, {"model": self}, crs=crs)
            walkway = walkway_creator.from_GeoDataFrame(walkway_df)
            self.grid.add_agents(walkway)

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

    def __load_driveway_from_file(self, driveway_file: str, crs: str) -> None:
        driveway_df = gpd.read_file(driveway_file).set_index("Id").set_crs(self.data_crs,
                                                                           allow_override=True).to_crs(crs)
        driveway_creator = AgentCreator(Driveway, {"model": self}, crs=crs)
        driveway = driveway_creator.from_GeoDataFrame(driveway_df)
        self.grid.add_agents(driveway)

    def __load_lakes_and_rivers_from_file(self, lake_river_file: str, crs: str) -> None:
        lake_river_df = gpd.read_file(lake_river_file).set_crs(self.data_crs, allow_override=True).to_crs(crs)
        lake_river_df.index.names = ["Id"]
        lake_river_creator = AgentCreator(LakeAndRiver, {"model": self}, crs=crs)
        gmu_lake_river = lake_river_creator.from_GeoDataFrame(lake_river_df)
        self.grid.add_agents(gmu_lake_river)

    def __set_building_entrance(self) -> None:
        for building in (*self.grid.homes, *self.grid.works, *self.grid.other_buildings):
            nearest_vertex = self.vertex_grid.get_nearest_vertex(building.centroid)
            nearest_vertex.is_entrance = True
            building.entrance_pos = nearest_vertex.shape.x, nearest_vertex.shape.y
            building.entrance_id = nearest_vertex.unique_id

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
