#!/usr/bin/env python
""" Loads forecast info, fits beta distributions to marginals.
"""

import pandas as pd
import numpy as np
import os
from kernel_regression import KernelRegression
from itertools import izip

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
OBSNAME = 'ts'
TESTNODE = 1069
TESTDELTA = '2d 3h'
MIN_VARIANCE = 0.0001
TSVAULTFILE = 'data/TSVault.h5'

kreg = KernelRegression()
testx = np.linspace(0, 1, 101)

# Possible gammas
gammas = np.logspace(1, 4, 31)
TEST_GAMMA = 100  # Gaussian width ~ 1/100 = 1% of production
kreg.gamma = TEST_GAMMA

store = pd.HDFStore(TSVAULTFILE)
nodes = store['nodes']
store.close()

# optimal_gammas = []
outmeandict = {}
outvardict = {}
# for node in nodes:
for node in nodes[TESTNODE:TESTNODE+1]:
    print node
    store = pd.HDFStore(TSVAULTFILE)
    fcdf = store['/'.join((CATEGORY, FCNAME, node))]
    obsdf = store['/'.join((CATEGORY, OBSNAME, node))]
    store.close()
    outmeandict[node] = {}
    outvardict[node] = {}
    # Pull out each node's DF's seperately.
    for (k1, fcc), (k2, obsc) in izip(fcdf.iteritems(), obsdf.iteritems()):
        print k1
        obsc = obsc.dropna()
        fcc = fcc.ix[obsc.index]

        # Kernelregression Forecasted => mean
        kreg.fit(fcc.values.reshape(-1, 1), obsc)
        meanpredict = kreg.predict(testx.reshape(-1, 1))
        # Select optimal bandwidth
        # kreg.gamma = kreg._optimize_gamma(gammas)
        # optimal_gammas.append(kreg.gamma)
        # Get polynomial fit for mean production
        # meanpolycoeff = np.polyfit(testx, kreg.predict(testx.reshape(-1, 1)),4)

        # Our predicted mean based on point forecast
        # prediction = np.polyval(meanpolycoeff, fcc)
        prediction = np.interp(fcc, testx, meanpredict)
        # Calculate errors squared
        err2 = (prediction - obsc)**2
        # Fit variance curve
        kreg.fit(fcc.values.reshape(-1, 1), err2)
        varpredict = kreg.predict(testx.reshape(-1, 1))
        # Select optimal bandwidth
        # kreg.gamma = kreg._optimize_gamma(gammas)
        # Get coefficients of polynomial fit
        # varpolycoeff = np.polyfit(testx, kreg.predict(testx.reshape(-1, 1)), 4)
        # Save the coefficients of the polynomial fit.
        # outdict[node][k1] = {'mean': meanpolycoeff, 'var': varpolycoeff}
        outmeandict[node][k1] = meanpredict
        # testvar = np.polyval(varpolycoeff, testx)
        outvardict[node][k1] = varpredict

# #TEST: Get values of the  mean that we can plot
# testmean = np.polyval(meanpolycoeff, testx)

# #TEST: Get values of the std that we can plot
# testvar = np.polyval(varpolycoeff, testx)
# testvar = np.where(testvar > MIN_VARIANCE, testvar, MIN_VARIANCE)
