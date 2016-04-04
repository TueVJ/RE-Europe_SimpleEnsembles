#!/usr/bin/env python
""" Extracts RES-Europe data to examine forecasting issues.
"""

import numpy as np
import pandas as pd
import networkx as nx
import os

from load_network import load_network
from scipy.stats import norm

__copyright__ = "Copyright 2016, Tue Vissing Jensen"
__credits__ = ["Tue Vissing Jensen"]
__license__ = "MIT"
__version__ = "1.0"
__maintainer__ = "Tue Vissing Jensen"
__email__ = "tvjens@elektro.dtu.dk"
__status__ = "Prototype"

# category = 'wind'
category = 'solar'

store = pd.HDFStore('covariance.h5')
cov = store['/'.join((category, 'empirical'))]
store.close()

# Generate 100 samples with marginal normal distribution and the measured covariance.
vs = np.random.multivariate_normal([0]*len(cov), cov.values, 100)
# Convert these samples to uniformly distributed values
unfvs = norm.cdf(vs)