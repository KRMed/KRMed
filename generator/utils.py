"""Utility functions, color maps, math helpers, and SVG icon paths."""

import re
import math
import hashlib
from xml.sax.saxutils import escape as xml_escape

HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

# Language bucketing rules — keep the composition legend a stable size
MIN_LANGUAGE_PCT = 2.0
LANGUAGE_TOP_N = 7

# WCAG non-text contrast floor for a color swatch against the panel fill
MIN_SWATCH_CONTRAST = 3.0

# Default deep-space theme palette
DEFAULT_THEME = {
    "void": "#080c14",
    "nebula": "#0f1623",
    "star_dust": "#1a2332",
    "synapse_cyan": "#00d4ff",
    "dendrite_violet": "#a78bfa",
    "axon_amber": "#ffb020",
    "text_bright": "#f1f5f9",
    "text_dim": "#94a3b8",
    "text_faint": "#64748b",
}


def resolve_theme(user_theme: dict) -> dict:
    """Merge user theme overrides with defaults, returning a complete theme dict."""
    return {**DEFAULT_THEME, **(user_theme or {})}


def resolve_arm_colors(galaxy_arms: list, theme: dict) -> list:
    """Return a list of hex color strings, one per arm, resolved from the theme."""
    fallback = theme.get("synapse_cyan", "#00d4ff")
    return [
        theme.get(arm.get("color", "synapse_cyan"), fallback)
        for arm in galaxy_arms
    ]


# GitHub Linguist colors for popular languages
LANGUAGE_COLORS = {
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Java": "#b07219",
    "C#": "#178600",
    "C++": "#f34b7d",
    "C": "#555555",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Ruby": "#701516",
    "PHP": "#4F5D95",
    "Swift": "#F05138",
    "Kotlin": "#A97BFF",
    "Dart": "#00B4AB",
    "Scala": "#c22d40",
    "R": "#198CE7",
    "Lua": "#000080",
    "Shell": "#89e051",
    "PowerShell": "#012456",
    "Haskell": "#5e5086",
    "Elixir": "#6e4a7e",
    "Clojure": "#db5855",
    "Erlang": "#B83998",
    "Julia": "#a270ba",
    "Vim Script": "#199f4b",
    "Objective-C": "#438eff",
    "Perl": "#0298c3",
    "MATLAB": "#e16737",
    "Groovy": "#4298b8",
    "Vue": "#41b883",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "SCSS": "#c6538c",
    "Dockerfile": "#384d54",
    "Makefile": "#427819",
    "HCL": "#844FBA",
    "Nix": "#7e7eff",
    "Zig": "#ec915c",
    "Svelte": "#ff3e00",
    "Astro": "#ff5a03",
    # Official Linguist colors for other common languages, uncomment as needed:
    # "Jupyter Notebook": "#DA5B0B",
    # "CMake": "#DA3434",
    # "Batchfile": "#C1F12E",
    # "YAML": "#cb171e",
    # "Markdown": "#083fa1",
    # "TeX": "#3D6117",
}

# SVG icon paths (16x16 viewBox)
COMMIT_ICON = (
    '<path d="M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1zm0 2.5a4.5 4.5 0 0 1 '
    '4.473 4H14.5a.5.5 0 0 1 0 1h-2.027A4.5 4.5 0 0 1 8 12.5a4.5 4.5 '
    '0 0 1-4.473-4H1.5a.5.5 0 0 1 0-1h2.027A4.5 4.5 0 0 1 8 3.5zm0 '
    '1.5a3 3 0 1 0 0 6 3 3 0 0 0 0-6z"/>'
)

STAR_ICON = (
    '<path d="M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 '
    '0 0 1 .416 1.279l-3.046 2.97.719 4.192a.75.75 0 0 1-1.088.791L8 '
    '12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 '
    '6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25z"/>'
)

