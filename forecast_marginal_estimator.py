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
AUTOSCALE = True

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
scalefactors = {}
for node in nodes:
    print node
    store = pd.HDFStore(TSVAULTFILE)
    fcdf = store['/'.join((CATEGORY, FCNAME, node))]
    obsdf = store['/'.join((CATEGORY, OBSNAME, node))]
    store.close()

    if AUTOSCALE:
        scalefactor = max((1.0, obsdf.max().max(), fcdf.max().max()))
    else:
        scalefactor = 1.0
    scalefactors[node] = scalefactor

    outmeandict[node] = {}
    outvardict[node] = {}
    # Pull out each node's DF's seperately.
    for (k1, fcc), (k2, obsc) in izip(fcdf.iteritems(), obsdf.iteritems()):
        # print k1
        obsc = obsc.dropna()/scalefactor
        fcc = fcc.ix[obsc.index]/scalefactor

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

ks = fcdf.columns
intnodes = nodes.map(lambda x: int(x[1:]))
meanpanel = pd.Panel(items=intnodes, major_axis=ks, minor_axis=testx, data=[[outmeandict[n][k] for k in ks] for n in nodes])
varpanel = pd.Panel(items=intnodes, major_axis=ks, minor_axis=testx, data=[[outvardict[n][k] for k in ks] for n in nodes])

meanpanel.major_axis = [pd.Timedelta(x) for x in meanpanel.major_axis]
varpanel.major_axis = [pd.Timedelta(x) for x in varpanel.major_axis]

cpanel = meanpanel.multiply(1-meanpanel).divide(varpanel) - 1
alphapanel = meanpanel.multiply(cpanel)
betapanel = (1-meanpanel).multiply(cpanel)

store = pd.HDFStore('data/marginalstore.h5')
store['/'.join((CATEGORY, 'mean'))] = meanpanel
store['/'.join((CATEGORY, 'var'))] = varpanel
store['/'.join((CATEGORY, 'alpha'))] = alphapanel
store['/'.join((CATEGORY, 'beta'))] = betapanel
store.close()
