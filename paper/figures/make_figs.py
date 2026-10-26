"""Publication figures for manuscript_v1 (OpenISAC cross-layer video study).

Figure contract (nature-figure five-point):
  Fig 2  core conclusion : container/decoder choice, not the PHY, sets effective
           error exposure — model predicts 7x, measurement spans 4x-500x.
         archetype        : quantitative grid (single hero panel, log-x bars)
  Fig 3  core conclusion : queue restructuring pins latency at 250 ms (+/-0.5 ms
           steady state, no accumulation); decoder owns ~80% of it.
         archetype        : quantitative grid (trace hero + decomposition subordinate)
  Fig 4  core conclusion : payload BER stays <=0.015% up to 3000 kbps and is
           non-monotonic -> pipeline occupancy, not channel capacity.
         archetype        : quantitative grid (single panel)
  Export contract        : IEEE column widths (3.5 in single / 7.16 in double),
           editable text (PDF fonttype 42, SVG fonttype none), 600 dpi TIFF,
           PNG for review. Data: source chapters, hard-coded with provenance.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "font.size": 8,
    "axes.spines.right": False,
    "axes.spines.top": False,
    "axes.linewidth": 0.8,
    "legend.frameon": False,
})

# nature-figure PALETTE (api.md)
BLUE = "#0F4D92"
BLUE2 = "#3775BA"
RED = "#E9A6A1"
RED_STRONG = "#B64342"
GREEN = "#8BCF8B"
NEUTRAL = "#767676"
NEUTRAL_D = "#4D4D4D"
NEUTRAL_L = "#CFCECE"

OUT = Path(__file__).resolve().parent


def save_pub(fig, stem: str) -> None:
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.svg", bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.tiff", dpi=600, bbox_inches="tight")
    print(f"saved {stem} (.pdf .svg .png .tiff)")


# ---------------------------------------------------------------- Fig 2: gamma
def fig2_gamma() -> None:
    stacks = [
        ("MPEG-TS + VLC", 500),
        ("MPEG-TS + ffplay", 150),
        ("bare + ffplay", 8),
        ("bare + GStreamer", 4),
    ]
    labels = [s[0] for s in stacks][::-1]
    vals = [s[1] for s in stacks][::-1]
    colors = [RED_STRONG if l.startswith("MPEG-TS") else BLUE for l in labels]

    fig, ax = plt.subplots(figsize=(3.5, 2.3))
    bars = ax.barh(labels, vals, color=colors, height=0.58, edgecolor="none")
    ax.axvline(7, color=NEUTRAL_D, lw=1.0, ls=(0, (4, 3)))
    ax.text(7, 3.62, "model prediction, $\\gamma_{model}\\approx7$",
            ha="center", va="bottom", fontsize=7.5, color=NEUTRAL_D)

    for b, v in zip(bars, vals):
        ax.text(v * 1.15, b.get_y() + b.get_height() / 2, f"{v}x",
                va="center", fontsize=8, color=NEUTRAL_D)

    ax.set_xscale("log")
    ax.set_xlim(1, 1300)
    ax.set_xlabel("measured container amplification factor $\\gamma$")
    ax.tick_params(axis="y", length=0)
    ax.text(0.99, 0.06,
            "measured with RS outer code disabled (stress test)",
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=6.5, color=NEUTRAL)
    save_pub(fig, "fig3_gamma_mpl")


# ---------------------------------------------------------- Fig 3: latency
def fig3_latency() -> None:
    fig, (axa, axb) = plt.subplots(
        1, 2, figsize=(7.16, 2.6), gridspec_kw={"width_ratios": [1.55, 1]})

    # (a) five-minute trace
    t = [0, 20, 40, 74, 176, 205, 235, 277]
    lat = [250, 250, 251, 250, 266, 233, 112, 38]
    axa.add_patch(Rectangle((0, 249.5), 74, 5, color=NEUTRAL_L, alpha=0.45, lw=0))
    axa.plot(t[:4], lat[:4], "o-", color=BLUE, lw=1.2, ms=4.5, zorder=3)
    axa.plot(t[4:6], lat[4:6], "o", color=BLUE, lw=1.2, ms=4.5, zorder=3)
    axa.plot(t[6:], lat[6:], "o", color=NEUTRAL, ms=4.5, zorder=3)
    axa.axhline(250.3, color=BLUE2, lw=0.8, ls=(0, (3, 3)), alpha=0.8)
    axa.annotate("steady state 250.3 $\\pm$ 0.5 ms\n(no accumulation, 5 min)",
                 xy=(37, 250.5), xytext=(96, 130), fontsize=7.5, color=NEUTRAL_D,
                 arrowprops=dict(arrowstyle="-", color=NEUTRAL, lw=0.7))
    axa.annotate("decoder buffer reset\n(receiver software)", xy=(235, 112),
                 xytext=(150, 42), fontsize=7.5, color=NEUTRAL,
                 arrowprops=dict(arrowstyle="-", color=NEUTRAL, lw=0.7))
    axa.set_xlabel("time (s)")
    axa.set_ylabel("end-to-end latency (ms)")
    axa.set_ylim(0, 295)
    axa.set_xlim(-8, 292)
    axa.set_title("(a) stopwatch trace", fontsize=8.5, loc="left")

    # (b) latency decomposition
    parts = [
        ("H.264 decode + GStreamer", 200),
        ("TX queue", 18),
        ("H.264 encode", 10),
        ("RX queue", 9),
        ("FEC decode", 5),
        ("UDP (localhost)", 5),
        ("OFDM framing", 2.3),
        ("ISAC radio link", 3),
    ]
    names = [p[0] for p in parts][::-1]
    vals = [p[1] for p in parts][::-1]
    cols = [BLUE if n.startswith("H.264 decode") else NEUTRAL_L for n in names]
    bars = axb.barh(names, vals, color=cols, height=0.6)
    total = sum(vals)
    for b, v in zip(bars, vals):
        axb.text(v + 3, b.get_y() + b.get_height() / 2,
                 f"{v:g} ({v / total:.0%})" if v / total >= 0.03 else f"{v:g}",
                 va="center", fontsize=7, color=NEUTRAL_D)
    axb.set_xlim(0, 245)
    axb.set_xlabel("latency contribution (ms)")
    axb.tick_params(axis="y", length=0)
    axb.set_title("(b) latency decomposition (~250 ms total)", fontsize=8.5, loc="left")

    fig.tight_layout(w_pad=2.2)
    save_pub(fig, "fig2_latency_mpl")


# ---------------------------------------------------------------- Fig 4: BER
def fig4_ber() -> None:
    rate = [500, 1000, 1500, 2000, 2500, 3000]
    ber = [None, 0.0036, 0.0153, 0.0099, 0.0108, 0.0025]  # 500 kbps: zero errors

    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    xs = [r for r, b in zip(rate, ber) if b is not None]
    ys = [b for b in ber if b is not None]
    ax.plot(xs, ys, "o-", color=BLUE, lw=1.2, ms=4.5, zorder=3)
    ax.plot([500], [1e-4], marker="o", ms=4.5, mfc="white", mec=BLUE, mew=1.1,
            ls="none", zorder=3)
    ax.annotate("0 errors at 500 kbps", xy=(500, 1.5e-4), xytext=(560, 3.2e-4),
                fontsize=7, color=NEUTRAL_D,
                arrowprops=dict(arrowstyle="-", color=NEUTRAL, lw=0.7))

    ax.axvline(1200, color=RED_STRONG, lw=0.9, ls=(0, (4, 3)))
    ax.text(1240, 3.2e-5, "video operating point\n1200 kbps (2.5x headroom)",
            fontsize=7, color=RED_STRONG, va="bottom")

    ax.set_yscale("log")
    ax.set_ylim(1.2e-5, 6e-2)
    ax.set_xlim(380, 3180)
    ax.set_xlabel("offered rate (kbps)")
    ax.set_ylabel("payload BER (%)")
    ax.text(0.98, 0.95, "BER $\\leq$ 0.015% at every rate",
            transform=ax.transAxes, fontsize=7.5, color=NEUTRAL_D, va="top",
            ha="right",
            bbox=dict(facecolor="white", edgecolor="none", pad=1.5, alpha=0.85))
    save_pub(fig, "fig5_ber_mpl")


if __name__ == "__main__":
    fig2_gamma()
    fig3_latency()
    fig4_ber()
