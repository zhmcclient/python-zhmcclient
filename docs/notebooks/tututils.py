# Copyright 2016-2017 IBM Corp. All Rights Reserved.
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
Utility module for the Jupyter notebooks used as tutorials.
"""

import getpass
import requests
import six

import zhmcclient

requests.packages.urllib3.disable_warnings()

USERID = None
PASSWORD = None


def make_client(zhmc, userid=None, password=None):
    """
    Create a `Session` object for the specified HMC and log that on. Create a
    `Client` object using that `Session` object, and return it.

    If no userid and password are specified, and if no previous call to this
    method was made, userid and password are interactively inquired.
    Userid and password are saved in module-global variables for future calls
    to this method.
    """

    global USERID, PASSWORD  # pylint: disable=global-statement

    USERID = userid or USERID or \
        six.input('Enter userid for HMC {}: '.format(zhmc))
    PASSWORD = password or PASSWORD or \
        getpass.getpass('Enter password for {}: '.format(USERID))

    session = zhmcclient.Session(zhmc, USERID, PASSWORD)
    session.logon()
    client = zhmcclient.Client(session)
    print('Established logged-on session with HMC {} using userid {}'.
          format(zhmc, USERID))
    return client
