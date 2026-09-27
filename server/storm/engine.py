"""Pure wind, fragility, repair and Monte Carlo calculations for GL-1."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class WindContext:
    """Asset location relative to travel at its baseline peak hour."""

    cross_km: float
    along_km: float
    rmax_km: float
    dp_hpa: float
    latitude: float
    forward_ms: float
    physics: dict[str, float]


def shifted_wind(context: WindContext, pressure_multiplier: float | np.ndarray, offset_km: float | np.ndarray) -> float | np.ndarray:
    """Holland wind when the synthetic track shifts perpendicular to travel."""
    signed_cross = context.cross_km - np.asarray(offset_km)
    radius = np.hypot(signed_cross, context.along_km)
    physics = context.physics
    base = wind_speed(radius, context.rmax_km, context.dp_hpa * pressure_multiplier, context.latitude,
                      air_density=physics["air_density_kg_m3"], holland_b=physics["holland_b"],
                      omega=physics["earth_omega_s"], surface_factor=physics["surface_factor"])
    result = np.maximum(0, base + physics["forward_speed_factor"] * context.forward_ms * signed_cross / np.maximum(radius, 0.001))
    return float(result) if np.ndim(result) == 0 else result


def wind_speed(
    distance_km: float | np.ndarray,
    rmax_km: float,
    dp_hpa: float,
    latitude: float,
    *,
    air_density: float,
    holland_b: float,
    omega: float,
    surface_factor: float,
) -> float | np.ndarray:
    """Holland (1980) symmetric gradient wind, reduced to 10 m height."""
    radius_m = np.maximum(np.asarray(distance_km, dtype=float) * 1000, 1.0)
    ratio_power = np.minimum((rmax_km * 1000 / radius_m) ** holland_b, 700.0)
    coriolis = 2 * omega * np.sin(np.radians(latitude))
    curve = (holland_b * dp_hpa * 100 / air_density) * ratio_power * np.exp(-ratio_power)
    speed = (np.sqrt(curve + (radius_m * coriolis / 2) ** 2) - radius_m * coriolis / 2) * surface_factor
    return float(speed) if np.ndim(speed) == 0 else speed


def damage_exceedance(wind_ms: float, medians_ms: Sequence[float], beta: float) -> tuple[float, float, float, float]:
    """Illustrative lognormal exceedance probabilities, from minor to failed."""
    if wind_ms <= 0:
        return (0.0, 0.0, 0.0, 0.0)
    return tuple(0.5 * math.erfc(-math.log(wind_ms / median) / (beta * math.sqrt(2))) for median in medians_ms)  # type: ignore[return-value]


def expected_cost(exceedance: Sequence[float], replacement_usd: float | None, ratios: Sequence[float]) -> float | None:
    """Expected repair value from mutually exclusive damage states."""
    if replacement_usd is None:
        return None
    states = [exceedance[i] - exceedance[i + 1] for i in range(3)] + [exceedance[3]]
    return replacement_usd * sum(probability * ratio for probability, ratio in zip(states, ratios))


def monte_carlo(
    assets: Sequence[tuple[float, Sequence[float], float, float | None, tuple[float, float] | None, WindContext]],
    *,
    seed: int,
    draws: int,
    dp_multiplier: tuple[float, float],
    cross_track_offset_km: tuple[float, float],
    median_multiplier: tuple[float, float],
    ratios: Sequence[float],
) -> tuple[int, int, int, int]:
    """Draw correlated storm and fragility uncertainty, with optional sourced cost bounds.

    The shifted Holland wind is recalculated at each asset's baseline peak frame.
    No bounds in the cost file means the reference cost is held fixed, never invented.
    """
    covered = [item for item in assets if item[3] is not None]
    if not covered:
        return (0, 0, 0, 0)
    rng = np.random.default_rng(seed)
    pressures = rng.uniform(*dp_multiplier, size=draws)
    offsets = rng.uniform(*cross_track_offset_km, size=draws)
    fragility_scales = rng.uniform(*median_multiplier, size=draws)
    totals = np.zeros(draws)
    for wind, medians, beta, replacement, bounds, context in covered:
        draw_wind = shifted_wind(context, pressures, offsets)
        medians_array = np.asarray(medians, dtype=float)
        z = np.log(np.maximum(draw_wind[:, None], 1e-12) / (medians_array[None, :] * fragility_scales[:, None])) / beta
        # numpy 2 exposes erf only through math; the 1000-draw input is small.
        exceed = np.asarray([0.5 * math.erfc(-float(v) / math.sqrt(2)) for v in z.flat]).reshape(draws, 4)
        states = np.column_stack((exceed[:, :-1] - exceed[:, 1:], exceed[:, -1]))
        unit_costs = rng.uniform(*bounds, size=draws) if bounds is not None else replacement
        totals += (states @ np.asarray(ratios)) * unit_costs
    values = np.percentile(totals, (10, 50, 90))
    return tuple(int(round(float(value) / 1000) * 1000) for value in (*values, totals.mean()))  # type: ignore[return-value]
