"""Tests for SVG generation (SVGBuilder + templates)."""

import pytest

from generator.config import validate_config
from generator.svg_builder import SVGBuilder


class TestSVGBuilder:
    def test_init(self, svg_builder):
        assert svg_builder.config["username"] == "galaxy-dev"

    def test_render_galaxy_header_valid_svg(self, svg_builder):
        svg = svg_builder.render_galaxy_header()
        assert svg.strip().startswith("<svg")
        assert svg.strip().endswith("</svg>")

    def test_galaxy_header_contains_name(self, svg_builder):
        svg = svg_builder.render_galaxy_header()
        assert "Nyx Orion" in svg

    def test_galaxy_header_contains_animations(self, svg_builder):
        svg = svg_builder.render_galaxy_header()
        assert "animate" in svg

    def test_render_stats_card_valid_svg(self, svg_builder):
        svg = svg_builder.render_stats_card()
        assert svg.strip().startswith("<svg")
        assert svg.strip().endswith("</svg>")

    def test_stats_card_contains_formatted_values(self, svg_builder):
        svg = svg_builder.render_stats_card()
        assert "1.8k" in svg  # commits=1847
        assert "342" in svg   # stars
        assert "156" in svg   # prs

    def test_render_language_composition_valid_svg(self, svg_builder):
        svg = svg_builder.render_language_composition()
        assert svg.strip().startswith("<svg")
        assert svg.strip().endswith("</svg>")

    def test_language_composition_contains_language_names(self, svg_builder):
        svg = svg_builder.render_language_composition()
        assert "Python" in svg
        assert "TypeScript" in svg

    def test_language_composition_contains_activity_stats(self, svg_builder):
        svg = svg_builder.render_language_composition()
        assert "Commits" in svg
        assert "PRs" in svg
        assert "Repos" in svg
        assert "Stars" in svg
        assert "Issues" not in svg


class TestEdgeCases:
    def test_empty_languages(self, cfg, sample_stats):
        config = validate_config(cfg)
        builder = SVGBuilder(config, sample_stats, {})
        svg = builder.render_language_composition()
        assert svg.strip().startswith("<svg")
        assert svg.strip().endswith("</svg>")

    def test_partial_last_row_is_balanced(self, cfg, sample_stats):
        config = validate_config(cfg)
        langs = {name: 100 for name in ("Python", "Go", "Rust", "Ruby", "Zig")}
        builder = SVGBuilder(config, sample_stats, langs)
        svg = builder.render_language_composition()
        assert svg.count('rx="9"') == 5
        assert svg.strip().endswith("</svg>")

    def test_zero_stats(self, cfg, sample_languages):
        config = validate_config(cfg)
        zero_stats = {"commits": 0, "stars": 0, "prs": 0, "issues": 0, "repos": 0}
        builder = SVGBuilder(config, zero_stats, sample_languages)
        svg = builder.render_stats_card()
        assert svg.strip().startswith("<svg")
        assert svg.strip().endswith("</svg>")
