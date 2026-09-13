<p style="display: flex; align-items: center; justify-content: center; margin: 0;">
    <img src="https://raw.githubusercontent.com/hfarruda/doces/main/.github/figures/brigadeiro.png" alt="icon" style="width: 100%; max-width: 600px; height: auto; margin-right: 15px;"/>
</p>

DOCES (Dynamical Opinion Clusters Exploration Suite) is an experimental Python library to simulate opinion dynamics on adaptive complex networks. Its background is implemented in C for performance.

# Install

DOCES 0.1.0 supports Python 3.9–3.14 and NumPy 2.x. Installation selects a NumPy version compatible with your Python version.

To install DOCES, simply use the following:

```bash
pip install doces
```

If the first command does not find a compatible version of DOCES for your Python version, use the following command to install the package:
```bash
pip install git+https://github.com/hfarruda/doces.git
```

To build a source distribution and wheel and test the installed package in temporary environments, run `bash runtest.sh` from the repository root. Set `PYTHON=/path/to/python` to test a particular interpreter.

# Usage

Once installed, you can set up the agent-based simulation by instantiating an object with the constructor `Opinion_dynamics()` with a network, like in the example below.

```python
import doces
# Initializes the network parameters
...
# Creates a Opinion_dynamics object.
od = doces.Opinion_dynamics( 
    vertex_count, 
    edges,
    directed)
```

The constructor takes the features of the network connecting agents as arguments. They are:
- `vertex_count` - number of nodes/agents in the network;
- `edges` - a python list of 2-tuples of nodes denoting the network edges ((source, target) in the case it is directed);
- `directed` - a boolean indicating whether the network is directed or not;

Once the `od` object is initialized, the simulation can be performed by calling its method `simulate_dynamics()` as

```python
# Initializes the dynamics parameters
...
# Run the dynamics
output_dictionary = od.simulate_dynamics(
    number_of_iterations,
    phi,
    mu, 
    posting_filter, 
    receiving_filter,
    b = None,
    feed_size = 5,
    rewire = True,
    cascade_stats_output_file = None,
    min_opinion = -1, 
    max_opinion = 1,
    delta = 0.1,
    verbose = True,
    rand_seed = None)

opinions = output_dictionary["b"]
edge_list = output_dictionary["edges"]
```

The method outputs are a list `opinions` of continuous values between `min_opinion` and `max_opinion` for each agent and a Python list of 2-tuples with the network structure after the simulation is finished. Its inputs are:

- `number_of_iterations` - an integer (positive value) that is used as the number of iterations for the model to run;
- `phi` - a float number which controls the receiving filter;
- `mu` - a float number that controls the innovation parameter. If `mu = 0`, there is no innovation, and if `mu = 1`, all the posts are new and the feed posts are never re-posted;
- `posting_filter` - an integer from 0 to 6 to set which function filters posting activity, according to the below specification;
- `receiving_filter` - an integer from 0 to 6 to set which function filters how posts are received, according to the below specification;
- `b` - an array of floats corresponding to the initial opinions of agents;
- `feed_size` - an integer to set the size of the feed. The default value is 5;
- `rewire` - a boolean to allow rewiring in each iteration or not;
- `cascade_stats_output_file` - a string representing the output file path for cascade statistics. The default value is None;
- `min_opinion` - a float corresponding to the minimum opinion value agents can have;
- `max_opinion` - a float corresponding to the maximum opinion value agents can have;
- `delta` - a float corresponding to the increment (or decrement) applied to opinions in each iteration;
- `verbose` - a boolean that allows the code to print details of each simulation;
- `rand_seed` - an integer (positive value) used as a seed for random number generation;

The library provides the following filter functions and selection modes; in the formulas below, `d` is the absolute, unnormalized difference and `phi` is the receiving-filter parameter (zero for posting):

