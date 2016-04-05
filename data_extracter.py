#!/usr/bin/env python
""" Extracts RES-Europe data to examine forecasting issues.
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



category = 'wind'
fcdir = 'RE-Europe_dataset_package/Nodal_FC'
fcfilename = 'wind_forecast.csv'
tsdir = 'RE-Europe_dataset_package/Nodal_TS'
tsfilename = 'wind_signal_COSMO.csv'

fcdirlist = sorted(os.listdir(fcdir))

tsfile = pd.read_csv(os.path.join(tsdir, tsfilename), index_col=0, parse_dates=True)

store = pd.HDFStore('TSVault.h5')
nodes = ['n' + i for i in tsfile.columns]
store['tstypes'] = pd.Series(['fc', 'obs'])
store['nodes'] = pd.Series(nodes)
raise SystemExit
out_panel4d = {}

i=0
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


# # Adding error column
# # Order: {fc, ts, error},{Forecast from},{Lookahead time},{Node}
# final_panel = final_panel.transpose(1, 0, 2, 3)
# final_panel['err'] = final_panel.fc.subtract(final_panel.ts)

# # Order: {Node},{fc, ts, error},{Lookahead time},{Forecast from}
# final_panel = final_panel.transpose(3, 0, 1, 2)

# store = pd.HDFStore('TSVault.h5')
# store['nodes'] = 'n' + pd.Series(final_panel.labels)
# store['categories'] = pd.Series(['wind', 'solar'])
# store['tstypes'] = pd.Series(final_panel.items)
# for node, pan in final_panel.iteritems():
#     for tstype, df in pan.iteritems():
#         store['/'.join((category, str(tstype), 'n' + str(node)))] = df
# store.close()
