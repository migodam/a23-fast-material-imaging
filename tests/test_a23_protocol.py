"""Frozen protocol, accounting and runtime capability checks; no production pass inference."""
from __future__ import annotations

from dataclasses import fields
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from a20.backend import BasisView, ForbiddenAccess, Problem, RUNTIME_KEYS, load_problem
from a20.costs import BudgetExceeded
from a23.physics import ReferencePhysics, load_online
from tests.a23_test_support import CONFIG, ROOT, audit_book, tiny_problem


class FrozenContractTests(unittest.TestCase):
    def test_primary_scene_amplitude_noise_and_full_material_contract_is_frozen(self):
        self.assertTrue(CONFIG["frozen_before_results"])
        self.assertEqual(CONFIG["scenes"], [2001, 2003, 2014, 2009])
        self.assertEqual(CONFIG["amplitudes"], [.15, .5, 1.])
        self.assertEqual(CONFIG["noise"], ["zero", "20dB_nominal_difference"])
        self.assertTrue(CONFIG["historically_exposed"])
        self.assertEqual(CONFIG["background"], [.1, .04])
        self.assertEqual(CONFIG["material_chart"], "full-cell real mass normalized [ReN,ImN]")
        self.assertEqual(CONFIG["dtype"], "complex128/float64")
        self.assertEqual(CONFIG["feedback_gamma"], 1.)
        self.assertEqual(CONFIG["tikhonov_relative"], .001)
        self.assertTrue(CONFIG["material_rejection_not_projection"])
        self.assertEqual(CONFIG["physical_real_lower"], -.5)
        self.assertEqual(CONFIG["physical_imag_lower"], 0.)
        self.assertEqual(CONFIG["pole_relative_floor"], 1e-10)

    def test_fixed_ranks_degrees_probes_and_expensive_call_caps(self):
        opm = CONFIG["OPM"]
        self.assertEqual(opm["degree"], 1)
        self.assertEqual([opm["seed_rank_"+s] for s in "OPM"], [4, 4, 4])
        self.assertEqual(opm["retained_rank"], 8)
        self.assertEqual(CONFIG["randomized_transfer_rank"], 32)
        self.assertEqual(CONFIG["quadratic_data_rank"], 32)
        self.assertEqual(CONFIG["quadratic_training_probes"], 32)
        self.assertEqual(CONFIG["quadratic_holdout_probes"], 8)
        self.assertEqual(CONFIG["independent_transfer_probes"], 8)
        self.assertEqual(CONFIG["clean_full_forward_cap"], 12)
        self.assertEqual(CONFIG["primary_prediction_full_forward_cap"], 12)
        self.assertEqual(CONFIG["calibration_prediction_full_forward_cap"], 8)
        self.assertEqual(CONFIG["gpu_occupation_cap_seconds"], 7200)
        self.assertEqual(CONFIG["cold_repeats"], 1)
        self.assertEqual(CONFIG["warm_repeats"], 5)
        self.assertEqual(CONFIG["master_seed"], 2026102301)
        self.assertEqual(CONFIG["calibration_source_amplitude"], .05)
        self.assertEqual(CONFIG["calibration_receiver_gain"], .03)
        self.assertTrue({"NN", "flow", "diffusion", "new_Maxwell_solver", "degree_search",
                         "new_scene_campaign", "truth_runtime"}.issubset(CONFIG["forbidden"]))

    def test_declared_gates_are_not_moved_by_tests(self):
        self.assertEqual(CONFIG["gates"], {
            "H1_transfer_error_max": .05,
            "H1_encoder_time_reduction_min": .2,
            "H2_full_material_improvement_min": .1,
            "H2_distinct_shapes_min": 2,
            "H3_full_material_NRMSE_max": .6,
            "H3_difference_data_residual_max": .2,
            "H3_time_reduction_min": .2,
        })
        self.assertEqual(CONFIG, json.loads((ROOT/"FROZEN_CONFIG.json").read_text(encoding="utf-8")))


