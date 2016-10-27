# RES-Europe scenario generator

Generates simple scenarios which are not coupled in time.
See method.pdf for a description of the method used.

Required packages (Tested version in parens):
- Pandas (0.15)
- Numpy (1.11)
- NetworkX (1.11)
- Matplotlib (1.5.1) [optional]

# Usage

- Extract the RE-Europe dataset package to ./RE-Europe_dataset_package/
- run data_extracter.py
- run forecast_marginal_estimator.py
- run correlation_extracter.py
- run build_scenarios.py
- data/scenariostore.h5 now contains the generated scenarios

Edit the CAPITAL VARIABLES at the top of each script to tweak settings.
