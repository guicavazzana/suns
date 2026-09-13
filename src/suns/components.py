"""Optical components in the SUNS light path."""
from __future__ import annotations

import re
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional, Tuple, Union

import numpy as np
import pandas as pd

from .io import read_digitized_csv
from .plotting import plot_component_transmittance

Kind = Literal["direct", "reflection_loss"]


@dataclass
class OpticalElement:
    """A single optical element, described by a digitized curve.

    Parameters
    ----------
    name:
        Human-readable name, used in plot titles/legends and (slugified)
        in output file names.
    path:
        Path to the digitized CSV (see :func:`suns.io.read_digitized_csv`).
    kind:
        What the digitized *value* means for the light that reaches the SUNS:

        - ``"direct"``: the value already IS the transmittance of this
          element for the light path of interest (a filter's transmission,
          a fiber's transmission, or the reflectance off the *working* port
          of a beamsplitter/dichroic when that is the port the SUNS sits on).
        - ``"reflection_loss"``: the value is a reflectance that takes light
          AWAY from the desired transmission path (e.g. residual reflectance
          of an AR-coated lens surface); transmittance = ``1 - value``.
    percent:
        Whether the digitized values are on a 0-100 scale (default) rather
        than already a 0-1 fraction.
    enabled:
        Set to ``False`` to keep this element defined (documentation of what
        exists in the light path) but exclude it from
        :func:`~suns.loss.compute_losses` / :func:`~suns.pipeline.generate_report`
        without deleting it from your list - handy for "what if this element
        weren't there" comparisons.
    """

    name: str
    path: Union[str, Path]
    kind: Kind = "direct"
    percent: bool = True
    enabled: bool = True
    _df: Optional[pd.DataFrame] = field(default=None, init=False, repr=False)

    def slug(self) -> str:
        s = re.sub(r"[^a-z0-9]+", "_", self.name.strip().lower()).strip("_")
        return s or "component"

    def data(self) -> pd.DataFrame:
        """The raw digitized (wavelength, value) curve, as read from ``path``
        - e.g. print/inspect it directly (``element.data()``) to see exactly
        what was digitized for this element, before any interpolation or
        ``kind`` conversion."""
        if self._df is None:
            self._df = read_digitized_csv(self.path)
        return self._df

    def plot_curve(
        self,
        out_path: Union[str, Path],
        wl_grid: Optional[np.ndarray] = None,
        lang: str = "en",
        xlim: Optional[Tuple[float, float]] = None,
    ) -> None:
        """Plot just this element's transmittance curve to ``out_path`` (a
        PNG), without needing :func:`~suns.pipeline.generate_report`'s full
        pipeline - handy to look at one optical element's data on its own.

        If ``wl_grid`` is omitted, plots on the element's own digitized
        wavelength points (no interpolation); pass a grid (e.g. the SUNS's
        wavelength array) to see it as it will actually be used in a
        correction.
        """
        if wl_grid is None:
            wl_grid = self.data()["wavelength"].values
        T = self.transmittance(wl_grid)
        plot_component_transmittance(self.name, wl_grid, T, out_path, lang=lang, xlim=xlim)

    def transmittance(self, wl_grid: np.ndarray, clip: bool = True) -> np.ndarray:
        """Interpolate this component's transmittance onto ``wl_grid``.

        Wavelengths outside the digitized data's range are flat-extrapolated
        (``numpy.interp`` behavior) and trigger a warning.
        """
        df = self.data()
        wl, val = df["wavelength"].values, df["value"].values
        interp = np.interp(wl_grid, wl, val)
        frac = interp / 100.0 if self.percent else interp

        if self.kind == "direct":
            T = frac
        elif self.kind == "reflection_loss":
            T = 1.0 - frac
        else:
            raise ValueError(f"unknown kind {self.kind!r} for component {self.name!r}")

        lo, hi = wl.min(), wl.max()
        if wl_grid.min() < lo or wl_grid.max() > hi:
            warnings.warn(
                f"[{self.name}] requested grid ({wl_grid.min():.1f}-{wl_grid.max():.1f} nm) "
                f"extends beyond digitized data range ({lo:.1f}-{hi:.1f} nm); "
                "edges are flat-extrapolated."
            )

        if clip:
            out_of_bounds = (T < 0.0) | (T > 1.0)
            if np.any(out_of_bounds):
                warnings.warn(
                    f"[{self.name}] transmittance out of [0,1] before clipping "
                    f"(min={T.min():.3f}, max={T.max():.3f})."
                )
            T = np.clip(T, 0.0, 1.0)
        return T
