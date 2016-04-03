#!/usr/bin/env python
""" Loads forecast info, fits beta distributions to marginals.
"""

import pandas as pd
import numpy as np
import os
from kernel_regression import KernelRegression

__copyright__ = "Copyright 2016, Tue Vissing Jensen"
__credits__ = ["Tue Vissing Jensen"]
__license__ = "MIT"
__version__ = "1.0"
__maintainer__ = "Tue Vissing Jensen"
__email__ = "tvjens@elektro.dtu.dk"
__status__ = "Prototype"

def get_beta_params(mean, variance):
    alpha = mean*(mean*(1-mean)/variance - 1)
    beta = (1-mean)*(mean*(1-mean)/variance - 1)
    return alpha, beta

CATEGORY = 'wind'
FCNAME = 'fc'
# ERRNAME = 'err'
OBSNAME = 'ts'
TESTNODE = 1069
TESTDELTA = '2d 3h'
MIN_VARIANCE = 0.0001

kreg = KernelRegression()
testx = np.linspace(0,1,1001)

# Possible gammas
gammas = np.logspace(1,3,21)

store = pd.HDFStore('TSVault.h5')
nodes = store['nodes']

fcdf = store['/'.join((CATEGORY, FCNAME, nodes[TESTNODE]))]
obsdf = store['/'.join((CATEGORY, OBSNAME, nodes[TESTNODE]))]
store.close()


# for fcc, obsc in zip(fcdf, obsdf):

# Pull out each node's DF's seperately.
# Save the coefficients of the polynomial fit.
fcc = fcdf[TESTDELTA]
obsc = obsdf[TESTDELTA]

obsc = obsc.dropna()
fcc = fcc.ix[obsc.index]

# Fitting mean production
kreg.fit(fcc.values.reshape(-1,1), obsc)
# Select optimal bandwidth
kreg.gamma = kreg._optimize_gamma(gammas)
# Get polynomial fit for mean production
meanpolycoeff = np.polyfit(testx, kreg.predict(testx.reshape(-1,1)),4) 

#TEST: Get values of the  mean that we can plot
testmean = np.polyval(meanpolycoeff, testx)

# Get mean predictions
prediction = np.polyval(meanpolycoeff, fcc)
# Calculate errors squared
err2 = (prediction - obsc)**2
# Fitting errors
kreg.fit(fcc.values.reshape(-1,1), err2)
# Get coefficients of polynomial fit
varpolycoeff = np.polyfit(testx, kreg.predict(testx.reshape(-1,1)),4) 

#TEST: Get values of the std that we can plot
testvar = np.polyval(varpolycoeff, testx)
testvar = np.where(testvar > MIN_VARIANCE, testvar, MIN_VARIANCE)
