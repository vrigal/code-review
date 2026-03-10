# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from functools import cached_property
from urllib.parse import urlparse

import requests
import structlog

from code_review_bot import taskcluster
from code_review_bot.revisions import Revision

logger = structlog.get_logger(__name__)


class GithubRevision(Revision):
    """
    A revision from a github pull-request
    """

    def __init__(self, repo_url, branch, pull_number, pull_head_sha):
        super().__init__()

        self.repo_url = repo_url
        self.branch = branch
        self.pull_number = pull_number
        self.pull_head_sha = pull_head_sha

        # Load the patch from Github
        self.patch = self.load_patch()

    def __str__(self):
        return f"Github pull request {self.repo_url} #{self.pull_number} ({self.pull_head_sha[:8]})"

    def __repr__(self):
        return f"GithubRevision repo_url={self.repo_url} branch={self.branch} pull_number={self.pull_number} sha={self.pull_head_sha}"

    @property
    def repo_name(self):
        """
        Extract the name of the repository from its URL
        """
        return urlparse(self.repo_url).path.strip("/")

    @property
    def repository_slug(self):
        """
        Generate a slug from the Github repository.
        This method copies the automatic slug creation in backend's RepositoryGetOrCreateField serializer field.
        """
        base_repo_url = self.pull_request.base.repo.html_url
        parsed = urlparse(base_repo_url)
        return parsed.path.lstrip("/").replace("/", "-")

    def load_patch(self):
        """
        Load the patch content for the current pull request HEAD
        """
        # TODO: use specific sha
        url = f"{self.repo_url}/pull/{self.pull_number}.diff"
        logger.info("Loading github patch", url=url)
        resp = requests.get(url, allow_redirects=True)
        resp.raise_for_status()
        return resp.content.decode()

    def as_dict(self):
        return {
            "repo_url": self.repo_url,
            "branch": self.branch,
            "pull_number": self.pull_number,
            "pull_head_sha": self.pull_head_sha,
        }

    @cached_property
    def pull_request(self):
        from code_review_bot.sources.github import GithubClient

        reporter_conf = next(
            (
                reporter
                for reporter in taskcluster.secrets["REPORTERS"]
                if reporter["reporter"] == "github"
            ),
            None,
        )
        # A github reporter configuration is required to perform a github Pull Request analysis
        assert reporter_conf, "Github reporter secrets must be set to access information about the pull request"
        client = GithubClient(
            client_id=reporter_conf["client_id"],
            private_key=reporter_conf["private_key_pem"],
            installation_id=reporter_conf["installation_id"],
        )
        return client.get_pull_request(self)

    def serialize(self):
        """
        Outputs a tuple of dicts for revision and diff (empty for Github) sent to backend
        """
        revision = {
            "provider": "github",
            "provider_id": self.pull_number,
            "title": self.pull_request.title,
            "bugzilla_id": None,
            "base_repository": self.pull_request.base.repo.html_url,
            "head_repository": self.repo_url,
        }
        diff = {
            "provider": "github",
            "provider_id": self.pull_head_sha,
            "mercurial_hash": self.pull_head_sha,
            "repository": self.repo_url,
        }
        return revision, diff
