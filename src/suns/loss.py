"""Combine per-component transmittances into a total system loss."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

import numpy as np

from .components import OpticalElement


@dataclass
class LossResult:
    wl: np.ndarray
    per_item: Dict[str, np.ndarray]  # element name -> transmittance array
    total: np.ndarray  # cumulative (product of all) transmittance


def compute_losses(components: Iterable[OpticalElement], wl_grid: np.ndarray) -> LossResult:
    """Interpolate every *enabled* component onto ``wl_grid`` and multiply
    them together. Elements with ``enabled=False`` are skipped entirely
    (absent from both ``per_item`` and ``total``) - use that to leave an
    element defined for reference while excluding it from the combination."""
    per_item: Dict[str, np.ndarray] = {}
    total = np.ones_like(wl_grid, dtype=float)
    for comp in components:
        if not comp.enabled:
            continue
        T = comp.transmittance(wl_grid)
        per_item[comp.name] = T
        total = total * T
    return LossResult(wl=wl_grid, per_item=per_item, total=total)


def correct_spectrum(spectrum: np.ndarray, transmittance: np.ndarray) -> np.ndarray:
    """Recover the spectrum before a loss, given the measured spectrum and
    the transmittance of what stood in the way."""
    return spectrum / transmittance


def apply_correction(
    suns_wl: np.ndarray,
    suns_dn: np.ndarray,
    elements: Iterable[OpticalElement],
) -> Tuple[LossResult, np.ndarray]:
    """The one function you call to correct the SUNS spectrum for a chosen
    set of optical elements - pass every element for the full end-to-end
    calibration, or any subset (one filter, a few, whatever you want to
    isolate) to correct for only those. Equivalent to calling
    :func:`compute_losses` followed by :func:`correct_spectrum`, bundled
    into a single call.

    Returns the :class:`LossResult` (so you can inspect ``.per_item`` and
    ``.total``) and the corrected spectrum.
    """
    result = compute_losses(elements, suns_wl)
    corrected = correct_spectrum(suns_dn, result.total)
    return result, corrected
