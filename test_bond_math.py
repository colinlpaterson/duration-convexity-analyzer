"""Tests for the pricing and sensitivity invariants in bond_math."""

import numpy as np
import pytest

from bond_math import (
    approximation_curves,
    bond_price,
    cash_flows,
    risk_measures,
)

FACE = 1_000.0
# Reference bond used by the finite-difference and Taylor tests.
COUPON, MATURITY, YTM, FREQ = 0.06, 12, 0.045, 2


@pytest.mark.parametrize("payments_per_year", [1, 2, 4])
def test_prices_at_par_when_coupon_equals_yield(payments_per_year):
    price = bond_price(FACE, 0.05, 10, 0.05, payments_per_year)
    assert price == pytest.approx(FACE, abs=1e-8)


def test_zero_coupon_matches_closed_form():
    price = bond_price(FACE, 0.0, 5, 0.06, 2)
    assert price == pytest.approx(FACE / 1.03**10, rel=1e-12)


def test_bond_price_scalar_returns_float():
    assert isinstance(bond_price(FACE, 0.05, 10, 0.05, FREQ), float)


def test_cash_flows_structure():
    times, flows = cash_flows(FACE, 0.06, 3, FREQ)
    assert times.tolist() == [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    assert flows[:-1].tolist() == [30.0] * 5
    assert flows[-1] == pytest.approx(FACE + 30.0)


def test_price_decreases_with_yield():
    yields = np.linspace(0.001, 0.15, 50)
    prices = bond_price(FACE, COUPON, 10, yields, FREQ)
    assert np.all(np.diff(prices) < 0)


def test_zero_coupon_macaulay_duration_equals_maturity():
    _, macaulay, modified, _ = risk_measures(FACE, 0.0, 7, 0.05, FREQ)
    assert macaulay == pytest.approx(7.0, rel=1e-10)
    assert modified == pytest.approx(7.0 / 1.025, rel=1e-10)


def test_modified_duration_matches_finite_difference():
    price, _, modified, _ = risk_measures(FACE, COUPON, MATURITY, YTM, FREQ)
    h = 1e-6
    p_up = bond_price(FACE, COUPON, MATURITY, YTM + h, FREQ)
    p_dn = bond_price(FACE, COUPON, MATURITY, YTM - h, FREQ)
    modified_fd = -(p_up - p_dn) / (2 * h * price)
    assert modified == pytest.approx(modified_fd, rel=1e-6)


def test_convexity_matches_finite_difference():
    price, _, _, convexity = risk_measures(FACE, COUPON, MATURITY, YTM, FREQ)
    h = 1e-6
    p_up = bond_price(FACE, COUPON, MATURITY, YTM + h, FREQ)
    p_dn = bond_price(FACE, COUPON, MATURITY, YTM - h, FREQ)
    convexity_fd = (p_up + p_dn - 2 * price) / (h**2 * price)
    # Loose tolerance: the second-derivative finite difference carries
    # O(eps/h^2) cancellation error.
    assert convexity == pytest.approx(convexity_fd, rel=1e-3)


def test_approximation_at_base_yield_returns_base_price():
    price, _, modified, convexity = risk_measures(FACE, COUPON, MATURITY, YTM, FREQ)
    duration_est, convexity_est = approximation_curves(
        price, modified, convexity, YTM, np.array([YTM])
    )
    assert duration_est[0] == pytest.approx(price)
    assert convexity_est[0] == pytest.approx(price)


@pytest.mark.parametrize("shift", [-0.02, -0.01, 0.01, 0.02])
def test_convexity_adjusted_approximation_beats_duration_only(shift):
    price, _, modified, convexity = risk_measures(FACE, COUPON, MATURITY, YTM, FREQ)
    exact = bond_price(FACE, COUPON, MATURITY, YTM + shift, FREQ)
    duration_est, convexity_est = approximation_curves(
        price, modified, convexity, YTM, np.array([YTM + shift])
    )
    duration_error = abs(duration_est[0] - exact)
    convexity_error = abs(convexity_est[0] - exact)
    assert convexity_error < duration_error
    assert convexity_error / exact < 0.005


@pytest.mark.parametrize("shift", [-0.02, 0.02])
def test_duration_only_estimate_underestimates_price(shift):
    # Positive convexity means the linear estimate lies below the true
    # price curve on both sides of the base yield.
    price, _, modified, convexity = risk_measures(FACE, COUPON, MATURITY, YTM, FREQ)
    exact = bond_price(FACE, COUPON, MATURITY, YTM + shift, FREQ)
    duration_est, _ = approximation_curves(
        price, modified, convexity, YTM, np.array([YTM + shift])
    )
    assert duration_est[0] < exact
