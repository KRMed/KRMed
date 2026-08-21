"""Tests for the GitHub API client (token handling, lifetime windows, REST fallback)."""

from datetime import datetime, timezone

import pytest

from generator.github_api import GitHubAPI


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.headers = {}
        self.text = ""

    def json(self):
        return self._payload

    def raise_for_status(self):
        pass


class TestTokenResolution:
    def test_prefers_pat_over_actions_token(self, monkeypatch):
        monkeypatch.setenv("PROFILE_TOKEN", "pat-value")
        monkeypatch.setenv("GITHUB_TOKEN", "actions-value")
        assert GitHubAPI("someone").token == "pat-value"

    def test_falls_back_to_actions_token(self, monkeypatch):
        monkeypatch.delenv("PROFILE_TOKEN", raising=False)
        monkeypatch.delenv("GH_PAT", raising=False)
        monkeypatch.setenv("GITHUB_TOKEN", "actions-value")
        assert GitHubAPI("someone").token == "actions-value"

    def test_no_token_is_empty(self, monkeypatch):
        for name in ("PROFILE_TOKEN", "GH_PAT", "GITHUB_TOKEN"):
            monkeypatch.delenv(name, raising=False)
        assert GitHubAPI("someone").token == ""

    def test_unauthenticated_never_sees_private(self, monkeypatch):
        for name in ("PROFILE_TOKEN", "GH_PAT", "GITHUB_TOKEN"):
            monkeypatch.delenv(name, raising=False)
        assert GitHubAPI("someone")._sees_private_data() is False


class TestContributionWindows:
    def test_one_window_per_year(self):
        api = GitHubAPI("someone", token="x")
        windows = api._contribution_windows("2019-04-17T12:30:00Z")
        expected = datetime.now(timezone.utc).year - 2019 + 1
        assert len(windows) == expected

    def test_first_window_starts_at_signup(self):
        api = GitHubAPI("someone", token="x")
        windows = api._contribution_windows("2019-04-17T12:30:00Z")
        assert windows[0][0] == "2019-04-17T12:30:00Z"

    def test_windows_do_not_overlap(self):
        api = GitHubAPI("someone", token="x")
        windows = api._contribution_windows("2019-04-17T12:30:00Z")
        for (_, end), (start, _) in zip(windows, windows[1:]):
            assert end < start

    def test_each_window_within_one_year(self):
        api = GitHubAPI("someone", token="x")
        fmt = "%Y-%m-%dT%H:%M:%SZ"
        for start, end in api._contribution_windows("2019-04-17T12:30:00Z"):
            span = datetime.strptime(end, fmt) - datetime.strptime(start, fmt)
            assert span.days <= 366

    def test_account_created_this_year(self):
        api = GitHubAPI("someone", token="x")
        this_year = datetime.now(timezone.utc).year
        windows = api._contribution_windows(f"{this_year}-01-02T00:00:00Z")
        assert len(windows) == 1


class TestRestStats:
    @pytest.fixture
    def api(self, monkeypatch):
        for name in ("PROFILE_TOKEN", "GH_PAT", "GITHUB_TOKEN"):
            monkeypatch.delenv(name, raising=False)
        return GitHubAPI("someone")

    def test_excludes_forks_from_repos_and_stars(self, api, monkeypatch):
        page = [
            {"fork": False, "stargazers_count": 10},
            {"fork": True, "stargazers_count": 500},
            {"fork": False, "stargazers_count": 3},
        ]
        monkeypatch.setattr(api, "_paginate_repos", lambda: iter([page]))
        monkeypatch.setattr(api, "_search_count", lambda endpoint, query: 0)
        stats = api._fetch_stats_rest()
        assert stats["repos"] == 2
        assert stats["stars"] == 13

    def test_commits_come_from_commit_search(self, api, monkeypatch):
        monkeypatch.setattr(api, "_paginate_repos", lambda: iter([]))
        calls = []

        def fake_search(endpoint, query):
            calls.append((endpoint, query))
            return {"commits": 303, "issues": 99}[endpoint]

        monkeypatch.setattr(api, "_search_count", fake_search)
        stats = api._fetch_stats_rest()
        assert stats["commits"] == 303
        assert ("commits", "author:someone") in calls

    def test_search_count_hits_requested_endpoint(self, api, monkeypatch):
        seen = {}

        def fake_request(method, url, **kwargs):
            seen["url"] = url
            seen["q"] = kwargs["params"]["q"]
            return FakeResponse({"total_count": 42})

        monkeypatch.setattr(api, "_request", fake_request)
        assert api._search_count("commits", "author:someone") == 42
        assert seen["url"].endswith("/search/commits")
        assert seen["q"] == "author:someone"

    def test_search_count_returns_zero_on_error(self, api, monkeypatch):
        monkeypatch.setattr(
            api, "_request", lambda *a, **k: FakeResponse({}, status_code=422)
        )
        assert api._search_count("commits", "author:someone") == 0
