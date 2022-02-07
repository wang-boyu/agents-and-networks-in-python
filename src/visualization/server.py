import logging

from mesa.visualization.modules import ChartModule, TextElement
from mesa.visualization.UserParam import UserSettableParameter
from mesa_geo.visualization.MapModule import MapModule
from mesa_geo.visualization.ModularVisualization import ModularServer

from src.agent.commuter import Commuter
from src.agent.gmu_building import GmuBuilding
from src.agent.geo_agents import GmuDriveway, GmuLakeAndRiver, GmuWalkway
from src.model.gmu_social import GmuSocial


class ClockElement(TextElement):
    def __init__(self):
        super().__init__()
        pass

    def render(self, model):
        return f"Day {model.day}, {model.hour:02d}:{model.minute:02d}"


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
    "num_commuters": UserSettableParameter('slider',
                                           'Number of Commuters', value=50, min_value=10, max_value=150, step=10)
}


def gmu_social_draw(agent):
    portrayal = dict()
    portrayal["color"] = "White"
    if isinstance(agent, GmuDriveway):
        portrayal["color"] = "#D08004"
    elif isinstance(agent, GmuWalkway):
        portrayal["color"] = "Brown"
    elif isinstance(agent, GmuLakeAndRiver):
        portrayal["color"] = "#04D0CD"
    elif isinstance(agent, GmuBuilding):
        portrayal["color"] = "Grey"
        # if agent.function is None:
        #     portrayal["color"] = "Grey"
        # elif agent.function == 1.0:
        #     portrayal["color"] = "Blue"
        # elif agent.function == 2.0:
        #     portrayal["color"] = "Green"
        # else:
        #     portrayal["color"] = "Grey"
    elif isinstance(agent, Commuter):
        if agent.status == "home":
            portrayal["color"] = "Green"
        elif agent.status == "work":
            portrayal["color"] = "Blue"
        elif agent.status == "transport":
            portrayal["color"] = "Red"
        else:
            portrayal["color"] = "Grey"
        portrayal["radius"] = "3"
        portrayal["fillOpacity"] = 1
    return portrayal


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s',
                    level=logging.INFO)
log = logging.getLogger(__name__)
log.info('Entered module: %s' % __name__)
map_element = MapModule(gmu_social_draw, GmuSocial.MAP_COORDS, zoom=16, map_height=500, map_width=500)
clock_element = ClockElement()
status_chart = ChartModule([{"Label": "status_home", "Color": "Green"},
                            {"Label": "status_work", "Color": "Blue"},
                            {"Label": "status_traveling", "Color": "Red"}],
                           data_collector_name='datacollector')
friendship_chart = ChartModule([{"Label": "friendship_home", "Color": "Green"},
                                {"Label": "friendship_work", "Color": "Blue"}],
                               data_collector_name='datacollector')
server = ModularServer(
    GmuSocial, [map_element, clock_element, status_chart, friendship_chart], "GMU-Social", model_params
)
server.launch()
