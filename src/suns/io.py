"""Readers for digitized optical-curve CSVs and SUNS spectrum data."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Union

import pandas as pd

PathLike = Union[str, Path]


def read_digitized_csv(path: PathLike) -> pd.DataFrame:
    """Robustly read a digitized (e.g. PlotDigitizer) CSV export.

    Handles both shapes seen in this project without needing to know in
    advance which one a given file uses:

    - "clean": the first line is already the real header, e.g.::

        WAVELENGTH (nm),PERCENT
        201.591,37.9487
        ...

    - "raw" (PlotDigitizer's native export): a quoted metadata line, a
      "Date: ..." line, blank lines, a bare point-count line, the real
      header, then data rows that may end with a trailing comma, e.g.::

        "Relative Transmission(Wavelength (nm)), created by Plot Digitizer, 2.6.12"
        "Date: 13/09/2026, 15:32:33"


        179
        Wavelength (nm),Relative Transmission
        198.071,81.4550,
        ...

    The parser treats any line whose first two comma-separated tokens both
    parse as floats as a ``(wavelength, value)`` data row; every other line
    (metadata, date, point count, header, blank) is silently skipped. This
    makes it agnostic to which shape the file is in, and to which exact
    column names/typos the header uses.

    Rows are sorted by wavelength; duplicate wavelengths are averaged.
    """
    path = Path(path)
    rows = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue
            parts = [p.strip().strip('"') for p in line.split(",")]
            if len(parts) < 2:
                continue
            try:
                x = float(parts[0].replace(",", "."))
                y = float(parts[1].replace(",", "."))
            except ValueError:
                continue
            rows.append((x, y))

    if not rows:
        raise ValueError(f"No numeric (wavelength, value) rows found in {path}")

    df = pd.DataFrame(rows, columns=["wavelength", "value"])
    df = df.groupby("wavelength", as_index=False)["value"].mean()
    df = df.sort_values("wavelength").reset_index(drop=True)
    return df


def read_suns_spectrum(path: PathLike) -> pd.DataFrame:
    """Load an already-averaged SUNS spectrum CSV (columns: ``wavelength``, ``dn``).

    Use this when you (or :func:`read_suns_raw`) already produced a single
    averaged CSV. To start straight from the spectrometer's raw scans, use
    :func:`read_suns_raw` instead.
    """
    path = Path(path)
    df = pd.read_csv(path)
    expected = {"wavelength", "dn"}
    if not expected.issubset(df.columns):
        raise ValueError(f"{path} must have columns {expected}, got {list(df.columns)}")
    return df.sort_values("wavelength").reset_index(drop=True)


def _read_single_scan(path: Path) -> pd.DataFrame:
    """Parse one raw spectrometer scan (e.g. an Ocean Insight ``.txt`` export
    with a ``Begin Spectral Data`` section) into a ``(wavelength, dn)`` table."""
    rows = []
    reading = False
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for raw_line in f:
            line = raw_line.strip()
            if "Begin Spectral Data" in line:
                reading = True
                continue
            if not reading or not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            try:
                wl = float(parts[0].replace(",", "."))
                dn = float(parts[1].replace(",", "."))
            except ValueError:
                continue
            rows.append((wl, dn))
    return pd.DataFrame(rows, columns=["wavelength", "dn"])


def read_suns_raw(
    folder: Union[PathLike, Iterable[PathLike]],
    pattern: str = "*.txt",
) -> pd.DataFrame:
    """Load the SUNS's raw spectrometer scan(s) straight from disk and
    average them into a single spectrum - the raw-data entry point, for when
    you have the original ``.txt`` file(s) instead of an already-averaged
    CSV (that case is :func:`read_suns_spectrum`).

    Parameters
    ----------
    folder:
        Any of:

        - a **single scan file** (e.g. one ``.txt`` you just pulled off the
          SUNS after an observation) - read on its own, no averaging needed;
        - a **directory** containing several scans, one ``.txt`` per file
          (each with a ``Begin Spectral Data`` section, one ``wavelength dn``
          pair per line) - every file matching ``pattern`` is read and
          averaged together;
        - an **explicit list/tuple of file paths** - e.g. when you want to
          average only a hand-picked subset of scans, or files that live in
          more than one folder. ``pattern`` is ignored in this case.
    pattern:
        Glob pattern selecting which files to read when ``folder`` is a
        directory (default ``"*.txt"``); ignored otherwise.

    Returns
    -------
    A ``(wavelength, dn)`` DataFrame, sorted by wavelength (duplicate
    wavelengths - e.g. from averaging multiple scans - are averaged too).
    Feed this straight into :func:`~suns.loss.apply_correction` or
    :func:`~suns.pipeline.generate_report`.

    Examples
    --------
    >>> suns.read_suns_raw("scan.txt")                       # one file
    >>> suns.read_suns_raw("SUNS_pre-firstlight")             # a whole folder
    >>> suns.read_suns_raw(["scan_a.txt", "scan_b.txt"])      # a hand-picked subset
    """
    if isinstance(folder, (str, Path)):
        path = Path(folder)
        if path.is_file():
            files = [path]
        else:
            files = sorted(path.glob(pattern))
            if not files:
                raise ValueError(f"No files matching {pattern!r} found in {path}")
    else:
        files = [Path(p) for p in folder]
        if not files:
            raise ValueError("read_suns_raw() got an empty list of files")

    frames = [_read_single_scan(p) for p in files]
    df = pd.concat(frames, ignore_index=True)
    if df.empty:
        raise ValueError(
            f"No 'Begin Spectral Data' readings found in any of the "
            f"{len(files)} file(s): {[str(p) for p in files]}"
        )

    df = df.groupby("wavelength", as_index=False)["dn"].mean()
    return df.sort_values("wavelength").reset_index(drop=True)


def write_corrected_csv(wl, dn, path: PathLike) -> None:
    """Save a (corrected or raw) spectrum as a CSV with columns
    ``wavelength``, ``dn`` - the same shape :func:`read_suns_spectrum` reads
    back. Use this after :func:`~suns.loss.apply_correction` to keep the
    numeric result of a correction (one element, several, or all of them),
    not just its plot.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"wavelength": wl, "dn": dn}).to_csv(path, index=False)
