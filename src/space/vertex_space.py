from typing import Dict, List, Tuple, Optional

import numpy as np
from mesa.agent import Agent
from mesa.space import SingleGrid, Coordinate, FloatCoordinate
from sklearn.neighbors import KDTree
from mesa_geo.geospace import GeoSpace

from src.space.utils import get_rounded_coordinate


class VertexSpace(GeoSpace):
    __tree: KDTree
    __path_select_cache: Dict[Tuple[int, int], List[FloatCoordinate]]

    def __init__(self, crs: str) -> None:
        super().__init__(crs=crs)
        self.__path_select_cache = dict()

    def update_agent(self, new_agent: Agent, pos: Coordinate):

        raise NotImplementedError

        if not self.is_cell_empty(pos):
            self.remove_agent(self[pos])
        self.place_agent(new_agent, pos)

    def get_nearest_vertex(self, float_pos: FloatCoordinate) -> Agent:
        vertex_index = self.__tree.query([float_pos], k=1, return_distance=False)
        vertex_pos = self.__tree.get_arrays()[0][vertex_index[0, 0]]
        return self[get_rounded_coordinate(vertex_pos)]

    def delete_not_connected(self) -> None:
        not_connected_agents = []
        for agent in self.agents:
            if len(list(self.get_neighbors_within_distance(agent, distance=10.0))) < 2:
                not_connected_agents.append(agent)
        for agent in not_connected_agents:
            self.remove_agent(agent)
            # delete_agent() not working properly. Reference: https://github.com/Corvince/mesa-geo/issues/28
            del self.idx.agents[id(agent)]
        self.__build_kd_tree()

    def __build_kd_tree(self) -> None:
        vertices_pos = [agent.shape.coords[0] for agent in self.agents]
        self.__tree = KDTree(vertices_pos)

    def cache_path(self, from_vertex_id: int, to_vertex_id: int, path: List[FloatCoordinate]) -> None:
        self.__path_select_cache[(from_vertex_id, to_vertex_id)] = path
        self.__path_select_cache[(to_vertex_id, from_vertex_id)] = list(reversed(path))

    def get_cached_path(self, from_vertex_id: int, to_vertex_id: int) -> Optional[List[FloatCoordinate]]:
        return self.__path_select_cache.get((from_vertex_id, to_vertex_id), None)
