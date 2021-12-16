from typing import Tuple, DefaultDict, Optional
import random
from collections import defaultdict

from mesa.space import MultiGrid, Coordinate

from src.space.building_centroid import BuildingCentroid


class CommuterGrid(MultiGrid):
    homes: Tuple[BuildingCentroid]
    works: Tuple[BuildingCentroid]
    other_buildings: Tuple[BuildingCentroid]
    home_counter: DefaultDict[Coordinate, int]

    def __init__(self, width: int, height: int, torus: bool) -> None:
        super().__init__(width, height, torus)
        self.home_counter = defaultdict(int)

    def get_random_home(self) -> BuildingCentroid:
        return random.choice(self.homes)

    def get_random_work(self) -> BuildingCentroid:
        return random.choice(self.works)

    def update_home_counter(self, old_home_pos: Optional[Coordinate], new_home_pos: Coordinate) -> None:
        if old_home_pos is not None:
            self.home_counter[old_home_pos] -= 1
        self.home_counter[new_home_pos] += 1
