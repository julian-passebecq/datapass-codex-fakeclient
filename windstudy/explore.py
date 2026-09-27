"""Dependency-free notebook views, derived from the native model."""
from html import escape
from .model import power_kw


def table_html(speeds: list[float]) -> str:
    rows = "".join(f"<tr><td>{h}</td><td>{v:.2f}</td><td>{power_kw(v):.3f}</td></tr>"
                   for h, v in enumerate(speeds[:8]))
    return ("<table><caption>First 8 synthetic hourly samples</caption>"
            "<thead><tr><th>Hour</th><th>Wind (m/s)</th><th>Toy power (kW)</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>")


def chart_svg() -> str:
    # All values come from the same function as the CLI; a discontinuity at cut-out
    # is represented explicitly rather than interpolated through it.
    speeds = [i / 10 for i in range(251)]
    pts = " ".join(f"{65+v*21:.1f},{280-power_kw(v)*20:.1f}" for v in speeds[:-1])
    pts += " 590.0,80.0 590.0,280.0 695.0,280.0"
    ticks = []
    for v in (0, 3, 12, 25, 30):
        x = 65 + v * 21
        ticks.append(f'<text x="{x}" y="301" text-anchor="middle">{v}</text>')
    for p in (0, 5, 10):
        y = 280 - p * 20
        ticks.append(f'<text x="52" y="{y+5}" text-anchor="end">{p}</text>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 370" role="img" '
            'aria-label="Synthetic toy power curve, cut-in 3, rated speed 12, cut-out 25 metres per second">'
            '<rect width="760" height="370" fill="white"/>'
            '<g font-family="sans-serif" font-size="14" fill="#24333d">'
            '<text x="65" y="29" font-size="20">Synthetic toy power curve</text>'
            '<text x="65" y="51">Arbitrary 10 kW rating; not a measured turbine</text>'
            '<path d="M65 66V280H695" fill="none" stroke="#24333d"/>'
            '<path d="M65 180H695 M65 80H695" fill="none" stroke="#e2e7eb"/>'
            f'<polyline points="{escape(pts)}" fill="none" stroke="#166b8c" stroke-width="2.5"/>'
            + ''.join(ticks) + '<text x="380" y="332" text-anchor="middle">Wind speed (m/s)</text>'
            '<text transform="translate(18 180) rotate(-90)" text-anchor="middle">Power (kW)</text>'
            '<text x="65" y="360" font-size="12">Source: windstudy.model.power_kw; model version 1.0</text>'
            '</g></svg>')
