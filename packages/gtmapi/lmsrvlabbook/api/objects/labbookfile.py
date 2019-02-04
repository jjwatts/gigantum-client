# Copyright (c) 2018 FlashX, LLC
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
import graphene
import base64

from gtmcore.files import FileOperations
from lmsrvcore.api.interfaces import GitRepository
from lmsrvcore.auth.user import get_logged_in_username


class LabbookFile(graphene.ObjectType, interfaces=(graphene.relay.Node, GitRepository)):
    """A type representing a file or directory inside the labbook file system."""
    # Loaded file info
    _file_info = None

    # Section in the LabBook (code, input, output)
    section = graphene.String(required=True)

    # Relative path from labbook section.
    key = graphene.String(required=True)

    # True indicates that path points to a directory
    is_dir = graphene.Boolean()

    # True indicates that path points to a favorite
    is_favorite = graphene.Boolean()

    # Modified at contains timestamp of last modified - NOT creation - in epoch time with nanosecond resolution if
    # supported by the underlying filesystem of the host
    modified_at = graphene.Float()

    # Size in bytes encoded as a string.
    size = graphene.String()

    def _load_file_info(self, dataloader):
        """Private method to retrieve file info for a given key"""
        if not self._file_info:
            # Load file info from LabBook
            if not self.section or not self.key:
                raise ValueError("Must set `section` and `key` on object creation to resolve file info")

            # Load labbook instance
            lb = dataloader.load(f"{get_logged_in_username()}&{self.owner}&{self.name}").get()

            # Retrieve file info
            self._file_info = FileOperations.get_file_info(lb, self.section, self.key)

        # Set class properties
        self.is_dir = self._file_info['is_dir']
        self.modified_at = self._file_info['modified_at']
        self.size = f"{self._file_info['size']}"
        self.is_favorite = self._file_info['is_favorite']

    @classmethod
    def get_node(cls, info, id):
        """Method to resolve the object based on it's Node ID"""
        # Parse the key
        owner, name, section, key = id.split("&")

        return LabbookFile(id=f"{owner}&{name}&{section}&{key}", name=name, owner=owner, section=section, key=key)

    def resolve_id(self, info):
        """Resolve the unique Node id for this object"""
        if not self.id:
            if not self.owner or not self.name or not self.section or not self.key:
                raise ValueError("Resolving a LabbookFile Node ID requires owner, name, section, and key to be set")
            self.id = f"{self.owner}&{self.name}&{self.section}&{self.key}"

        return self.id

    def resolve_is_dir(self, info):
        """Resolve the is_dir field"""
        if self.is_dir is None:
            self._load_file_info(info.context.labbook_loader)
        return self.is_dir

    def resolve_modified_at(self, info):
        """Resolve the modified_at field"""
        if self.modified_at is None:
            self._load_file_info(info.context.labbook_loader)
        return self.modified_at

    def resolve_size(self, info):
        """Resolve the size field"""
        if self.size is None:
            self._load_file_info(info.context.labbook_loader)
        return self.size

    def resolve_is_favorite(self, info):
        """Resolve the is_favorite field"""
        if self.is_favorite is None:
            self._load_file_info(info.context.labbook_loader)
        return self.is_favorite


class LabbookFavorite(graphene.ObjectType, interfaces=(graphene.relay.Node, GitRepository)):
    """A type representing a file or directory that has been favorited in the labbook file system."""
    # An instance of loaded favorite data
    _favorite_data = None

    # Section in the LabBook (code, input, output)
    section = graphene.String(required=True)

    # Relative path from labbook root directory.
    key = graphene.String(required=True)

    # Index value indicating the order of the favorite
    index = graphene.Int()

    # Short description about the favorite
    description = graphene.String()

    # The graphene type id for the associated file
    associated_labbook_file_id = graphene.String()

    # True indicates that the favorite is a directory
    is_dir = graphene.Boolean()

    def _load_favorite_info(self, dataloader):
        """Private method to retrieve file info for a given key"""
        if not self._favorite_data:
            # Load file info from LabBook
            if not self.section or self.key is None:
                raise ValueError("Must set `section` and `key` on object creation to resolve favorite info")

            # Load labbook instance
            lb = dataloader.load(f"{get_logged_in_username()}&{self.owner}&{self.name}").get()

            data = lb.get_favorites(self.section)

            # Pull out single entry
            self._favorite_data = data[self.key]

        # Set class properties
        self.description = self._favorite_data['description']
        self.index = self._favorite_data['index']
        self.is_dir = self._favorite_data['is_dir']

    @classmethod
    def get_node(cls, info, id):
        """Method to resolve the object based on it's Node ID"""
        # Parse the key
        owner, name, section, key = id.split("&")

        return LabbookFavorite(id=f"{owner}&{name}&{section}&{key}", name=name, owner=owner, section=section,
                               key=key)

    def resolve_id(self, info):
        """Resolve the unique Node id for this object"""
        if not self.id:
            if not self.owner or not self.name or not self.section or self.key is None:
                raise ValueError("Resolving a LabbookFavorite Node ID requires owner,name,section, and key to be set")

            self.id = f"{self.owner}&{self.name}&{self.section}&{self.key}"

        return self.id

    def resolve_is_dir(self, info):
        """Resolve the is_dir field"""
        if self.is_dir is None:
            self._load_favorite_info(info.context.labbook_loader)
        return self.is_dir

    def resolve_key(self, info):
        """Resolve the is_dir field"""
        if self.key is None:
            self._load_favorite_info(info.context.labbook_loader)
        return self.key

    def resolve_index(self, info):
        """Resolve the index field"""
        if self.index is None:
            self._load_favorite_info(info.context.labbook_loader)
        return self.index

    def resolve_description(self, info):
        """Resolve the is_dir field"""
        if self.description is None:
            self._load_favorite_info(info.context.labbook_loader)
        return self.description

    def resolve_associated_labbook_file_id(self, info):
        """Resolve the associated_labbook_file_id field"""
        return base64.b64encode(f"LabbookFile:{self.owner}&{self.name}&{self.section}&{self.key}".encode()).decode()
