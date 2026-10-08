"""Actual tiny A17/A20 adapter tests, distinct from production imaging claims."""
from __future__ import annotations

import unittest

import numpy as np

from a20.backend import Adapter, MaterialChart, kernel, pack, unpack
from a23.physics import ReferencePhysics, gaussian_noise
from a23.encoder import PhysicsEncoder, TikhonovDecoder
from tests.a23_test_support import CONFIG, audit_book, record_measurement, relative_error, tiny_problem


class RealCoordinateTests(unittest.TestCase):
    def test_per_source_pack_roundtrip_and_real_inner_product(self):
        rng = np.random.default_rng(23001)
        y = rng.normal(size=(3, 5)) + 1j*rng.normal(size=(3, 5))
        w = rng.normal(size=(3, 5)) + 1j*rng.normal(size=(3, 5))
        expected = np.concatenate([
            np.r_[y[source].real, y[source].imag] for source in range(len(y))
        ])
        np.testing.assert_array_equal(pack(y), expected)
        np.testing.assert_array_equal(unpack(pack(y), 3, 5), y)
        self.assertAlmostEqual(float(pack(y) @ pack(w)), float(np.vdot(y, w).real), places=12)
        batched = np.stack([y, 2*y], axis=-1)
        np.testing.assert_array_equal(unpack(pack(batched), 3, 5), batched)
        with self.assertRaises(ValueError):
            unpack(pack(y).astype(complex), 3, 5)

    def test_full_chart_is_a_real_mass_isometry(self):
        volume, n = .22**3, 8
        chart = MaterialChart(volume, n, None, "full-cell")
        rng = np.random.default_rng(23002)
        d = rng.normal(size=2*n)
        dc = chart.expand(d)
        self.assertEqual(chart.d, 2*n)
        self.assertAlmostEqual(float(d @ d), float(volume*np.vdot(dc, dc).real), places=12)
        np.testing.assert_allclose(chart.project(dc), d, rtol=1e-14, atol=1e-14)
        g = rng.normal(size=n) + 1j*rng.normal(size=n)
        self.assertAlmostEqual(float(d @ chart.adjoint(g)), float(np.vdot(dc, g).real), places=12)
        with self.assertRaises(ValueError):
            chart.expand(d.astype(complex))
        with self.assertRaises(ValueError):
            chart.expand(d[:-1])

    def test_whitening_is_applied_after_pack_with_its_real_adjoint(self):
        problem = tiny_problem()
        rng = np.random.default_rng(23003)
        dimension = 2*problem.data.size
        # A nonsymmetric real metric makes accidental W/W.T interchange observable.
        whitening = np.diag(np.linspace(.7, 1.3, dimension))
        whitening[0, 1] = .2
        adapter = Adapter(problem, book=audit_book(enforce=False), whitening=whitening)
        state = adapter.full_state(problem.init)
        d = rng.normal(size=problem.chart.d)
        w = rng.normal(size=dimension)
        tangent = adapter.full_tangent_action(problem.init, state, d)
        np.testing.assert_allclose(tangent, whitening @ pack(state.jvp(problem.chart.expand(d))),
                                   rtol=1e-13, atol=1e-13)
        adjoint = adapter.full_adjoint_action(problem.init, state, w)
        lhs, rhs = float(w @ tangent), float(d @ adjoint)
        error = abs(lhs-rhs)/max(abs(lhs), abs(rhs), 1e-30)
        record_measurement("nonsymmetric_whitening_real_adjoint_relative_error", error)
        self.assertLess(error, 1e-10)


class ReferenceResponseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ref = ReferencePhysics(tiny_problem(), book=audit_book(enforce=False),
                                   device="cpu", config=CONFIG)
        cls.A = cls.ref.matrix()

    def setUp(self):
        # A test's probes do not change when another test is inserted or rerun.
        seed_offset = sum((index+1)*ord(char) for index, char in enumerate(self._testMethodName))
        self.rng = np.random.default_rng(23004+seed_offset)

    def assertRelative(self, left, right, tolerance=1e-10):
        self.assertLess(relative_error(left, right), tolerance)

    def test_actual_backend_reference_and_full_material_dimensions(self):
        ref = self.ref
        self.assertIsInstance(ref.adapter, Adapter)
        self.assertEqual(ref.adapter.model.N, 8)
        self.assertEqual(ref.adapter.n, 24)
        self.assertEqual(ref.adapter.p, 16)
        self.assertIsNone(ref.adapter.chart.Q)
        self.assertEqual(self.A.shape, (288, 16))
        self.assertFalse(np.iscomplexobj(self.A))
        self.assertEqual(ref.adapter.device, "cpu")
        self.assertRelative(ref.data0, ref.adapter.whiten(pack(ref.state.field)))
        predicted, state = ref.predict(ref.chi0)
        self.assertRelative(predicted, ref.data0)
        self.assertLess(state.source_residual(), CONFIG["full_backward_residual_rtol"])

    def test_reference_linear_and_real_adjoint_are_exact_on_tiny_backend(self):
        ref = self.ref
        d = self.rng.normal(size=self.A.shape[1])
        w = self.rng.normal(size=self.A.shape[0])
        np.testing.assert_allclose(ref.linear(d), self.A @ d, rtol=1e-11, atol=1e-11)
        self.assertRelative(ref.linear_adjoint(w), self.A.T @ w)
        lhs, rhs = float(w @ ref.linear(d)), float(d @ ref.linear_adjoint(w))
        self.assertLess(abs(lhs-rhs)/max(abs(lhs), abs(rhs), 1e-30), 1e-10)
        native = ref.adapter.full_tangent_action(ref.chi0, ref.state, d)
        self.assertRelative(ref.linear(d), native)
        record_measurement("streamed_matrix_native_jvp_relative_error", relative_error(ref.linear(d), native))
        record_measurement("reference_real_adjoint_relative_error", abs(lhs-rhs)/max(abs(lhs), abs(rhs), 1e-30))

    def test_uncached_vector_and_batched_response_match_streamed_matrix(self):
        ref = ReferencePhysics(tiny_problem(), config=CONFIG, device="cpu",
                               book=audit_book(enforce=False))
        rng = np.random.default_rng(23007)
        directions = rng.normal(size=(ref.p, 3))
        data_cotangent = rng.normal(size=ref.data0.size)
        vector = ref.linear(directions[:, 0])
        batched = ref.linear(directions)
        uncached_adjoint = ref.linear_adjoint(data_cotangent)
        matrix = ref.matrix()
        self.assertRelative(vector, matrix @ directions[:, 0])
        self.assertRelative(batched, matrix @ directions)
        self.assertRelative(uncached_adjoint, matrix.T @ data_cotangent)
        before = dict(ref.book.counts)
        self.assertIs(ref.matrix(), matrix)
        self.assertEqual(before, dict(ref.book.counts))
        record_measurement("uncached_matrix_response_relative_errors", {
            "vector": relative_error(vector, matrix @ directions[:, 0]),
            "batched": relative_error(batched, matrix @ directions),
            "real_adjoint": relative_error(uncached_adjoint, matrix.T @ data_cotangent),
            "second_matrix_call_new_actions": 0,
        })

    def test_reference_rejects_a_restricted_chart(self):
        problem = tiny_problem()
        q = np.ones((len(problem.points), 1))/np.sqrt(problem.volume*len(problem.points))
        problem.chart = MaterialChart(problem.volume, len(problem.points), q, "restricted-diagnostic")
        with self.assertRaisesRegex(ValueError, "A23_PRIMARY_REQUIRES_FULL_CELL_CHART"):
            ReferencePhysics(problem, config=CONFIG, device="cpu", book=audit_book(enforce=False))

    def test_primal_and_adjoint_quadratic_outer_paths_agree(self):
        ref = self.ref
        u, v = self.rng.normal(size=(2, ref.p))*.01
        adjoint = ref.quadratic(u, v, components=True, outer="adjoint")
        primal = ref.quadratic(u, v, components=True, outer="primal")
        for component in ["total", "local", "feedback"]:
            self.assertRelative(primal[component], adjoint[component])
        record_measurement("quadratic_primal_adjoint_outer_relative_errors",
                           {key: relative_error(primal[key], adjoint[key]) for key in adjoint})

    def test_polarizability_first_and_second_derivative_plateaus(self):
        ref = self.ref
        chi, volume, k = ref.chi0, ref.adapter.problem.volume, ref.adapter.problem.frequency
        u = self.rng.normal(size=chi.size) + 1j*self.rng.normal(size=chi.size)
        u /= np.linalg.norm(u)
        a0, da = kernel.polarizability(chi, volume, k)
        kappa = 1 - 1j*k**3*volume/(2*np.pi)
        dda = -18*volume*kappa/(3+kappa*chi)**3
        first, second = [], []
        for epsilon in [1e-2, 3e-3, 1e-3, 3e-4, 1e-4, 3e-5, 1e-5]:
            ap, dap = kernel.polarizability(chi+epsilon*u, volume, k)
            am, dam = kernel.polarizability(chi-epsilon*u, volume, k)
            first.append(relative_error((ap-am)/(2*epsilon), da*u))
            second.append(relative_error((dap-dam)/(2*epsilon), dda*u))
        self.assertLess(min(first), 1e-9)
        self.assertLess(min(second), 1e-9)
        self.assertGreater(first[0]/min(first), 1e3)
        self.assertGreater(second[0]/min(second), 1e3)
        np.testing.assert_allclose(ref.state.a, a0, rtol=1e-14, atol=1e-14)
        record_measurement("polarizability_derivative_plateau", {
            "epsilon": [1e-2, 3e-3, 1e-3, 3e-4, 1e-4, 3e-5, 1e-5],
            "first_relative_errors": first, "second_relative_errors": second,
        })

    def test_quadratic_is_symmetric_bilinear_and_contains_half_hessian(self):
        ref, p = self.ref, self.A.shape[1]
        u, v, w = self.rng.normal(size=(3, p)) * .03
        self.assertRelative(ref.quadratic(u, v), ref.quadratic(v, u))
        self.assertRelative(ref.quadratic(1.7*u-.3*v, w),
                            1.7*ref.quadratic(u, w)-.3*ref.quadratic(v, w))
        self.assertRelative(ref.quadratic(u), ref.quadratic(u, u))
        parts = ref.quadratic(u, v, components=True)
        self.assertEqual(set(parts), {"total", "local", "feedback"})
        self.assertRelative(parts["total"], parts["local"] + parts["feedback"])
        volume, k = ref.adapter.problem.volume, ref.adapter.problem.frequency
        kappa = 1 - 1j*k**3*volume/(2*np.pi)
        dda = -18*volume*kappa/(3+kappa*ref.chi0)**3
        da = ref.state.da
        du, dv = ref.adapter.chart.expand(u), ref.adapter.chart.expand(v)
        # The constitutive term is half J_alpha(a'' du dv), with a physical-chi pullback.
        local_expected = .5*ref.linear(ref.adapter.chart.project(dda*du*dv/da))
        self.assertRelative(parts["local"], local_expected)
        record_measurement("chi_local_constitutive_relative_error", relative_error(parts["local"], local_expected))
        eps = np.array([.04, .02, .01, .005])
        errors = []
        for t in eps:
            yp, _ = ref.predict(ref.chi0+t*du)
            ym, _ = ref.predict(ref.chi0-t*du)
            estimate = (yp+ym-2*ref.data0)/(2*t*t)
            errors.append(relative_error(estimate, ref.quadratic(u)))
        record_measurement("quadratic_half_hessian", {"epsilon": eps.tolist(), "relative_errors": errors})
        self.assertLess(min(errors), 2e-6)

    def test_alpha_coordinate_pullback_matches_chi_linear_and_quadratic(self):
        ref = self.ref
        chart = ref.adapter.chart
        u, v = self.rng.normal(size=(2, chart.d))*.02
        hu = ref.prior_coordinate_to_alpha(u)-ref.state.a
        hv = ref.prior_coordinate_to_alpha(v)-ref.state.a
        du, dv = chart.expand(u), chart.expand(v)
        np.testing.assert_allclose(hu, ref.state.da*du, rtol=1e-13, atol=1e-13)
        np.testing.assert_allclose(hv, ref.state.da*dv, rtol=1e-13, atol=1e-13)
        model, state = ref.adapter.model, ref.state
        sqrt_v = np.sqrt(model.volume)
        # These solves use the SAME backend state L; there is no independent Maxwell kernel.
        Xu = np.linalg.solve(state.L, (state.exciting*np.repeat(hu, 3)[None, :]/sqrt_v).T)
        Xv = np.linalg.solve(state.L, (state.exciting*np.repeat(hv, 3)[None, :]/sqrt_v).T)
        gu, gv = model.Goff @ Xu, model.Goff @ Xv
        rhs = .5*(np.repeat(hu, 3)[:, None]*gv + np.repeat(hv, 3)[:, None]*gu)
        q_alpha = ref.adapter.whiten(pack((model.GS @ np.linalg.solve(state.L, rhs)).T))
        parts = ref.quadratic(u, v, components=True)
        self.assertRelative(parts["feedback"], q_alpha)
        self.assertRelative(parts["total"], q_alpha+parts["local"])
        record_measurement("alpha_chi_feedback_relative_error", relative_error(parts["feedback"], q_alpha))

    def test_half_hessian_finite_difference_regression_probe_converges(self):
        # Preserve the exact probe from run 0003's finite-difference failure.
        # Its truncation error needed one smaller step; no tolerance is relaxed.
        ref = self.ref
        rng = np.random.default_rng(23004)
        rng.normal(size=128)
        u, _, _ = rng.normal(size=(3, ref.p))*.03
        du = ref.adapter.chart.expand(u)
        steps = [.04, .02, .01, .005, .0025, .00125, .000625]
        errors = []
        for step in steps:
            yp, _ = ref.predict(ref.chi0+step*du)
            ym, _ = ref.predict(ref.chi0-step*du)
            estimate = (yp+ym-2*ref.data0)/(2*step*step)
            errors.append(relative_error(estimate, ref.quadratic(u)))
        record_measurement("finite_difference_regression_run_0003", {
            "epsilon": steps, "relative_errors": errors,
            "original_error_at_epsilon_0_005": errors[3],
            "original_tolerance_unchanged": 2e-6,
            "interpretation": "central second-difference truncation error converges as epsilon squared",
        })
        self.assertGreater(errors[3], 2e-6)
        self.assertLess(errors[4], 2e-6)
        self.assertLess(errors[-1], 1e-7)
        self.assertTrue(all(3.8 < errors[i]/errors[i+1] < 4.2 for i in range(5)))

    def test_exact_alpha_field_identity_and_norm_remainder_bound(self):
        ref = self.ref
        direction = self.rng.normal(size=ref.p)
        direction *= .015/np.linalg.norm(direction)
        model, state = ref.adapter.model, ref.state
        rows = []
        for amplitude in [.2, .1, .05, .025]:
            x = amplitude*direction
            h = ref.prior_coordinate_to_alpha(x)-state.a
            converted = ref.polarization_to_chi(state.a+h)
            measured, trial = ref.predict(converted)
            delta = measured-ref.data0
            H = np.repeat(h, 3)[:, None]
            X = np.linalg.solve(state.L, H*state.exciting.T/np.sqrt(ref.v))
            transition = np.linalg.solve(state.L, H*model.Goff)
            exact_current_delta = np.linalg.solve(np.eye(model.n)-transition, X)
            exact_output_delta = ref.adapter.whiten(pack((model.GS @ exact_current_delta).T))
            identity_error = relative_error(exact_output_delta, delta)
            self.assertLess(identity_error, 1e-10)
            self.assertLess(trial.source_residual(), CONFIG["full_backward_residual_rtol"])
            eta = float(np.linalg.norm(transition, ord=2))
            self.assertLess(eta, 1.)
            q_alpha = ref.quadratic(x, components=True)["feedback"]
            remainder = float(np.linalg.norm(delta-ref.linear(x)-q_alpha))
            bound = float(np.linalg.norm(model.GS, ord=2)/ref.scale *
                          eta**2/(1-eta)*np.linalg.norm(X))
            self.assertLessEqual(remainder, bound*(1+1e-8))
            rows.append({"amplitude": amplitude, "eta": eta,
                         "exact_identity_relative_error": identity_error,
                         "quadratic_remainder_norm": remainder, "norm_bound": bound})
        record_measurement("exact_alpha_response_and_remainder_bound", rows)

    def test_full_forward_remainder_and_inverse_minus_sign_have_expected_orders(self):
        ref = self.ref
        direction = self.rng.normal(size=self.A.shape[1])
        direction /= np.linalg.norm(direction)
        direction *= .03
        amplitudes = np.array([.2, .1, .05, .025])
        decoder = np.linalg.pinv(self.A, rcond=1e-13)
        self.assertLess(relative_error(decoder @ self.A, np.eye(self.A.shape[1])), 1e-10)
        errors = {name: [] for name in ["linear", "quadratic", "inverse_linear", "inverse_feedback"]}
        for amplitude in amplitudes:
            x = amplitude*direction
            measured, _ = ref.predict(ref.chi0+ref.adapter.chart.expand(x))
            measured_delta = measured - ref.data0
            linear, quadratic = ref.linear(x), ref.quadratic(x)
            errors["linear"].append(np.linalg.norm(measured_delta-linear))
            errors["quadratic"].append(np.linalg.norm(measured_delta-linear-quadratic))
            x1 = decoder @ measured_delta
            correction = decoder @ ref.quadratic(x1)
            x2 = x1-correction
            errors["inverse_linear"].append(np.linalg.norm(x1-x))
            errors["inverse_feedback"].append(np.linalg.norm(x2-x))
            self.assertLess(np.linalg.norm(x2-x), np.linalg.norm(x1+correction-x))
        slopes = {name: float(np.polyfit(np.log(amplitudes), np.log(values), 1)[0])
                  for name, values in errors.items()}
        self.assertTrue(1.9 < slopes["linear"] < 2.1, slopes)
        self.assertTrue(2.85 < slopes["quadratic"] < 3.15, slopes)
        self.assertTrue(1.9 < slopes["inverse_linear"] < 2.1, slopes)
        self.assertTrue(2.8 < slopes["inverse_feedback"] < 3.2, slopes)
        record_measurement("full_forward_and_inverse_orders", {
            "amplitudes": amplitudes.tolist(), "slopes": slopes,
            "absolute_errors": {name: np.asarray(values).tolist() for name, values in errors.items()},
            "decoder": "tiny full-rank Moore-Penrose control; not production Tikhonov",
        })

    def test_polarizability_inverse_is_exact_and_zero_signal_is_finite(self):
        ref = self.ref
        chi = np.linspace(0., 2., ref.chi0.size) + 1j*np.linspace(0., .4, ref.chi0.size)
        alpha, _ = kernel.polarizability(chi, ref.adapter.problem.volume, ref.adapter.problem.frequency)
        np.testing.assert_allclose(ref.polarization_to_chi(alpha), chi, rtol=1e-12, atol=1e-12)
        zero_material = np.zeros_like(chi)
        predicted, state = ref.predict(zero_material)
        np.testing.assert_array_equal(predicted, np.zeros_like(ref.data0))
        self.assertLessEqual(state.source_residual(), 1e-12)
        zeros = np.zeros(self.A.shape[1])
        np.testing.assert_array_equal(ref.linear(zeros), np.zeros_like(ref.data0))
        np.testing.assert_array_equal(ref.quadratic(zeros), np.zeros_like(ref.data0))

    def test_invalid_material_and_inverse_pole_are_rejected_without_clipping(self):
        ref = self.ref
        for bad in [-.51+.1j, .2-.01j, np.nan+.1j, np.inf+.1j]:
            chi = ref.chi0.copy()
            chi[0] = bad
            original = chi.copy()
            with self.assertRaises((ValueError, FloatingPointError)):
                ref.validate_material(chi)
            np.testing.assert_array_equal(chi, original)
        volume, k = ref.adapter.problem.volume, ref.adapter.problem.frequency
        kappa = 1 - 1j*k**3*volume/(2*np.pi)
        pole = np.full(ref.chi0.shape, 3*volume/kappa)
        with self.assertRaises((ValueError, FloatingPointError)):
            ref.polarization_to_chi(pole)

    def test_true_constitutive_pole_has_a_specific_rejection_path(self):
        # Permit this nonphysical point only inside a separate error-path fixture,
        # so the pole guard itself is exercised after the ordinary material guard.
        error_config = dict(CONFIG, physical_real_lower=-4., physical_imag_lower=-1.)
        ref = ReferencePhysics(tiny_problem(), config=error_config, device="cpu",
                               book=audit_book(enforce=False))
        kappa = 1-1j*ref.k**3*ref.v/(2*np.pi)
        chi = np.full(ref.N, -3/kappa)
        with self.assertRaisesRegex(ValueError, "CONSTITUTIVE_POLE"):
            ref.validate_material(chi)

    def test_declared_zero_reference_is_rejected_as_zero_signal(self):
        problem = tiny_problem()
        problem.init = np.zeros_like(problem.init)
        with self.assertRaisesRegex(ValueError, "ZERO_REFERENCE_SIGNAL"):
            ReferencePhysics(problem, config=CONFIG, device="cpu", book=audit_book(enforce=False))

    def test_real_material_and_data_error_paths(self):
        ref = self.ref
        with self.assertRaises(ValueError):
            ref.linear(np.zeros(self.A.shape[1], dtype=complex))
        with self.assertRaises(ValueError):
            ref.linear_adjoint(np.zeros(self.A.shape[0], dtype=complex))
        with self.assertRaises(ValueError):
            ref.quadratic(np.zeros(self.A.shape[1], dtype=complex))
        with self.assertRaises(ValueError):
            ref.quadratic(np.zeros(self.A.shape[1]-1))

    def test_tikhonov_decoder_matches_explicit_regularized_normal_equation(self):
        decoder = TikhonovDecoder(self.A, relative=CONFIG["tikhonov_relative"],
                                  device="cpu", book=audit_book(enforce=False))
        data = self.rng.normal(size=self.A.shape[0])
        expected = np.linalg.solve(self.A.T@self.A+decoder.lam*np.eye(self.A.shape[1]),
                                   self.A.T@data)
        np.testing.assert_allclose(decoder.decode(data), expected, rtol=1e-8, atol=1e-8)
        record_measurement("tikhonov_normal_equation_relative_error", relative_error(decoder.decode(data), expected))

    def test_actual_encoder_uses_measured_minus_reference_and_negative_feedback(self):
        decoder = TikhonovDecoder(self.A, relative=CONFIG["tikhonov_relative"],
                                  device="cpu", book=audit_book(enforce=False))
        encoder = PhysicsEncoder(self.ref, decoder, gamma=CONFIG["feedback_gamma"])
        code = self.A @ (self.rng.normal(size=self.A.shape[1])*.002)
        np.testing.assert_allclose(encoder.encode(self.ref.data0+code), code, rtol=1e-12, atol=1e-12)
        x1 = decoder.decode(code)
        correction = decoder.decode(self.ref.quadratic(x1))
        np.testing.assert_allclose(encoder.decode_linear(code), x1, rtol=1e-13, atol=1e-13)
        np.testing.assert_allclose(encoder.decode_feedback(code), x1-correction, rtol=1e-13, atol=1e-13)
        self.assertGreater(np.linalg.norm(correction), 1e-12)
        self.assertGreater(np.linalg.norm(encoder.decode_feedback(code)-(x1+correction)), 1e-12)
        with self.assertRaises(ValueError):
            decoder.decode(code.astype(complex))
        with self.assertRaises(ValueError):
            TikhonovDecoder(np.zeros_like(self.A), book=audit_book(enforce=False))
        with self.assertRaises(ValueError):
            TikhonovDecoder(self.A, relative=0., book=audit_book(enforce=False))


