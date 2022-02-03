from typing import Dict, List, Tuple, Optional

import numpy as np
from mesa.agent import Agent
from mesa.space import SingleGrid, Coordinate, FloatCoordinate
from sklearn.neighbors import KDTree

from src.space.utils import get_rounded_coordinate
from src.logger import logger


class VertexGrid(SingleGrid):
    __tree: KDTree
    __path_select_cache: Dict[Tuple[int, int], List[FloatCoordinate]]

    def __init__(self, width: int, height: int, torus: bool) -> None:
        super().__init__(width, height, torus)
        self.__path_select_cache = dict()

    def update_agent(self, new_agent: Agent, pos: Coordinate):
        if not self.is_cell_empty(pos):
            self.remove_agent(self[pos])
        self.place_agent(new_agent, pos)

    def get_nearest_vertex(self, pos: Coordinate) -> Agent:
        vertex_index = self.__tree.query([pos], k=1, return_distance=False)
        vertex_pos = self.__tree.get_arrays()[0][vertex_index[0, 0]]
        return self[get_rounded_coordinate(vertex_pos)]

    def delete_not_connected(self) -> None:
        for row in self.grid:
            for agent in row:
                if agent is not None and not self.get_neighbors(agent.pos, moore=True):
                    self.remove_agent(agent)
        self.__build_kd_tree()

    def __build_kd_tree(self) -> None:
        vertices_pos = [agent.float_pos for row in self.grid for agent in row if agent is not None]
        self.__tree = KDTree(vertices_pos)

    def get_distance(self, pos_1: FloatCoordinate, pos_2: FloatCoordinate) -> float:
        x1, y1 = pos_1
        x2, y2 = pos_2
        dx = np.abs(x1 - x2)
        dy = np.abs(y1 - y2)
        if self.torus:
            dx = min(dx, self.width - dx)
            dy = min(dy, self.height - dy)
        return np.sqrt(dx * dx + dy * dy)

    def cache_path(self, from_vertex_id: int, to_vertex_id: int, path: List[FloatCoordinate]) -> None:
        self.__path_select_cache[(from_vertex_id, to_vertex_id)] = path
        self.__path_select_cache[(to_vertex_id, from_vertex_id)] = list(reversed(path))

    def get_cached_path(self, from_vertex_id: int, to_vertex_id: int) -> Optional[List[FloatCoordinate]]:
        return self.__path_select_cache.get((from_vertex_id, to_vertex_id), None)