- 0: `COSINE`: Controversial posting rule (eq. 1);
- 1: `STRETCHED_HALF_COSINE`: Stretched squared cosine probability, `cos(pi*d/4 + phi)**2`;
- 2: `UNIFORM`: Priority receiving rule;
- 3: `HALF_COSINE` Aligned posting rule (eq. 2),  
- 4: `RANDOM_DISTR`: Selection mode that randomly assigns `COSINE`, `UNIFORM`, or `HALF_COSINE` to each agent;
- 5: `CUSTOM`: Selection mode that activates posting or receiving filters previously configured through their setters. Use one filter for all agents or a list with one entry per agent; entries can mix built-in identifiers, sampled Python functions, and `ProbabilityTable` objects (see [Python probability functions](#python-probability-functions));
- 6: `REVERSED_HALF_COSINE`: Probability zero for `d <= 1`, and `cos(pi*d/2)**2` otherwise; the default rewiring probability.

To use option 5, you can call the methods `set_posting_filter()` and `set_receiving_filter()`, as in the example below. Additionally, agents can be set as stubborn by passing a list with integers indicating those agents to the method `set_stubborn()`. Remember to do this before calling `simulate_dynamics()`.

```python
# Initializes the lists to be set
...
# Set the posting filter
od.set_posting_filter(posting_filter)

# Set the receiving filter
od.set_receiving_filter(receiving_filter)

# Set stubborn users 
od.set_stubborn(stubborn_users)
```

## Python probability functions

`set_posting_filter`, `set_receiving_filter`, and `set_rewiring_filter` also accept a Python function or a `doces.ProbabilityTable`. Pass one choice for all nodes, or a list with one choice per node; lists can mix tables, functions, and built-in filters (`COSINE`, `STRETCHED_HALF_COSINE`, `UNIFORM`, `HALF_COSINE`, and `REVERSED_HALF_COSINE`). Existing integer-array setters continue to work.

```python
import numpy as np

grid = np.linspace(0.0, 2.0, 1001)
od.set_posting_filter(lambda difference: np.exp(-difference**2), grid=grid)
od.set_receiving_filter(doces.ProbabilityTable([0.0, 2.0], [1.0, 0.2]))
od.set_rewiring_filter(lambda difference: (difference / 2.0)**2, grid=grid)
# Run with posting_filter=doces.CUSTOM and receiving_filter=doces.CUSTOM.
```

Functions receive the **absolute, unnormalized difference** and must return a finite scalar probability in `[0, 1]`. Posting uses the difference between a post's value and the posting node's opinion. Receiving uses the difference between the posting node's and follower's opinions; the **posting node's** assignment selects the receiving filter, preserving the existing model. Rewiring uses the difference between the two nodes' opinions and the assignment of the **node changing its connection**, after any repulsion update.

Functions are sampled when configured; each repeated function is sampled once per grid point per setter call. C uses the table's interpolation method during simulation, with linear interpolation as the default. Choose the grid resolution to suit the function; this approximates its curve. Changing a captured parameter requires configuring the function again. `phi` still applies to native cosine filters, and does not alter sampled probabilities. These functions cannot depend on changing simulation state or time during the C loop.

When `receiving_filter=doces.CUSTOM` and `phi` is nonzero, DOCES reports `doces.FilterParameterWarning` once per receiving-filter configuration if it contains a sampled function/table and **none** of its node assignments uses the native `COSINE` or `STRETCHED_HALF_COSINE` filter. In that case, simulation-time `phi` has no effect. Include the parameter in the sampled function and call `set_receiving_filter` again when its value changes:

```python
custom_phi = 0.25
receiving = doces.ProbabilityTable.from_function(
    lambda difference: np.cos(np.pi * difference / 2 + custom_phi) ** 2,
    grid,
)
od.set_receiving_filter(receiving)
```

No warning is shown for `phi=0`, or when at least one node uses native `COSINE` or `STRETCHED_HALF_COSINE`, because `phi` affects that part of the mixed configuration. Native `UNIFORM`, `HALF_COSINE`, and `REVERSED_HALF_COSINE` do not use `phi`. To suppress this specific warning when the behavior is intentional:

```python
import warnings
warnings.filterwarnings("ignore", category=doces.FilterParameterWarning)
```

Both `ProbabilityTable` and `ProbabilityTable.from_function` accept `interpolation="linear"` or `interpolation="previous"`. Linear interpolation joins neighboring samples with a straight line. Previous interpolation holds each sample's probability until the next knot; at an exact knot, that knot's probability applies, including the final endpoint. Include a step's threshold in the grid to represent it exactly:

```python
step = doces.ProbabilityTable(
    [0.0, 0.5, 2.0], [1.0, 0.0, 0.0], interpolation="previous"
)
od.set_posting_filter(step)  # 1 for difference < 0.5; 0 otherwise
```

Each table chooses its own interpolation method, so per-node lists can mix both modes for posting, receiving, or rewiring. Direct callables passed to setters use linear interpolation; use `ProbabilityTable.from_function(..., interpolation="previous")` to sample a step function. Queries outside a table's domain remain errors in either mode.

Tables require at least two finite, strictly increasing, nonnegative differences and matching probabilities in `[0, 1]`. Active tables must cover differences from zero through `max_opinion - min_opinion` (`[0, 2]` for the defaults), and any wider range needed by retained opinions or posts when resuming. Invalid tables or sampled results are rejected before replacing the configuration; insufficient coverage is rejected before simulation changes state. Tables own copies of their arrays, and C owns its own copies too.

Use `CUSTOM` in `simulate_dynamics` to activate configured posting and receiving filters. Selecting a global built-in replaces that role's configuration, as with the existing integer-array setters; configure it again before returning to `CUSTOM`. The rewiring configuration persists across simulation calls. `rewire=True` uses it, and `rewire=False` prevents **all rewiring, including stubborn nodes**. This fixes the previous stubborn-node exception to `rewire=False`; seeded trajectories involving that bug can therefore change.

By default, `rewire=True` retains the original probability: zero for differences `d <= 1`, and `cos(pi*d/2)**2` otherwise. It is also available as `doces.REVERSED_HALF_COSINE` (6). Calling `od.set_rewiring_filter()` restores this default with the original random draws. Custom rewiring probabilities keep the existing conditions for considering rewiring and the existing selection of a replacement connection.

See the runnable [custom filters tutorial](docs/tutorial/custom_filters.py) for per-node functions and a check that `rewire=False` keeps the network fixed with stubborn nodes.

# Tested OS

Linux (Debian and Ubuntu), MacOS, and Windows

# DOCES Architecture

DOCES combines high-performance C code for computational efficiency with Python for an easy-to-use interface. The architecture is modular, with the **Core** implemented in C and **Methods** accessible via Python.

<div align="center">
  <img src="https://raw.githubusercontent.com/hfarruda/doces/main/.github/figures/diagram.png" alt="DOCES Architecture" style="width:90%;">
</div>

# Optional Conda Environment

To use the optional Conda environment provided in this repository, run the following commands from the repository root:

```bash
conda env create -f environment.yml
conda activate doces
```

# Citation Request

If you publish a scientific paper using this software, please cite the corresponding reference:

Henrique Ferraz de Arruda, Kleber Andrade Oliveira, and Yamir Moreno. "Dynamical opinion clusters exploration suite: Modeling social media opinion dynamics." SoftwareX, Vol. 30, 2025, p. 102136. DOI: 
[10.1016/j.softx.2025.102136](https://doi.org/10.1016/j.softx.2025.102136).  

[Read the paper here](https://www.sciencedirect.com/science/article/pii/S2352711025001037).

The BibTeX entry for this reference can be found [here](https://raw.githubusercontent.com/hfarruda/doces/main/doces.bib).

In addition, if your work addresses specific aspects of the opinion dynamics modeled in this software, please also cite the relevant references:

- Henrique Ferraz de Arruda, Felipe Maciel Cardoso, Guilherme Ferraz de Arruda, Alexis R. Hernández, Luciano da Fontoura Costa, and Yamir Moreno. "Modelling how social network algorithms can influence opinion polarization." Information Sciences 588 (2022): 265-278.

The dynamics for directed networks, or with the use of particular types of users (e.g., stubborn and verified) is cited as follows:

- Henrique Ferraz de Arruda, Kleber Andrade Oliveira, and Yamir Moreno. "Echo chamber formation sharpened by priority users." iScience (2024).

The dynamics with feeds (innovation parameter `mu < 1`) is cited as follows:

- Kleber Andrade Oliveira, Henrique Ferraz de Arruda, and Yamir Moreno. "Mechanistic interplay between information spreading and opinion polarization." PNAS Nexus (2026).

# Coding Assistant Disclaimer

Starting with version v0.1.0, Codex is used as a coding assistant in the development of this library.
