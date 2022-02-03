import random
from collections import defaultdict
from typing import Dict, Tuple, Optional, DefaultDict, Set

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
    __commuters_pos_map: DefaultDict[FloatCoordinate, Set[Commuter]]
    __commuter_id_map: Dict[int, Commuter]

    def __init__(self, crs: str) -> None:
        super().__init__(crs=crs)
        self.homes = tuple()
        self.works = tuple()
        self.other_buildings = tuple()
        self.home_counter = defaultdict(int)
        self.__buildings = dict()
        self.__commuters_pos_map = defaultdict(set)
        self.__commuter_id_map = dict()

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

    def get_commuters_by_pos(self, float_pos: FloatCoordinate) -> Set[Commuter]:
        return self.__commuters_pos_map[float_pos]

    def get_commuter_by_id(self, commuter_id: int) -> Commuter:
        return self.__commuter_id_map[commuter_id]

    def add_commuter(self, agent: Commuter) -> None:
        super().add_agents(agent)
        self.__commuters_pos_map[(agent.shape.x, agent.shape.y)].add(agent)
        self.__commuter_id_map[agent.unique_id] = agent

    def update_home_counter(self, old_home_pos: Optional[FloatCoordinate], new_home_pos: FloatCoordinate) -> None:
        if old_home_pos is not None:
            self.home_counter[old_home_pos] -= 1
        self.home_counter[new_home_pos] += 1

    def move_commuter(self, commuter: Commuter, pos: FloatCoordinate) -> None:
        self.__remove_commuter(commuter)
        commuter.shape = Point(pos)
        self.add_commuter(commuter)

    def __remove_commuter(self, commuter: Commuter) -> None:
        super().remove_agent(commuter)
        # delete_agent() not working properly. Reference: https://github.com/Corvince/mesa-geo/issues/28
        del self.idx.agents[id(commuter)]
        del self.__commuter_id_map[commuter.unique_id]
        self.__commuters_pos_map[(commuter.shape.x, commuter.shape.y)].remove(commuter)
