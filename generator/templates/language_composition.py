"""SVG template: Language Composition — stacked bar, legend, activity (dynamic height)."""

from generator.utils import (
    METRIC_COLORS,
    METRIC_ICONS,
    METRIC_LABELS,
    bucket_languages,
    ensure_contrast,
    esc,
    format_number,
)

WIDTH = 850
PAD = 30
CONTENT_W = WIDTH - PAD * 2

# Band 1: bar geometry from the LANGUAGE TELEMETRY bars
BAR_Y = 59
BAR_H = 12
BAR_RX = 3
BAR_OPACITY = "0.85"
SEG_GAP = 3

# Band 2: pill styling from the FEATURED SYSTEMS tag chips
PILL_H = 18
PILL_RX = 9
PILL_FILL_OPACITY = "0.12"
PILL_PAD = 8
PILL_FONT = 11
PILL_BASELINE_DY = 12
CHAR_W = 0.6 * PILL_FONT  # monospace advance
LEGEND_COLS = 4
LEGEND_TOP_GAP = 18  # 1.5 bar heights
ROW_PITCH = PILL_H + PILL_PAD
MAX_NAME_CHARS = 12
SWATCH_W = BAR_H
SWATCH_H = PILL_PAD
SWATCH_RX = BAR_RX
SWATCH_GAP = PILL_PAD

# Band 3: cell offsets from the MISSION TELEMETRY metric cells
ACTIVITY_METRICS = ["commits", "prs", "repos", "stars"]
DIVIDER_GAP = PILL_H
STAT_TOP_GAP = 18
STAT_ICON_DY = -40  # clears the number's ascender
STAT_NUM_DY = 2
STAT_CAPTION_DY = 20
STAT_NUM_SIZE = 28
STAT_CAPTION_SIZE = 11


def _layout(row_count: int) -> dict:
    """Resolve vertical geometry. Height is a function of legend row count only."""
    legend_top = BAR_Y + BAR_H + LEGEND_TOP_GAP
    legend_bottom = legend_top + (row_count - 1) * ROW_PITCH + PILL_H
    divider_y = legend_bottom + DIVIDER_GAP
    stat_base_y = divider_y + STAT_TOP_GAP - STAT_ICON_DY
    return {
        "legend_top": legend_top,
        "divider_y": divider_y,
        "stat_base_y": stat_base_y,
        "height": stat_base_y + STAT_CAPTION_DY + PAD,
    }


def _row_slices(count: int) -> list:
    """Return (start_index, columns) per row, rebalancing a partial last row."""
    rows = []
    start = 0
    while start < count:
        cols = min(LEGEND_COLS, count - start)
        rows.append((start, cols))
        start += cols
    return rows


def _truncate(name: str) -> str:
    """Clamp a language name so pill widths stay bounded."""
    return name[:MAX_NAME_CHARS]


def _resolve_entries(languages: dict, exclude: list, theme: dict) -> list:
    """Bucket languages, then resolve display name and panel-safe swatch color."""
    entries = []
    for entry in bucket_languages(languages, exclude):
        color = (
            theme["text_faint"]
            if entry["folded"]
            else ensure_contrast(entry["color"], theme["nebula"])
        )
        entries.append(
            {
                "name": _truncate(entry["name"]),
                "percentage": entry["percentage"],
                "color": color,
            }
        )
    return entries


def _build_bar(entries: list) -> str:
    """Build the stacked bar: square segments under a rounded clipPath."""
    right_edge = PAD + CONTENT_W
    segments = []
    cursor = float(PAD)

    for i, entry in enumerate(entries):
        span = CONTENT_W * entry["percentage"] / 100
        if i == len(entries) - 1:
            seg_w = right_edge - cursor
        else:
            seg_w = span - SEG_GAP
        if seg_w > 0:
            segments.append(
                f'      <rect x="{cursor:.2f}" y="{BAR_Y}" width="{seg_w:.2f}" '
                f'height="{BAR_H}" fill="{entry["color"]}" opacity="{BAR_OPACITY}"/>'
            )
        cursor += span

    return (
        f'    <g clip-path="url(#lang-bar-clip)">\n'
        + "\n".join(segments)
        + "\n    </g>"
    )


def _build_pill(entry: dict, cx: float, row_y: float, theme: dict) -> str:
    """Build one legend pill: swatch, language name, percentage."""
    name = esc(entry["name"])
    pct = f"{entry['percentage']:.1f}%"
    text_w = (len(entry["name"]) + 1 + len(pct)) * CHAR_W
    pill_w = PILL_PAD * 2 + SWATCH_W + SWATCH_GAP + text_w
    pill_x = cx - pill_w / 2

    swatch_x = pill_x + PILL_PAD
    swatch_y = row_y + (PILL_H - SWATCH_H) / 2
    text_x = swatch_x + SWATCH_W + SWATCH_GAP
    pct_x = text_x + (len(entry["name"]) + 1) * CHAR_W
    baseline = row_y + PILL_BASELINE_DY

    return (
        f'    <g>\n'
        f'      <rect x="{pill_x:.2f}" y="{row_y}" width="{pill_w:.2f}" height="{PILL_H}" '
        f'rx="{PILL_RX}" ry="{PILL_RX}" fill="{entry["color"]}" opacity="{PILL_FILL_OPACITY}"/>\n'
        f'      <rect x="{swatch_x:.2f}" y="{swatch_y:.2f}" width="{SWATCH_W}" height="{SWATCH_H}" '
        f'rx="{SWATCH_RX}" ry="{SWATCH_RX}" fill="{entry["color"]}"/>\n'
        f'      <text x="{text_x:.2f}" y="{baseline}" fill="{theme["text_dim"]}" '
        f'font-size="{PILL_FONT}" font-family="monospace">{name}</text>\n'
        f'      <text x="{pct_x:.2f}" y="{baseline}" fill="{theme["text_faint"]}" '
        f'font-size="{PILL_FONT}" font-family="monospace">{pct}</text>\n'
        f'    </g>'
    )