class RuntimeIsolationTests(unittest.TestCase):
    def test_online_problem_exposes_no_truth_teacher_or_full_derivatives(self):
        problem = tiny_problem()
        dataclass_fields = {field.name for field in fields(Problem)}
        for forbidden in ["truth", "teacher", "full_J", "full_H", "reference_step", "labels"]:
            self.assertNotIn(forbidden, dataclass_fields)
            with self.assertRaises(ForbiddenAccess):
                getattr(problem, forbidden)

    def test_online_file_rejects_all_unregistered_or_offline_keys(self):
        problem = tiny_problem()
        runtime = {
            "parent_id": problem.parent_id, "points": problem.points, "volume": problem.volume,
            "data0": problem.data, "scale": problem.scale, "init": problem.init,
            "Q": np.empty((0, 0)), "kind": "full-cell", "dirs": problem.dirs,
            "pols": problem.pols, "receivers": problem.receivers,
            "obs_basis": problem.obs_basis, "k": problem.frequency, "historical_exposed": True,
        }
        self.assertEqual(set(runtime), RUNTIME_KEYS)
        with tempfile.TemporaryDirectory(prefix="a23-test-runtime-") as directory:
            path = Path(directory)/"online.npz"
            np.savez(path, **runtime)
            loaded = load_problem(path)
            self.assertEqual(loaded.chart.d, 16)
            # The primary loader discards old data/scale/chart and uses the declared reference.
            primary = load_online(path)
            self.assertIsNone(primary.chart.Q)
            np.testing.assert_array_equal(primary.data, np.zeros_like(problem.data))
            self.assertEqual(primary.scale, 1.)
            np.testing.assert_array_equal(primary.init, np.full(len(problem.points), .1+.04j))
            for extra in ["truth", "teacher", "full_J", "clean_label", "truth_rank", "arbitrary_new_key"]:
                np.savez(path, **runtime, **{extra: np.zeros(1)})
                with self.assertRaises(ForbiddenAccess):
                    load_problem(path)
                with self.assertRaises(ForbiddenAccess):
                    load_online(path)

    def test_basis_capability_rejects_full_state_current_and_truth_access(self):
        # __getattr__ is checked without allocating any additional physics state.
        view = BasisView.__new__(BasisView)
        for forbidden in ["teacher", "truth", "full_J", "full_H", "full_current",
                          "current_correction", "full_state", "reference_step", "old_anchor", "labels"]:
            with self.assertRaises(ForbiddenAccess):
                getattr(view, forbidden)


class AccountingTests(unittest.TestCase):
    def test_failed_actions_are_recorded_and_charged(self):
        with tempfile.TemporaryDirectory(prefix="a23-test-ledger-") as directory:
            path = Path(directory)/"test_actions.jsonl"
            book = audit_book(path=path, enforce=False)
            with self.assertRaisesRegex(ValueError, "deliberate tiny failure"):
                with book.span("tiny_failed_action", solve_forward_rhs=3):
                    raise ValueError("deliberate tiny failure")
            self.assertEqual(book.counts["solve_forward_rhs"], 3)
            row = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(row["status"], "FAILED")
            self.assertEqual(row["counters"]["solve_forward_rhs"], 3)
            self.assertGreaterEqual(row["wall_seconds"], 0.)
            self.assertIn("ValueError", row["error"])
            self.assertEqual(book.receipt()["gpu_occupation_seconds"], 0.)

    def test_cpu_limit_reserves_shutdown_space_before_starting_an_action(self):
        book = audit_book(cpu_limit=1., cpu_reserve=.2, prior_cpu=.81, enforce=True)
        with self.assertRaises(BudgetExceeded):
            with book.span("must_not_start", solve_forward_rhs=1):
                self.fail("budget-exhausted operation ran")
        self.assertEqual(book.counts["solve_forward_rhs"], 0)

    def test_nested_wall_is_exclusive_and_cpu_receipt_does_not_claim_gpu_work(self):
        book = audit_book(enforce=False)
        with book.span("parent", B_rhs=1):
            with book.span("child", S_rhs=2):
                np.linalg.norm(np.ones(8))
        receipt = book.receipt()
        self.assertEqual(receipt["counts"]["B_rhs"], 1)
        self.assertEqual(receipt["counts"]["S_rhs"], 2)
        self.assertEqual(receipt["gpu_occupation_seconds"], 0.)
        self.assertLessEqual(sum(receipt["exclusive_walls"].values()), receipt["wall_seconds"])
        self.assertEqual(receipt["device"], "cpu")


if __name__ == "__main__":
    unittest.main()
