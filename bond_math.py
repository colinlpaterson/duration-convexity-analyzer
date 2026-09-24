"""Bond pricing and interest-rate sensitivity calculations."""

from __future__ import annotations

import numpy as np

# Tolerance for treating maturity * payments_per_year as a whole number.
_PERIOD_TOLERANCE = 1e-9


def _validate_yield(
    yield_to_maturity: float | np.ndarray, payments_per_year: int
) -> np.ndarray:
    """Return yields as an array, rejecting values that break discounting."""
    yields = np.asarray(yield_to_maturity, dtype=float)
    if not np.all(np.isfinite(yields)):
        raise ValueError("yield_to_maturity must be finite")
    if np.any(1 + yields / payments_per_year <= 0):
        raise ValueError(
            "yield_to_maturity must be greater than -payments_per_year "
            "(each period's discount factor must be positive)"
        )
    return yields


def cash_flows(
    face_value: float,
    coupon_rate: float,
    maturity_years: float,
    payments_per_year: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Return payment times (years) and cash flows for a plain fixed-rate bond.

    Raises:
        ValueError: If any term is out of range, or if the maturity is not a
            whole number of coupon periods.
    """
    if isinstance(payments_per_year, bool) or not isinstance(
        payments_per_year, (int, np.integer)
    ):
        raise ValueError("payments_per_year must be an integer")
    if payments_per_year <= 0:
        raise ValueError("payments_per_year must be positive")
    if not np.isfinite(face_value) or face_value <= 0:
        raise ValueError("face_value must be positive")
    if not np.isfinite(coupon_rate) or coupon_rate < 0:
        raise ValueError("coupon_rate must be non-negative")
    if not np.isfinite(maturity_years) or maturity_years <= 0:
        raise ValueError("maturity_years must be positive")

    exact_periods = maturity_years * payments_per_year
    periods = int(round(exact_periods))
    if periods < 1 or abs(exact_periods - periods) > _PERIOD_TOLERANCE:
        raise ValueError(
            "maturity_years must be a whole number of coupon periods "
            f"(got {maturity_years} years at {payments_per_year} payments/year)"
        )
    times = np.arange(1, periods + 1, dtype=float) / payments_per_year
    flows = np.full(periods, face_value * coupon_rate / payments_per_year)
    flows[-1] += face_value
    return times, flows


def bond_price(
    face_value: float,
    coupon_rate: float,
    maturity_years: float,
    yield_to_maturity: float | np.ndarray,
    payments_per_year: int,
) -> float | np.ndarray:
    """Price a plain fixed-rate bond from its nominal annual yield."""
    times, flows = cash_flows(
        face_value, coupon_rate, maturity_years, payments_per_year
    )
    yields = _validate_yield(yield_to_maturity, payments_per_year)
    discount_base = 1 + yields[..., None] / payments_per_year
    prices = np.sum(flows / discount_base ** (times * payments_per_year), axis=-1)
    return float(prices) if prices.ndim == 0 else prices


def risk_measures(
    face_value: float,
    coupon_rate: float,
    maturity_years: float,
    yield_to_maturity: float,
    payments_per_year: int,
) -> tuple[float, float, float, float]:
    """Return price, Macaulay duration, modified duration, and convexity."""
    times, flows = cash_flows(
        face_value, coupon_rate, maturity_years, payments_per_year
    )
    period_numbers = times * payments_per_year
    _validate_yield(yield_to_maturity, payments_per_year)
    period_yield = yield_to_maturity / payments_per_year
    present_values = flows / (1 + period_yield) ** period_numbers
    price = float(np.sum(present_values))

    macaulay_duration = float(np.sum(times * present_values) / price)
    modified_duration = macaulay_duration / (1 + period_yield)
    convexity = float(
        np.sum(
            flows
            * period_numbers
            * (period_numbers + 1)
            / (1 + period_yield) ** (period_numbers + 2)
        )
        / (price * payments_per_year**2)
    )
    return price, macaulay_duration, modified_duration, convexity


def approximation_curves(
    base_price: float,
    modified_duration: float,
    convexity: float,
    base_yield: float,
    yields: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return first- and second-order price approximations around base yield."""
    yield_change = yields - base_yield
    duration_prices = base_price * (1 - modified_duration * yield_change)
    convexity_prices = base_price * (
        1 - modified_duration * yield_change + 0.5 * convexity * yield_change**2
    )
    return duration_prices, convexity_prices
