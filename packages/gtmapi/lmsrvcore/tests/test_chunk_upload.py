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
import pytest
import graphene

from lmsrvcore.tests.fixtures import fixture_working_dir_with_cached_user
from lmsrvcore.api.mutations import ChunkUploadMutation


class MyMutation(graphene.relay.ClientIDMutation, ChunkUploadMutation):
    class Arguments:
        var = graphene.String()

    @classmethod
    def mutate_and_process_upload(cls, info, upload_file_path, upload_filename, **kwargs):
        return "success"


class TestChunkUpload(object):
    def test_get_temp_filename(self):
        """Test getting the filename"""
        mut = MyMutation()
        assert mut.get_temp_filename("asdf", "1234.txt") == "/tmp/asdf-1234.txt"

    def test_validate_args(self):
        """Test errors on bad args"""
        mut = MyMutation()

        args = {
                  "upload_id": "dsffghfdsahgf",
                  "chunk_size": 100,
                  "total_chunks": 2,
                  "chunk_index": 3,
                  "file_size_kb": 200,
                  "filename": "test.txt"
                }

        with pytest.raises(ValueError):
            mut.validate_args(args)

        args = {
                  "upload_id": "dsffghfdsahgf",
                  "chunk_size": 100,
                  "total_chunks": 2,
                  "chunk_index": 1,
                  "file_size_kb": 1000,
                  "filename": "test.txt"
                }

        with pytest.raises(ValueError):
            mut.validate_args(args)

    def test_no_file(self):
        """Test error on no file"""
        class DummyContext(object):
            def __init__(self):
                self.files = {'blah': None}

        class DummyInfo(object):
            def __init__(self):
                self.context = DummyContext()

        mut = MyMutation()

        args = {
                  "upload_id": "dsffghfdsahgf",
                  "chunk_size": 100,
                  "total_chunks": 2,
                  "chunk_index": 1,
                  "file_size_kb": 200,
                  "filename": "test.txt"
                }

        with pytest.raises(ValueError):
            mut.mutate_and_get_payload(None, DummyInfo(), **{"chunk_upload_params": args})
