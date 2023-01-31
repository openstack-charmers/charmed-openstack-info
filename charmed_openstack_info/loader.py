#
# Copyright (C) 2023 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import pprint

import yaml

from collections.abc import Sequence
from collections import OrderedDict
from importlib.resources import files
from pathlib import Path
from typing import (
    Any,
    Dict,
    Iterator,
    List,
    Optional,
    Union,
)

from charmed_openstack_info.exceptions import CategoryFileNotFound


logger = logging.getLogger(__name__)


class CharmProjectInfo:
    """Represents a CharmProjectInfo.

    The CharmProjectInfo is defined in a yaml file and has the following form:

    name: the human friendly name of the project
    charmhub: the charmhub store name
    launchpad: the launchpad project name
    team: the team who should own the branches and charm recipes
    repo: a URL to the upstream repository to be mirrored in
          launchpad
    branches: a list of branch -> recipe_info mappings for charm recipes on
            launchpad.

    The branch_info dictionary consists of the following keys:

      * channels (optional) - a list of fully qualified channel names to
          publish the charm to after building.
      * build-path (optional) - subdirectory within the branch containing
          metadata.yaml
      * recipe-name (optional) - A string used to format the name of the
          recipe. The project name will be passed as 'project', the branch
          name will be passed as 'branch', and the track name will be passed
          as 'track'. The default recipe-name is '{project}.{branch}.{track}'.
      * auto-build (optional) - a boolean indicating whether to automatically
          build the charm when the branch changes. Default value is True.
      * upload (optional) - a boolean indicating whether to upload to the store
          after a charm is built. Default value is True.
      * build-channels (optional) - a dictionary indicating which channels
          should be used by the launchpad builder for building charms. The
          key is the name of the snap or base and the value is the full
          channel identifier (e.g. latest/edge). Currently, Launchpad accepts
          the following keys: charmcraft, core, core18, core20 and core22.

    The following examples provide information for various scenarios.

    The following example uses all launchpad builder charm_recipe defaults
    publishes the main branch to the latest/edge channel and the stable
    branch to the latest/stable channel:

    name: Awesome Charm
    charmhub: awesome
    launchpad: charm-awesome
    team: awesome-charmers
    repo: https://github.com/canonical/charm-awesome-operator
    branches:
      main:
        channels: latest/edge
      stable:
        channels: latest/stable

    The following example builds a charm using the latest/edge channel of
    charmcraft, and does not upload the results to the store

    name: Awesome Charm
    charmhub: awesome
    launchpad: charm-awesome
    team: awesome-charmers
    repo: https://github.com/canonical/charm-awesome-operator
    branches:
      main:
        store-upload: False
        build-channels:
          charmcraft: latest/edge

    The following example builds a charm on the main branch of the git
    repository and publishes the results to the yoga/edge and latest/edge
    channels and builds a charm on the stable/xena branch of the git
    repository and publishes the results to xena/edge.

    name: Awesome Charm
    charmhub: awesome
    launchpad: charm-awesome
    team: awesome-charmers
    repo: https://github.com/canonical/charm-awesome-operator
    branches:
      main:
        channels:
          - yoga/edge
          - latest/edge
      stable/xena:
        channels:
          - xena/edge
    """

    def __init__(self, config: Dict[str, Any]):
        self.name: str = config.get('name')  # type: ignore
        self.team: str = config.get('team')  # type: ignore
        self.charmhub_name: str = config.get('charmhub')  # type: ignore
        self.launchpad_project: str = config.get('launchpad')  # type: ignore
        self.repository: str = config.get('repository')  # type: ignore
        self.branches: Dict[str, Dict[str, Any]] = {}
        self._add_branches(config.get('branches', {}))

    def _add_branches(self, branches_spec: Dict[str, Dict]) -> None:
        default_branch_info = {
            'auto-build': True,
            'upload': True,
            'recipe-name': '{project}.{branch}.{track}'
        }
        for branch, branch_info in branches_spec.items():
            ref = f'refs/heads/{branch}'
            if ref not in self.branches:
                self.branches[ref] = dict(default_branch_info)
            if type(branch_info) != dict:
                raise ValueError('Expected a dict for key branches, '
                                 f' instead got {type(branch_info)}')

            self.branches[ref].update(branch_info)

    def merge(self, config: Dict[str, Any]) -> None:
        """Merge config, by overwriting."""
        self.name = config.get('name', self.name)
        self.team = config.get('team', self.team)
        self.charmhub_name = config.get('charmhub', self.charmhub_name)
        self.launchpad_project = config.get('launchpad',
                                            self.launchpad_project)
        self.repository = config.get('repository', self.repository)
        self._add_branches(config.get('branches', {}))

    def is_supported(self, channel="latest/stable"):
        """Is the charm available on the channel supported?"""


