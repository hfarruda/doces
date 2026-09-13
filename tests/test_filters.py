"""Behavioral checks for sampled probabilities and the global rewiring switch."""

import gc
import unittest
import warnings
import weakref

import numpy as np

import doces
from simulation_snapshot import (
    EDGES, OPINIONS, VERTEX_COUNT, capture, new_dynamics, simulate,
)


def constant(probability, maximum=2.0):
    return doces.ProbabilityTable([0.0, maximum], [probability, probability])


class ProbabilityTableTests(unittest.TestCase):
    def test_interpolation_at_knots_and_between_uneven_samples(self):
        table = doces.ProbabilityTable([0.0, 0.5, 2.0], [1.0, 0.25, 0.0])
        np.testing.assert_array_equal(
            table([0.0, 0.25, 0.5, 1.25, 2.0]),
            [1.0, 0.625, 0.25, 0.125, 0.0],
        )
        self.assertEqual(table(0.5), 0.25)

    def test_arrays_are_owned_and_read_only(self):
        differences = np.array([0.0, 0.5, 2.0])
        probabilities = np.array([1.0, 0.25, 0.0])
        table = doces.ProbabilityTable(differences, probabilities)
        differences[:] = 99
        probabilities[:] = 0
        self.assertEqual(table(0.25), 0.625)
        for values in (table.differences, table.probabilities):
            self.assertEqual(values.dtype, np.dtype("float64"))
            self.assertFalse(values.flags.writeable)
            with self.assertRaises(ValueError):
                values[0] = 0.5
            with self.assertRaises(ValueError):
                values.setflags(write=True)

    def test_strided_and_byte_swapped_input(self):
        values = np.array([0.0, 0.5, 2.0])
        variants = (
            np.repeat(values, 2)[::2],
            values[::-1].copy()[::-1],
            values.astype(values.dtype.newbyteorder("S")),
        )
        for differences in variants:
            with self.subTest(strides=differences.strides, dtype=differences.dtype):
                table = doces.ProbabilityTable(differences, [1.0, 0.25, 0.0])
                self.assertEqual(table(0.25), 0.625)

    def test_invalid_tables_are_rejected(self):
        cases = (
            ([], []), ([0], [1]), ([0, 2], [1]),
            ([[0, 2]], [1, 0]), ([0, 2], [[1, 0]]),
            ([0, 0, 2], [1, 0.5, 0]), ([2, 0], [1, 0]),
            ([-1, 2], [1, 0]), ([0, np.nan], [1, 0]),
            ([0, np.inf], [1, 0]), ([0, 2], [np.nan, 0]),
            ([0, 2], [1, np.inf]), ([0, 2], [-0.01, 0]),
            ([0, 2], [1.01, 0]), ([0, 2j], [1, 0]),
            ([0, 2], [1j, 0]), (["0", "2"], [1, 0]),
        )
        for differences, probabilities in cases:
            with self.subTest(differences=differences, probabilities=probabilities):
                with self.assertRaises((TypeError, ValueError)):
                    doces.ProbabilityTable(differences, probabilities)

    def test_queries_cannot_extrapolate_or_contain_nonfinite_values(self):
        table = constant(0.5)
        for difference in (-0.01, 2.01, np.nan, np.inf, [0, 3]):
            with self.subTest(difference=difference):
                with self.assertRaises(ValueError):
                    table(difference)

    def test_function_is_sampled_once_and_parameters_are_frozen(self):
        state = {"probability": 0.25}
        calls = []

        def probability(difference):
            calls.append(difference)
            return state["probability"]

        table = doces.ProbabilityTable.from_function(probability, [0, 0.5, 2])
        self.assertEqual(calls, [0, 0.5, 2])
        state["probability"] = 0.75
        self.assertEqual(table(1), 0.25)
        self.assertEqual(len(calls), 3)

    def test_sampling_rejects_invalid_results_and_preserves_exceptions(self):
        for value in (-0.1, 1.1, np.nan, np.inf, [0.5], 0.5j, "0.5"):
            with self.subTest(value=value):
                with self.assertRaises((TypeError, ValueError)):
                    doces.ProbabilityTable.from_function(lambda d: value, [0, 2])

        error = RuntimeError("probability sampling failed")

        def fail(difference):
            raise error

        with self.assertRaises(RuntimeError) as raised:
            doces.ProbabilityTable.from_function(fail, [0, 2])
        self.assertIs(raised.exception, error)


