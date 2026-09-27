from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import tempfile
from .model import study


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Synthetic wind study (not measured AEP)")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--site", required=True, type=Path)
    run.add_argument("--out", required=True, type=Path)
    run.add_argument("--rated-kw", type=float, default=10.0)
    args = parser.parse_args(argv)
    temp = None
    try:
        result = study(args.site, args.rated_kw)
        args.out.mkdir(parents=True, exist_ok=True)
        target = args.out / "study_result.json"
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=args.out,
                                         prefix=".study-", delete=False) as stream:
            temp = Path(stream.name)
            json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
        os.replace(temp, target)
        print(target)
        return 0
    except (OSError, ValueError, UnicodeError) as exc:
        parser.exit(1, f"Study failed: {exc}\n")
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
