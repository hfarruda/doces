"""Interpolation contracts in Python and through the installed C engine."""

import unittest

import numpy as np

import doces
from simulation_snapshot import VERTEX_COUNT, capture, new_dynamics, simulate


def constant(probability):
    return doces.ProbabilityTable([0, 2], [probability, probability])


def frozen_ring():
    dynamics = new_dynamics(
        edges=[[node, (node + 1) % VERTEX_COUNT] for node in range(VERTEX_COUNT)]
    )
    dynamics.set_stubborn([1] * VERTEX_COUNT)
    return dynamics


class ProbabilityInterpolationTests(unittest.TestCase):
    def test_linear_default_and_explicit_mode_match(self):
        implicit = doces.ProbabilityTable([0, 0.5, 2], [1, 0.25, 0])
        explicit = doces.ProbabilityTable(
            [0, 0.5, 2], [1, 0.25, 0], interpolation="linear"
        )
        self.assertEqual(implicit.interpolation, "linear")
        queries = [0, 0.25, 0.5, 1.25, 2]
        np.testing.assert_array_equal(explicit(queries), [1, 0.625, 0.25, 0.125, 0])
        np.testing.assert_array_equal(implicit(queries), explicit(queries))

    def test_previous_switches_at_each_knot(self):
        table = doces.ProbabilityTable(
            [0, 0.5, 1.25, 2], [1, 0, 0.75, 0.25], interpolation="previous"
        )
        queries = [
            0, np.nextafter(0.5, 0), 0.5, np.nextafter(0.5, 1),
            np.nextafter(1.25, 0), 1.25, np.nextafter(1.25, 2),
            np.nextafter(2.0, 0), 2,
        ]
        expected = [1, 1, 0, 0, 0, 0.75, 0.75, 0.75, 0.25]
        np.testing.assert_array_equal(table(queries), expected)
        for difference, probability in zip(queries, expected):
            with self.subTest(difference=difference):
                self.assertEqual(table(difference), probability)

    def test_previous_preserves_query_shape(self):
        table = doces.ProbabilityTable(
            [0, 0.5, 2], [1, 0, 0.25], interpolation="previous"
        )
        np.testing.assert_array_equal(
            table(np.array([[0, 0.25], [0.5, 2]])), [[1, 1], [0, 0.25]]
        )
        self.assertEqual(table(np.empty((0, 2))).shape, (0, 2))

    def test_modes_do_not_allow_extrapolation(self):
        for mode in ("linear", "previous"):
            table = doces.ProbabilityTable([0.25, 2], [1, 0], interpolation=mode)
            for query in (0, np.nextafter(2.0, 3), np.nan, np.inf, [0.5, 3]):
                with self.subTest(mode=mode, query=query):
                    with self.assertRaises(ValueError):
                        table(query)

    def test_interpolation_property_is_read_only(self):
        table = doces.ProbabilityTable([0, 2], [1, 0], interpolation="previous")
        self.assertEqual(table.interpolation, "previous")
        with self.assertRaises(AttributeError):
            table.interpolation = "linear"

    def test_invalid_modes_fail_before_sampling(self):
        for mode in ("nearest", "Previous", "", None, 0, [], np.array(["previous"])):
            with self.subTest(mode=mode):
                with self.assertRaises(ValueError):
                    doces.ProbabilityTable([0, 2], [1, 0], interpolation=mode)
                calls = []

                def probability(difference):
                    calls.append(difference)
                    return 1

                with self.assertRaises(ValueError):
                    doces.ProbabilityTable.from_function(
                        probability, [0, 2], interpolation=mode
                    )
                self.assertEqual(calls, [])

    def test_from_function_samples_knots_and_retains_previous_mode(self):
        calls = []

        def step(difference):
            calls.append(difference)
            return float(difference < 0.5)

        table = doces.ProbabilityTable.from_function(
            step, [0, 0.5, 2], interpolation="previous"
        )
        self.assertEqual(table.interpolation, "previous")
        self.assertEqual(calls, [0, 0.5, 2])
        np.testing.assert_array_equal(table([0, 0.25, 0.5, 1, 2]), [1, 1, 0, 0, 0])
        self.assertEqual(calls, [0, 0.5, 2])


