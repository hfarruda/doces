"""Capture exact seeded results for comparison between builds on one platform.

Run this script with each installed DOCES build, outside the source checkout.
Pass an output path to save JSON, or omit it to write JSON to stdout. The C
engine uses platform-specific random generators, so compare matching platforms.
"""

import argparse
import json
from pathlib import Path

import numpy as np

import doces


VERTEX_COUNT = 8
EDGES = [
    [0, 1], [0, 3], [1, 2], [1, 4],
    [2, 3], [2, 5], [3, 4], [3, 6],
    [4, 5], [4, 7], [5, 6], [5, 0],
    [6, 7], [6, 1], [7, 0], [7, 2],
]
OPINIONS = [-0.875, -0.625, -0.375, -0.125, 0.125, 0.375, 0.625, 0.875]
FILTERS = (
    ("cosine", doces.COSINE),
    ("stretched_half_cosine", doces.STRETCHED_HALF_COSINE),
    ("uniform", doces.UNIFORM),
    ("half_cosine", doces.HALF_COSINE),
    ("random", doces.RANDOM_DISTR),
)
CASCADE_KEYS = (
    "post_id", "theta", "count", "cascade_size", "birth", "death",
    "live_posts", "user_opinion",
)


def new_dynamics(edges=None, directed=True):
    return doces.Opinion_dynamics(
        VERTEX_COUNT, EDGES if edges is None else edges,
        directed=directed, verbose=False,
    )


def simulate(dynamics, **overrides):
    parameters = dict(
        number_of_iterations=180,
        phi=0.25,
        mu=0.35,
        posting_filter=doces.COSINE,
        receiving_filter=doces.STRETCHED_HALF_COSINE,
        b=OPINIONS,
        feed_size=3,
        rewire=False,
        delta=0.125,
        verbose=False,
        rand_seed=271828,
    )
    parameters.update(overrides)
    return dynamics.simulate_dynamics(**parameters)


def capture(dynamics, result):
    return {
        "result": result,
        "rewiring_count": dynamics.rewiring_count,
        "cascade_stats": dynamics.get_cascade_stats_dict(),
        "post_id_to_stats": dynamics.get_cascade_stats_post_id2stats_dict(),
    }


def run_scenarios():
    snapshots = {}
    for directed in (True, False):
        graph_kind = "directed" if directed else "undirected"
        for name, selector in FILTERS:
            for rewire in (False, True):
                dynamics = new_dynamics(directed=directed)
                result = simulate(
                    dynamics, posting_filter=selector, receiving_filter=selector,
                    rewire=rewire,
                )
                key = "{}_{}_rewire_{}".format(graph_kind, name, rewire)
                snapshots[key] = capture(dynamics, result)

    dynamics = new_dynamics()
    dynamics.set_posting_filter([doces.COSINE, doces.UNIFORM] * 4)
    dynamics.set_receiving_filter(np.array([
        doces.HALF_COSINE, doces.STRETCHED_HALF_COSINE,
        doces.UNIFORM, doces.COSINE,
    ] * 2, dtype=np.int32))
    dynamics.set_stubborn(np.array([1, 0, 0, 1, 0, 0, 1, 0], dtype=np.int64))
    result = simulate(
        dynamics, posting_filter=doces.CUSTOM, receiving_filter=doces.CUSTOM,
        rewire=True,
    )
    snapshots["custom_stubborn_first"] = capture(dynamics, result)
    result = simulate(
        dynamics, number_of_iterations=90, b=None,
        posting_filter=doces.CUSTOM, receiving_filter=doces.CUSTOM,
        rewire=True, rand_seed=314159,
    )
    snapshots["custom_stubborn_resumed"] = capture(dynamics, result)
    result = simulate(
        dynamics, number_of_iterations=90, b=np.array(OPINIONS, dtype=np.float64),
        posting_filter=doces.UNIFORM, receiving_filter=doces.COSINE,
        rewire=True, rand_seed=161803,
    )
    snapshots["replaced_opinions_and_filters"] = capture(dynamics, result)
    return snapshots


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", type=Path)
    arguments = parser.parse_args()
    output = json.dumps(run_scenarios(), sort_keys=True, indent=2, allow_nan=False)
    if arguments.output is None:
        print(output)
    else:
        arguments.output.write_text(output + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
