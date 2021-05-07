# Copyright 2016 IBM Corp. All Rights Reserved.
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
Encapsulation of the HMC info file.

This module is used for testing only. It is contained in the main package
subtree in order for it to be found for importing.

An *HMC info file* contains the input and output to HMC operations at a level
that can be used to verify these operations, and to set up the mock environment
for the operations.

An HMC info file can be produced with the `tools/extract.py` script and is
consumed by the `tests/test_hmc.py` test case.
"""

from __future__ import absolute_import

import json
from datetime import datetime
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
import pytz

from zhmcclient import Error


class HMCInfo(object):
    """
    The content of an HMC info file.
    """

    def __init__(self, hmc, userid):
        """
        Parameters:
          hmc (string): Host name or IP address of HMC
          userid (string): Userid on HMC that was used to extract the data
        """
        dt = datetime.now(pytz.utc).isoformat()  # timezone-aware UTC time
        ops = OrderedDict()  # key: method + uri, value: see add_op()
        self._data = OrderedDict()
        # The following kind of initialization preserves the order:
        self._data['hmc'] = hmc
        self._data['userid'] = userid
        self._data['created'] = dt
        self._data['operations'] = ops

    @staticmethod
    def _ops_key(method, uri):
        method = method.lower()
        return "{} {}".format(method, uri)

    def add_op(self, method, uri, error, request_body, response_body):
        """
        Add the information about an HMC operation to this object.
        """
        key = self._ops_key(method, uri)
        op = OrderedDict()
        # The following kind of initialization preserves the order:
        op['method'] = method
        op['uri'] = uri
        op['error'] = error
        op['request_body'] = request_body
        op['response_body'] = response_body
        self._data['operations'][key] = op

    def record_op(self, session, method, uri, request_body=None):
        """
        Perform an HMC operation and record the result in this object.
        """
        method = method.lower()
        try:
            if method == 'get':
                result = session.get(uri)
            # TODO: Add support for the other HTTP methods (POST, DELETE)
            else:
                raise ValueError("Invalid HTTP method: %s" % method)
            error = None
        except Error as exc:
            error = OrderedDict()
            error['classname'] = exc.__class__.__name__
            error['object'] = exc.__dict__
            result = None
        self.add_op(method, uri, error, None, result)
        return result

    def record_get(self, session, uri):
        """
        Perform an HMC GET operation and record the result in this object.
        """
        return self.record_op(session, 'get', uri, None)

    def get_op(self, method, uri):
        """
        Return the HMC operation data (dict, see add_op()) for an HTTP method
        and URI.

        Returns None if the combination of HTTP method and URI cannot be found.
        """
        key = self._ops_key(method, uri)
        try:
            return self._data['operations'][key]
        except KeyError:
            return None

    def dump(self, fp):
        """
        Write the HMC info content of this object to an open file, in JSON
        format.
        """
        json.dump(self._data, fp, indent=2)

    def load(self, fp):
        """
        Read the HMC info content from an open file (in JSON format) and set
        up this object with that data.
        """
        self._data = json.load(fp, object_pairs_hook=OrderedDict)
