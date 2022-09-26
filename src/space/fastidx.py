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
      self._clear_gdf()
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

    @property
    def is_index_dirty(self):
      return self._gdf_is_dirty

    def register_class(self, class_type):
      self._filter_classes.append(class_type)

    def _clear_gdf(self):
      df = pd.DataFrame(
        {'agentid': [],
        'geometry': []
        })

      self._agdf = gpd.GeoDataFrame(df)  

    def _create_gdf(self, use_ntrees=False):
      #self._clear_gdf()

      columns = ["agentid","geometry"]
      agent_idxs = []
      geometries = []
      for agent in self._fastagents.values():
        agent_idxs.append(agent.unique_id)
        geometries.append(agent.geometry)
            
      d = {
        'agentid': agent_idxs,
        'geometry': geometries
        }
      
      self._agdf = gpd.GeoDataFrame(d, crs=self._crs)              

      # Ensure that index in right gdf is formed of sequential numbers
      self._right = self._agdf.copy().reset_index(drop=True)      
      _right_r = np.array(self._right["geometry"].apply(
        lambda geom: (geom.x * np.pi / 180, geom.y * np.pi / 180)).to_list()
        )      
      # Create tree from the candidate points

      self._tree = KDTree(_right_r, leaf_size=2)    

      self._gdf_is_dirty = False
    
          

    def get_nearest(self, src_points, radius=2.0):
      """Find nearest neighbors for all source points from a set of candidate points"""

      # Find closest points and distances
      indices = self._tree.query_radius(src_points, radius)

      # Transpose to get indices into arrays
      indices = indices.transpose().tolist()

      # Return indices and distances
      return indices

    def agents_at(self, pos, max_num=5, radius=2.0):
      res = self._agents_at(pos, max_num, radius)
      agents = [self.fast_get(unique_id) for unique_id in res["agentid"]]
      return agents

    def _agents_at(self, pos, max_num=5, radius=2.0):
      """Return a list of agents at given pos."""
     
      # Parse coordinates from points and insert them into a numpy array as RADIANS
      left_r = np.array(
         [ (pos[0] * np.pi / 180, pos[1] * np.pi / 180) ]
        )
      
      # Find the nearest points
      # -----------------------
      # closest ==> index in right_gdf that corresponds to the closest point
      
      closest = self.get_nearest(
        src_points=left_r, radius=radius
        )
      
      # Return points from right GeoDataFrame that are closest to points in left GeoDataFrame
      closest_points = self._right.loc[closest[0]]

      # Ensure that the index corresponds the one in left_gdf
      #closest_points = closest_points.reset_index(drop=True)
      
      return closest_points
      

