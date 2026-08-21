"""GitHub API client for fetching user stats and language data."""

import logging
import os
import time
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)

# A personal access token sees private contributions; the Actions GITHUB_TOKEN does not
TOKEN_ENV_VARS = ("PROFILE_TOKEN", "GH_PAT", "GITHUB_TOKEN")


class GitHubAPI:
    """Fetches GitHub stats via GraphQL (with token) or REST (fallback)."""

    GRAPHQL_URL = "https://api.github.com/graphql"
    REST_URL = "https://api.github.com"

    def __init__(self, username: str, token: str = None):
        self.username = username
        self.token = token or self._token_from_env()
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"
        self._viewer_login = None
        self._viewer_checked = False

    @staticmethod
    def _token_from_env() -> str:
        """Return the first token found, preferring a PAT over the Actions token."""
        for name in TOKEN_ENV_VARS:
            value = os.environ.get(name, "")
            if value:
                if name == "GITHUB_TOKEN":
                    logger.warning(
                        "Using GITHUB_TOKEN. It cannot read private contributions; "
                        "set PROFILE_TOKEN to a PAT with repo + read:user for full stats."
                    )
                return value
        return ""

    def _authenticated_login(self) -> str:
        """Return the login the token belongs to, or '' when unauthenticated."""
        if self._viewer_checked:
            return self._viewer_login or ""
        self._viewer_checked = True
        if not self.token:
            return ""
        try:
            resp = self._request("GET", f"{self.REST_URL}/user")
            if resp.status_code == 200:
                self._viewer_login = resp.json().get("login", "")
        except requests.exceptions.RequestException as e:
            logger.warning("Could not identify token owner: %s", e)
        return self._viewer_login or ""

    def _sees_private_data(self) -> bool:
        """True when the token belongs to the profile being rendered."""
        login = self._authenticated_login()
        return bool(login) and login.lower() == self.username.lower()

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make an HTTP request with rate-limit awareness and retry.

        Checks X-RateLimit-Remaining after each response.
        On 403 rate-limit, waits until reset and retries once.
        """
        kwargs.setdefault("headers", self.headers)
        kwargs.setdefault("timeout", 15)

        resp = requests.request(method, url, **kwargs)

        # Check rate limit headers
        remaining = resp.headers.get("X-RateLimit-Remaining")
        if remaining is not None and int(remaining) < 10:
            reset_ts = int(resp.headers.get("X-RateLimit-Reset", 0))
            logger.warning(
                "GitHub API rate limit low: %s remaining (resets at %s)",
                remaining,
                time.strftime("%H:%M:%S", time.localtime(reset_ts)),
            )

        # Retry once on rate-limit 403
        if resp.status_code == 403 and "rate limit" in resp.text.lower():
            reset_ts = int(resp.headers.get("X-RateLimit-Reset", 0))
            wait = max(reset_ts - int(time.time()), 1)
            logger.warning("Rate limited. Waiting %ds for reset...", wait)
            time.sleep(wait)
            resp = requests.request(method, url, **kwargs)

        return resp

    def fetch_stats(self) -> dict:
        """Fetch user statistics. Uses GraphQL if token available, REST otherwise."""
        if self.token:
            return self._fetch_stats_graphql()
        return self._fetch_stats_rest()

    def _graphql(self, query: str, variables: dict) -> dict:
        """Run a GraphQL query, returning the `data.user` payload or None on failure."""
        try:
            resp = self._request(
                "POST",
                self.GRAPHQL_URL,
                json={"query": query, "variables": variables},
            )
            resp.raise_for_status()
        except requests.exceptions.Timeout:
            logger.warning("GraphQL request timed out.")
            return None
        except requests.exceptions.HTTPError as e:
            logger.warning("GraphQL HTTP error (%s).", e)
            return None

        data = resp.json()
        if "errors" in data:
            logger.warning("GraphQL errors: %s", data["errors"])
            return None
        return (data.get("data") or {}).get("user")

    PROFILE_QUERY = """
    query($username: String!, $cursor: String) {
      user(login: $username) {
        createdAt
        pullRequests { totalCount }
        issues { totalCount }
        repositories(ownerAffiliations: OWNER, isFork: false, first: 100, after: $cursor) {
          totalCount
          pageInfo { hasNextPage endCursor }
          nodes { stargazerCount }
        }
      }
    }
    """

    def _fetch_stats_graphql(self) -> dict:
        """Fetch lifetime stats via GraphQL, including private data when the token allows."""
        if not self._sees_private_data():
            logger.warning(
                "Token does not belong to @%s; private contributions will be excluded.",
                self.username,
            )

        user = self._graphql(self.PROFILE_QUERY, {"username": self.username, "cursor": None})
        if user is None:
            return self._fetch_stats_rest()

        repos = user["repositories"]
        total_stars = sum(n["stargazerCount"] for n in repos["nodes"])
        page = repos["pageInfo"]

        # Star totals need every owned repo, not just the first page
        while page["hasNextPage"]:
            nxt = self._graphql(
                self.PROFILE_QUERY,
                {"username": self.username, "cursor": page["endCursor"]},
            )
            if nxt is None:
                break
            total_stars += sum(n["stargazerCount"] for n in nxt["repositories"]["nodes"])
            page = nxt["repositories"]["pageInfo"]

        return {
            "commits": self._fetch_lifetime_commits(user["createdAt"]),
            "stars": total_stars,
            "prs": user["pullRequests"]["totalCount"],
            "issues": user["issues"]["totalCount"],
            "repos": repos["totalCount"],
        }

    def _contribution_windows(self, created_at: str) -> list:
        """Return one (from, to) ISO-8601 pair per year since signup.

        contributionsCollection accepts at most a one-year span, so lifetime
        totals require one window per year.
        """
        start = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        windows = []
        for year in range(start.year, now.year + 1):
            frm = max(start, datetime(year, 1, 1, tzinfo=timezone.utc))
            to = min(now, datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc))
            if frm < to:
                windows.append((frm.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                to.strftime("%Y-%m-%dT%H:%M:%SZ")))
        return windows

    def _fetch_lifetime_commits(self, created_at: str) -> int:
        """Sum commit contributions across every year since the account was created."""
        windows = self._contribution_windows(created_at)
        if not windows:
            return 0

        fields = "\n".join(
            f'          y{i}: contributionsCollection(from: "{frm}", to: "{to}") {{\n'
            f"            totalCommitContributions\n"
            f"            restrictedContributionsCount\n"
            f"          }}"
            for i, (frm, to) in enumerate(windows)
        )
        query = (
            "query($username: String!) {\n"
            "  user(login: $username) {\n"
            f"{fields}\n"
            "  }\n"
            "}"
        )

        user = self._graphql(query, {"username": self.username})
        if user is None:
            logger.warning("Lifetime commit query failed; commit count may be incomplete.")
            return 0

        # restrictedContributionsCount is 0 when the token can already see private repos
        return sum(
            c["totalCommitContributions"] + c["restrictedContributionsCount"]
            for c in user.values()
        )

    def _fetch_stats_rest(self) -> dict:
        """Fetch lifetime stats via REST. Public data only, but complete."""
        logger.info("Using REST (public data only).")

        # Non-fork owned repos, matching the GraphQL path and language aggregation
        total_stars = 0
        repo_count = 0
        for repos in self._paginate_repos():
            for repo in repos:
                if repo.get("fork"):
                    continue
                repo_count += 1
                total_stars += repo.get("stargazers_count", 0)

        return {
            "commits": self._search_count("commits", f"author:{self.username}"),
            "stars": total_stars,
            "prs": self._search_count("issues", f"author:{self.username} type:pr"),
            "issues": self._search_count("issues", f"author:{self.username} type:issue"),
            "repos": repo_count,
        }

    def _paginate_repos(self):
        """Yield pages of owned repos, including private ones when the token allows."""
        if self._sees_private_data():
            url = f"{self.REST_URL}/user/repos"
            base_params = {"affiliation": "owner", "visibility": "all"}
        else:
            url = f"{self.REST_URL}/users/{self.username}/repos"
            base_params = {"type": "owner"}

        page = 1
        while True:
            repos_resp = self._request(
                "GET",
                url,
                params={**base_params, "per_page": 100, "page": page},
            )
            repos_resp.raise_for_status()
            repos = repos_resp.json()
            if not repos:
                break
            yield repos
            if len(repos) < 100:
                break
            page += 1

    def _search_count(self, endpoint: str, query: str) -> int:
        """Use the GitHub Search API to get a total_count for a query."""
        try:
            resp = self._request(
                "GET",
                f"{self.REST_URL}/search/{endpoint}",
                params={"q": query, "per_page": 1},
            )
            if resp.status_code == 200:
                return resp.json().get("total_count", 0)
            logger.warning("Search API returned %d for query '%s'", resp.status_code, query)
        except requests.exceptions.RequestException as e:
            logger.warning("Search API failed for '%s': %s", query, e)
        return 0

    def fetch_languages(self) -> dict:
        """Fetch language byte counts aggregated across all owned non-fork repos."""
        languages = {}
        for repos in self._paginate_repos():
            for repo in repos:
                if repo.get("fork"):
                    continue
                try:
                    lang_resp = self._request("GET", repo["languages_url"])
                    if lang_resp.status_code == 200:
                        for lang, bytes_count in lang_resp.json().items():
                            languages[lang] = languages.get(lang, 0) + bytes_count
                    else:
                        logger.warning(
                            "Could not fetch languages for %s (HTTP %d)",
                            repo.get("full_name", "unknown"),
                            lang_resp.status_code,
                        )
                except requests.exceptions.RequestException as e:
                    logger.warning(
                        "Error fetching languages for %s: %s",
                        repo.get("full_name", "unknown"),
                        e,
                    )
        return languages
