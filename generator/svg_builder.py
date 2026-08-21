"""SVG Builder — orchestrator connecting config, stats, and templates."""

from generator.templates import galaxy_header, stats_card, language_composition


class SVGBuilder:
    """Builds all SVG assets from config and GitHub data.

    Expects a config dict that has already been through validate_config(),
    which resolves theme defaults and applies missing optional fields.
    """

    def __init__(self, config: dict, stats: dict, languages: dict):
        self.config = config
        self.stats = stats
        self.languages = languages
        self.theme = config["theme"]
        self.galaxy_arms = config.get("galaxy_arms", [])
        self.projects = config.get("projects", [])

    def render_galaxy_header(self) -> str:
        return galaxy_header.render(
            config=self.config,
            theme=self.theme,
            galaxy_arms=self.galaxy_arms,
            projects=self.projects,
        )

    def render_stats_card(self) -> str:
        metrics = self.config["stats"]["metrics"]
        return stats_card.render(
            stats=self.stats,
            metrics=metrics,
            theme=self.theme,
        )

    def render_language_composition(self) -> str:
        lang_config = self.config.get("languages", {})
        return language_composition.render(
            languages=self.languages,
            stats=self.stats,
            theme=self.theme,
            exclude=lang_config.get("exclude", []),
        )
