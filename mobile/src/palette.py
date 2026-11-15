"""Colour palettes (copied from the desktop theme.py, without any Qt code).

Pages read colours from `C` at build time, e.g. C.TEXT, so switching the
theme only needs `set_theme(name)` followed by a rebuild of the UI.
"""

from __future__ import annotations

from types import SimpleNamespace

PALETTES: dict[str, dict[str, object]] = {
    "dark": {
        "CARD_ALPHA": 0.85,
        "BG": "#0d1117",
        "CARD": "#161b22",
        "BORDER": "#30363d",
        "TEXT": "#e6edf3",
        "MUTED": "#8b949e",
        "ACCENT": "#2f81f7",
        "SUCCESS": "#3fb950",
        "ORANGE": "#f0ad4e",
        "PRIMARY": "#238636",
        "WARN_BG": "#9e6a03",
        "DANGER": "#f85149",
        "DANGER_BG": "#b62324",
        "BTN": "#21262d",
        "HEAT_COLORS": ["#1c2128", "#0e4429", "#006d32", "#26a641", "#39d353"],
        "SLICE_COLORS": [
            "#39d353", "#58a6ff", "#f0ad4e", "#e05780", "#a78bfa", "#2dd4bf",
            "#f97316", "#facc15", "#60a5fa", "#f472b6", "#4ade80", "#c084fc",
        ],
    },
    "light": {
        "CARD_ALPHA": 0.4,
        "BG": "#f6f8fa",
        "CARD": "#ffffff",
        "BORDER": "#d0d7de",
        "TEXT": "#1f2328",
        "MUTED": "#59636e",
        "ACCENT": "#0969da",
        "SUCCESS": "#1a7f37",
        "ORANGE": "#bc4c00",
        "PRIMARY": "#1f883d",
        "WARN_BG": "#bf8700",
        "DANGER": "#cf222e",
        "DANGER_BG": "#cf222e",
        "BTN": "#e6e9ed",
        "HEAT_COLORS": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
        "SLICE_COLORS": [
            "#2da44e", "#0969da", "#bc4c00", "#bf3989", "#8250df", "#1b7c83",
            "#e16f24", "#bf8700", "#218bff", "#d1429a", "#1a7f37", "#a475f9",
        ],
    },
}

C = SimpleNamespace(**PALETTES["dark"])


def set_theme(name: str) -> str:
    name = name if name in PALETTES else "dark"
    C.__dict__.update(PALETTES[name])
    return name
