import numpy as np 
import matplotlib.pyplot as plt 
from scipy.stats import gaussian_kde
import matplotlib.colors as mcolors
import matplotlib.cm as cm
import igraph as ig
import doces as od
from tqdm import tqdm

folder_out = "./"

vertex_count = 20000
k = 80
p = k/float(vertex_count)
g = ig.Graph()
g = g.Erdos_Renyi(vertex_count, p)
g = g.components(mode=ig.WEAK).giant()
# g.to_directed()
g = g.simplify()
edges = np.array(g.get_edgelist())

verbose = True
directed = False #True
b = np.random.random(size=vertex_count)
b = b * 2 - 1


for i in range(100):
    print(str(i) + ":")
    rand_seed = np.random.randint(0, 1000000)
    print("seed =", rand_seed)
    simulator = od.Opinion_dynamics(vertex_count = vertex_count, edges=edges, directed=directed, verbose=True)

    for time_step in tqdm(range(100)):
        out = simulator.simulate_dynamics(number_of_iterations = 10000,
                                        min_opinion = -1, 
                                        max_opinion = 1,
                                        phi = 1.4726215563702154,
                                        mu = 0.2,
                                        delta = 0.1,
                                        posting_filter = od.UNIFORM, 
                                        receiving_filter = od.STRETCHED_HALF_COSINE,
                                        rewire = True,
                                        b=b,
                                        feed_size = 1,
                                        verbose = False)
        
        b = out['b']
        