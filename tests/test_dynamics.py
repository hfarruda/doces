"""Behavioral checks."""

import csv
from pathlib import Path
import tempfile
import unittest

import numpy as np

import doces
from simulation_snapshot import (
    CASCADE_KEYS, EDGES, FILTERS, OPINIONS, VERTEX_COUNT,
    capture, new_dynamics, run_scenarios, simulate,
)


class DynamicsCompatibilityTests(unittest.TestCase):
    def test_public_version(self):
        import doces_core

        self.assertIsInstance(doces.__version__, str)
        self.assertEqual(doces.__version__, doces_core.__version__)

    def test_public_constants(self):
        self.assertEqual([selector for _, selector in FILTERS], list(range(5)))
        self.assertEqual(doces.CUSTOM, 5)

    def test_result_contract_and_fixed_network(self):
        dynamics = new_dynamics()
        initial_edges = dynamics.edge_list
        result = simulate(dynamics)
        self.assertEqual(set(result), {"b", "edges"})
        self.assertIsInstance(result["b"], list)
        self.assertEqual(len(result["b"]), VERTEX_COUNT)
        self.assertTrue(all(type(value) is float for value in result["b"]))
        self.assertTrue(all(-1 <= value <= 1 for value in result["b"]))
        self.assertEqual(result["b"], dynamics.opinions)
        self.assertIsInstance(result["edges"], list)
        self.assertTrue(all(
            isinstance(edge, list) and len(edge) == 2
            and all(type(vertex) is int for vertex in edge)
            for edge in result["edges"]
        ))
        self.assertEqual(result["edges"], initial_edges)
        self.assertEqual(dynamics.rewiring_count, 0)

    def test_seeded_scenarios_are_exactly_reproducible(self):
        self.assertEqual(run_scenarios(), run_scenarios())

    def test_edge_array_dtypes_and_layouts(self):
        expected_dynamics = new_dynamics()
        expected = capture(expected_dynamics, simulate(expected_dynamics))
        edges = np.array(EDGES, dtype=np.int64)
        strided = np.repeat(edges, 2, axis=0)[::2]
        reversed_storage = edges[::-1].copy()[::-1]
        variants = {
            "list": EDGES,
            "int32": edges.astype(np.int32),
            "int64": edges,
            "fortran": np.asfortranarray(edges),
            "strided": strided,
            "negative_stride": reversed_storage,
            "flat": edges.reshape(-1),
            "byte_swapped": edges.astype(edges.dtype.newbyteorder("S")),
        }
        for name, variant in variants.items():
            with self.subTest(layout=name):
                dynamics = new_dynamics(edges=variant)
                self.assertEqual(capture(dynamics, simulate(dynamics)), expected)

    def test_opinion_array_dtypes_and_layouts(self):
        expected_dynamics = new_dynamics()
        expected = capture(expected_dynamics, simulate(expected_dynamics))
        opinions = np.array(OPINIONS, dtype=np.float32)
        variants = {
            "list": OPINIONS,
            "float32": opinions,
            "float64": opinions.astype(np.float64),
            "strided": np.repeat(opinions, 2)[::2],
            "negative_stride": opinions[::-1].copy()[::-1],
            "byte_swapped": opinions.astype(opinions.dtype.newbyteorder("S")),
        }
        for name, variant in variants.items():
            with self.subTest(layout=name):
                original = np.array(variant, copy=True)
                dynamics = new_dynamics()
                self.assertEqual(capture(dynamics, simulate(dynamics, b=variant)), expected)
                np.testing.assert_array_equal(variant, original)

    def test_native_array_conversions_preserve_strided_values(self):
        # Pass views directly to C as well: the public wrapper makes its own copy.
        import doces_core

        edges = np.array(EDGES, dtype=np.int32)
        opinions = np.array(OPINIONS, dtype=np.float32)
        parameters = dict(
            number_of_iterations=180, min_opinion=-1, max_opinion=1,
            phi=0.25, mu=0.35, delta=0.125, posting_filter=doces.COSINE,
            receiving_filter=doces.STRETCHED_HALF_COSINE, rewire=False,
            feed_size=3, verbose=False, rand_seed=271828,
        )
        expected = new_dynamics()
        result = simulate(expected)
        for edge_values in (np.asfortranarray(edges), np.repeat(edges, 2, axis=0)[::2]):
            with self.subTest(strides=edge_values.strides):
                dynamics = doces_core.Dynamics(VERTEX_COUNT, edge_values, True, False)
                dynamics._simulate_dynamics(b=np.repeat(opinions, 2)[::2], **parameters)
                self.assertEqual(dynamics.opinions, result["b"])
                self.assertEqual(dynamics.edge_list, result["edges"])
                self.assertEqual(dynamics.post_thetas, expected.post_thetas)

    def test_positional_arguments_match_keyword_arguments(self):
        positional = new_dynamics()
        result = positional.simulate_dynamics(
            180, 0.25, 0.35, doces.COSINE, doces.STRETCHED_HALF_COSINE,
            OPINIONS, 3, False, None, -1, 1, 0.125, False, 271828,
        )
        keyword = new_dynamics()
        self.assertEqual(capture(positional, result), capture(keyword, simulate(keyword)))

    def test_default_options_match_explicit_values(self):
        defaults = new_dynamics()
        result = defaults.simulate_dynamics(
            180, 0.25, 0.35, doces.COSINE, doces.STRETCHED_HALF_COSINE,
            b=OPINIONS, verbose=False, rand_seed=271828,
        )
        explicit = new_dynamics()
        expected = simulate(
            explicit, feed_size=5, rewire=True, cascade_stats_output_file=None,
            min_opinion=-1, max_opinion=1, delta=0.1,
        )
        self.assertEqual(capture(defaults, result), capture(explicit, expected))

    def test_custom_uniform_filters_match_builtin(self):
        builtin = new_dynamics()
        expected = simulate(
            builtin, posting_filter=doces.UNIFORM, receiving_filter=doces.UNIFORM,
        )
        custom = new_dynamics()
        custom.set_posting_filter([doces.UNIFORM] * VERTEX_COUNT)
        custom.set_receiving_filter(np.full(VERTEX_COUNT, doces.UNIFORM, dtype=np.int32))
        result = simulate(custom, posting_filter=doces.CUSTOM, receiving_filter=doces.CUSTOM)
        self.assertEqual(capture(custom, result), capture(builtin, expected))

    def test_stubborn_agents_keep_initial_opinions(self):
        dynamics = new_dynamics()
        stubborn = np.array([1, 0, 0, 1, 0, 0, 1, 0], dtype=np.int32)
        dynamics.set_stubborn(stubborn)
        result = simulate(dynamics, rewire=True)
        for index in np.flatnonzero(stubborn):
            self.assertEqual(result["b"][index], OPINIONS[index])
        self.assertTrue(any(
            result["b"][index] != OPINIONS[index]
            for index in np.flatnonzero(stubborn == 0)
        ))

    def test_rewiring_occurs_and_preserves_valid_edges(self):
        dynamics = new_dynamics()
        result = simulate(
            dynamics, number_of_iterations=1000, posting_filter=doces.UNIFORM,
            receiving_filter=doces.UNIFORM, rewire=True,
        )
        self.assertGreater(dynamics.rewiring_count, 0)
        self.assertEqual(len(result["edges"]), len(EDGES))
        for source, target in result["edges"]:
            self.assertTrue(0 <= source < VERTEX_COUNT)
            self.assertTrue(0 <= target < VERTEX_COUNT)
            self.assertNotEqual(source, target)

    def test_cascade_accessors_and_cache_refresh_on_resume(self):
        dynamics = new_dynamics()
        simulate(dynamics, posting_filter=doces.UNIFORM, receiving_filter=doces.UNIFORM)
        first_stats = dynamics.get_cascade_stats_dict()
        self.assertEqual(tuple(first_stats), CASCADE_KEYS)
        self.assertIs(first_stats, dynamics.get_cascade_stats_dict())
        first_by_id = dynamics.get_cascade_stats_post_id2stats_dict()
        self.assertIs(first_by_id, dynamics.get_cascade_stats_post_id2stats_dict())
        self.assertGreater(len(first_stats["post_id"]), 0)
        for index, post_id in enumerate(first_stats["post_id"]):
            self.assertEqual(first_by_id[post_id], {
                key: first_stats[key][index] for key in CASCADE_KEYS if key != "post_id"
            })
        for values in first_stats.values():
            self.assertIsInstance(values, list)
            self.assertEqual(len(values), len(first_stats["post_id"]))

        simulate(
            dynamics, b=None, mu=1, posting_filter=doces.UNIFORM,
            receiving_filter=doces.UNIFORM, rand_seed=314159,
        )
        resumed_stats = dynamics.get_cascade_stats_dict()
        self.assertIsNot(first_stats, resumed_stats)
        self.assertIsNot(first_by_id, dynamics.get_cascade_stats_post_id2stats_dict())
        self.assertGreater(len(resumed_stats["post_id"]), len(first_stats["post_id"]))
        self.assertEqual(
            resumed_stats["post_id"][:len(first_stats["post_id"])], first_stats["post_id"],
        )

    def test_cascade_csv_output(self):
        with tempfile.TemporaryDirectory(prefix="doces-test-") as directory:
            output = Path(directory) / "cascade"
            dynamics = new_dynamics()
            simulate(dynamics, cascade_stats_output_file=str(output))
            with output.with_suffix(".csv").open(newline="", encoding="utf-8") as stream:
                reader = csv.DictReader(stream)
                rows = list(reader)
                self.assertEqual(tuple(reader.fieldnames), CASCADE_KEYS)
            stats = dynamics.get_cascade_stats_dict()
            self.assertEqual([int(row["post_id"]) for row in rows], stats["post_id"])
            for key in ("count", "cascade_size", "birth", "death", "live_posts"):
                self.assertEqual([int(row[key]) for row in rows], stats[key])

    def test_invalid_opinion_dimensions_and_lengths_raise(self):
        for opinions in ([0.0] * (VERTEX_COUNT - 1), np.zeros((VERTEX_COUNT, 1))):
            with self.subTest(shape=np.shape(opinions)):
                dynamics = new_dynamics()
                with self.assertRaises(TypeError):
                    simulate(dynamics, b=opinions)

    def test_invalid_setter_dimensions_and_lengths_raise(self):
        for setter in ("set_posting_filter", "set_receiving_filter", "set_stubborn"):
            for values in ([0] * (VERTEX_COUNT - 1), np.zeros((VERTEX_COUNT, 1), dtype=int)):
                with self.subTest(setter=setter, shape=np.shape(values)):
                    dynamics = new_dynamics()
                    with self.assertRaises(TypeError):
                        getattr(dynamics, setter)(values)


if __name__ == "__main__":
    unittest.main()
