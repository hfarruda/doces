import numpy as np 
import matplotlib.pyplot as plt 
from scipy.stats import gaussian_kde
import matplotlib.colors as mcolors
import matplotlib.cm as cm
import igraph as ig
import doces as od
from tqdm import tqdm
from scipy.stats import kurtosis
from scipy.stats import skew
from matplotlib.gridspec import GridSpec
import scipy.stats as st
from scipy.stats import gaussian_kde
import xnetwork as xnet

plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})

def average_neighbors_opinion(b, g):
    out = []
    b = np.array(b)
    for i in range(g.vcount()):
        neighbors = g.neighbors(i) # mode='out' is directed
        out.append(np.mean(b[neighbors]))
    return out

def bimodality_index(b):
    n = len(b)
    return (np.power(skew(b),2) + 1)/(kurtosis(b) + (3*np.power(n-1,2))/((n-2)*(n-3)))

def balance(b):
    b = np.array(b)
    c_1 = np.sum(b > 0)
    c_2 = np.sum(b < 0)
    return np.min([c_1,c_2])/np.max([c_1,c_2])


folder_out = "./"

vertex_count = 1000
k = 8
p = k/vertex_count
g = ig.Graph()
g = g.Erdos_Renyi(vertex_count, p)
g = g.components(mode=ig.WEAK).giant()
g = g.simplify()
# g.to_directed()
edges = g.get_edgelist()

verbose = True
directed = False #True
b = np.random.random(size=vertex_count)
b = b * 2 - 1

rand_seed = np.random.randint(0, 1000000)
print("seed =", rand_seed)
simulator = od.Opinion_dynamics(vertex_count = vertex_count, edges=edges, directed=directed, verbose=verbose)

fig = plt.figure(figsize=(6,4)) 
ax = fig.gca()

steps = 10000000

out = simulator.simulate_dynamics(number_of_iterations = steps,
                                min_opinion = -1., 
                                max_opinion = 1.,
                                phi = 1.473,
                                mu = 1.,
                                delta = 0.1,
                                posting_filter = od.UNIFORM, 
                                receiving_filter = od.STRETCHED_HALF_COSINE,
                                rewire = True,
                                b=b,
                                feed_size = 1,
                                verbose = verbose)
    
b = out['b']
print("BC:", bimodality_index(b))
print("Balance:", balance(b))

g = ig.Graph(out["edges"], directed = False)
g.vs['b'] = list(b)
g = g.components(mode=ig.WEAK).giant()
b = np.array(g.vs['b'])

xnet.igraph2xnet(g, "test.xnet")

xmin, xmax = -1., 1.
ymin, ymax = -1., 1.

# Peform the kernel density estimate
xx, yy = np.mgrid[xmin:xmax:0.01, ymin:ymax:0.01]
positions = np.vstack([xx.ravel(), yy.ravel()])
b_neighbors = average_neighbors_opinion(b, g)
values = np.vstack([b, b_neighbors])
kernel = st.gaussian_kde(values)
f_ = np.reshape(kernel(positions).T, xx.shape)

fig = plt.figure(figsize=(3.3,3))
gs = GridSpec(4,4)
ax_joint = fig.add_subplot(gs[1:4,0:3])
ax_marg_x = fig.add_subplot(gs[0,0:3])
ax_marg_y = fig.add_subplot(gs[1:4,3])

extent = [-1,1,-1,1]
ax_joint.imshow(f_.T, extent=extent, origin='lower', cmap=cm.inferno)
ax_joint.set_ylabel(r"$b_{NN}$")
ax_joint.set_xlabel(r"$b$")
# plt.xlim(-1, 1)
# plt.ylim(-1, 1)

x_grid = np.linspace(-1,1,150)
kde = gaussian_kde(b, bw_method=0.25)
y = kde.evaluate(x_grid)
ax_marg_x.plot(x_grid, y, color = "#404040")
ax_marg_x.set_xlim(-1,1)

kde = gaussian_kde(b_neighbors, bw_method=0.25)
y = kde.evaluate(x_grid)
ax_marg_y.plot(y, x_grid, color = "#404040")
ax_marg_y.set_ylim(-1,1)

ax_marg_x.xaxis.set_visible(False)
ax_marg_x.yaxis.set_visible(False)
ax_marg_x.spines['right'].set_visible(False)
ax_marg_x.spines['left'].set_visible(False)
ax_marg_x.spines['top'].set_visible(False)

ax_marg_y.xaxis.set_visible(False)
ax_marg_y.yaxis.set_visible(False)
ax_marg_y.spines['right'].set_visible(False)
ax_marg_y.spines['bottom'].set_visible(False)
ax_marg_y.spines['top'].set_visible(False)

plt.tight_layout()

pos1 = ax_joint.get_position(original=False)
pos0 = ax_marg_x.get_position(original=False)
ax_marg_x.set_position([pos1.x0, pos0.y0, pos1.width, pos0.height])

pos1 = ax_joint.get_position(original=False)
pos0 = ax_marg_y.get_position(original=False)
ax_marg_y.set_position([pos0.x0, pos1.y0, pos0.width, pos1.height])

name_out = "echo_chamber.pdf"
plt.savefig(name_out)
plt.close()

print("rewire count:", simulator.rewiring_count)