PR_ICON = (
    '<path d="M1.5 3.25a2.25 2.25 0 1 1 3 2.122v5.256a2.251 2.251 0 1 1-1.5 '
    '0V5.372A2.25 2.25 0 0 1 1.5 3.25Zm5.677-.177L9.573.677A.25.25 0 0 1 10 '
    '.854V2.5h1A2.5 2.5 0 0 1 13.5 5v5.628a2.251 2.251 0 1 1-1.5 0V5a1 1 0 0 '
    '0-1-1h-1v1.646a.25.25 0 0 1-.427.177L7.177 3.427a.25.25 0 0 1 '
    '0-.354ZM3.75 2.5a.75.75 0 1 0 0 1.5.75.75 0 0 0 0-1.5Zm0 9.5a.75.75 0 1 '
    '0 0 1.5.75.75 0 0 0 0-1.5Zm8.25.75a.75.75 0 1 0 1.5 0 .75.75 0 0 0-1.5 0Z"/>'
)

ISSUE_ICON = (
    '<path d="M8 9.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z"/>'
    '<path d="M8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0zm0 1.5a6.5 6.5 0 1 0 0 '
    '13 6.5 6.5 0 0 0 0-13z"/>'
)

REPO_ICON = (
    '<path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 '
    '0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 '
    '1.7.75.75 0 0 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5zm10.5-1h-8a1 '
    '1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8zM5 12.25a.25.25 0 0 '
    '1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-'
    '1.087a.25.25 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2z"/>'
)

METRIC_ICONS = {
    "commits": COMMIT_ICON,
    "stars": STAR_ICON,
    "prs": PR_ICON,
    "issues": ISSUE_ICON,
    "repos": REPO_ICON,
}

METRIC_LABELS = {
    "commits": "Commits",
    "stars": "Stars",
    "prs": "PRs",
    "issues": "Issues",
    "repos": "Repos",
}

METRIC_COLORS = {
    "commits": "synapse_cyan",
    "stars": "axon_amber",
    "prs": "dendrite_violet",
    "issues": "synapse_cyan",
    "repos": "dendrite_violet",
}


def get_language_color(lang: str) -> str:
    """Return the GitHub linguist hex color for a language."""
    return LANGUAGE_COLORS.get(lang, "#8b949e")


def calculate_language_percentages(
    languages: dict, exclude: list, max_display: int
) -> list:
    """Calculate language percentages from byte counts.

    Args:
        languages: dict mapping language name to byte count
        exclude: list of language names to exclude
        max_display: maximum number of languages to show

    Returns:
        list of dicts with keys: name, bytes, percentage, color
    """
    filtered = {k: v for k, v in languages.items() if k not in exclude}
    total = sum(filtered.values())
    if total == 0:
        return []

    sorted_langs = sorted(filtered.items(), key=lambda x: x[1], reverse=True)
    top = sorted_langs[:max_display]

    return [
        {
            "name": name,
            "bytes": count,
            "percentage": round((count / total) * 100, 1),
            "color": get_language_color(name),
        }
        for name, count in top
    ]


def _hex_to_rgb(hex_color: str) -> tuple:
    """Convert '#rrggbb' to an (r, g, b) tuple of 0-255 ints."""
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb: tuple) -> str:
    """Convert an (r, g, b) tuple of 0-255 ints to '#rrggbb'."""
    return "#{:02x}{:02x}{:02x}".format(*(max(0, min(255, round(c))) for c in rgb))


def _relative_luminance(hex_color: str) -> float:
    """WCAG relative luminance of a hex color."""
    channels = []
    for c in _hex_to_rgb(hex_color):
        s = c / 255
        channels.append(s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4)
    r, g, b = channels
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(color_a: str, color_b: str) -> float:
    """WCAG contrast ratio between two hex colors (1.0 to 21.0)."""
    la, lb = _relative_luminance(color_a), _relative_luminance(color_b)
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


