import random
from collections import defaultdict
from typing import Dict, Tuple, Optional, DefaultDict

from mesa.space import FloatCoordinate
from mesa_geo.geospace import GeoSpace
from shapely.geometry import Point

from src.agent.commuter import Commuter
from src.agent.gmu_building import GmuBuilding


class GmuCampus(GeoSpace):
    homes: Tuple[GmuBuilding]
    works: Tuple[GmuBuilding]
    other_buildings: Tuple[GmuBuilding]
    home_counter: DefaultDict[FloatCoordinate, int]
    __buildings: Dict[int, GmuBuilding]

    def __init__(self, crs: str) -> None:
        super().__init__(crs=crs)
        self.homes = tuple()
        self.works = tuple()
        self.other_buildings = tuple()
        self.home_counter = defaultdict(int)
        self.__buildings = dict()

    def get_random_home(self) -> GmuBuilding:
        return random.choice(self.homes)

    def get_random_work(self) -> GmuBuilding:
        return random.choice(self.works)

    def get_building_by_id(self, unique_id: int) -> GmuBuilding:
        return self.__buildings[unique_id]

    def add_buildings(self, agents) -> None:
        super().add_agents(agents)
        homes, works, other_buildings = [], [], []
        for agent in agents:
            if isinstance(agent, GmuBuilding):
                self.__buildings[agent.unique_id] = agent
                if agent.function == 0.0:
                    other_buildings.append(agent)
                elif agent.function == 1.0:
                    works.append(agent)
                elif agent.function == 2.0:
                    homes.append(agent)
        self.other_buildings = self.other_buildings + tuple(other_buildings)
        self.works = self.works + tuple(works)
        self.homes = self.homes + tuple(homes)

    def update_home_counter(self, old_home_pos: Optional[FloatCoordinate], new_home_pos: FloatCoordinate) -> None:
        if old_home_pos is not None:
            self.home_counter[old_home_pos] -= 1
        self.home_counter[new_home_pos] += 1

    def move_commuter(self, commuter: Commuter, pos: FloatCoordinate) -> None:
        self.__remove_agent(commuter)
        commuter.shape = Point(pos)
        self.add_agents(commuter)

    def __remove_agent(self, commuter: Commuter) -> None:
        super().remove_agent(commuter)
        # delete_agent() not working properly. Reference: https://github.com/Corvince/mesa-geo/issues/28
        del self.idx.agents[id(commuter)]
