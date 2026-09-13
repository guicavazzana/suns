from .components import OpticalElement
from .io import (
    read_digitized_csv,
    read_suns_raw,
    read_suns_spectrum,
    write_corrected_csv,
)
from .loss import LossResult, apply_correction, compute_losses, correct_spectrum
from .pipeline import generate_report
from .plotting import plot_component_transmittance, plot_spectrum_correction

__version__ = "1.0.0"

__all__ = [
    "OpticalElement",
    "read_digitized_csv",
    "read_suns_raw",
    "read_suns_spectrum",
    "write_corrected_csv",
    "LossResult",
    "compute_losses",
    "apply_correction",
    "correct_spectrum",
    "generate_report",
    "plot_component_transmittance",
    "plot_spectrum_correction",
]
