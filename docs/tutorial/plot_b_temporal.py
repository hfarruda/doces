import numpy as np 
import matplotlib.pyplot as plt 
from scipy.stats import gaussian_kde
import matplotlib.colors as mcolors
import matplotlib.cm as cm
import igraph as ig
import doces as od
from tqdm import tqdm

folder_out = "./"

vertex_count = 1000
k = 8
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

rand_seed = np.random.randint(0, 1000000)
print("seed =", rand_seed)
simulator = od.Opinion_dynamics(vertex_count = vertex_count, edges=edges, directed=directed, verbose=verbose)

fig = plt.figure(figsize=(6,4)) 
ax = fig.gca()

step = 1000000
time_steps = list(range(15))#list(range(1000))#np.linspace(0,999,50, dtype=int)#list(range(15))

colorparams = [(t+1) * step for t in time_steps]
# Choose a colormap
colormap = cm.cividis
normalize = mcolors.Normalize(vmin=np.min(colorparams), vmax=np.max(colorparams))

verbose = False
for time_step in tqdm(time_steps):
    out = simulator.simulate_dynamics(number_of_iterations = step,
                                    min_opinion = -1, 
                                    max_opinion = 1,
                                    phi = 1.4726215563702154,
                                    mu = 1,
                                    delta = 0.1,
                                    posting_filter = od.UNIFORM, 
                                    receiving_filter = od.STRETCHED_HALF_COSINE,
                                    rewire = True,
                                    b=b,
                                    feed_size = 1,
                                    verbose = verbose)
    
    b = out['b']
    kde = gaussian_kde(b, bw_method=0.25)
    x_grid = np.linspace(-1,1,150)
    y = kde.evaluate(x_grid)
    color = colormap(normalize((time_step+1)*step),alpha=0.9)
    ax.plot(x_grid, y, color=color)

s_map = cm.ScalarMappable(norm=normalize, cmap=colormap)
s_map.set_array(colorparams)

halfdist = (colorparams[1] - colorparams[0])/2.0
boundaries = np.linspace(colorparams[0] - halfdist, colorparams[-1] + halfdist, len(colorparams) + 1)

cbar = fig.colorbar(s_map, spacing='proportional', boundaries=boundaries, format='%2.2g')
cbarlabel = "Number of iterations"
cbar.set_label(cbarlabel, fontsize=12)

ax.set_xlabel("b")
ax.set_ylabel("density")
ax.set_xlim(-1,1)
# ax.set_ylim(0, 1)
plt.tight_layout()
plt.savefig(folder_out + "b_evolution.pdf")
plt.close()
