"""Versioned toy calculations using SI inputs and explicit simplifications."""
from __future__ import annotations
import csv
import hashlib
import io
import json
import math
from pathlib import Path

MODEL_VERSION = "1.0"


def finite(value: float, label: str) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{label} must be finite")
    return value


def lift_coefficient(alpha_deg: float, stall_deg: float = 15.0) -> float:
    """2*pi*alpha in radians, clipped symmetrically; not post-stall physics."""
    alpha = finite(alpha_deg, "angle")
    stall = finite(stall_deg, "stall angle")
    if not 0 < stall < 90:
        raise ValueError("stall angle must be between 0 and 90 degrees")
    return 2.0 * math.pi * math.radians(max(-stall, min(stall, alpha)))


def power_kw(speed_mps: float, rated_kw: float = 10.0) -> float:
    """Toy cubic curve: cut-in 3, rated speed 12, cut-out 25 m/s."""
    speed = finite(speed_mps, "wind speed")
    rated = finite(rated_kw, "rated power")
    if speed < 0 or rated <= 0:
        raise ValueError("wind speed must be nonnegative and rated power positive")
    if speed < 3.0 or speed >= 25.0:
        return 0.0
    return rated * min(1.0, (speed ** 3 - 3.0 ** 3) / (12.0 ** 3 - 3.0 ** 3))


def _read_site_bytes(raw: bytes) -> list[float]:
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    if reader.fieldnames != ["hour", "wind_speed_mps"]:
        raise ValueError("CSV must have exactly: hour,wind_speed_mps")
    speeds: list[float] = []
    previous = None
    for row in reader:
        if None in row or any(v is None for v in row.values()):
            raise ValueError("CSV row has a missing or extra column")
        hour = int(row["hour"])
        speed = finite(row["wind_speed_mps"], "wind speed")
        if hour < 0 or speed < 0 or (previous is not None and hour != previous + 1):
            raise ValueError("hours must be nonnegative and consecutive; speeds nonnegative")
        previous = hour
        speeds.append(speed)
    if not speeds:
        raise ValueError("site has no observations")
    return speeds


def read_site(path: str | Path) -> list[float]:
    return _read_site_bytes(Path(path).read_bytes())


def study(path: str | Path, rated_kw: float = 10.0) -> dict:
    # One read: checksum and calculation refer to the same bytes.
    raw = Path(path).read_bytes()
    speeds = _read_site_bytes(raw)
    powers = [power_kw(v, rated_kw) for v in speeds]
    mean_power = math.fsum(powers) / len(powers)
    source_sha = hashlib.sha256(raw).hexdigest()
    parameters = {"rated_power_kw": float(rated_kw), "cut_in_mps": 3.0,
                  "rated_speed_mps": 12.0, "cut_out_mps": 25.0,
                  "annualization_hours": 8760}
    identity = json.dumps({"version": MODEL_VERSION, "source_sha256": source_sha,
                           "parameters": parameters}, sort_keys=True, separators=(",", ":"))
    return {"version": MODEL_VERSION, "synthetic": True,
            "result_id": hashlib.sha256(identity.encode()).hexdigest(),
            "source_sha256": source_sha, "sample_count": len(speeds),
            "duration_hours": len(speeds), "parameters": parameters,
            "mean_wind_speed_mps": math.fsum(speeds) / len(speeds),
            "mean_power_kw": mean_power, "sample_energy_kwh": math.fsum(powers),
            "annual_energy_kwh_estimate": mean_power * 8760.0,
            "lift_example": {"alpha_deg": 5.0, "stall_deg": 15.0, "cl": lift_coefficient(5.0)},
            "limitations": "Synthetic hours; fixed 8760-hour extrapolation; no availability, wake, density or uncertainty model. Not measured AEP."}
