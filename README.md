<p style="display: flex; align-items: center; justify-content: center; margin: 0;">
    <img src="https://raw.githubusercontent.com/hfarruda/doces/main/.github/figures/brigadeiro.png" alt="icon" style="width: 100%; max-width: 600px; height: auto; margin-right: 15px;"/>
</p>

DOCES (Dynamical Opinion Clusters Exploration Suite) is an experimental Python library to simulate opinion dynamics on adaptive complex networks. Its background is implemented in C for performance.

# Install

To install DOCES, simply use the following:

```bash
pip install doces
```

If the first command does not find a compatible version of DOCES for your Python version, use the following command to install the package:
```bash
pip install git+https://github.com/hfarruda/doces.git
```

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
- `posting_filter` - an integer from 0 to 5 to set which function filters posting activity, according to the below specification;
- `receiving_filter` - an integer from 0 to 5 to set which function filters how posts are received, according to the below specification;
- `b` - an array of floats corresponding to the initial opinions of agents;
- `feed_size` - an integer to set the size of the feed. The default value is 5;
- `rewire` - a boolean to allow rewiring in each iteration or not;
- `cascade_stats_output_file` - a string representing the output file path for cascade statistics. The default value is None;
- `min_opinion` - a float corresponding to the minimum opinion value agents can have;
- `max_opinion` - a float corresponding to the maximum opinion value agents can have;
- `delta` - a float corresponding to the increment (or decrement) applied to opinions in each iteration;
- `verbose` - a boolean that allows the code to print details of each simulation;
- `rand_seed` - an integer (positive value) used as a seed for random number generation;

The filter functions are predefined in the library in the variables  
- 0: `COSINE`: Controversial posting rule (eq. 1);
- 2: `UNIFORM`: Priority receiving rule;
- 3: `HALF_COSINE` Aligned posting rule (eq. 2),  
- 5:`CUSTOM` Allows different filters to be passed as a list of integers (with size equal to the number of agents).

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

# Tested OS

Linux (Debian and Ubuntu), MacOS, and Windows

# DOCES Architecture

DOCES combines high-performance C code for computational efficiency with Python for an easy-to-use interface. The architecture is modular, with the **Core** implemented in C and **Methods** accessible via Python.

<div align="center">
  <img src="https://raw.githubusercontent.com/hfarruda/doces/main/.github/figures/diagram.png" alt="DOCES Architecture" style="width:90%;">
</div>

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

- Kleber Andrade Oliveira, Henrique Ferraz de Arruda, and Yamir Moreno. "Mechanistic interplay between information spreading and opinion polarization." arXiv preprint arXiv:2410.17151 (2024).
