# Copyright 2026 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Abstract base class for a transport session for use by zhmcclient.Session.
"""


class Transport:
    """
    Abstract base class for a transport session for use by zhmcclient.Session.
    """

    def __init__(self, session):
        self._session = session
        # The following must be set in the derived classes:
        self._req_session = None

    def test_mount(self, scheme, adapter):
        """
        Mount an adapter to the requests session.
        This is used only for test purposes.
        """
        self._req_session.mount(scheme, adapter)

    def get(self, request, *, verify, timeout):
        """
        Abstract method: Perform the GET HTTP method.
        """
        raise NotImplementedError

    def post(self, request, *, verify, timeout):
        """
        Abstract method: Perform the POST HTTP method.
        """
        raise NotImplementedError

    def delete(self, request, *, verify, timeout):
        """
        Abstract method: Perform the DELETE HTTP method.
        """
        raise NotImplementedError
