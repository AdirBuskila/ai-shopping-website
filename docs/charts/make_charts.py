"""Generate the README charts (light + dark) from real, reproducible project data.

Every number here comes from the actual artifacts:
  * churn metrics/coefficients/ROC → retrain the seed-42 model (matches report.md)
  * catalog composition            → data/products.seed.json (151 products)
  * test-suite breakdown           → counted from backend/tests

Design follows the `dataviz` skill: validated reference palette, recessive chrome,
thin marks, direct labels, one axis. Each chart is emitted twice — a light variant
and a dark variant — so the README can swap them with <picture> per color scheme.

Run:  python docs/charts/make_charts.py
"""
from __future__ import annotations

import collections
import json
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "charts"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "ml_training"))
from app.ml.features import FEATURE_NAMES  # noqa: E402
from generate_dataset import sample_rows  # noqa: E402

# ── validated reference palette (see dataviz/references/palette.md) ──────────────
THEMES = {
    "light": dict(
        surface="#fcfcfb", ink="#0b0b0b", sec="#52514e", muted="#898781",
        grid="#e1e0d9", axis="#c3c2b7",
        blue="#2a78d6", orange="#eb6834", red="#e34948", chance="#b9b8b1",
    ),
    "dark": dict(
        surface="#1a1a19", ink="#ffffff", sec="#c3c2b7", muted="#898781",
        grid="#2c2c2a", axis="#383835",
        blue="#3987e5", orange="#d95926", red="#e66767", chance="#4a4a47",
    ),
}

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
    "svg.fonttype": "none",
    "axes.linewidth": 0,
    "figure.dpi": 200,
})


def _new(t: dict, w=7.4, h=4.0):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor(t["surface"])
    ax.set_facecolor(t["surface"])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0, colors=t["muted"], labelsize=10)
    return fig, ax


def _title(ax, t, title, subtitle):
    ax.set_title(title, color=t["ink"], fontsize=15, fontweight="bold",
                 loc="left", pad=32)
    ax.annotate(subtitle, xy=(0, 1.0), xytext=(0, 11), textcoords="offset points",
                xycoords="axes fraction", color=t["sec"], fontsize=10.5, va="bottom")


def _save(fig, name):
    for mode in ("",):  # single call; theme baked in name
        pass
    fig.savefig(OUT / name, facecolor=fig.get_facecolor(), bbox_inches="tight",
                pad_inches=0.28)
    plt.close(fig)
    print("wrote", name)


# ── 1. churn drivers — diverging horizontal bar ─────────────────────────────────
def churn_drivers():
    df_rows = sample_rows(2000, seed=42)
    X = np.array([[r[f] for f in FEATURE_NAMES] for r in df_rows], float)
    y = np.array([r["churn"] for r in df_rows], int)
    Xtr, _, ytr, _ = train_test_split(X, y, test_size=0.25, stratify=y, random_state=42)
    scaler = StandardScaler().fit(Xtr)
    lr = LogisticRegression(max_iter=1000, random_state=42).fit(scaler.transform(Xtr), ytr)
    coefs = dict(zip(FEATURE_NAMES, lr.coef_[0]))

    label = {
        "recency_days": "Days since last order",
        "tenure_days": "Account tenure",
        "monetary": "Total spend",
        "favorites_count": "Favorites saved",
        "frequency": "Purchase frequency",
    }
    items = sorted(coefs.items(), key=lambda kv: kv[1])  # most-negative first (bottom)
    names = [label[k] for k, _ in items]
    vals = [v for _, v in items]

    for mode, t in THEMES.items():
        fig, ax = _new(t, 7.6, 4.1)
        colors = [t["red"] if v > 0 else t["blue"] for v in vals]
        ypos = np.arange(len(vals))
        ax.barh(ypos, vals, color=colors, height=0.6, zorder=3)
        ax.axvline(0, color=t["axis"], lw=1.2, zorder=2)
        ax.set_yticks(ypos)
        ax.set_yticklabels(names, color=t["ink"], fontsize=11)
        ax.set_xticks([])
        lim = max(abs(min(vals)), abs(max(vals))) * 1.32
        ax.set_xlim(-lim, lim)
        for yi, v in zip(ypos, vals):
            ha = "left" if v > 0 else "right"
            off = 0.03 if v > 0 else -0.03
            ax.text(v + off, yi, f"{v:+.2f}", va="center", ha=ha,
                    color=t["sec"], fontsize=10, fontweight="bold")
        ax.text(-lim, len(vals) - 0.3, "← lowers churn risk", color=t["blue"],
                fontsize=9.5, fontweight="bold", ha="left")
        ax.text(lim, len(vals) - 0.3, "raises churn risk →", color=t["red"],
                fontsize=9.5, fontweight="bold", ha="right")
        _title(ax, t, "What drives churn",
               "Standardized logistic-regression weights — the model explains itself")
        ax.margins(y=0.12)
        _save(fig, f"churn-drivers-{mode}.png")


# ── 2. ROC curve — logreg vs random forest ──────────────────────────────────────
def roc():
    df_rows = sample_rows(2000, seed=42)
    X = np.array([[r[f] for f in FEATURE_NAMES] for r in df_rows], float)
    y = np.array([r["churn"] for r in df_rows], int)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, stratify=y, random_state=42)
    scaler = StandardScaler().fit(Xtr)
    Xtr, Xte = scaler.transform(Xtr), scaler.transform(Xte)
    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=200, random_state=42),
    }
    curves = {}
    for name, m in models.items():
        m.fit(Xtr, ytr)
        p = m.predict_proba(Xte)[:, 1]
        fpr, tpr, _ = roc_curve(yte, p)
        curves[name] = (fpr, tpr, roc_auc_score(yte, p))

    for mode, t in THEMES.items():
        fig, ax = _new(t, 6.2, 5.4)
        ax.plot([0, 1], [0, 1], "--", color=t["chance"], lw=1.4, zorder=2)
        ax.text(0.63, 0.58, "random guess", color=t["muted"], fontsize=9.5,
                rotation=38, rotation_mode="anchor", va="bottom")
        style = {"Logistic Regression": t["blue"], "Random Forest": t["orange"]}
        for name, (fpr, tpr, auc) in curves.items():
            ax.plot(fpr, tpr, color=style[name], lw=2.4, zorder=4,
                    label=f"{name}  ·  AUC {auc:.3f}")
        for spine in ("bottom", "left"):
            ax.spines[spine].set_visible(True)
            ax.spines[spine].set_color(t["axis"])
            ax.spines[spine].set_linewidth(1.1)
        ax.set_xlim(-0.01, 1.01)
        ax.set_ylim(-0.01, 1.01)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.tick_params(colors=t["muted"], labelsize=9.5)
        ax.set_xlabel("False-positive rate", color=t["sec"], fontsize=11)
        ax.set_ylabel("True-positive rate", color=t["sec"], fontsize=11)
        ax.grid(True, color=t["grid"], lw=0.8, zorder=1)
        ax.set_axisbelow(True)
        leg = ax.legend(loc="lower right", frameon=False, fontsize=11,
                        labelcolor=t["ink"], borderpad=0.6)
        _title(ax, t, "Churn model — ROC",
               "Chosen by AUC on a held-out 25% test split (seed 42)")
        ax.set_aspect("equal")
        _save(fig, f"roc-{mode}.png")


# ── 3. test suite by area — horizontal bar ──────────────────────────────────────
def tests_by_area():
    areas = [
        ("Orders & stock", 24), ("AI assistant & RAG", 23),
        ("Auth & security", 13), ("ML churn", 13),
        ("Products & search", 11), ("Core, models & health", 9),
        ("Favorites", 7),
    ]
    areas.sort(key=lambda kv: kv[1])
    names = [a for a, _ in areas]
    vals = [v for _, v in areas]
    for mode, t in THEMES.items():
        fig, ax = _new(t, 7.6, 4.1)
        ypos = np.arange(len(vals))
        ax.barh(ypos, vals, color=t["blue"], height=0.62, zorder=3)
        ax.set_yticks(ypos)
        ax.set_yticklabels(names, color=t["ink"], fontsize=11)
        ax.set_xticks([])
        ax.set_xlim(0, max(vals) * 1.16)
        for yi, v in zip(ypos, vals):
            ax.text(v + max(vals) * 0.015, yi, str(v), va="center", ha="left",
                    color=t["sec"], fontsize=10.5, fontweight="bold")
        _title(ax, t, "100 automated tests",
               "Every layer covered — 98 run offline, 2 integration (live Redis)")
        ax.margins(y=0.10)
        _save(fig, f"tests-{mode}.png")


# ── 4. catalog composition — horizontal bar ─────────────────────────────────────
def catalog():
    data = json.load(open(ROOT / "data" / "products.seed.json", encoding="utf-8"))
    cats = collections.Counter(p.get("category", "?") for p in data)
    pretty = {"smartphone": "Smartphones", "headphones": "Headphones",
              "accessory": "Accessories", "smartwatch": "Smartwatches",
              "tablet": "Tablets"}
    items = sorted(cats.items(), key=lambda kv: kv[1])
    names = [pretty.get(k, k.title()) for k, _ in items]
    vals = [v for _, v in items]
    for mode, t in THEMES.items():
        fig, ax = _new(t, 7.6, 3.7)
        ypos = np.arange(len(vals))
        ax.barh(ypos, vals, color=t["blue"], height=0.6, zorder=3)
        ax.set_yticks(ypos)
        ax.set_yticklabels(names, color=t["ink"], fontsize=11)
        ax.set_xticks([])
        ax.set_xlim(0, max(vals) * 1.16)
        for yi, v in zip(ypos, vals):
            ax.text(v + max(vals) * 0.015, yi, str(v), va="center", ha="left",
                    color=t["sec"], fontsize=10.5, fontweight="bold")
        _title(ax, t, "151 real products",
               "Seeded from a live electronics catalog, across 5 categories")
        ax.margins(y=0.12)
        _save(fig, f"catalog-{mode}.png")


# ── 0. hero banner (dark, premium) ──────────────────────────────────────────────
def banner():
    from matplotlib.patches import FancyBboxPatch
    W, H = 1280, 340
    fig = plt.figure(figsize=(W / 200, H / 200), dpi=200)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
    ax.set_xlim(0, W); ax.set_ylim(0, H)

    # diagonal dark->purple gradient wash
    gx, gy = np.meshgrid(np.linspace(0, 1, W), np.linspace(0, 1, H))
    t = np.clip(0.55 * gx + 0.45 * gy, 0, 1)
    c0 = np.array([9, 9, 11]); c1 = np.array([38, 22, 58])       # #09090b -> #26163a
    rgb = (c0[None, None] + (c1 - c0)[None, None] * t[..., None]) / 255
    # soft purple glow, upper-right
    glow = np.exp(-(((gx - 0.82) * 2.1) ** 2 + ((gy - 0.75) * 2.6) ** 2))
    rgb = rgb + glow[..., None] * (np.array([124, 58, 237]) / 255) * 0.34
    ax.imshow(np.clip(rgb, 0, 1), extent=(0, W, 0, H), origin="lower",
              aspect="auto", zorder=0)

    ax.text(70, 214, "Shopwise", color="#ffffff", fontsize=58, fontweight="bold",
            va="center", ha="left", zorder=3)
    ax.add_patch(FancyBboxPatch((74, 150), 132, 8,
                 boxstyle="round,pad=0,rounding_size=4",
                 linewidth=0, facecolor="#8b5cf6", zorder=3))
    ax.text(72, 116,
            "AI-powered e-commerce  ·  agentic RAG assistant  ·  churn ML",
            color="#d9d6e3", fontsize=14, va="center", ha="left", zorder=3)
    ax.text(72, 66,
            "FastAPI  ·  MySQL  ·  Redis  ·  Docker  ·  OpenAI  ·  scikit-learn  ·  Next.js",
            color="#9a95ad", fontsize=12, va="center", ha="left", zorder=3,
            fontweight="bold")
    fig.savefig(OUT / "banner.png", facecolor="#09090b")
    plt.close(fig)
    print("wrote banner.png")


if __name__ == "__main__":
    banner()
    churn_drivers()
    roc()
    tests_by_area()
    catalog()
    print("done", OUT)
