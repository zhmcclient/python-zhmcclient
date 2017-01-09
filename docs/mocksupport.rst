.. Copyright 2016 IBM Corp. All Rights Reserved.
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..    http://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.
..

.. _`Mock support`:

Mock support
============

The zhmcclient PyPI package provides unit testing support for its users via its
`zhmcclient_mock` Python package. This package allows users of
the zhmcclient package to easily define a mocked environment that provides
a faked HMC that is pre-populated with resource state as needed by the test
case, and that supports all relevant operations.

The mocked environment is set up by the user by using an instance of the
:class:`zhmcclient_mock.FakedSession` class instead of the
:class:`zhmcclient.Session` class when setting up the zhmcclient package
in a unit test::

    import unittest
    import zhmcclient
    import zhmcclient_mock

    class MyTests(unittest.TestCase):

        def setUp(self):

            self.session = zhmcclient_mock.FakedSession(
                'fake-host', 'fake-hmc', '2.13.1', '1.8')
            self.session.hmc.add_resources({
                'cpcs': [
                    {
                        'properties': {
                            'name': 'cpc_1',
                            'description': 'CPC #1',
                        },
                        'adapters': [
                            {
                                'properties': {
                                    'name': 'osa_1',
                                    'description': 'OSA #1',
                                },
                                'ports': [
                                    {
                                        'properties': {
                                            'name': 'osa_1_1',
                                            'description': 'OSA #1 Port #1',
                                        },
                                    },
                                ]
                            },
                        ]
                    },
                ]
            })
            self.client = zhmcclient.Client(self.session)

        def test_list(self):
            cpcs = self.client.cpcs.list()
            self.assertEqual(len(cpcs), 1)
            self.assertEqual(cpcs[0].name, 'cpc_1')

In this example, the faked HMC of the faked session is preloaded with a
CPC that has one adapter with one port. For details on the format of
the input dictionary, see :meth:`zhmcclient_mock.FakedHmc.add_resources`.

It is also possible to add resources one by one, from top to bottom,
by using add() methods on the resource manager classes, for example see
:meth:`zhmcclient_mock.FakedBaseManager.add`.

.. _`Faked session`:

Faked session
-------------

TODO: Add the faked Session class.


.. _`Faked HMC`:

Faked HMC
---------

.. automodule:: zhmcclient_mock._hmc

.. autoclass:: zhmcclient_mock.FakedHmc
   :members:

.. autoclass:: zhmcclient_mock.FakedActivationProfileManager
   :members:

.. autoclass:: zhmcclient_mock.FakedActivationProfile
   :members:

.. autoclass:: zhmcclient_mock.FakedAdapterManager
   :members:

.. autoclass:: zhmcclient_mock.FakedAdapter
   :members:

.. autoclass:: zhmcclient_mock.FakedCpcManager
   :members:

.. autoclass:: zhmcclient_mock.FakedCpc
   :members:

.. autoclass:: zhmcclient_mock.FakedHbaManager
   :members:

.. autoclass:: zhmcclient_mock.FakedHba
   :members:

.. autoclass:: zhmcclient_mock.FakedLparManager
   :members:

.. autoclass:: zhmcclient_mock.FakedLpar
   :members:

.. autoclass:: zhmcclient_mock.FakedNicManager
   :members:

.. autoclass:: zhmcclient_mock.FakedNic
   :members:

.. autoclass:: zhmcclient_mock.FakedPartitionManager
   :members:

.. autoclass:: zhmcclient_mock.FakedPartition
   :members:

.. autoclass:: zhmcclient_mock.FakedPortManager
   :members:

.. autoclass:: zhmcclient_mock.FakedPort
   :members:

.. autoclass:: zhmcclient_mock.FakedVirtualFunctionManager
   :members:

.. autoclass:: zhmcclient_mock.FakedVirtualFunction
   :members:

.. autoclass:: zhmcclient_mock.FakedVirtualSwitchManager
   :members:

.. autoclass:: zhmcclient_mock.FakedVirtualSwitch
   :members:

.. autoclass:: zhmcclient_mock.FakedBaseManager
   :members:

.. autoclass:: zhmcclient_mock.FakedBaseResource
   :members:
