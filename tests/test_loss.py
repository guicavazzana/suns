from pathlib import Path

import numpy as np
import pytest

from suns import OpticalElement, compute_losses, correct_spectrum


def _write_csv(path: Path, wl, val):
    lines = ["wavelength,value"] + [f"{w},{v}" for w, v in zip(wl, val)]
    path.write_text("\n".join(lines), encoding="utf-8")


def test_direct_component_transmittance_is_value_over_100(tmp_path: Path):
    p = tmp_path / "direct.csv"
    _write_csv(p, [400, 500, 600], [50, 80, 100])
    comp = OpticalElement(name="filter", path=p, kind="direct")
    T = comp.transmittance(np.array([400.0, 500.0, 600.0]))
    assert T == pytest.approx([0.5, 0.8, 1.0])


def test_reflection_loss_component_inverts(tmp_path: Path):
    p = tmp_path / "refl.csv"
    _write_csv(p, [400, 500, 600], [2, 1, 3])
    comp = OpticalElement(name="AR coating", path=p, kind="reflection_loss")
    T = comp.transmittance(np.array([400.0, 500.0, 600.0]))
    assert T == pytest.approx([0.98, 0.99, 0.97])


def test_transmittance_is_clipped_to_unit_interval(tmp_path: Path):
    p = tmp_path / "over.csv"
    _write_csv(p, [400, 500], [-10, 150])
    comp = OpticalElement(name="weird", path=p, kind="direct")
    with pytest.warns(UserWarning):
        T = comp.transmittance(np.array([400.0, 500.0]))
    assert T.min() >= 0.0
    assert T.max() <= 1.0


def test_out_of_range_grid_warns(tmp_path: Path):
    p = tmp_path / "range.csv"
    _write_csv(p, [400, 500], [50, 60])
    comp = OpticalElement(name="c", path=p, kind="direct")
    with pytest.warns(UserWarning, match="extends beyond digitized data range"):
        comp.transmittance(np.array([300.0, 400.0, 500.0]))


def test_compute_losses_combines_components_multiplicatively(tmp_path: Path):
    p1 = tmp_path / "a.csv"
    p2 = tmp_path / "b.csv"
    _write_csv(p1, [400, 500], [50, 50])   # T = 0.5
    _write_csv(p2, [400, 500], [10, 10])   # reflection_loss -> T = 0.9
    comps = [
        OpticalElement(name="a", path=p1, kind="direct"),
        OpticalElement(name="b", path=p2, kind="reflection_loss"),
    ]
    wl = np.array([400.0, 500.0])
    result = compute_losses(comps, wl)
    assert result.per_item["a"] == pytest.approx([0.5, 0.5])
    assert result.per_item["b"] == pytest.approx([0.9, 0.9])
    assert result.total == pytest.approx([0.45, 0.45])


def test_compute_losses_skips_disabled_components(tmp_path: Path):
    p1 = tmp_path / "a.csv"
    p2 = tmp_path / "b.csv"
    _write_csv(p1, [400, 500], [50, 50])   # T = 0.5
    _write_csv(p2, [400, 500], [10, 10])   # would be T = 0.1, but disabled
    comps = [
        OpticalElement(name="a", path=p1, kind="direct"),
        OpticalElement(name="b", path=p2, kind="direct", enabled=False),
    ]
    wl = np.array([400.0, 500.0])
    result = compute_losses(comps, wl)
    assert "b" not in result.per_item
    assert result.total == pytest.approx([0.5, 0.5])


def test_correct_spectrum_divides_by_transmittance():
    spectrum = np.array([10.0, 20.0])
    T = np.array([0.5, 0.25])
    corrected = correct_spectrum(spectrum, T)
    assert corrected == pytest.approx([20.0, 80.0])


def test_component_slug():
    c = OpticalElement(name="PDOT-2 beamsplitter (Reflec.)", path="x.csv")
    assert c.slug() == "pdot_2_beamsplitter_reflec"