class InterpolationDynamicsTests(unittest.TestCase):
    def test_previous_posting_holds_probability_between_knots(self):
        dynamics = new_dynamics()
        dynamics.set_stubborn([1] * VERTEX_COUNT)
        dynamics.set_posting_filter(doces.ProbabilityTable(
            [0, 2], [1, 0], interpolation="previous"
        ))
        baseline = new_dynamics()
        baseline.set_stubborn([1] * VERTEX_COUNT)
        # Frozen fixture opinions lie strictly inside [-1, 1], so no possible
        # generated post reaches the final knot at difference 2.
        result = simulate(dynamics, mu=1, posting_filter=doces.CUSTOM,
                          receiving_filter=doces.UNIFORM)
        expected = simulate(baseline, mu=1, posting_filter=doces.UNIFORM,
                            receiving_filter=doces.UNIFORM)
        self.assertEqual(capture(dynamics, result), capture(baseline, expected))

    def test_previous_receiving_switches_at_float32_threshold(self):
        threshold = np.float32(0.5)
        cases = (
            (np.nextafter(threshold, np.float32(0)), 1),
            (threshold, 0),
            (np.nextafter(threshold, np.float32(1)), 0),
        )
        for difference, probability in cases:
            with self.subTest(difference=difference, probability=probability):
                dynamics, baseline = frozen_ring(), frozen_ring()
                dynamics.set_receiving_filter(doces.ProbabilityTable(
                    [0, 0.5, 2], [1, 0, 0], interpolation="previous"
                ))
                baseline.set_receiving_filter(constant(probability))
                options = dict(b=[0, float(difference)] * (VERTEX_COUNT // 2),
                               mu=1, posting_filter=doces.UNIFORM,
                               receiving_filter=doces.CUSTOM)
                result = simulate(dynamics, **options)
                expected = simulate(baseline, **options)
                self.assertEqual(capture(dynamics, result), capture(baseline, expected))
                # This checks receipt itself, since stubborn opinions cannot move.
                new_post_counts = dynamics.post_posted_counts[VERTEX_COUNT * 3:]
                self.assertTrue(new_post_counts)
                self.assertEqual(set(new_post_counts), {1 + probability})

    def test_per_node_tables_can_use_different_modes(self):
        previous = doces.ProbabilityTable([0, 1, 2], [0, 1, 0], interpolation="previous")
        linear = doces.ProbabilityTable([0, 1, 2], [0, 1, 0], interpolation="linear")
        dynamics, baseline = frozen_ring(), frozen_ring()
        dynamics.set_receiving_filter([previous, linear] * (VERTEX_COUNT // 2))
        # Every edge joins opinions 0 and 0.5: the previous table gives zero,
        # and the linear table gives exactly one half.
        baseline.set_receiving_filter([constant(0), constant(0.5)] * (VERTEX_COUNT // 2))
        options = dict(b=[0, 0.5] * (VERTEX_COUNT // 2), mu=1,
                       posting_filter=doces.UNIFORM, receiving_filter=doces.CUSTOM)
        result = simulate(dynamics, **options)
        expected = simulate(baseline, **options)
        self.assertEqual(capture(dynamics, result), capture(baseline, expected))
        self.assertEqual(set(dynamics.post_posted_counts[VERTEX_COUNT * 3:]), {1, 2})

    def test_previous_rewiring_holds_zero_between_knots(self):
        outputs = {}
        for mode in ("linear", "previous"):
            dynamics = new_dynamics()
            dynamics.set_stubborn([1] * VERTEX_COUNT)
            dynamics.set_rewiring_filter(doces.ProbabilityTable(
                [0, 2], [0, 1], interpolation=mode
            ))
            initial_edges = dynamics.edge_list
            result = simulate(dynamics, number_of_iterations=1000, mu=1,
                              posting_filter=doces.UNIFORM,
                              receiving_filter=doces.UNIFORM, rewire=True)
            outputs[mode] = dynamics.rewiring_count
            if mode == "previous":
                self.assertEqual(result["edges"], initial_edges)
        self.assertEqual(outputs["previous"], 0)
        self.assertGreater(outputs["linear"], 0)

    def test_native_pair_and_explicit_linear_payloads_match_for_every_role(self):
        for role in ("posting", "receiving", "rewiring"):
            with self.subTest(role=role):
                outputs = []
                for explicit in (False, True):
                    dynamics = new_dynamics()
                    table = ([0, 0.5, 2], [1, 0.25, 0.75])
                    if explicit:
                        table += ("linear",)
                    dynamics._set_filter_configuration(
                        role, [-1] * VERTEX_COUNT, [table]
                    )
                    options = dict(posting_filter=doces.UNIFORM,
                                   receiving_filter=doces.UNIFORM,
                                   rewire=role == "rewiring")
                    if role != "rewiring":
                        options[role + "_filter"] = doces.CUSTOM
                    outputs.append(capture(dynamics, simulate(dynamics, **options)))
                self.assertEqual(outputs[0], outputs[1])

    def test_invalid_native_modes_leave_existing_configuration_intact(self):
        for role in ("posting", "receiving", "rewiring"):
            with self.subTest(role=role):
                dynamics, baseline = new_dynamics(), new_dynamics()
                original = doces.ProbabilityTable(
                    [0, 0.5, 2], [1, 0, 0.75], interpolation="previous"
                )
                for instance in (dynamics, baseline):
                    getattr(instance, "set_" + role + "_filter")(original)
                for mode in ("nearest", "Previous", "previous\0linear", None, 0, []):
                    with self.subTest(mode=mode):
                        with self.assertRaises(ValueError):
                            dynamics._set_filter_configuration(
                                role, [-1] * VERTEX_COUNT,
                                [([0, 2], [0, 0], mode)],
                            )
                options = dict(posting_filter=doces.UNIFORM,
                               receiving_filter=doces.UNIFORM,
                               rewire=role == "rewiring")
                if role != "rewiring":
                    options[role + "_filter"] = doces.CUSTOM
                result = simulate(dynamics, **options)
                expected = simulate(baseline, **options)
                self.assertEqual(capture(dynamics, result), capture(baseline, expected))


if __name__ == "__main__":
    unittest.main()
