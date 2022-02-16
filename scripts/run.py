import argparse

from mesa.visualization.UserParam import UserSettableParameter
from mesa_geo.visualization.MapModule import MapModule
from mesa_geo.visualization.ModularVisualization import ModularServer

from src.model.model import AgentsAndNetworks
from src.visualization.server import agent_draw, clock_element, status_chart, friendship_chart


def make_parser():
    parser = argparse.ArgumentParser("Agents and Networks in Python")
    parser.add_argument("--campus", type=str, required=True)
    return parser


if __name__ == "__main__":
    args = make_parser().parse_args()

    if args.campus == "ub":
        data_file_prefix = "UB"
    elif args.campus == "gmu":
        data_file_prefix = "Mason"
    else:
        raise ValueError("Invalid campus name. Choose from ub or gmu.")

    map_coord = {
        "ub": [43.0022471679366, -78.785149],
        "gmu": [38.830417362141866, -77.3073675720387]
    }
    model_params = {
        "campus": args.campus,
        "buildings_file": f"data/raw/{args.campus}/{data_file_prefix}_bld.shp",
        "walkway_file": f"data/raw/{args.campus}/{data_file_prefix}_walkway_line.shp",
        "lakes_file": f"data/raw/{args.campus}/hydrop.shp",
        "rivers_file": f"data/raw/{args.campus}/hydrol.shp",
        "driveway_file": f"data/raw/{args.campus}/{data_file_prefix}_Rds.shp",
        "show_walkway": True,
        "show_lakes_and_rivers": True,
        "show_driveway": True,
        "num_commuters": UserSettableParameter('slider',
                                               'Number of Commuters', value=50, min_value=10, max_value=150, step=10)
    }
    map_element = MapModule(agent_draw, map_coord[args.campus], zoom=16, map_height=500, map_width=500)
    server = ModularServer(
        AgentsAndNetworks, [map_element, clock_element, status_chart, friendship_chart], "Agents-and-Networks",
        model_params
    )
    server.launch()