def lighten(hex_color: str, amount: float) -> str:
    """Mix a hex color toward white by `amount` (0.0 = unchanged, 1.0 = white)."""
    return _rgb_to_hex(tuple(c + (255 - c) * amount for c in _hex_to_rgb(hex_color)))


def ensure_contrast(
    hex_color: str, background: str, min_ratio: float = MIN_SWATCH_CONTRAST
) -> str:
    """Lighten a color until it clears `min_ratio` against `background`."""
    step = 0.05
    amount = 0.0
    current = hex_color
    while contrast_ratio(current, background) < min_ratio and amount < 1.0:
        amount += step
        current = lighten(hex_color, amount)
    return current


def bucket_languages(languages: dict, exclude: list) -> list:
    """Bucket language percentages into a fixed-size, layout-stable list.

    Languages below MIN_LANGUAGE_PCT, plus anything past LANGUAGE_TOP_N, fold
    into a trailing "Other" entry labelled with its constituent count.

    Args:
        languages: dict mapping language name to byte count
        exclude: list of language names to exclude

    Returns:
        list of dicts with keys: name, percentage, color, folded.
        `folded` is 0 for a real language and the constituent count for "Other".
        Percentages sum to 100.0 when an "Other" entry is present.
    """
    ranked = calculate_language_percentages(languages, exclude, len(languages))
    if not ranked:
        return []

    kept = [lang for lang in ranked if lang["percentage"] >= MIN_LANGUAGE_PCT]
    folded = [lang for lang in ranked if lang["percentage"] < MIN_LANGUAGE_PCT]

    if len(kept) > LANGUAGE_TOP_N:
        folded = kept[LANGUAGE_TOP_N:] + folded
        kept = kept[:LANGUAGE_TOP_N]

    entries = [
        {
            "name": lang["name"],
            "percentage": lang["percentage"],
            "color": lang["color"],
            "folded": 0,
        }
        for lang in kept
    ]

    if folded:
        remainder = round(100.0 - sum(e["percentage"] for e in entries), 1)
        entries.append(
            {
                "name": f"Other ({len(folded)})",
                "percentage": max(0.0, remainder),
                "color": None,
                "folded": len(folded),
            }
        )

    return entries


def format_number(n: int) -> str:
    """Format a number for display. 1234 -> '1.2k', 1000000 -> '1.0M'."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def spiral_points(
    cx: float,
    cy: float,
    start_angle: float,
    num_points: int,
    max_radius: float,
    turns: float = 1.2,
    x_scale: float = 1.0,
    y_scale: float = 1.0,
) -> list:
    """Generate points along an Archimedean spiral.

    Args:
        cx, cy: center coordinates
        start_angle: starting angle in degrees
        num_points: number of points to generate
        max_radius: maximum radius of the spiral
        turns: number of full turns
        x_scale: horizontal stretch factor (>1 widens, <1 narrows)
        y_scale: vertical stretch factor (>1 tallens, <1 flattens)

    Returns:
        list of (x, y) tuples
    """
    points = []
    for i in range(num_points):
        t = i / max(num_points - 1, 1)
        angle = math.radians(start_angle) + t * turns * 2 * math.pi
        r = t * max_radius
        x = cx + r * math.cos(angle) * x_scale
        y = cy + r * math.sin(angle) * y_scale
        points.append((x, y))
    return points


def deterministic_random(seed_str: str, count: int, min_val: float, max_val: float) -> list:
    """Generate deterministic pseudo-random values from a seed string.

    Uses hash-based approach for reproducible star field positions.
    """
    values = []
    for i in range(count):
        h = hashlib.md5(f"{seed_str}_{i}".encode()).hexdigest()
        normalized = int(h[:8], 16) / 0xFFFFFFFF
        values.append(min_val + normalized * (max_val - min_val))
    return values


def esc(text: str) -> str:
    """Escape text for safe embedding in SVG/XML."""
    return xml_escape(str(text), entities={'"': "&quot;", "'": "&apos;"})