class GaussianNoiseTests(unittest.TestCase):
    def test_complex_noise_has_declared_total_variance_and_packed_half_variances(self):
        rng = np.random.default_rng(23005)
        sigma = .37
        samples = gaussian_noise(rng, (3, 5, 20000), sigma)
        packed = pack(samples)
        self.assertEqual(packed.shape, (30, 20000))
        np.testing.assert_allclose(np.var(packed, axis=1), sigma*sigma/2., rtol=.03, atol=0.)
        self.assertLess(abs(float(np.mean(np.abs(samples)**2))/sigma**2-1), .01)
        self.assertLess(abs(float(np.mean(samples.real)))/sigma, .01)
        self.assertLess(abs(float(np.mean(samples.imag)))/sigma, .01)
        record_measurement("gaussian_packed_noise_variance", {
            "sigma_complex_rms": sigma, "expected_per_real_component": sigma*sigma/2,
            "minimum_sample_variance": float(np.min(np.var(packed, axis=1))),
            "maximum_sample_variance": float(np.max(np.var(packed, axis=1))),
            "complex_mean_energy_ratio": float(np.mean(np.abs(samples)**2))/sigma**2,
            "samples_per_packed_component": packed.shape[1],
        })

    def test_zero_noise_invalid_sigma_and_shared_realization(self):
        for sigma in [-1., np.nan, np.inf]:
            with self.assertRaisesRegex(ValueError, "INVALID_NOISE_SIGMA"):
                gaussian_noise(np.random.default_rng(23006), (3, 5), sigma)
        np.testing.assert_array_equal(gaussian_noise(np.random.default_rng(23006), (3, 5), 0.),
                                      np.zeros((3, 5), complex))
        first = gaussian_noise(np.random.default_rng(23006), (3, 5), .2)
        second = gaussian_noise(np.random.default_rng(23006), (3, 5), .2)
        np.testing.assert_array_equal(first, second)


if __name__ == "__main__":
    unittest.main()
