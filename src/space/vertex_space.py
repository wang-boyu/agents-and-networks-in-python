from typing import Dict, List, Tuple, Optional

import numpy as np
from mesa.space import FloatCoordinate
from mesa_geo.geoagent import GeoAgent
from mesa_geo.geospace import GeoSpace
from sklearn.neighbors import KDTree

from src.agent.road_vertex import RoadVertex


class VertexSpace(GeoSpace):
    __tree: KDTree
    __path_select_cache: Dict[Tuple[int, int], List[FloatCoordinate]]
    __vertices_pos_map: Dict[Tuple[float, float], RoadVertex]
    __vertices_id_map: Dict[int, RoadVertex]

    def __init__(self, crs: str) -> None:
        super().__init__(crs=crs)
        self.__path_select_cache = dict()
        self.__vertices_pos_map = dict()
        self.__vertices_id_map = dict()

    def add_agents(self, agents: List[RoadVertex]) -> None:
        super().add_agents(agents)
        for agent in agents:
            self.__vertices_pos_map[(agent.shape.x, agent.shape.y)] = agent
            self.__vertices_id_map[agent.unique_id] = agent

    def get_vertex_by_pos(self, float_pos: FloatCoordinate) -> RoadVertex:
        return self.__vertices_pos_map[float_pos]

    def get_vertex_by_id(self, vertex_id: int) -> RoadVertex:
        return self.__vertices_id_map[vertex_id]

    def get_distance(self, pos_1: FloatCoordinate, pos_2: FloatCoordinate) -> float:
        x1, y1 = pos_1
        x2, y2 = pos_2
        dx = np.abs(x1 - x2)
        dy = np.abs(y1 - y2)
        return np.sqrt(dx * dx + dy * dy)

    def get_nearest_vertex(self, float_pos: FloatCoordinate) -> RoadVertex:
        vertex_index = self.__tree.query([float_pos], k=1, return_distance=False)
        vertex_pos = self.__tree.get_arrays()[0][vertex_index[0, 0]]
        return self.__vertices_pos_map[tuple(vertex_pos)]

    def __remove_agent(self, agent: GeoAgent) -> None:
        super().remove_agent(agent)
        # delete_agent() not working properly. Reference: https://github.com/Corvince/mesa-geo/issues/28
        del self.idx.agents[id(agent)]
        del self.__vertices_pos_map[(agent.shape.x, agent.shape.y)]
        del self.__vertices_id_map[agent.unique_id]

    def delete_not_connected(self) -> None:
        not_connected_agents = []
        for agent in self.agents:
            if len(list(self.get_neighbors_within_distance(agent, distance=100.0))) < 2:
                not_connected_agents.append(agent)
        for agent in not_connected_agents:
            self.__remove_agent(agent)
        self.__build_kd_tree()

    def __build_kd_tree(self) -> None:
        vertices_pos = [agent.shape.coords[0] for agent in self.agents]
        self.__tree = KDTree(vertices_pos)

    def cache_path(self, from_vertex_id: int, to_vertex_id: int, path: List[FloatCoordinate]) -> None:
        self.__path_select_cache[(from_vertex_id, to_vertex_id)] = path
        self.__path_select_cache[(to_vertex_id, from_vertex_id)] = list(reversed(path))

    def get_cached_path(self, from_vertex_id: int, to_vertex_id: int) -> Optional[List[FloatCoordinate]]:
        return self.__path_select_cache.get((from_vertex_id, to_vertex_id), None)
