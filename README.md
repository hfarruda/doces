# DOCES
DOCES (Dynamical Opinion Clusters Exploration Suite) is an experimental Python library to simulate opinion dynamics on adaptive complex networks. Its background is implemented in C for performance.

# INSTALL

It requires python headers and a C11 compatible compiler, such as gcc or clang. To install it, run the script `setup.py`.

```bash
python setup.py build_ext --inplace install
```

# USAGE

Once installed, you can setup the agent-based simulation by instantiating an object with the constructor `Opinion_dynamics()` with a network, like in the example below.

```python
import doces
# Initializes the network parameters
...
# Creates a DOCES object.
od = doces.Opinion_dynamics( 
    vertex_count, 
    edges,
    directed)
```

The constructor takes as arguments features of the network connecting agents. They are:
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
    1, 
    posting_filter, 
    receiving_filter,
    b = None,
    1,
    rewire = True,
    None,
    min_opinion = -1, 
    max_opinion = 1,
    delta = 0.1,
    verbose = True,
    rand_seed = None)

opinions = output_dictionary["b"]
edge_list = output_dictionary["edges"]
```

The method outputs are a list `opinions` of continuous values between `min_opinion` and `max_opinion` for each agent and a python list of 2-tuples with the network structure after the simulation is finished. Its inputs are:

- `number_of_iterations` - number of iterations the model runs for;
- `phi` - a float number which controls the receiving filter;
- `posting_filter` - an integer from 0 to 5 to set which function filters posting activity, according to the below specification.;
- `receiving_filter` - an integer from 0 to 5 to set which function filters how posts are received, according to the below specification.;
- `b` - an array of floats corresponding to the initial opinions of agents;
- `rewire` - boolean to allow rewiring in each iteration or not;
- `min_opinion` - float corresponding to the minimum opinion value agents can have;
- `max_opinion` - float corresponding to the maximum opinion value agents can have;
- `delta` - float corresponding to the increment (or decrement) applied to opinions in each iteration;
- `verbose` - boolean which allows the code to print details of each simulation;
- `rand_seed` - float used as seed for random number generation;

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
