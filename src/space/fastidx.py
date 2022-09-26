import os
import numpy as np
import pandas as pd
import geopandas as gpd

from shapely.geometry import Point
from mesa_geo import GeoSpace
from sklearn.neighbors import KDTree

  
class FastIdxSpace(GeoSpace):
    def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      
      self._fastagents = {}
      self._gdf_is_dirty = False  
      
      self._filter_classes = []    
      
    def add_agents(self, agents):
      toProcess = []
      for agent in agents:
        if type(agent) in self._filter_classes:
          toProcess.append(agent)

      for agent in toProcess: 
        agents.remove(agent)
        self.fast_add(agent)
      
      # For the remaining, use the normal GeoSpace methods
      if len(agents) > 0: super().add_agents(agents)

    def fast_get(self, aid):
      aid=str(aid)
      if aid in self._fastagents:
        return self._fastagents[aid]

    def fast_add(self, agent):
      if not agent.unique_id in self._fastagents: self._fastagents[agent.unique_id] = agent
      self._gdf_is_dirty = True

    def fast_remove(self, agent, pos):
      if not agent.unique_id in self._fastagents: return
      del self._fastagents[agent.unique_id]
      self._gdf_is_dirty = True

    def fast_move(self, agent, pos):
      if agent.unique_id in self._fastagents:
        agent.geometry = Point(*pos)
        self._gdf_is_dirty = True
        return True
      
      return False

######################## Fast index creation and management

    def register_class(self, class_type):
      self._filter_classes.append(class_type)

      

