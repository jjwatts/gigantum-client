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
from flask import current_app
from mock import patch

from lmsrvcore.auth.identity import get_identity_manager_instance, AuthenticationError
from lmsrvcore.middleware import AuthorizationMiddleware, error_middleware, time_all_resolvers_middleware, \
    DataloaderMiddleware
from lmsrvcore.tests.fixtures import fixture_working_dir_with_cached_user
from gtmcore.configuration import Configuration

from gtmcore.auth.local import LocalIdentityManager


class MockCurrentApp(object):
    """Mock class to test get_identity_manager_instance() without Flask in the loop"""
    def __init__(self, id_manager=None):
        self.config = {"LABMGR_ID_MGR": id_manager}


class MockFlaskContext(object):
    """Mock class to test middleware"""
    def __init__(self):
        self.headers = {"Authorization": "Bearer adkajshfgklujasdhfiuashfiusahf"}
        self.labbook_loader = None


class MockGrapheneInfo(object):
    """Mock class to test middleware"""
    def __init__(self):
        self.context = MockFlaskContext()


class TestAuthIdentity(object):
    def test_get_identity_manager_instance(self, fixture_working_dir_with_cached_user):
        """Test getting identity manager in a flask app"""

        # Test normal
        mgr = get_identity_manager_instance()
        assert type(mgr) == LocalIdentityManager

        # Test when no mgr is set
        current_app.config["LABMGR_ID_MGR"] = None
        mgr = get_identity_manager_instance()
        assert mgr is None

        # Test when mgr is missing from the current Flask application config
        del current_app.config["LABMGR_ID_MGR"]
        with pytest.raises(AuthenticationError):
            get_identity_manager_instance()

    def test_authorization_middleware_user_local(self, fixture_working_dir_with_cached_user):
        """Test authorization middlewhere when loading a user exists locally"""

        def next_fnc(root, info, **args):
            """Dummy method to test next chain in middleware"""
            assert root == "something"
            assert type(info) == MockGrapheneInfo
            assert args['foo'] == "a"
            assert args['bar'] == "b"

        # Create a mocked info obj and remove the auth header since you are testing the logged in user pull from cache
        fake_info = MockGrapheneInfo()
        del fake_info.context.headers["Authorization"]

        mw = AuthorizationMiddleware()

        mw.resolve(next_fnc, "something", fake_info, foo="a", bar="b")

    def test_authorization_middleware_bad_header(self, fixture_working_dir_with_cached_user):
        """Test authorization middlewhere when a token header is malformed"""

        def next_fnc(root, info, **args):
            """Dummy method to test next chain in middleware"""
            assert "Should not get here"

        fake_info = MockGrapheneInfo()
        fake_info.context.headers["Authorization"] = "Token asdfasdfhasdf"

        mw = AuthorizationMiddleware()
        with pytest.raises(AuthenticationError):
            mw.resolve(next_fnc, "something", fake_info, foo="a", bar="b")


    # TODO: Add test when easier to mock a token
    # def test_authorization_middleware_token(self):
    #     """Test authorization middlewhere when a token is provided"""
    #     pass


