#define SIMULATE_DYNAMICS_DOC simulate_dynamics(self, args, kwds)\n\
Simulate dynamics on the given PyDynamics object.\n\
\n\
Args:\n\
        number_of_iterations (int): The number of iterations to run the simulation for.\n\
        min_opinion (float): The minimum opinion value.\n\
        max_opinion (float): The maximum opinion value.\n\
        phi (float): The phi value for the receiving function.\n\
        mu (float): The mu value.\n\
        delta (float): The delta value.\n\
        posting_filter (int): The posting filter value.\n\
        receiving_filter (int): The receiving filter value.\n\
        rewire (int): The rewire value.\n\
        b (ndarray): A 1D numpy array containing the b values.\n\
        feed_size (int): The feed size value.\n\
        cascade_stats_output_file (str): The output file to write cascade statistics to (optional).\n\
        verbose (bool): Whether to print verbose output (optional).\n\
        rand_seed (int): Define the random seed (optional).\n\
\n\
Returns:\n\
Dictionary with resulting opinions and edge list.

#define PRINT_FEEDS_DOC Print the feeds on the screen.

#define DESTROY_NETWORK_DOC Destroy Network.

#define SET_NETWORK_DOC Set the network for the dynamics simulation.\n\
\n\
    Args:\n\
        vertexCount (int): Number of nodes in the network.\n\
        edges (array_like): An array of edges.\n\
        directed (bool): Whether the edges are directed or not. Default is False.\n\
        b (ndarray): A 1D numpy array containing the b values.

// #define RESET_VARIABLES_DOC Reset variables.
#define SET_POSTING_FILTER_DOC Set posting filter (np array of integers).

#define SET_RECEIVING_FILTER_DOC Set receiving filter (np array of integers).

#define FORCE_DEALLOC_DOC Clean the memory. Returns: None.

#define SET_STUBBORN_DOC Set nodes that never change their opinions (numpy array of integers).