class CharmsGroupConfig:
    """Collect together all the config files and build CharmProjectInfo objects.

    This collects together the files passed (which define a charm projects
    config and creates CharmProject objects to ensure git repositories and
    ensure that the charm builder recipes in launchpad exist with the correct
    settings.
    """

    def __init__(self,
                 files: Optional[List[Union[str, Path]]] = None) -> None:
        """Configure the GroupConfig object.

        :param files: the list of files to load config from.
        """
        self.charm_projects: Dict[str, CharmProjectInfo] = OrderedDict()
        if files is not None:
            self.load_files(files)

    def load_files(
            self,
            files: Optional[List[Union[str, Path]]] = None,
    ) -> None:
        """Load the files into the object.

        This loads the files, and configures the projects and then creates
        CharmProjectInfo objects.

        :param files: the list of files to load config from.
        """
        assert not isinstance(files, str), "param files must not be str"
        assert isinstance(files, Sequence), "Must pass a list or tuple."
        for file in files:
            with open(file, 'r') as f:
                group_config = yaml.safe_load(f)
            logger.debug('group_config is: \n%s', pprint.pformat(group_config))
            project_defaults = group_config.get('defaults', {})
            for project in group_config.get('projects', []):
                for key, value in project_defaults.items():
                    project.setdefault(key, value)
                logger.debug('Loaded project %s', project.get('name'))
                self.add_charm_project(project)

    def add_charm_project(self,
                          project_config: Dict[str, Any],
                          merge: bool = False,
                          ) -> None:
        """Add a CharmProjectInfo object from the project specification dict.

        :param project: the project to add.
        :param merge: if merge is True, merge/overwrite the existing object.
        :raises: ValueError if merge is false and the charm project already
            exists.
        """
        name: str = project_config.get('name')  # type: ignore
        if name in self.charm_projects:
            if merge:
                self.charm_projects[name].merge(project_config)
            else:
                raise ValueError(
                    f"Project config for '{name}' already exists.")
        else:
            self.charm_projects[name] = CharmProjectInfo(project_config)

    def projects(self, select: Optional[List[str]] = None,
                 ) -> Iterator[CharmProjectInfo]:
        """Generator returns a list of projects."""
        if not (select):
            select = None
        for project in self.charm_projects.values():
            if (select is None or
                    project.launchpad_project in select or
                    project.charmhub_name in select):
                yield project


def find_file(category: str) -> Path:
    """Find the configuration file associated to a category"""
    fpath = files(
        'charmed_openstack_info.data.lp-builder-config'
    ).joinpath('%s.yaml' % category)
    if not fpath.is_file():
        raise CategoryFileNotFound(fpath)

    return Path(str(fpath))


def load_file(
        fpath: Union[str, Path],
        gc: Optional[CharmsGroupConfig] = None,
) -> CharmsGroupConfig:
    """Get a list of CharmProjectInfo objects.

    Parses the contents of the file.

    :param fpath: path to the configuration file to parse
    :returns: list of CharmProjectInfo objects
    """
    if not gc:
        gc = CharmsGroupConfig()

    gc.load_files([fpath])
    return gc
