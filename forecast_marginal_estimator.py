#!/usr/bin/env python
""" Loads forecast info, fits beta distributions to marginals.
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


CATEGORY = 'wind'
FCNAME = 'fc'
ERRNAME = 'err'
OBSNAME = 'ts'
TESTNODE = 1069

store = pd.HDFStore('TSVault.h5')
nodes = store['nodes']

fcdf = store['/'.join((CATEGORY, FCNAME, nodes[TESTNODE]))]
errdf = store['/'.join((CATEGORY, ERRNAME, nodes[TESTNODE]))]
obsdf = store['/'.join((CATEGORY, OBSNAME, nodes[TESTNODE]))]
store.close()


# outlist = []
# for 

# Pull out each node's DF's seperately.
# Save the coefficients of the polynomial fit.
# Q: Use logs or direct numbers?
# errc = errdf.iloc[:,80]
# fcc = fcdf.iloc[:,80]
# polycoeff = np.polyfit(fcc.values, errc.values**2+0.0001)
# polycoeff = np.polyfit(fcc.values, np.log(errc.values**2+0.0001))
