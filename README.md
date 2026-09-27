# Wind study 2D - synthetic pilot

Standalone Python 3.11+ package, no cloud, Docker or coordination extension required. All 1,000 hourly observations are generated, not measured. All turbine values are arbitrary teaching parameters, not a proposed real machine.

## Run and test

```sh
python -m windstudy run --site data/site_a_wind.csv --out out/
python -m pip install 'pytest>=8,<9'
python -m pytest -q
```

Regenerate the committed CSV using `python scripts/make_data.py` (explicit LCG seed 42, cross-platform stable bytes). Hours are consecutive integer offsets, one hour per row. Missing, duplicated, negative and nonfinite observations fail closed.

## Model and exchange contract

`windstudy/model.py` owns the formulas. Thin-airfoil lift uses radians and a symmetric 15-degree clipping limit; clipping is **not** a post-stall model. The independent toy power curve is zero below 3 m/s and at/above 25 m/s, reaches 10 kW at 12 m/s, and uses a shifted cubic curve in between. Lift does not determine the power curve.

`out/study_result.json` has `version: "1.0"`, `synthetic: true`, the checksum of the exact source bytes, a deterministic result ID, sample energy in kWh and an annualized estimate. Annualization is sample mean power multiplied by 8,760 hours, not an observed annual yield; it assumes representativeness and omits losses, wakes, uncertainty and availability. Source bytes, model version and rated power enter the result identity. Failed runs preserve an existing output; successful writes replace it atomically.

## Notebook

`notebooks/explore_site_a.ipynb` has executed, saved outputs: a sample table and an embedded SVG power-curve image. It imports the native package, not duplicate formulas. Rerun using Jupyter or the VS Code notebook extension (IPython required); the chart itself uses no external library or network. Data tables show the first eight of 1,000 synthetic hours. The chart displays the model curve, not observations.

## Independence and evidence

Pass the JSON file explicitly to the blade repository; no cross-repository import or bridge dependency. Generated `out/` is ignored by Git. The ten tests exercise the local code. CI repeats them on Python 3.11, 3.12 and 3.13. Native tests do not establish deployment or extension-UI evidence.
