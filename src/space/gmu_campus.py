from typing import Dict, List, Tuple, Optional, DefaultDict
import random

import numpy as np
from mesa.agent import Agent
from mesa.space import SingleGrid, Coordinate, FloatCoordinate
from sklearn.neighbors import KDTree
from mesa_geo.geospace import GeoSpace

from src.space.utils import get_rounded_coordinate
from src.agent.gmu_building import GmuBuilding


class GmuCampus(GeoSpace):
    homes: Tuple[GmuBuilding]
    works: Tuple[GmuBuilding]
    other_buildings: Tuple[GmuBuilding]
    home_counter: DefaultDict[Coordinate, int]

    def __init__(self, crs: str) -> None:
        super().__init__(crs=crs)
        self.homes = tuple()
        self.works = tuple()
        self.other_buildings = tuple()

    def get_random_home(self) -> GmuBuilding:
        return random.choice(self.homes)

    def get_random_work(self) -> GmuBuilding:
        return random.choice(self.works)

    def add_agents(self, agents) -> None:
        super().add_agents(agents)
        homes, works, other_buildings = [], [], []
        for agent in agents:
            if isinstance(agent, GmuBuilding):
                if agent.function == 0.0:
                    other_buildings.append(agent)
                elif agent.function == 1.0:
                    works.append(agent)
                elif agent.function == 2.0:
                    homes.append(agent)
        self.other_buildings = self.other_buildings + tuple(other_buildings)
        self.works = self.works + tuple(works)
        self.homes = self.homes + tuple(homes)

    def update_home_counter(self, old_home_pos: Optional[Coordinate], new_home_pos: Coordinate) -> None:
        # TODO: implement
        raise NotImplementedError

        if old_home_pos is not None:
            self.home_counter[old_home_pos] -= 1
        self.home_counter[new_home_pos] += 1
