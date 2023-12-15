import numpy as np
import doces
# import gc 
# gc.set_debug(gc.DEBUG_LEAK)

vertex_count = 4
# edges = np.random.randint(0, vertex_count, (vertex_count*4, 2))
# edges = np.array([(0, 1), (1, 2), (0, 3), (1, 3), (2, 3), (2, 4), (3, 4), (0, 4), (4, 5), (3, 5), (1, 5), (1, 6), (3, 6), (4, 6), (5, 7), (4, 7), (0, 7), (5, 8), (4, 8), (3, 8), (3, 9), (7, 9), (0, 9)])
edges = np.array([(0, 1), (1, 2), (0, 3), (1, 3), (2, 3)])
verbose = True#True
directed = True #False#

rand_seed = np.random.randint(0, 1000000)# 263657#
print("seed =", rand_seed)
simulator = doces.Opinion_dynamics(vertex_count=vertex_count, edges=edges, directed=directed, verbose=verbose)

b = [-0.7812723, -0.5168539, 0.48190793, -0.41460833] #np.random.rand(vertex_count) * 2 - 1

number_of_iterations = 10000

# print("b (Python):", b)
posting_filter = np.array([doces.COSINE for _ in range(vertex_count)])
simulator.set_posting_filter(posting_filter = posting_filter)

receiving_filter = np.array([doces.STRETCHED_HALF_COSINE for _ in range(vertex_count)])
simulator.set_receiving_filter(receiving_filter = receiving_filter)

simulator.set_stubborn([0,1,1,0])

out = simulator.simulate_dynamics(number_of_iterations = number_of_iterations,
                                  min_opinion = -1, 
                                  max_opinion = 1,
                                  phi = 0.001,
                                  mu = 1,
                                  delta = 0.1,
                                  posting_filter = doces.CUSTOM, 
                                  receiving_filter = doces.CUSTOM,
                                  rewire = True,
                                  b=b,
                                  feed_size = 5,
                                  cascade_stats_output_file= "./test",
                                  verbose = verbose,
                                  rand_seed = rand_seed)

print("Feeds:")
simulator.print_feeds()
print(out)

print("-> Simulate the dynamics (2nd time).")
number_of_iterations = 1000#10
simulator = doces.Opinion_dynamics(vertex_count=vertex_count, edges=edges, directed=directed, verbose=verbose)

out = simulator.simulate_dynamics( 
                            number_of_iterations = number_of_iterations,
                            min_opinion = -1, 
                            max_opinion = 1,
                            phi = 0.001,
                            mu = 0.2, 
                            delta = 0.1,
                            posting_filter = doces.COSINE, 
                            receiving_filter = doces.COSINE,
                            rewire = False,
                            b=b,
                            feed_size = 5,
                            cascade_stats_output_file= "./test",
                            verbose = verbose)

print(out)
# print(simulator.get_cascade_stats_post_id2stats_dict())
del simulator

print("---> Deleted!!!!")

simulator = doces.Opinion_dynamics(vertex_count=vertex_count, edges=edges, directed=directed, verbose=True)


