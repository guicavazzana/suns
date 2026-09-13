"""Figure generation for per-item and combined loss correction plots."""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple, Union

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

PathLike = Union[str, Path]

STYLE = {
    "font.size": 20,
    "axes.titlesize": 18,
    "axes.labelsize": 18,
    "xtick.labelsize": 16,
    "ytick.labelsize": 16,
    "legend.fontsize": 14,
}

TEXT = {
    "en": dict(
        wavelength="Wavelength (nm)",
        transmittance="Transmittance",
        dn="DN",
        norm_intensity="Normalized intensity",
        original="Original",
        corrected="Corrected",
        loss_title="{name}: transmittance",
        suns_item_title="SUNS spectrum corrected for {name}",
        total_loss_title="Total system loss",
        suns_total_title="Original vs. fully corrected spectrum",
        suns_total_log_title="Original vs. fully corrected spectrum (log scale)",
        suns_norm_title="Comparison of normalized spectra",
    ),
    "pt": dict(
        wavelength="Comprimento de onda (nm)",
        transmittance="Transmitância",
        dn="DN",
        norm_intensity="Intensidade normalizada",
        original="Original",
        corrected="Corrigido",
        loss_title="{name}: transmitância",
        suns_item_title="Espectro do SUNS corrigido para {name}",
        total_loss_title="Perda total do sistema",
        suns_total_title="Espectro original vs. corrigido",
        suns_total_log_title="Espectro original vs. corrigido (escala log)",
        suns_norm_title="Comparação dos espectros normalizados",
    ),
}


def apply_style() -> None:
    plt.rcParams.update(STYLE)


def _save(fig, out_path: PathLike) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)


def plot_component_transmittance(
    name: str,
    wl: np.ndarray,
    T: np.ndarray,
    out_path: PathLike,
    lang: str = "en",
    xlim: Optional[Tuple[float, float]] = None,
):
    apply_style()
    txt = TEXT[lang]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(wl, T)
    ax.set_xlabel(txt["wavelength"])
    ax.set_ylabel(txt["transmittance"])
    ax.set_title(txt["loss_title"].format(name=name))
    if xlim:
        ax.set_xlim(*xlim)
    ax.grid(True)
    _save(fig, out_path)


def plot_spectrum_correction(
    name: str,
    wl: np.ndarray,
    original: np.ndarray,
    corrected: np.ndarray,
    out_path: PathLike,
    lang: str = "en",
    xlim: Optional[Tuple[float, float]] = None,
    log: bool = False,
    title: Optional[str] = None,
):
    apply_style()
    txt = TEXT[lang]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(wl, original, label=txt["original"])
    ax.plot(wl, corrected, label=txt["corrected"])
    if log:
        ax.set_yscale("log")
        ax.grid(True, which="both")
    else:
        ax.grid(True)
    ax.set_xlabel(txt["wavelength"])
    ax.set_ylabel(txt["dn"])
    ax.set_title(title or txt["suns_item_title"].format(name=name))
    if xlim:
        ax.set_xlim(*xlim)
    ax.legend()
    _save(fig, out_path)


def plot_total_loss(
    wl: np.ndarray,
    total_transmittance: np.ndarray,
    out_path: PathLike,
    lang: str = "en",
    xlim: Optional[Tuple[float, float]] = None,
    sci_y: bool = True,
):
    apply_style()
    txt = TEXT[lang]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(wl, total_transmittance)
    if sci_y:
        formatter = ScalarFormatter(useMathText=True)
        formatter.set_scientific(True)
        formatter.set_powerlimits((0, 0))
        ax.yaxis.set_major_formatter(formatter)
    ax.set_xlabel(txt["wavelength"])
    ax.set_ylabel(txt["transmittance"])
    ax.set_title(txt["total_loss_title"])
    if xlim:
        ax.set_xlim(*xlim)
    ax.grid(True)
    _save(fig, out_path)


def plot_normalized_comparison(
    wl: np.ndarray,
    original: np.ndarray,
    corrected: np.ndarray,
    out_path: PathLike,
    lang: str = "en",
    xlim: Optional[Tuple[float, float]] = None,
):
    apply_style()
    txt = TEXT[lang]
    o = original / original.max()
    c = corrected / corrected.max()
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(wl, o, label=txt["original"])
    ax.plot(wl, c, label=txt["corrected"])
    ax.set_xlabel(txt["wavelength"])
    ax.set_ylabel(txt["norm_intensity"])
    ax.set_title(txt["suns_norm_title"])
    if xlim:
        ax.set_xlim(*xlim)
    ax.grid(True)
    ax.legend()
    _save(fig, out_path)
