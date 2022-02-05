import logging

from mesa_geo.visualization.MapModule import MapModule
from mesa_geo.visualization.ModularVisualization import ModularServer

from src.agent.commuter import Commuter
from src.agent.gmu_building import GmuBuilding
from src.agent.geo_agents import GmuDriveway, GmuLakeAndRiver, GmuWalkway
from src.model.gmu_social import GmuSocial

model_params = {
    "gmu_buildings_file": "data/raw/campus/Mason_bld.shp",
    "gmu_walkway_file": "data/raw/campus/Mason_walkway_line.shp",
    "world_file": "data/raw/campus/world.shp",
    "gmu_lakes_file": "data/raw/campus/hydrop.shp",
    "gmu_rivers_file": "data/raw/campus/hydrol.shp",
    "gmu_driveway_file": "data/raw/campus/Mason_Rds.shp",
    "show_walkway": True,
    "show_lakes_and_rivers": True,
    "show_driveway": True,
    "num_commuters": 109
    # "density": UserSettableParameter("slider", "Agent density", 0.6, 0.1, 1.0, 0.1),
    # "minority_pc": UserSettableParameter(
    #     "slider", "Fraction minority", 0.2, 0.00, 1.0, 0.05
    # ),
}


def gmu_social_draw(agent):
    portrayal = dict()
    portrayal["color"] = "White"
    if isinstance(agent, GmuDriveway):
        portrayal["color"] = "Brown"
    if isinstance(agent, GmuWalkway):
        portrayal["color"] = "Brown"
    if isinstance(agent, GmuLakeAndRiver):
        portrayal["color"] = "Blue"
    if isinstance(agent, GmuBuilding):
        if agent.function is None:
            portrayal["color"] = "Grey"
        elif agent.function == 1.0:
            portrayal["color"] = "Blue"
        elif agent.function == 2.0:
            portrayal["color"] = "Green"
        else:
            portrayal["color"] = "Grey"
    # if isinstance(agent, RoadVertex):
    #     portrayal["radius"] = "2"
    #     portrayal["fillOpacity"] = 0.5
    #     if agent.is_entrance:
    #         portrayal["color"] = "Purple"
    #     else:
    #         portrayal["color"] = "Yellow"
    if isinstance(agent, Commuter):
        portrayal["radius"] = "3"
        portrayal["fillOpacity"] = 1
        if agent.status == "home":
            portrayal["Color"] = "Green"
        elif agent.status == "work":
            portrayal["Color"] = "Blue"
        elif agent.status == "transport":
            portrayal["Color"] = "Red"
        else:
            portrayal["Color"] = "White"
    return portrayal


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s',
                    level=logging.INFO)
log = logging.getLogger(__name__)
log.info('Entered module: %s' % __name__)
map_element = MapModule(gmu_social_draw, GmuSocial.MAP_COORDS, zoom=16, map_height=500, map_width=500)
server = ModularServer(
    GmuSocial, [map_element], "GMU-Social", model_params
)
server.launch()
