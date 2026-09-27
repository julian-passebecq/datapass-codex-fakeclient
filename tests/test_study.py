from pathlib import Path
import hashlib
import json
import math
import subprocess
import sys
import pytest
from scripts.make_data import make_data
from windstudy import lift_coefficient, power_kw, read_site, study

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "data/site_a_wind.csv"


def test_small_angle_and_stall_cap():
    assert lift_coefficient(5) == pytest.approx(2 * math.pi * math.radians(5))
    assert lift_coefficient(80) == lift_coefficient(15)
    assert lift_coefficient(-80) == -lift_coefficient(15)


def test_power_boundaries():
    assert [power_kw(v) for v in (0, 3, 12, 24.9, 25, 40)] == [0, 0, 10, 10, 0, 0]
    assert 0 < power_kw(8) < 10


def test_invalid_numbers():
    for value in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ValueError):
            power_kw(value)
        with pytest.raises(ValueError):
            lift_coefficient(value)
    for args in ((-1, 10), (4, 0), (4, -1)):
        with pytest.raises(ValueError):
            power_kw(*args)
    with pytest.raises(ValueError):
        lift_coefficient(5, 0)


def test_seeded_data_matches_committed_bytes(tmp_path):
    path = tmp_path / "site.csv"
    make_data(path)
    assert path.read_bytes() == SITE.read_bytes()
    assert len(read_site(path)) == 1000


def test_annualization_and_provenance():
    result = study(SITE)
    assert result["version"] == "1.0" and result["synthetic"] is True
    assert result["annual_energy_kwh_estimate"] == pytest.approx(result["sample_energy_kwh"] / 1000 * 8760)
    assert result["source_sha256"] == hashlib.sha256(SITE.read_bytes()).hexdigest()
    assert result == study(SITE)
    assert result["result_id"] != study(SITE, rated_kw=20)["result_id"]


def test_known_constant_site(tmp_path):
    path = tmp_path / "constant.csv"
    path.write_text("hour,wind_speed_mps\n0,12\n1,12\n", encoding="utf-8")
    assert study(path)["annual_energy_kwh_estimate"] == 87600


def test_invalid_csv_fails_closed(tmp_path):
    for raw in ("hour,wind_speed_mps\n", "hour,speed\n0,5\n",
                "hour,wind_speed_mps\n0,-1\n", "hour,wind_speed_mps\n0,NaN\n",
                "hour,wind_speed_mps\n0,4\n2,5\n", "hour,wind_speed_mps\n0,4\n0,5\n",
                "hour,wind_speed_mps\n0,4,extra\n", "hour,wind_speed_mps\n0\n"):
        path = tmp_path / "bad.csv"
        path.write_text(raw, encoding="utf-8")
        with pytest.raises(ValueError):
            read_site(path)


def test_cli_and_atomic_output(tmp_path):
    command = [sys.executable, "-m", "windstudy", "run", "--site", str(SITE), "--out", str(tmp_path)]
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True)
    output = tmp_path / "study_result.json"
    assert json.loads(output.read_text()) == study(SITE)
    original = output.read_bytes()
    bad = subprocess.run(command + ["--rated-kw", "nan"], cwd=ROOT, capture_output=True)
    assert bad.returncode == 1 and output.read_bytes() == original
    assert not list(tmp_path.glob(".study-*"))


def test_notebook_has_saved_table_and_chart():
    book = json.loads((ROOT / "notebooks/explore_site_a.ipynb").read_text())
    outputs = [o for c in book["cells"] for o in c.get("outputs", [])]
    assert any("text/html" in o.get("data", {}) for o in outputs)
    assert any("image/svg+xml" in o.get("data", {}) for o in outputs)
    assert all(o["output_type"] != "error" for o in outputs)


def test_no_coordination_files_in_native_repository():
    assert not (ROOT / ".datapass").exists()
    assert not (ROOT / "datapass-auto.json").exists()
