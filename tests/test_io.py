from pathlib import Path

import pytest

from suns import read_digitized_csv, read_suns_spectrum

CLEAN_CSV = """WAVELENGTH (nm),PERCENT
201.591,37.9487
216.224,40.1188
236.464,41.3878
"""

RAW_CSV = """"Relative Transmission(Wavelength (nm)), created by Plot Digitizer, 2.6.12"
"Date: 13/09/2026, 15:32:33"


3
Wavelength (nm),Relative Transmission
198.071,81.4550,
202.098,80.8890,
202.944,79.5522,
"""


@pytest.fixture
def clean_csv(tmp_path: Path) -> Path:
    p = tmp_path / "clean.csv"
    p.write_text(CLEAN_CSV, encoding="utf-8")
    return p


@pytest.fixture
def raw_csv(tmp_path: Path) -> Path:
    p = tmp_path / "raw.csv"
    p.write_text(RAW_CSV, encoding="utf-8")
    return p


def test_read_clean_csv(clean_csv: Path):
    df = read_digitized_csv(clean_csv)
    assert list(df.columns) == ["wavelength", "value"]
    assert len(df) == 3
    assert df["wavelength"].tolist() == pytest.approx([201.591, 216.224, 236.464])
    assert df["value"].tolist() == pytest.approx([37.9487, 40.1188, 41.3878])


def test_read_raw_plotdigitizer_csv_skips_preamble_and_trailing_comma(raw_csv: Path):
    df = read_digitized_csv(raw_csv)
    assert len(df) == 3
    assert df["wavelength"].tolist() == pytest.approx([198.071, 202.098, 202.944])
    assert df["value"].tolist() == pytest.approx([81.4550, 80.8890, 79.5522])


def test_read_digitized_csv_averages_duplicate_wavelengths(tmp_path: Path):
    p = tmp_path / "dup.csv"
    p.write_text("wl,val\n100,10\n100,20\n200,30\n", encoding="utf-8")
    df = read_digitized_csv(p)
    assert len(df) == 2
    assert df.loc[df["wavelength"] == 100, "value"].iloc[0] == pytest.approx(15.0)


def test_read_digitized_csv_raises_on_no_data(tmp_path: Path):
    p = tmp_path / "empty.csv"
    p.write_text("just,text\nno,numbers,here\n", encoding="utf-8")
    with pytest.raises(ValueError):
        read_digitized_csv(p)


def test_read_suns_spectrum(tmp_path: Path):
    p = tmp_path / "suns.csv"
    p.write_text("wavelength,dn\n200,1.0\n195,2.0\n", encoding="utf-8")
    df = read_suns_spectrum(p)
    assert df["wavelength"].tolist() == [195, 200]


def test_read_suns_spectrum_bad_columns(tmp_path: Path):
    p = tmp_path / "bad.csv"
    p.write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError):
        read_suns_spectrum(p)
