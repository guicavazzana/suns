"""High-level orchestration: components -> per-item and combined figures."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Tuple, Union

import numpy as np

from . import plotting as plot
from .components import OpticalElement
from .loss import LossResult, compute_losses, correct_spectrum

PathLike = Union[str, Path]


def generate_report(
    suns_wl: np.ndarray,
    suns_dn: np.ndarray,
    components: Iterable[OpticalElement],
    out_dir: PathLike,
    lang: str = "en",
    xlim: Optional[Tuple[float, float]] = (340, 820),
) -> Tuple[LossResult, np.ndarray]:
    """Generate every figure (per optical component, and combined) and
    write them as PNGs under ``out_dir``.

    Layout::

        out_dir/
          per_item/<slug>_transmittance.png       # digitized curve, interpolated
          per_item/<slug>_suns_corrected.png       # SUNS corrected for THAT item alone
          combined/total_loss.png                  # product of every component
          combined/spectrum_original_vs_corrected.png
          combined/spectrum_original_vs_corrected_log.png
          combined/spectrum_normalized.png

    Elements with ``enabled=False`` are skipped entirely: no figures are
    generated for them and they don't enter the combined total.

    Returns the :class:`~suns.loss.LossResult` (per-item and
    total transmittance arrays) and the fully corrected spectrum.
    """
    out_dir = Path(out_dir)
    components = [c for c in components if c.enabled]
    result = compute_losses(components, suns_wl)

    per_item_dir = out_dir / "per_item"
    combined_dir = out_dir / "combined"

    for comp in components:
        T = result.per_item[comp.name]
        slug = comp.slug()
        plot.plot_component_transmittance(
            comp.name, suns_wl, T, per_item_dir / f"{slug}_transmittance.png",
            lang=lang, xlim=xlim,
        )
        corrected = correct_spectrum(suns_dn, T)
        plot.plot_spectrum_correction(
            comp.name, suns_wl, suns_dn, corrected,
            per_item_dir / f"{slug}_suns_corrected.png", lang=lang, xlim=xlim,
        )

    corrected_total = correct_spectrum(suns_dn, result.total)

    plot.plot_total_loss(
        suns_wl, result.total, combined_dir / "total_loss.png", lang=lang, xlim=xlim,
    )
    plot.plot_spectrum_correction(
        "all components", suns_wl, suns_dn, corrected_total,
        combined_dir / "spectrum_original_vs_corrected.png", lang=lang, xlim=xlim,
        title=plot.TEXT[lang]["suns_total_title"],
    )
    plot.plot_spectrum_correction(
        "all components", suns_wl, suns_dn, corrected_total,
        combined_dir / "spectrum_original_vs_corrected_log.png", lang=lang, xlim=xlim,
        log=True, title=plot.TEXT[lang]["suns_total_log_title"],
    )
    plot.plot_normalized_comparison(
        suns_wl, suns_dn, corrected_total,
        combined_dir / "spectrum_normalized.png", lang=lang, xlim=xlim,
    )

    return result, corrected_total
