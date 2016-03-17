#!/usr/bin/env python
""" Extracts RES-Europe data to examine forecasting issues.
"""

import pandas as pd
import os

from scipy.stats import norm

__copyright__ = "Copyright 2016, Tue Vissing Jensen"
__credits__ = ["Tue Vissing Jensen"]
__license__ = "MIT"
__version__ = "1.0"
__maintainer__ = "Tue Vissing Jensen"
__email__ = "tvjens@elektro.dtu.dk"
__status__ = "Prototype"



category = 'wind'
tsdir = 'RE-Europe_dataset_package/Nodal_TS'
tsfilename = 'wind_signal_COSMO.csv'

tsfile = pd.read_csv(os.path.join(tsdir, tsfilename), index_col=0, parse_dates=True)

normstats = norm.ppf((tsfile.rank()-0.5)/(len(tsfile)))
normedts = pd.DataFrame(index = tsfile.index, columns=tsfile.columns, data=normstats)
cov = normedts.cov()

store = pd.HDFStore('covariance.h5')
store['empirical'] = cov
store.close()

def spherical_dist(pos1, pos2, r=6371):
    pos1 = pos1 * np.pi / 180
    pos2 = pos2 * np.pi / 180
    cos_lat1 = np.cos(pos1[..., 0])
    cos_lat2 = np.cos(pos2[..., 0])
    cos_lat_d = np.cos(pos1[..., 0] - pos2[..., 0])
    cos_lon_d = np.cos(pos1[..., 1] - pos2[..., 1])
    return r * np.arccos(cos_lat_d - cos_lat1 * cos_lat2 * (1 - cos_lon_d))

import networkx as nx
from load_network import load_network

G = load_network()
lats = nx.get_node_attributes(G, 'latitude')
lons = nx.get_node_attributes(G, 'longitude')

latlons = pd.DataFrame({'latitude':lats, 'longitude':lons})
dist = spherical_dist(latlons.values[:,None], latlons.values)
distdf = pd.DataFrame(index=latlons.index, columns=latlons.index, data=dist)

store = pd.HDFStore('covariance.h5')
store['distance'] = distdf
store.close()