class SampledFilterDynamicsTests(unittest.TestCase):
    def test_reverse_half_cosine_constant_is_additive(self):
        self.assertEqual(doces.REVERSED_HALF_COSINE, 6)
        self.assertEqual(doces.CUSTOM, 5)

    def test_shared_one_tables_match_uniform_exactly(self):
        builtin = new_dynamics()
        expected = capture(builtin, simulate(
            builtin, posting_filter=doces.UNIFORM, receiving_filter=doces.UNIFORM,
        ))
        custom = new_dynamics()
        one = constant(1)
        custom.set_posting_filter(one)
        custom.set_receiving_filter(one)
        result = simulate(custom, posting_filter=doces.CUSTOM, receiving_filter=doces.CUSTOM)
        self.assertEqual(capture(custom, result), expected)

    def test_mixed_tables_and_builtins_match_existing_integer_assignments(self):
        posting = [doces.UNIFORM, doces.COSINE] * 4
        receiving = [doces.HALF_COSINE, doces.UNIFORM] * 4
        builtin = new_dynamics()
        builtin.set_posting_filter(posting)
        builtin.set_receiving_filter(receiving)
        expected = capture(builtin, simulate(
            builtin, posting_filter=doces.CUSTOM, receiving_filter=doces.CUSTOM,
        ))
        custom = new_dynamics()
        one = constant(1)
        custom.set_posting_filter([one, doces.COSINE] * 4)
        custom.set_receiving_filter([doces.HALF_COSINE, one] * 4)
        result = simulate(custom, posting_filter=doces.CUSTOM, receiving_filter=doces.CUSTOM)
        self.assertEqual(capture(custom, result), expected)

    def test_scalar_builtins_broadcast(self):
        dynamics = new_dynamics()
        dynamics.set_posting_filter(doces.COSINE)
        dynamics.set_receiving_filter(doces.UNIFORM)
        result = simulate(dynamics, posting_filter=doces.CUSTOM, receiving_filter=doces.CUSTOM)
        baseline = new_dynamics()
        expected = simulate(baseline, posting_filter=doces.COSINE, receiving_filter=doces.UNIFORM)
        self.assertEqual(capture(dynamics, result), capture(baseline, expected))

    def test_zero_posting_and_receiving_probabilities(self):
        for role in ("posting", "receiving"):
            with self.subTest(role=role):
                dynamics = new_dynamics()
                getattr(dynamics, "set_" + role + "_filter")(constant(0))
                selectors = {"posting_filter": doces.UNIFORM, "receiving_filter": doces.UNIFORM}
                selectors[role + "_filter"] = doces.CUSTOM
                result = simulate(dynamics, mu=1, **selectors)
                self.assertEqual(result["b"], OPINIONS)
                self.assertEqual(result["edges"], dynamics.edge_list)
                self.assertEqual(dynamics.rewiring_count, 0)
                if role == "posting":
                    # DOCES initially fills every feed before filtering starts.
                    self.assertEqual(len(dynamics.post_ids), VERTEX_COUNT * 3)
                    self.assertEqual(dynamics.post_posted_counts, [1] * (VERTEX_COUNT * 3))
                else:
                    self.assertGreater(len(dynamics.post_ids), VERTEX_COUNT * 3)

    def test_c_interpolation_matches_the_same_linear_curve_on_another_grid(self):
        outputs = []
        for grid in ([0, 2], [0, 0.5, 1, 1.5, 2]):
            dynamics = new_dynamics()
            table = doces.ProbabilityTable.from_function(lambda d: 1 - d / 2, grid)
            dynamics.set_posting_filter(table)
            dynamics.set_receiving_filter(table)
            result = simulate(dynamics, posting_filter=doces.CUSTOM, receiving_filter=doces.CUSTOM)
            outputs.append(capture(dynamics, result))
        self.assertEqual(outputs[0], outputs[1])
        uniform = new_dynamics()
        self.assertNotEqual(outputs[0], capture(uniform, simulate(
            uniform, posting_filter=doces.UNIFORM, receiving_filter=doces.UNIFORM,
        )))

    def test_posting_assignment_and_receiving_sender_ownership(self):
        zero, one = constant(0), constant(1)
        for sender_receives in (False, True):
            with self.subTest(sender_receives=sender_receives):
                dynamics = new_dynamics()
                dynamics.set_posting_filter([one] + [zero] * (VERTEX_COUNT - 1))
                # The legacy model selects the receiving filter on the posting node.
                dynamics.set_receiving_filter(
                    ([one] + [zero] * (VERTEX_COUNT - 1)) if sender_receives
                    else ([zero] + [one] * (VERTEX_COUNT - 1))
                )
                result = simulate(dynamics, number_of_iterations=800, mu=1,
                                  posting_filter=doces.CUSTOM, receiving_filter=doces.CUSTOM)
                self.assertGreater(len(dynamics.post_ids), 0)
                if sender_receives:
                    self.assertNotEqual(result["b"], OPINIONS)
                    for node in (0, 1, 2, 3, 4, 6):
                        self.assertEqual(result["b"][node], OPINIONS[node])
                else:
                    self.assertEqual(result["b"], OPINIONS)

    def test_callable_identity_is_sampled_once_and_not_called_in_c(self):
        calls = []

        def probability(difference):
            calls.append(difference)
            return 1.0

        dynamics = new_dynamics()
        dynamics.set_posting_filter([probability, doces.UNIFORM] * 4, grid=[0, 1, 2])
        self.assertEqual(calls, [0, 1, 2])
        simulate(dynamics, posting_filter=doces.CUSTOM, receiving_filter=doces.UNIFORM)
        simulate(dynamics, b=None, posting_filter=doces.CUSTOM, receiving_filter=doces.UNIFORM)
        self.assertEqual(calls, [0, 1, 2])

    def test_callables_do_not_have_to_survive_sampling(self):
        class Probability:
            def __call__(self, difference):
                return 1.0

        dynamics = new_dynamics()
        probability = Probability()
        reference = weakref.ref(probability)
        dynamics.set_posting_filter(probability, grid=[0, 2])
        del probability
        gc.collect()
        self.assertIsNone(reference())
        baseline = new_dynamics()
        result = simulate(dynamics, posting_filter=doces.CUSTOM, receiving_filter=doces.UNIFORM)
        expected = simulate(baseline, posting_filter=doces.UNIFORM, receiving_filter=doces.UNIFORM)
        self.assertEqual(capture(dynamics, result), capture(baseline, expected))

    def test_invalid_setter_keeps_previous_configuration(self):
        for role in ("posting", "receiving", "rewiring"):
            with self.subTest(role=role):
                dynamics = new_dynamics()
                baseline = new_dynamics()
                for instance in (dynamics, baseline):
                    getattr(instance, "set_" + role + "_filter")(constant(1))
                setter = getattr(dynamics, "set_" + role + "_filter")
                for invalid in ([constant(0)], [doces.UNIFORM] * (VERTEX_COUNT + 1)):
                    with self.assertRaises((TypeError, ValueError)):
                        setter(invalid)
                with self.assertRaises((TypeError, ValueError)):
                    setter(lambda d: 0.5)
                with self.assertRaises((TypeError, ValueError)):
                    setter(lambda d: np.nan, grid=[0, 2])
                options = dict(posting_filter=doces.UNIFORM, receiving_filter=doces.UNIFORM,
                               rewire=role == "rewiring")
                if role != "rewiring":
                    options[role + "_filter"] = doces.CUSTOM
                result = simulate(dynamics, **options)
                expected = simulate(baseline, **options)
                self.assertEqual(capture(dynamics, result), capture(baseline, expected))

    def test_reset_to_integer_filters_removes_tables(self):
        dynamics = new_dynamics()
        dynamics.set_posting_filter(constant(0))
        dynamics.set_receiving_filter(constant(0))
        dynamics.set_rewiring_filter(constant(0))
        dynamics.set_posting_filter([doces.UNIFORM] * VERTEX_COUNT)
        dynamics.set_receiving_filter(np.full(VERTEX_COUNT, doces.COSINE, dtype=np.int32))
        dynamics.set_rewiring_filter(doces.REVERSED_HALF_COSINE)
        baseline = new_dynamics()
        result = simulate(dynamics, posting_filter=doces.CUSTOM,
                          receiving_filter=doces.CUSTOM, rewire=True)
        expected = simulate(baseline, posting_filter=doces.UNIFORM,
                            receiving_filter=doces.COSINE, rewire=True)
        self.assertEqual(capture(dynamics, result), capture(baseline, expected))

    def test_custom_curves_are_independent_of_phi(self):
        outputs = []
        for phi in (0.0, 1.0):
            dynamics = new_dynamics()
            dynamics.set_posting_filter(doces.ProbabilityTable([0, 2], [1, 0]))
            dynamics.set_receiving_filter(constant(0.75))
            outputs.append(capture(dynamics, simulate(
                dynamics, phi=phi, posting_filter=doces.CUSTOM, receiving_filter=doces.CUSTOM,
            )))
        self.assertEqual(outputs[0], outputs[1])

    def test_more_than_127_distinct_tables(self):
        count = 140
        edges = [[node, (node + 1) % count] for node in range(count)]
        initial = np.linspace(-1, 1, count).tolist()
        builtin = doces.Opinion_dynamics(count, edges, verbose=False)
        custom = doces.Opinion_dynamics(count, edges, verbose=False)
        custom.set_posting_filter([constant(1) for _ in range(count)])
        custom.set_receiving_filter([constant(1) for _ in range(count)])
        result = simulate(custom, b=initial, number_of_iterations=600,
                          posting_filter=doces.CUSTOM, receiving_filter=doces.CUSTOM)
        expected = simulate(builtin, b=initial, number_of_iterations=600,
                            posting_filter=doces.UNIFORM, receiving_filter=doces.UNIFORM)
        self.assertEqual(capture(custom, result), capture(builtin, expected))

    def test_instance_isolation_and_repeated_table_replacement(self):
        dynamics = new_dynamics()
        quiet = new_dynamics()
        quiet.set_posting_filter(constant(0))
        for index in range(6):
            dynamics.set_posting_filter(constant(1))
            dynamics.set_receiving_filter(constant(1))
            dynamics.set_rewiring_filter(constant(0))
            gc.collect()
            baseline = new_dynamics()
            result = simulate(dynamics, posting_filter=doces.CUSTOM,
                              receiving_filter=doces.CUSTOM, rand_seed=271828 + index)
            self.assertTrue(all(np.isfinite(result["b"])))
            if index == 0:
                expected = simulate(baseline, posting_filter=doces.UNIFORM,
                                    receiving_filter=doces.UNIFORM)
                self.assertEqual(capture(dynamics, result), capture(baseline, expected))
            quiet_result = simulate(quiet, posting_filter=doces.CUSTOM,
                                    receiving_filter=doces.UNIFORM)
            self.assertEqual(quiet_result["b"], OPINIONS)
            self.assertEqual(len(quiet.post_ids), VERTEX_COUNT * 3)
            self.assertEqual(quiet.post_posted_counts, [1] * (VERTEX_COUNT * 3))

    def test_only_active_roles_require_domain_coverage(self):
        dynamics = new_dynamics()
        narrow = constant(0.5, maximum=1)
        dynamics.set_posting_filter(narrow)
        dynamics.set_receiving_filter(narrow)
        dynamics.set_rewiring_filter(narrow)
        # Built-in selectors and rewire=False leave every table inactive.
        simulate(dynamics, posting_filter=doces.UNIFORM, receiving_filter=doces.UNIFORM)
        before = capture(dynamics, {"b": dynamics.opinions, "edges": dynamics.edge_list})
        for options in (
            {"posting_filter": doces.CUSTOM},
            {"receiving_filter": doces.CUSTOM},
            {"rewire": True},
        ):
            with self.subTest(options=options):
                # A global built-in selector replaces the configured posting
                # or receiving assignments, as it did for legacy integer lists.
                if "posting_filter" in options:
                    dynamics.set_posting_filter(narrow)
                if "receiving_filter" in options:
                    dynamics.set_receiving_filter(narrow)
                with self.assertRaises(ValueError):
                    simulate(dynamics, b=None, **options)
                self.assertEqual(capture(dynamics, {"b": dynamics.opinions,
                                                   "edges": dynamics.edge_list}), before)

    def test_domain_must_include_zero_and_full_unnormalized_range(self):
        for differences, limits in (([0.25, 2], (-1, 1)), ([0, 2], (-2, 2))):
            with self.subTest(differences=differences, limits=limits):
                dynamics = new_dynamics()
                dynamics.set_posting_filter(doces.ProbabilityTable(differences, [1, 1]))
                with self.assertRaises(ValueError):
                    simulate(dynamics, min_opinion=limits[0], max_opinion=limits[1],
                             posting_filter=doces.CUSTOM)

    def test_domain_check_includes_retained_opinions_and_posts(self):
        dynamics = new_dynamics()
        simulate(dynamics, min_opinion=-3, max_opinion=3,
                 b=[-3] * VERTEX_COUNT, mu=1,
                 posting_filter=doces.UNIFORM, receiving_filter=doces.UNIFORM)
        self.assertTrue(any(abs(theta) > 1 for theta in dynamics.post_thetas))
        dynamics.set_posting_filter(constant(1))
        before = capture(dynamics, {"b": dynamics.opinions, "edges": dynamics.edge_list})
        for opinions in (None, OPINIONS):
            with self.subTest(replace_opinions=opinions is not None):
                with self.assertRaises(ValueError):
                    simulate(dynamics, b=opinions, posting_filter=doces.CUSTOM,
                             receiving_filter=doces.UNIFORM)
                self.assertEqual(capture(dynamics, {"b": dynamics.opinions,
                                                   "edges": dynamics.edge_list}), before)
        dynamics.set_posting_filter(constant(1, maximum=6))
        simulate(dynamics, b=None, posting_filter=doces.CUSTOM,
                 receiving_filter=doces.UNIFORM)


