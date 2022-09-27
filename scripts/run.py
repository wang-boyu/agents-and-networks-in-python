import argparse
import time
from tqdm.auto import tqdm
import mesa
from mesa_geo.visualization.ModularVisualization import ModularServer
from mesa_geo.visualization.modules import MapModule

from src.model.model import AgentsAndNetworks
from src.visualization.server import (
    agent_draw,
    clock_element,
    status_chart,
    friendship_chart,
)

def make_parser():
    parser = argparse.ArgumentParser("Agents and Networks in Python")
    parser.add_argument("--campus", type=str, required=True)
    parser.add_argument("--text", action="store_true")
    parser.add_argument("--steps", type=int, default=10)            
    parser.add_argument("--commuters", type=int, default=1000)
    parser.add_argument("--commuter_speed", type=float, default=0.9)
    return parser


if __name__ == "__main__":
    args = make_parser().parse_args()

    if args.campus == "ub":
        data_file_prefix = "UB"
    elif args.campus == "gmu":
        data_file_prefix = "Mason"
    else:
        raise ValueError("Invalid campus name. Choose from ub or gmu.")

    campus_params = {
        "ub": {"data_crs": "epsg:4326", "commuter_speed": 0.5},
        "gmu": {"data_crs": "epsg:2283", "commuter_speed": 0.4},
    }

    model_params = {
        "campus": args.campus,
        "data_crs": campus_params[args.campus]["data_crs"],
        "buildings_file": f"data/raw/{args.campus}/{data_file_prefix}_bld.shp",
        "walkway_file": f"data/raw/{args.campus}/{data_file_prefix}_walkway_line.shp",
        "lakes_file": f"data/raw/{args.campus}/hydrop.shp",
        "rivers_file": f"data/raw/{args.campus}/hydrol.shp",
        "driveway_file": f"data/raw/{args.campus}/{data_file_prefix}_Rds.shp",
        "show_walkway": True,
        "show_lakes_and_rivers": True,
        "show_driveway": True
    }
    map_params = {
        "ub": {"view": [43.0022471679366, -78.785149], "zoom": 14.8},
        "gmu": {"view": [38.830417362141866, -77.3073675720387], "zoom": 16},
    }
    map_element = MapModule(
        agent_draw, **map_params[args.campus], map_height=600, map_width=600
    )

    if not args.text:
      model_params.update(
          {
            "num_commuters": mesa.visualization.Slider(
                "Number of Commuters", value=100, min_value=10, max_value=1500, step=50
            ),
            "commuter_speed": mesa.visualization.Slider(
                "Commuter Walking Speed (m/s)",
                value=campus_params[args.campus]["commuter_speed"],
                min_value=0.1,
                max_value=1.5,
                step=0.1,
            )
            })
      server = ModularServer(
          AgentsAndNetworks,
          [map_element, clock_element, status_chart, friendship_chart],
          "Agents and Networks",
          model_params,
      )
      server.launch()
    else:    
      model_params.update(
          {
            "num_commuters": args.commuters,
            "commuter_speed": args.commuter_speed
          }
      )
      model = AgentsAndNetworks(**model_params)
 
      print(model_params)

      tic = time.time()
      for i in (pbar := tqdm(range(args.steps))):
        model.step()
        pbar.set_description("Simulation time: day %d %d:%d "%(model.day, model.hour, model.minute))

      toc = time.time()
      print(model.datacollector.get_model_vars_dataframe())

      print("Simulation took %.3f seconds"%(toc-tic))
    
    
