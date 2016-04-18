#!/usr/bin/env python
""" Extracts RES-Europe data to build forecasts.
"""

import pandas as pd
import os

__copyright__ = "Copyright 2016, Tue Vissing Jensen"
__credits__ = ["Tue Vissing Jensen"]
__license__ = "MIT"
__version__ = "1.0"
__maintainer__ = "Tue Vissing Jensen"
__email__ = "tvjens@elektro.dtu.dk"
__status__ = "Prototype"


fcdir = 'RE-Europe_dataset_package/Nodal_FC'
tsdir = 'RE-Europe_dataset_package/Nodal_TS'

# category = 'wind'
category = 'solar'

if category == 'wind':
    fcfilename = 'wind_forecast.csv'
    tsfilename = 'wind_signal_COSMO.csv'
elif category == 'solar':
    fcfilename = 'solar_forecast.csv'
    tsfilename = 'solar_signal_COSMO.csv'
else:
    raise ValueError('Unrecognized category: {0}'.format(category))

fcdirlist = sorted(os.listdir(fcdir))

tsfile = pd.read_csv(os.path.join(tsdir, tsfilename), index_col=0, parse_dates=True)

store = pd.HDFStore('data/TSVault.h5')
store['tstypes'] = pd.Series(['fc', 'obs'])
nodes = ['n' + i for i in tsfile.columns]
store['nodes'] = pd.Series(nodes)
out_panel4d = {}

i = 0
for one_fc in fcdirlist:
    try:
        fcfile = pd.read_csv(os.path.join(fcdir, one_fc, fcfilename), index_col=0, parse_dates=True)
        fcfrom = pd.to_datetime(one_fc, format='%Y%m%d%H')
        delta = (fcfile.index - fcfrom)
        tssnip = tsfile.ix[fcfile.index]
        fcfile.index = delta
        tssnip.index = delta
        out_panel = pd.Panel({'fc': fcfile, 'ts': tssnip})
        out_panel4d[fcfrom] = out_panel
    except IndexError:
        # We've run out of indices, break here.
        break
    # Intermediate saving, avoid memory errors
    i += 1
    if i % 100 == 0:
        print 'Saving at {0}'.format(fcfrom)
        # Save intermediate
        # Order : {Forecast from},{fc, ts},{Lookahead time},{Node}
        final_panel = pd.Panel4D(out_panel4d)
        # Order: {Node},{fc, ts},{Forecast from},{Lookahead time}
        final_panel = final_panel.transpose(3, 1, 0, 2)
        for node, pan in final_panel.iteritems():
            for tstype, df in pan.iteritems():
                key = '/'.join((category, str(tstype), 'n' + str(node)))
                try:
                    olddf = store[key]
                    store[key] = pd.concat([olddf, df])
                except KeyError:
                    store[key] = df
        out_panel4d = {}

# Final save
print 'Final save at {0}'.format(fcfrom)
# Order : {Forecast from},{fc, ts},{Lookahead time},{Node}
final_panel = pd.Panel4D(out_panel4d)
# Order: {Node},{fc, ts},{Forecast from},{Lookahead time}
final_panel = final_panel.transpose(3, 1, 0, 2)
for node, pan in final_panel.iteritems():
    for tstype, df in pan.iteritems():
        key = '/'.join((category, str(tstype), 'n' + str(node)))
        try:
            olddf = store[key]
            store[key] = pd.concat([olddf, df])
        except KeyError:
            store[key] = df
store.close()
