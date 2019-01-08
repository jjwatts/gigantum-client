# Copyright (c) 2017 FlashX, LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import os
import re
import yaml
import json
import datetime

from typing import (Dict, Optional)

from gtmcore.gitlib import GitAuthor
from gtmcore.logging import LMLogger
from gtmcore.labbook.schemas import validate_labbook_schema
from gtmcore.activity import ActivityType, ActivityDetailType

from gtmcore.inventory.repository import Repository

logger = LMLogger.get_logger()


class LabBook(Repository):
    """Class representing a single LabBook"""
    _default_activity_type = ActivityType.LABBOOK
    _default_activity_detail_type = ActivityDetailType.LABBOOK
    _default_activity_section = "Project Root"

    def __init__(self, config_file: Optional[str] = None, author: Optional[GitAuthor] = None) -> None:
        super().__init__(config_file, author)

        # LabBook Environment
        self._env = None

    def __str__(self):
        if self._root_dir:
            return f'<LabBook at `{self._root_dir}`>'
        else:
            return f'<LabBook UNINITIALIZED>'

    def __eq__(self, other):
        return isinstance(other, LabBook) and other.root_dir == self.root_dir

    @property
    def id(self) -> str:
        if self._data:
            return self._data["labbook"]["id"]
        else:
            raise ValueError("No ID assigned to Lab Book.")

    @property
    def name(self) -> str:
        if self._data:
            return self._data["labbook"]["name"]
        else:
            raise ValueError("No name assigned to Lab Book.")

    @name.setter
    def name(self, value: str) -> None:
        if not value:
            raise ValueError("value cannot be None or empty")

        if not self._data:
            self._data = {'labbook': {'name': value}}
        else:
            self._data["labbook"]["name"] = value
        self._validate_gigantum_data()

        # Update data file
        self._save_gigantum_data()

        # Rename directory
        if self._root_dir:
            base_dir, _ = self._root_dir.rsplit(os.path.sep, 1)
            os.rename(self._root_dir, os.path.join(base_dir, value))
        else:
            raise ValueError("Lab Book root dir not specified. Failed to configure git.")

        # Update the root directory to the new directory name
        self._set_root_dir(os.path.join(base_dir, value))

    @property
    def creation_date(self) -> Optional[datetime.datetime]:
        path = os.path.join(self.root_dir, '.gigantum', 'buildinfo')
        if os.path.isfile(path):
            with open(path) as p:
                info = json.load(p)
                date_str = info.get('creation_utc')
                d = datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%f')
                return d
        else:
            first_commit = self.git.repo.git.rev_list('HEAD', max_parents=0)
            create_date = self.git.log_entry(first_commit)['committed_on'].replace(tzinfo=None)
            return create_date

    @property
    def build_details(self) -> Optional[Dict[str, str]]:
        path = os.path.join(self.root_dir, '.gigantum', 'buildinfo')
        if os.path.isfile(path):
            with open(path) as p:
                info = json.load(p)
                return info.get('build_info')
        else:
            return None

    @property
    def description(self) -> str:
        if self._data:
            return self._data["labbook"]["description"]
        else:
            raise ValueError("No description assigned to Lab Book.")

    @description.setter
    def description(self, value) -> None:
        if not self._data:
            self._data = {'labbook': {'description': value}}
        else:
            self._data["labbook"]["description"] = value

        self._save_gigantum_data()

    @property
    def cuda_version(self) -> Optional[str]:
        if self._data and self._data.get("cuda_version"):
            return self._data.get("cuda_version")
        else:
            return None

    @cuda_version.setter
    def cuda_version(self, cuda_version: Optional[str] = None) -> None:
        if self._data:
            self._data['cuda_version'] = cuda_version
            self._save_gigantum_data()
        else:
            raise ValueError("LabBook _data cannot be None")

    def _save_gigantum_data(self) -> None:
        """Method to save changes to the LabBook

        Returns:
            None
        """
        if not self.root_dir:
            raise ValueError("No root directory assigned to lab book. Failed to get root directory.")

        with open(os.path.join(self.root_dir, ".gigantum", "labbook.yaml"), 'wt') as lbfile:
            lbfile.write(yaml.safe_dump(self._data, default_flow_style=False))
            lbfile.flush()

    def _load_gigantum_data(self) -> None:
        """Method to load the labbook YAML file to a dictionary

        Returns:
            None
        """
        if not self.root_dir:
            raise ValueError("No root directory assigned to lab book. Failed to get root directory.")

        with open(os.path.join(self.root_dir, ".gigantum", "labbook.yaml"), 'rt') as lbfile:
            self._data = yaml.safe_load(lbfile)

    def _validate_gigantum_data(self) -> None:
        """Method to validate the LabBook data file contents

        Returns:
            None
        """
        if not re.match("^(?!-)(?!.*--)[a-z0-9-]+(?<!-)$", self.name):
            raise ValueError("Invalid `name`. Only a-z 0-9 and hyphens allowed. No leading or trailing hyphens.")

        if len(self.name) > 100:
            raise ValueError("Invalid `name`. Max length is 100 characters")

        # Validate schema is supported by running version of the software and valid
        if not validate_labbook_schema(self.schema, self.data):
            errmsg = f"Schema in Labbook {str(self)} does not match indicated version {self.schema}"
            logger.error(errmsg)
            raise ValueError(errmsg)
