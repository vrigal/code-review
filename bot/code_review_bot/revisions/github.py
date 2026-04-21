# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from urllib.parse import urlparse

import requests
import structlog

from code_review_bot.revisions import Revision

logger = structlog.get_logger(__name__)


class GithubRevision(Revision):
    """
    A revision from a github pull-request
    """

    def __init__(self, base_repo_url, head_repo_url, pull_number, pull_head_sha):
        super().__init__()

        self.base_repo_url = base_repo_url
        self.head_repo_url = head_repo_url
        self.pull_number = pull_number
        self.pull_head_sha = pull_head_sha

        # Load the patch from Github
        self.patch = self.load_patch()

    def __str__(self):
        return f"Github pull request {self.base_repo_url} #{self.pull_number} ({self.pull_head_sha[:8]})"

    def __repr__(self):
        return f"GithubRevision base_repo={self.base_repo_url} head_repo={self.head_repo_url} pull_number={self.pull_number} sha={self.pull_head_sha}"

    @property
    def repo_name(self):
        """
        Extract the name of the repository from its URL
        """
        return urlparse(self.base_repo_url).path.strip("/")

    @property
    def repository_slug(self):
        """
        Generate a slug from the Github repository.
        This method copies the automatic slug creation in backend's RepositoryGetOrCreateField serializer field.
        """
        parsed = urlparse(self.base_repo_url)
        return parsed.path.lstrip("/").replace("/", "-")

    def load_patch(self):
        """
        Load the patch content for the current pull request HEAD
        """
        # TODO: use specific sha
        url = f"{self.base_repo_url}/pull/{self.pull_number}.diff"
        logger.info("Loading github patch", url=url)
        resp = requests.get(url, allow_redirects=True)
        resp.raise_for_status()
        return resp.content.decode()

    def as_dict(self):
        return {
            "base_repo_url": self.base_repo_url,
            "head_repo_url": self.head_repo_url,
            "pull_number": self.pull_number,
            "pull_head_sha": self.pull_head_sha,
        }

    def serialize(self):
        """
        Outputs a tuple of dicts for revision and diff (empty for Github) sent to backend
        """
        revision = {
            "provider": "github",
            "provider_id": self.pull_number,
            # TODO: Use the pull request information from the API
            "title": f"Issue {self.pull_number}",
            "bugzilla_id": None,
            "base_repository": self.base_repo_url,
            "head_repository": self.head_repo_url,
        }
        diff = {
            "provider": "github",
            "provider_id": self.pull_head_sha,
            "mercurial_hash": self.pull_head_sha,
            "repository": self.base_repo_url,
        }
        return revision, diff
