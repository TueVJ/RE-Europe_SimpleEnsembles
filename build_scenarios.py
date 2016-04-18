#!/usr/bin/env python
""" Extracts RES-Europe data to examine forecasting issues.
"""

import numpy as np
import pandas as pd
import networkx as nx
import os

from load_network import load_network
from scipy.stats import norm, beta

__copyright__ = "Copyright 2016, Tue Vissing Jensen"
__credits__ = ["Tue Vissing Jensen"]
__license__ = "MIT"
__version__ = "1.0"
__maintainer__ = "Tue Vissing Jensen"
__email__ = "tvjens@elektro.dtu.dk"
__status__ = "Prototype"

# CATEGORY = 'wind'
CATEGORY = 'solar'
NUM_SCENARIOS = 100


scenarios = ['s' + str(i) for i in np.arange(NUM_SCENARIOS)]
store = pd.HDFStore('covariance.h5')
cov = store['/'.join((CATEGORY, 'empirical'))]
store.close()


# Point forecasts [n,k] -> pfc
# EXAMPLE: Use mean as point forecast
# store = pd.HDFStore('data/TSVault.h5')
# if CATEGORY == 'wind':
#     windmean = store['windmean']
# elif CATEGORY == 'solar':
#     solarmean = store['solarmean']
# store.close()
# pfcs = pd.DataFrame(data=np.array([windmean]*2).T, index=cov.index, columns=[pd.Timedelta('1d'), pd.Timedelta('2d')])

# EXAMPLE: Extract from time series
if CATEGORY == 'wind':
    tsfile = pd.read_csv('RE-Europe_dataset_package/Nodal_TS/wind_signal_COSMO.csv', index_col=0, parse_dates=True)
elif CATEGORY == 'solar':
    tsfile = pd.read_csv('RE-Europe_dataset_package/Nodal_TS/solar_signal_COSMO.csv', index_col=0, parse_dates=True)
tsfile.columns = tsfile.columns.astype(int)
pfcs = tsfile['2013-06-24']
pfcs.index = pfcs.index - pd.to_datetime('2013-06-23 12:00')

# Load marginal distributions
store = pd.HDFStore('data/marginalstore.h5')
meanpanel = store['/'.join((CATEGORY, 'mean'))]
varpanel = store['/'.join((CATEGORY, 'var'))]
scalefactors = store['/'.join((CATEGORY, 'scalefactors'))]
store.close()

outpanel = {}
for k, pfc in pfcs.iterrows():
    print k
    # Generate NUM_SCENARIOS samples with marginal normal distribution and the measured covariance.
    vs = np.random.multivariate_normal([0]*len(cov), cov.values, NUM_SCENARIOS)
    # Convert these samples to uniformly distributed values
    unfvs = pd.DataFrame(
        data=norm.cdf(vs),
        columns=cov.columns,
        index=scenarios)
    outpanel[k] = {}
    for n, col in unfvs.iteritems():
        meancol = meanpanel[n, k]
        varcol = varpanel[n, k]
        mean = np.interp(pfc[n], meancol.index, meancol.values)
        var = np.interp(pfc[n], varcol.index, varcol.values)
        outcol = beta.ppf(
            col,
            mean*(mean*(1-mean)/var - 1),
            (1 - mean)*(mean*(1-mean)/var - 1)
        )
        outpanel[k][n] = pd.Series(data=outcol*scalefactors[n], index=col.index)

scenariopanel = pd.Panel(outpanel)
outscenarios = scenariopanel
outscenarios.items = outscenarios.items + pd.to_datetime('2013-06-23 12:00')
store = pd.HDFStore('data/scenariostore.h5')
store['/'.join(CATEGORY, 'scenarios')] = outscenarios
store.close()