def _build_legend(entries: list, legend_top: float, theme: dict) -> str:
    """Build the legend grid, balancing the columns of a partial last row."""
    pills = []
    for row_index, (start, cols) in enumerate(_row_slices(len(entries))):
        row_y = legend_top + row_index * ROW_PITCH
        col_w = CONTENT_W / cols
        for col in range(cols):
            cx = PAD + col_w * (col + 0.5)
            pills.append(_build_pill(entries[start + col], cx, row_y, theme))
    return "\n".join(pills)


def _build_activity(stats: dict, base_y: float, theme: dict) -> str:
    """Build the four stat cells, reusing the MISSION TELEMETRY cell geometry."""
    cell_width = CONTENT_W / len(ACTIVITY_METRICS)
    cells = []

    for i, key in enumerate(ACTIVITY_METRICS):
        cx = PAD + cell_width * i + cell_width / 2
        icon_color = theme.get(METRIC_COLORS.get(key, "synapse_cyan"), "#00d4ff")
        value = format_number(stats.get(key, 0))
        label = METRIC_LABELS.get(key, key.title())
        icon_path = METRIC_ICONS.get(key, "")
        delay = f"{i * 0.3}s"

        cells.append(f'''    <g class="metric-cell" transform="translate({cx}, {base_y})">
      <g transform="translate(-8, {STAT_ICON_DY}) scale(1)">
        <svg viewBox="0 0 16 16" width="16" height="16" fill="{icon_color}" class="metric-icon" style="animation-delay: {delay}">
          {icon_path}
        </svg>
      </g>
      <text x="0" y="{STAT_NUM_DY}" text-anchor="middle" fill="{icon_color}" font-size="{STAT_NUM_SIZE}" font-weight="bold" font-family="sans-serif" opacity="0.35" filter="url(#num-glow)">{value}</text>
      <text x="0" y="{STAT_NUM_DY}" text-anchor="middle" fill="{theme['text_bright']}" font-size="{STAT_NUM_SIZE}" font-weight="bold" font-family="sans-serif">{value}</text>
      <text x="0" y="{STAT_CAPTION_DY}" text-anchor="middle" fill="{theme['text_faint']}" font-size="{STAT_CAPTION_SIZE}" font-family="monospace" letter-spacing="1">{label}</text>
    </g>''')

    return "\n".join(cells)


def render(
    languages: dict,
    stats: dict,
    theme: dict,
    exclude: list,
) -> str:
    """Render the language composition SVG.

    Args:
        languages: dict of language name -> byte count
        stats: dict with keys like commits, prs, repos, stars
        theme: color palette dict
        exclude: languages to exclude
    """
    entries = _resolve_entries(languages, exclude, theme)
    row_count = max(1, len(_row_slices(len(entries))))
    geom = _layout(row_count)
    height = geom["height"]

    bar_str = _build_bar(entries) if entries else ""
    legend_str = _build_legend(entries, geom["legend_top"], theme) if entries else ""
    activity_str = _build_activity(stats, geom["stat_base_y"], theme)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}">
  <defs>
    <style>
      .metric-icon {{
        animation: count-glow 4s ease-in-out infinite;
      }}
      @keyframes count-glow {{
        0%, 100% {{ fill-opacity: 0.7; }}
        50% {{ fill-opacity: 1; }}
      }}
    </style>
    <filter id="num-glow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="3"/>
    </filter>
    <clipPath id="lang-bar-clip">
      <rect x="{PAD}" y="{BAR_Y}" width="{CONTENT_W}" height="{BAR_H}" rx="{BAR_RX}" ry="{BAR_RX}"/>
    </clipPath>
  </defs>

  <!-- Card background -->
  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="12" ry="12"
        fill="{theme['nebula']}" stroke="{theme['star_dust']}" stroke-width="1"/>

  <!-- Section title -->
  <text x="{PAD}" y="38" fill="{theme['text_faint']}" font-size="11" font-family="monospace" letter-spacing="3">MISSION TELEMETRY</text>

  <!-- Band 1: stacked language bar -->
{bar_str}

  <!-- Band 2: legend -->
{legend_str}

  <!-- Band 3: activity -->
  <line x1="{PAD}" y1="{geom['divider_y']}" x2="{PAD + CONTENT_W}" y2="{geom['divider_y']}" stroke="{theme['star_dust']}" stroke-width="1" opacity="0.5"/>
{activity_str}
</svg>'''
