"""Generate 1,000 synthetic hourly observations with cross-platform stable bytes."""
from pathlib import Path
import argparse


def make_data(path: Path, rows: int = 1000, seed: int = 42) -> None:
    if rows <= 0:
        raise ValueError("rows must be positive")
    state = seed
    lines = ["hour,wind_speed_mps"]
    for hour in range(rows):
        state = (1664525 * state + 1013904223) % (2 ** 32)
        speed = 2.0 + (state % 1601) / 100.0
        lines.append(f"{hour},{speed:.2f}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(("\n".join(lines) + "\n").encode("ascii"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "data/site_a_wind.csv")
    parser.add_argument("--rows", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    make_data(args.out, args.rows, args.seed)
