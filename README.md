# DOCES
DOCES (Dynamical Opinion Clusters Exploration Suite) is an experimental Python library to simulate opinion dynamics on adaptive complex networks. Its background is implemented in C for performance.

It requires python headers and a C11 compatible compiler, such as gcc or clang. To install it, run the script `setup.py`.

```bash
python setup.py build_ext --inplace install
```

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







