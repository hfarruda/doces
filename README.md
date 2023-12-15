# DOCES
DOCES (Dynamical Opinion Clusters Exploration Suite) is an experimental library to simulate opinion dynamics on adaptive complex networks.


```
import doces
# Initializes the network parameters
...
# Creates a DOCES object.
od = doces.Opinion_dynamics( 
    vertex_count, 
    edges, 
    directed)
```


```
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



```
# To get a dictionary with all information
stats_dict = od.get_cascade_stats_dict()

# The contents of the output dictionary are
# stats_dict = {
# "post_id": od.post_ids,
# "theta": od.post_thetas,
# "count": od.post_posted_counts,
# "cascade_size": od.post_cascade_sizes,
# "birth": od.post_births,
# "death": od.post_deaths,
# "live_posts": od.post_live_post_counts,
# "user_opinion": od.post_user_opinions
# }
```

```
# Initializes the lists to be set
...
# Set the posting filter
od.set_posting_filter(posting_filter)

# Set the receiving filter
od.set_receiving_filter(receiving_filter)

# Set stubborn users 
od.set_stubborn(stubborn_users)
```