class FilterParameterWarningTests(unittest.TestCase):
    def recorded_warnings(self, dynamics, **overrides):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            simulate(dynamics, **overrides)
        return [item for item in caught
                if issubclass(item.category, doces.FilterParameterWarning)]

    def test_nonzero_phi_warns_once_per_sampled_receiving_configuration(self):
        dynamics = new_dynamics()
        dynamics.set_receiving_filter(constant(1))
        self.assertEqual(self.recorded_warnings(
            dynamics, phi=0, receiving_filter=doces.CUSTOM
        ), [])

        caught = self.recorded_warnings(
            dynamics, b=None, phi=0.25, receiving_filter=doces.CUSTOM
        )
        self.assertEqual(len(caught), 1)
        self.assertIn("simulation-time phi", str(caught[0].message))
        self.assertEqual(self.recorded_warnings(
            dynamics, b=None, phi=0.5, receiving_filter=doces.CUSTOM
        ), [])

        dynamics.set_receiving_filter(constant(1))
        self.assertEqual(len(self.recorded_warnings(
            dynamics, b=None, phi=0.25, receiving_filter=doces.CUSTOM
        )), 1)

    def test_phi_aware_native_filter_suppresses_mixed_configuration_warning(self):
        sampled = constant(1)
        for native in (doces.COSINE, doces.STRETCHED_HALF_COSINE):
            with self.subTest(native=native):
                dynamics = new_dynamics()
                dynamics.set_receiving_filter([sampled, native] * (VERTEX_COUNT // 2))
                self.assertEqual(self.recorded_warnings(
                    dynamics, phi=0.25, receiving_filter=doces.CUSTOM
                ), [])

    def test_phi_independent_native_filters_do_not_hide_warning(self):
        sampled = constant(1)
        for native in (doces.UNIFORM, doces.HALF_COSINE,
                       doces.REVERSED_HALF_COSINE):
            with self.subTest(native=native):
                dynamics = new_dynamics()
                dynamics.set_receiving_filter([sampled, native] * (VERTEX_COUNT // 2))
                self.assertEqual(len(self.recorded_warnings(
                    dynamics, phi=0.25, receiving_filter=doces.CUSTOM
                )), 1)

    def test_legacy_integer_custom_configuration_does_not_warn(self):
        dynamics = new_dynamics()
        dynamics.set_receiving_filter([doces.UNIFORM] * VERTEX_COUNT)
        self.assertEqual(self.recorded_warnings(
            dynamics, phi=0.25, receiving_filter=doces.CUSTOM
        ), [])

    def test_warning_as_error_prevents_simulation_and_keeps_instance_usable(self):
        dynamics = new_dynamics()
        dynamics.set_receiving_filter(constant(1))
        initial_edges = dynamics.edge_list
        with warnings.catch_warnings():
            warnings.simplefilter("error", doces.FilterParameterWarning)
            with self.assertRaises(doces.FilterParameterWarning):
                simulate(dynamics, phi=0.25, receiving_filter=doces.CUSTOM)
        self.assertEqual(dynamics.opinions, [])
        self.assertEqual(dynamics.post_ids, [])
        self.assertEqual(dynamics.edge_list, initial_edges)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", doces.FilterParameterWarning)
            result = simulate(
                dynamics, phi=0.25, receiving_filter=doces.CUSTOM
            )
        self.assertEqual(len(result["b"]), VERTEX_COUNT)


class RewiringFilterTests(unittest.TestCase):
    def test_false_disables_every_branch_even_with_always_rewire_table(self):
        for directed in (True, False):
            for stubborn in ([0] * VERTEX_COUNT, [1] * VERTEX_COUNT, [1, 0] * 4):
                for custom in (False, True):
                    with self.subTest(directed=directed, stubborn=stubborn, custom=custom):
                        dynamics = new_dynamics(directed=directed)
                        dynamics.set_stubborn(stubborn)
                        if custom:
                            dynamics.set_rewiring_filter(constant(1))
                        initial_edges = dynamics.edge_list
                        result = simulate(dynamics, number_of_iterations=1000, mu=1,
                                          posting_filter=doces.UNIFORM,
                                          receiving_filter=doces.UNIFORM, rewire=False)
                        self.assertEqual(result["edges"], initial_edges)
                        self.assertEqual(dynamics.rewiring_count, 0)
                        for node, is_stubborn in enumerate(stubborn):
                            if is_stubborn:
                                self.assertEqual(result["b"][node], OPINIONS[node])

    def test_explicit_default_preserves_seeded_results(self):
        for stubborn in ([0] * VERTEX_COUNT, [1, 0] * 4, [1] * VERTEX_COUNT):
            with self.subTest(stubborn=stubborn):
                baseline = new_dynamics()
                explicit = new_dynamics()
                for instance in (baseline, explicit):
                    instance.set_stubborn(stubborn)
                explicit.set_rewiring_filter(doces.REVERSED_HALF_COSINE)
                result = simulate(explicit, number_of_iterations=1000, rewire=True,
                                  posting_filter=doces.UNIFORM, receiving_filter=doces.UNIFORM)
                expected = simulate(baseline, number_of_iterations=1000, rewire=True,
                                    posting_filter=doces.UNIFORM, receiving_filter=doces.UNIFORM)
                self.assertEqual(capture(explicit, result), capture(baseline, expected))

    def test_zero_probability_disables_rewiring_for_stubborn_and_other_nodes(self):
        for stubborn in ([0] * VERTEX_COUNT, [1] * VERTEX_COUNT, [1, 0] * 4):
            with self.subTest(stubborn=stubborn):
                dynamics = new_dynamics()
                dynamics.set_stubborn(stubborn)
                dynamics.set_rewiring_filter(constant(0))
                initial_edges = dynamics.edge_list
                result = simulate(dynamics, number_of_iterations=1000, rewire=True,
                                  posting_filter=doces.UNIFORM, receiving_filter=doces.UNIFORM)
                self.assertEqual(result["edges"], initial_edges)
                self.assertEqual(dynamics.rewiring_count, 0)

    def test_rewiring_uses_the_node_changing_its_connection(self):
        dynamics = new_dynamics()
        dynamics.set_stubborn([1] * VERTEX_COUNT)
        zero, one = constant(0), constant(1)
        dynamics.set_rewiring_filter([one] + [zero] * (VERTEX_COUNT - 1))
        initial_edges = dynamics.edge_list
        # All opinion differences stay zero; the custom probability can still
        # permit rewiring, unlike the built-in reversed half cosine.
        result = simulate(dynamics, b=[0] * VERTEX_COUNT, number_of_iterations=2000,
                          mu=1, rewire=True, posting_filter=doces.UNIFORM,
                          receiving_filter=doces.UNIFORM)
        self.assertGreater(dynamics.rewiring_count, 0)
        self.assertEqual(result["b"], [0] * VERTEX_COUNT)
        self.assertEqual(sorted(edge for edge in result["edges"] if edge[0] != 0),
                         sorted(edge for edge in initial_edges if edge[0] != 0))


class NativeFilterBoundaryTests(unittest.TestCase):
    def test_native_boundary_copies_strided_arrays(self):
        dynamics = new_dynamics()
        differences = np.repeat(np.array([0.0, 2.0]), 2)[::2]
        probabilities = np.repeat(np.array([1.0, 1.0]), 2)[::2]
        assignments = np.full(VERTEX_COUNT * 2, -1, dtype=np.int64)[::2]
        dynamics._set_filter_configuration(
            "posting", assignments, [(differences, probabilities)]
        )
        differences[:] = 99
        probabilities[:] = 0
        assignments[:] = doces.COSINE
        del differences, probabilities, assignments
        gc.collect()
        baseline = new_dynamics()
        result = simulate(dynamics, posting_filter=doces.CUSTOM,
                          receiving_filter=doces.UNIFORM)
        expected = simulate(baseline, posting_filter=doces.UNIFORM,
                            receiving_filter=doces.UNIFORM)
        self.assertEqual(capture(dynamics, result), capture(baseline, expected))

    def test_native_boundary_rejects_invalid_payloads_atomically(self):
        dynamics = new_dynamics()
        dynamics.set_posting_filter(constant(1))
        valid_ids = [-1] * VERTEX_COUNT
        valid_tables = [([0, 2], [1, 1])]
        cases = (
            ("unknown", valid_ids, valid_tables),
            ("posting", valid_ids[:-1], valid_tables),
            ("posting", [valid_ids], valid_tables),
            ("posting", [-2] * VERTEX_COUNT, valid_tables),
            ("posting", [np.iinfo(np.int64).min] * VERTEX_COUNT, valid_tables),
            ("posting", [doces.CUSTOM] * VERTEX_COUNT, valid_tables),
            ("posting", valid_ids, []),
            ("posting", valid_ids, [([0, 2],)]),
            ("posting", valid_ids, [([0], [1])]),
            ("posting", valid_ids, [([0, 2], [1])]),
            ("posting", valid_ids, [([0, 0, 2], [1, 1, 1])]),
            ("posting", valid_ids, [([0, np.inf], [1, 1])]),
            ("posting", valid_ids, [([0, 2], [np.nan, 1])]),
            ("posting", valid_ids, [([0, 2], [1, 1.01])]),
        )
        for role, assignments, tables in cases:
            with self.subTest(role=role, assignments=assignments, tables=tables):
                with self.assertRaises((TypeError, ValueError)):
                    dynamics._set_filter_configuration(role, assignments, tables)
        baseline = new_dynamics()
        result = simulate(dynamics, posting_filter=doces.CUSTOM,
                          receiving_filter=doces.UNIFORM)
        expected = simulate(baseline, posting_filter=doces.UNIFORM,
                            receiving_filter=doces.UNIFORM)
        self.assertEqual(capture(dynamics, result), capture(baseline, expected))

    def test_reinitialization_discards_filters_for_previous_graph(self):
        dynamics = new_dynamics()
        dynamics.set_posting_filter(constant(0))
        dynamics.set_receiving_filter(constant(0))
        dynamics.set_rewiring_filter(constant(0))
        count = 12
        edges = [[node, (node + offset) % count]
                 for node in range(count) for offset in (1, 3)]
        dynamics.__init__(count, edges, directed=True, verbose=False)
        dynamics.set_posting_filter(doces.UNIFORM)
        dynamics.set_receiving_filter(doces.UNIFORM)
        baseline = doces.Opinion_dynamics(count, edges, directed=True, verbose=False)
        initial = [-0.875, 0.875] * (count // 2)
        result = simulate(dynamics, b=initial, number_of_iterations=1000,
                          posting_filter=doces.CUSTOM, receiving_filter=doces.CUSTOM,
                          rewire=True)
        expected = simulate(baseline, b=initial, number_of_iterations=1000,
                            posting_filter=doces.UNIFORM, receiving_filter=doces.UNIFORM,
                            rewire=True)
        self.assertGreater(baseline.rewiring_count, 0)
        self.assertEqual(capture(dynamics, result), capture(baseline, expected))


if __name__ == "__main__":
    unittest.main()
