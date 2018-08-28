#!/usr/bin/env python
""" Extracts RES-Europe data and constructs time-uncoupled forecasts.
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

# CATEGORY = 'wind'
CATEGORY = 'solar'
NUM_SCENARIOS = 1000
FORECAST_FROM = '2013-06-23 12:00'
FORECAST_FOR = '2013-06-24'


def parse_date(date):
    '''
        Parses dates to the string format used by the RE-Europe data set
    '''
    return '{0:04d}{1:02d}{2:02d}{3:02d}'.format(
        date.year, date.month, date.day, date.hour)


def convert_index_and_columns(df, dtype=int, convert_index=True, index_dtype=None, convert_columns=True, columns_dtype=None):
    '''
        Given a dataframe _df_, convert the dtype of columns and index to the chosen dtype.
        Bools convert_index and convert_columns set whether to convert these.
        index_dtype and columns_dtype override the _dtype_ option.
        dtypes are any accepted by pandas dataframes' df.astype option.
    '''
    df = df.copy()
    if convert_index:
        if index_dtype is None:
            df.index = df.index.astype(dtype)
        else:
            df.index = df.index.astype(index_dtype)
    if convert_columns:
        if columns_dtype is None:
            df.columns = df.columns.astype(dtype)
        else:
            df.columns = df.columns.astype(index_dtype)
    return df


fcdir = parse_date(pd.to_datetime(FORECAST_FROM))

scenarios = ['s' + str(i) for i in np.arange(NUM_SCENARIOS)]

# Load empirical covariance matrix
store = pd.HDFStore('data/covariance.h5')
cov = store['/'.join((CATEGORY, 'empirical'))]
store.close()
cov = convert_index_and_columns(cov)

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

pfcs = tsfile.ix[FORECAST_FOR]
# Pfcs are indexed by time since forecast
pfcs.index = pfcs.index - pd.to_datetime(FORECAST_FROM)


# Load marginal distributions
store = pd.HDFStore('data/marginalstore.h5')
meanpanel = store['/'.join((CATEGORY, 'mean'))]
varpanel = store['/'.join((CATEGORY, 'var'))]
scalefactors = store['/'.join((CATEGORY, 'scalefactors'))]
store.close()

RNG = np.random.RandomState()
MAX_SEED = 2*(2**31-1)+1

outpanel = {}
for k, pfc in pfcs.iterrows():
    print k
    # Initialize pseudorandom number generator with seed equal timestamp
    RNG.seed(int(k.to_pytimedelta().seconds % MAX_SEED))
    # Generate NUM_SCENARIOS samples with marginal normal distribution and the measured covariance.
    vs = RNG.multivariate_normal([0]*len(cov), cov.values, NUM_SCENARIOS)
    # Convert these samples to uniformly distributed values
    unfvs = pd.DataFrame(
        data=norm.cdf(vs),
        columns=cov.columns,
        index=scenarios)
    outpanel[k] = {}
    # Convert uniformly distributed data to beta-distributed data according to marginal distributions
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
# Ordering of output: Scenario Number, Time for which Forecasted, Node
outscenarios = scenariopanel.transpose(1, 0, 2)
outscenarios.major_axis = outscenarios.major_axis + pd.to_datetime(FORECAST_FROM)

store = pd.HDFStore('data/scenariostore.h5')
store['/'.join((CATEGORY, 'scenarios'))] = outscenarios
store['/'.join((CATEGORY, 'pfcs'))] = tsfile[FORECAST_FOR]
store.close()

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

