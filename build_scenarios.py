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

category = 'wind'
# category = 'solar'

NUM_SCENARIOS = 100
scenarios = ['n' + str(i) for i in np.arange(NUM_SCENARIOS)]
store = pd.HDFStore('covariance.h5')
cov = store['/'.join((category, 'empirical'))]
store.close()

# Point forecasts [n,k] -> pfc
# pfcs = # LOAD FROM STORE

for k in ks:
    # Generate NUM_SCENARIOS samples with marginal normal distribution and the measured covariance.
    vs = pd.DataFrame(np.random.multivariate_normal([0]*len(cov), cov.values, NUM_SCENARIOS), columns=cov.columns, index=scenarios)
    # Convert these samples to uniformly distributed values
    unfvs = norm.cdf(vs)
    for n, col in unfvs.iteritems():
        outcol = beta.ppf(
            col,
            alphapanel[n, k].interp(pfcs[n, k]),
            betapanel[n, k].interp(pfcs[n, k])
        )
