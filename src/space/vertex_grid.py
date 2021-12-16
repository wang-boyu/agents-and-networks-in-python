from mesa.agent import Agent
from mesa.space import SingleGrid, Coordinate
from sklearn.neighbors import KDTree

from src.space.utils import get_rounded_coordinate


class VertexGrid(SingleGrid):
    tree: KDTree

    def __init__(self, width: int, height: int, torus: bool) -> None:
        super().__init__(width, height, torus)

    def update_agent(self, new_agent: Agent, pos: Coordinate):
        if not self.is_cell_empty(pos):
            self.remove_agent(self[pos])
        self.place_agent(new_agent, pos)

    def get_nearest_vertex(self, pos: Coordinate) -> Agent:
        vertex_index = self.tree.query([pos], k=1, return_distance=False)
        vertex_pos = self.tree.get_arrays()[0][vertex_index[0, 0]]
        return self[get_rounded_coordinate(vertex_pos)]

    def delete_not_connected(self) -> None:
        for row in self.grid:
            for agent in row:
                if agent is not None and not self.get_neighbors(agent.pos, moore=True):
                    self.remove_agent(agent)
        self.__build_kd_tree()

    def __build_kd_tree(self) -> None:
        vertices_pos = [agent.float_pos for row in self.grid for agent in row if agent is not None]
        self.tree = KDTree(vertices_pos)
