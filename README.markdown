# RES-Europe scenario generator

Generates simple scenarios which are not coupled in time.

Given a forecast $y_n$ at a lead time $k$ for node $n$, the observation is assumed to follow a beta distribution
$$
y_{n,obs} \sim\sim \beta(\mu=y_n, \sigma=\kappa_n(y_n, k)),
$$
where $\kappa_n$ is determined from the data.
Forecasts are _decoupled in time_ and _coupled in space_ by the heuristic
$$
Var(z_{n1}, z_{n2}) \propto \exp(\lambda d_{n1, n2})
$$
where $d_{n1, n2} is the distance between node n1 and n2.
$z_n$ is a normally distributed variable which is transformed to $y_n$ through the beta function marginal.

Required packages:
- Pandas >=0.15
