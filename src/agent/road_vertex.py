from mesa import Model
from mesa_geo import GeoAgent
from shapely.geometry import Point


class RoadVertex(GeoAgent):
    unique_id: int
    model: Model
    shape: Point
    is_entrance: bool  # if it is an entrance to a building
    delete_test: bool  # used to delete in test
    # the following variables are used and renewed in each path-selection
    dist: int  # distance from original point to here
    done: bool  # 1 if has calculated the shortest path through this point, 0 otherwise
    last_node_id: int  # last node to this point in shortest path

    def __init__(self, unique_id, model, shape) -> None:
        super().__init__(unique_id, model, shape)
        self.is_entrance = False
        self.delete_test = False
        self.dist = 0
        self.done = False
        self.last_node_id = None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(unique_id={self.unique_id}, shape={self.shape}, " \
               f"is_entrance={self.is_entrance}, dist={self.dist}, done={self.done})"

    def __eq__(self, other):
        if isinstance(other, RoadVertex):
            return self.unique_id == other.unique_id
        return False

    def step(self) -> None:
        pass

    def advance(self) -> None:
        raise NotImplementedError
