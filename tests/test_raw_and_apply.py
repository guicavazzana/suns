from pathlib import Path

import numpy as np
import pytest

from suns import (
    OpticalElement,
    apply_correction,
    read_suns_raw,
    read_suns_spectrum,
    write_corrected_csv,
)


SCAN_TEMPLATE = """SpectraSuite Data File
++++++++++++++++++++++++++++++++++++
Date: Thu Jan 01 00:00:00 2026
User: test
Number of Pixels in Processed Spectrum: 3
>>>>>Begin Processed Spectrum<<<<<
Begin Spectral Data
400.00\t{a}
500.00\t{b}
600.00\t{c}
>>>>>End Processed Spectrum<<<<<
"""


def _write_scan(path: Path, a, b, c):
    path.write_text(SCAN_TEMPLATE.format(a=a, b=b, c=c), encoding="utf-8")


def test_read_suns_raw_averages_multiple_scans(tmp_path: Path):
    _write_scan(tmp_path / "scan_000.txt", 10, 20, 30)
    _write_scan(tmp_path / "scan_001.txt", 20, 20, 40)
    df = read_suns_raw(tmp_path)
    assert df["wavelength"].tolist() == [400.0, 500.0, 600.0]
    assert df["dn"].tolist() == pytest.approx([15.0, 20.0, 35.0])


def test_read_suns_raw_raises_when_no_files_match(tmp_path: Path):
    with pytest.raises(ValueError):
        read_suns_raw(tmp_path)


def test_read_suns_raw_accepts_an_explicit_list_of_files(tmp_path: Path):
    a = tmp_path / "scan_a.txt"
    b = tmp_path / "scan_b.txt"
    _write_scan(a, 10, 20, 30)
    _write_scan(b, 20, 20, 40)
    # only these two, hand-picked, regardless of what else is in the folder
    df = read_suns_raw([a, b])
    assert df["wavelength"].tolist() == [400.0, 500.0, 600.0]
    assert df["dn"].tolist() == pytest.approx([15.0, 20.0, 35.0])


def test_read_suns_raw_raises_on_empty_list(tmp_path: Path):
    with pytest.raises(ValueError):
        read_suns_raw([])


def test_read_suns_raw_accepts_a_single_scan_file(tmp_path: Path):
    p = tmp_path / "SUNS_firstlight__0__12-00-00.txt"
    _write_scan(p, 10, 20, 30)
    df = read_suns_raw(p)  # path to ONE file, not a folder
    assert df["wavelength"].tolist() == [400.0, 500.0, 600.0]
    assert df["dn"].tolist() == pytest.approx([10.0, 20.0, 30.0])


def _write_csv(path: Path, wl, val):
    lines = ["wavelength,value"] + [f"{w},{v}" for w, v in zip(wl, val)]
    path.write_text("\n".join(lines), encoding="utf-8")


def test_apply_correction_matches_compute_losses_and_correct_spectrum(tmp_path: Path):
    p = tmp_path / "filter.csv"
    _write_csv(p, [400, 500, 600], [50, 50, 50])  # T = 0.5 everywhere
    element = OpticalElement(name="filter", path=p, kind="direct")

    wl = np.array([400.0, 500.0, 600.0])
    dn = np.array([10.0, 20.0, 30.0])

    result, corrected = apply_correction(wl, dn, [element])
    assert result.total == pytest.approx([0.5, 0.5, 0.5])
    assert corrected == pytest.approx([20.0, 40.0, 60.0])


def test_apply_correction_with_subset_of_elements(tmp_path: Path):
    p1 = tmp_path / "a.csv"
    p2 = tmp_path / "b.csv"
    _write_csv(p1, [400, 500], [50, 50])  # T = 0.5
    _write_csv(p2, [400, 500], [25, 25])  # T = 0.25
    a = OpticalElement(name="a", path=p1, kind="direct")
    b = OpticalElement(name="b", path=p2, kind="direct")

    wl = np.array([400.0, 500.0])
    dn = np.array([10.0, 10.0])

    _, corrected_both = apply_correction(wl, dn, [a, b])
    _, corrected_a_only = apply_correction(wl, dn, [a])

    assert corrected_both == pytest.approx([80.0, 80.0])   # dn / (0.5*0.25)
    assert corrected_a_only == pytest.approx([20.0, 20.0])  # dn / 0.5


def test_plot_curve_writes_a_png(tmp_path: Path):
    p = tmp_path / "curve.csv"
    _write_csv(p, [400, 500, 600], [50, 60, 70])
    element = OpticalElement(name="demo element", path=p, kind="direct")

    out = tmp_path / "curve.png"
    element.plot_curve(out)
    assert out.exists()
    assert out.stat().st_size > 0


def test_write_corrected_csv_round_trips_through_read_suns_spectrum(tmp_path: Path):
    wl = np.array([400.0, 500.0, 600.0])
    dn = np.array([12.5, 34.0, 56.75])

    out = tmp_path / "espectro_corrigido.csv"
    write_corrected_csv(wl, dn, out)

    assert out.exists()
    back = read_suns_spectrum(out)
    assert back["wavelength"].tolist() == pytest.approx(wl.tolist())
    assert back["dn"].tolist() == pytest.approx(dn.tolist())


def test_write_corrected_csv_creates_parent_directories(tmp_path: Path):
    out = tmp_path / "nested" / "dir" / "out.csv"
    write_corrected_csv(np.array([400.0]), np.array([1.0]), out)
    assert out.exists()
