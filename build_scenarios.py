#!/usr/bin/env python
""" Extracts RES-Europe data to examine forecasting issues.
"""

import numpy as np
import pandas as pd
import os

from scipy.stats import norm, beta

__copyright__ = "Copyright 2016, Tue Vissing Jensen"
__credits__ = ["Tue Vissing Jensen"]
__license__ = "MIT"
__version__ = "1.0"
__maintainer__ = "Tue Vissing Jensen"
__email__ = "tvjens@elektro.dtu.dk"
__status__ = "Prototype"

CATEGORY = 'wind'
# CATEGORY = 'solar'
NUM_SCENARIOS = 100
FORECAST_FROM = '2013-06-23 12:00'
FORECAST_FOR = '2013-06-24'


def parse_date(date):
    return '{0:04d}{1:02d}{2:02d}{3:02d}'.format(
        date.year, date.month, date.day, date.hour)

fcdir = parse_date(pd.to_datetime(FORECAST_FROM))

scenarios = ['s' + str(i) for i in np.arange(NUM_SCENARIOS)]

# Load empirical covariance matrix
store = pd.HDFStore('data/covariance.h5')
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

# # EXAMPLE: Extract from time series
# if CATEGORY == 'wind':
#     tsfile = pd.read_csv('RE-Europe_dataset_package/Nodal_TS/wind_signal_COSMO.csv', index_col=0, parse_dates=True)
# elif CATEGORY == 'solar':
#     tsfile = pd.read_csv('RE-Europe_dataset_package/Nodal_TS/solar_signal_COSMO.csv', index_col=0, parse_dates=True)
# tsfile.columns = tsfile.columns.astype(int)
# pfcs = tsfile[FORECAST_FOR]
# # Pfcs are indexed by time since forecast
# pfcs.index = pfcs.index - pd.to_datetime(FORECAST_FROM)

# EXAMPLE: Use forecast time series
if CATEGORY == 'wind':
    tsfile = pd.read_csv(os.path.join('RE-Europe_dataset_package', 'Nodal_FC', fcdir, 'wind_forecast.csv'), index_col=0, parse_dates=True)
elif CATEGORY == 'solar':
    tsfile = pd.read_csv(os.path.join('RE-Europe_dataset_package', 'Nodal_FC', fcdir, 'solar_forecast.csv'), index_col=0, parse_dates=True)
else:
    raise ValueError('Unrecognized category: {0}'.format())
tsfile.columns = tsfile.columns.astype(int)

pfcs = tsfile[FORECAST_FOR]
# Pfcs are indexed by time since forecast
pfcs.index = pfcs.index - pd.to_datetime(FORECAST_FROM)


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
    vs = np.random.multivariate_normal([0]*len(cov), cov.values, NUM_SCENARIOS, seed=int(k))
    # Convert these samples to uniformly distributed values
    unfvs = pd.DataFrame(
        data=norm.cdf(vs),
        columns=cov.columns,
        index=scenarios)
    outpanel[k] = {}
    for n, col in unfvs.iteritems():
        sf = scalefactors[n]
        meancol = meanpanel[n, k]
        varcol = varpanel[n, k]
        mean = np.interp(pfc[n]/sf, meancol.index, meancol.values)
        var = np.interp(pfc[n]/sf, varcol.index, varcol.values)
        outcol = beta.ppf(
            col,
            mean*(mean*(1-mean)/var - 1),
            (1 - mean)*(mean*(1-mean)/var - 1)
        )
        outpanel[k][n] = pd.Series(data=outcol*sf, index=col.index)

scenariopanel = pd.Panel(outpanel)
outscenarios = scenariopanel.transpose(1, 0, 2)
outscenarios.major_axis = outscenarios.major_axis + pd.to_datetime('2013-06-23 12:00')

store = pd.HDFStore('data/scenariostore.h5')
store['/'.join((CATEGORY, 'scenarios'))] = outscenarios
store['/'.join((CATEGORY, 'pfcs'))] = tsfile[FORECAST_FOR]
store.close()

raise SystemExit

# Save observation time series
windobsfile = pd.read_csv('RE-Europe_dataset_package/Nodal_TS/wind_signal_COSMO.csv', index_col=0, parse_dates=True)
windobs = windobsfile[FORECAST_FOR]
solarobsfile = pd.read_csv('RE-Europe_dataset_package/Nodal_TS/solar_signal_COSMO.csv', index_col=0, parse_dates=True)
solarobs = solarobsfile[FORECAST_FOR]
loadtsfile = pd.read_csv('RE-Europe_dataset_package/Nodal_TS/load_signal.csv', index_col=0, parse_dates=True)
loadobs = loadtsfile[FORECAST_FOR]

solarobs.columns = solarobs.columns.astype(int)
windobs.columns = windobs.columns.astype(int)
loadobs.columns = loadobs.columns.astype(int)

store = pd.HDFStore('data/scenariostore.h5')
store['solar/obs'] = solarobs
store['wind/obs'] = windobs
store['load/obs'] = loadobs
store.close()

raise SystemExit
# For comparison: Plot point forecast and realized production vs. scenarios
if CATEGORY == 'wind':
    obstsfile = pd.read_csv('RE-Europe_dataset_package/Nodal_TS/wind_signal_COSMO.csv', index_col=0, parse_dates=True)
elif CATEGORY == 'solar':
    obstsfile = pd.read_csv('RE-Europe_dataset_package/Nodal_TS/solar_signal_COSMO.csv', index_col=0, parse_dates=True)
obstsfile.columns = obstsfile.columns.astype(int)


import matplotlib.pyplot as plt
plt.ion()


plt.figure()
obstsfile[FORECAST_FOR].mean(axis=1).plot(ls='-', lw=2, c='k', ax=plt.gca(), label='Observed')
tsfile[FORECAST_FOR].mean(axis=1).plot(ls='--', lw=2, c='k', ax=plt.gca(), label='Point forecast')
outscenarios.mean(axis=2).T.quantile(q=0.1, axis=0).plot(ls='-', lw=1, c='k', ax=plt.gca(), label='Scenarios 10% quantile')
outscenarios.mean(axis=2).T.quantile(q=0.3, axis=0).plot(ls='-', lw=1, c='k', ax=plt.gca(), label='Scenarios 30% quantile')
outscenarios.mean(axis=2).T.quantile(q=0.5, axis=0).plot(ls='-', lw=1, c='k', ax=plt.gca(), label='Scenarios 50% quantile')
outscenarios.mean(axis=2).T.quantile(q=0.7, axis=0).plot(ls='-', lw=1, c='k', ax=plt.gca(), label='Scenarios 70% quantile')
outscenarios.mean(axis=2).T.quantile(q=0.9, axis=0).plot(ls='-', lw=1, c='k', ax=plt.gca(), label='Scenarios 90% quantile')
