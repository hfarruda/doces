"""Sample Python probabilities for per-node posting, receiving, and rewiring.

Run with an installed DOCES: python docs/tutorial/custom_filters.py
This example needs only NumPy and DOCES and does not write output files.
"""

import numpy as np

import doces


def main():
    vertex_count = 8
    edges = [
        (node, (node + offset) % vertex_count)
        for node in range(vertex_count)
        for offset in (1, 3)
    ]
    opinions = np.linspace(-0.9, 0.9, vertex_count)
    # Functions take absolute, unnormalized differences. With opinions in
    # [-1, 1], the table must cover [0, 2]. C interpolates between samples.
    grid = np.linspace(0.0, 2.0, 1001)

    def selective_posting(difference):
        return np.exp(-2.0 * difference**2)

    broad_receiving = doces.ProbabilityTable.from_function(
        lambda difference: 1.0 - 0.4 * difference, grid
    )
    # Tables may also come directly from measured or hand-selected samples.
    cautious_rewiring = doces.ProbabilityTable(
        differences=[0.0, 0.5, 1.0, 1.5, 2.0],
        probabilities=[0.0, 0.0, 0.05, 0.25, 0.6],
    )
    # "linear" (the default) joins neighboring samples with a straight line.
    # "previous" holds each probability until the next knot, giving an exact
    # step here: probability 1 below 0.5, and 0 at and above 0.5.
    step_posting = doces.ProbabilityTable.from_function(
        lambda difference: 1.0 if difference < 0.5 else 0.0,
        grid=[0.0, 0.5, 2.0],
        interpolation="previous",
    )
    linear_posting = doces.ProbabilityTable(
        [0.0, 0.5, 2.0], [1.0, 0.0, 0.0], interpolation="linear"
    )
    assert step_posting(0.25) == 1.0
    assert step_posting(0.5) == 0.0
    assert linear_posting(0.25) == 0.5
    simulator = doces.Opinion_dynamics(
        vertex_count, edges, directed=True, verbose=False
    )
    # Lists assign one choice per node. Repeated callables are sampled once
    # during this setter call; no Python function runs inside the C loop.
    simulator.set_posting_filter(
        [selective_posting, doces.UNIFORM, step_posting, linear_posting] * 2,
        grid=grid,
    )
    simulator.set_receiving_filter([broad_receiving, doces.COSINE] * 4)
    # Receiving preserves DOCES's existing convention: the posting node's
    # assignment selects the probability for distribution to its followers.
    # Rewiring uses the assignment of the node changing its connection.
    simulator.set_rewiring_filter(
        [cautious_rewiring, doces.REVERSED_HALF_COSINE] * 4
    )
    simulator.set_stubborn([1, 0] * 4)

    settings = dict(
        number_of_iterations=2000,
        phi=0.1,
        mu=0.5,
        posting_filter=doces.CUSTOM,
        receiving_filter=doces.CUSTOM,
        feed_size=5,
        min_opinion=-1,
        max_opinion=1,
        verbose=False,
        rand_seed=1729,
    )
    initial_edges = simulator.edge_list
    fixed = simulator.simulate_dynamics(b=opinions, rewire=False, **settings)
    assert fixed["edges"] == initial_edges
    assert simulator.rewiring_count == 0
    print("rewire=False: edges unchanged, including for stubborn nodes.")

    # Resume the same simulation with the configured rewiring probabilities.
    adaptive = simulator.simulate_dynamics(b=None, rewire=True, **settings)
    print("rewire=True: rewiring events:", simulator.rewiring_count)
    print("Final opinions:", adaptive["b"])

    # To restore the original rewiring probability for every node:
    simulator.set_rewiring_filter(doces.REVERSED_HALF_COSINE)
    # Without a rewiring setter, rewire=True already uses this built-in.
    # phi affects the built-in cosine filters, not sampled probabilities;
    # rebuild a table to change a parameter captured by a Python function.


if __name__ == "__main__":
    main()
