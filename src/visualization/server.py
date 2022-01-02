from mesa_geo.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import ChartModule, TextElement
from mesa.visualization.UserParam import UserSettableParameter
from mesa_geo.visualization.MapModule import MapModule

from src.model.gmu_social import GmuSocial
from src.agent.gmu_building import GmuBuilding
from src.agent.road_vertex import RoadVertex

# class HappyElement(TextElement):
#     def __init__(self):
#         pass
#
#     def render(self, model):
#         return "Happy agents: " + str(model.happy)


model_params = {
    "gmu_buildings_file": "data/raw/campus/Mason_bld.shp",
    "gmu_walkway_file": "data/raw/campus/Mason_walkway_line.shp",
    "world_file": "data/raw/campus/world.shp",
    "show_walkway": True
    # "density": UserSettableParameter("slider", "Agent density", 0.6, 0.1, 1.0, 0.1),
    # "minority_pc": UserSettableParameter(
    #     "slider", "Fraction minority", 0.2, 0.00, 1.0, 0.05
    # ),
}


def gmu_social_draw(agent):
    portrayal = dict()
    if isinstance(agent, GmuBuilding):
        if agent.function is None:
            portrayal["color"] = "Grey"
        elif agent.function == 1.0:
            portrayal["color"] = "Blue"
        elif agent.function == 2.0:
            portrayal["color"] = "Green"
        else:
            portrayal["color"] = "Grey"
    if isinstance(agent, RoadVertex):
        portrayal["radius"] = "1"
        portrayal["color"] = "Red"
    return portrayal


map_element = MapModule(gmu_social_draw, GmuSocial.MAP_COORDS, zoom=16, map_height=500, map_width=500)
server = ModularServer(
    GmuSocial, [map_element], "GMU-Social", model_params
)
server.launch()
