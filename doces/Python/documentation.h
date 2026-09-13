#define SIMULATE_DYNAMICS_DOC _simulate_dynamics(self, number_of_iterations, min_opinion, max_opinion, phi, mu, delta, posting_filter, receiving_filter, rewire[, b, feed_size, cascade_stats_output_file, verbose, rand_seed])\n\
Simulate dynamics on the given PyDynamics object.\n\
This is the private C method; the public Opinion_dynamics.simulate_dynamics wrapper has a different argument order and supplies defaults.\n\
\n\
Args:\n\
        number_of_iterations (int): The number of iterations to run the simulation for.\n\
        min_opinion (float): The minimum opinion value.\n\
        max_opinion (float): The maximum opinion value.\n\
        phi (float): The phi value for native receiving functions. Sampled probability tables do not use this value.\n\
        mu (float): The mu value.\n\
        delta (float): The delta value.\n\
        posting_filter (int): The posting filter selector. "CUSTOM" (5) activates previously configured per-node filters or probability tables.\n\
        receiving_filter (int): The receiving filter selector. "CUSTOM" (5) activates previously configured per-node filters or probability tables.\n\
        rewire (bool): Whether to allow rewiring. False disables rewiring for all nodes including stubborn nodes. True uses the configured rewiring filter or the original probability when none is configured.\n\
        b (array_like, optional): A one-dimensional array with one opinion per vertex within min_opinion and max_opinion. Omit only when opinions have already been initialized; passing None directly is not supported.\n\
        feed_size (int, optional): The feed size used when feeds are first created. Default is 5; existing feeds are retained on subsequent calls.\n\
        cascade_stats_output_file (str, optional): The output filename prefix for cascade statistics; .csv is appended. Omit to disable file output; passing None directly is not supported.\n\
        verbose (bool, optional): Whether to print verbose output. Defaults to the current verbosity of the object.\n\
        rand_seed (int, optional): Define the random seed. Omission or a negative value uses the current time. Each call seeds the random generator.\n\
\n\
Configure callables and ProbabilityTable objects through the public Python filter setters before simulation; this C method accepts integer filter selectors.\n\
Selecting a global posting or receiving filter other than "CUSTOM" discards the previous configuration for that role.\n\
\n\
Returns:\n\
None. Updates the simulation state in place. The public Python wrapper returns a dictionary with b (opinions) and edges (edge list).

#define PRINT_FEEDS_DOC Print the feeds on the screen.

#define DESTROY_NETWORK_DOC Destroy Network.

// Legacy documentation: set_network is not registered on the current C type.
// This macro does not describe the current Dynamics constructor.
#define SET_NETWORK_DOC Legacy documentation for the unregistered set_network method.\n\
Set the network for the dynamics simulation.\n\
\n\
    Args:\n\
        vertexCount (int): Number of nodes in the network.\n\
        edges (array_like): An array of edges.\n\
        directed (bool): Whether the edges are directed or not. Default is False.\n\
        b (ndarray): A 1D numpy array containing the b values.

// #define RESET_VARIABLES_DOC Reset variables.
#define SET_POSTING_FILTER_DOC _set_posting_filter(self, posting_filter)\n\
Set posting filter (one-dimensional integer array_like, one value per vertex).\n\
Copies per-node native filter identifiers and replaces any sampled posting configuration. Activate by passing the integer selector "CUSTOM" (5) as posting_filter during simulation.\n\
This private C setter does not accept callables or ProbabilityTable objects; use the public set_posting_filter method for those inputs.\n\
Returns: None.

#define SET_RECEIVING_FILTER_DOC _set_receiving_filter(self, receiving_filter)\n\
Set receiving filter (one-dimensional integer array_like, one value per vertex).\n\
Copies per-node native filter identifiers and replaces any sampled receiving configuration. Activate by passing the integer selector "CUSTOM" (5) as receiving_filter during simulation.\n\
This private C setter does not accept callables or ProbabilityTable objects; use the public set_receiving_filter method for those inputs.\n\
Returns: None.

#define FORCE_DEALLOC_DOC Clean the memory. Returns: None.

#define SET_STUBBORN_DOC _set_stubborn(self, stubborn)\n\
Set nodes that never change their opinions (one-dimensional integer array_like, one value per vertex).\n\
Zero marks a non-stubborn node; a nonzero value marks a stubborn node. Copies the flags into the simulation state.\n\
Returns: None.
