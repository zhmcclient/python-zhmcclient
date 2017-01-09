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
:class:`zhmcclient_mock.Session` class instead of the
:class:`zhmcclient.Session` class when setting up the zhmcclient package
in a unit test::

    import unittest
    import zhmcclient
    import zhmcclient_mock

    class MyTests(unittest.TestCase):

        def setUp(self):

            self.session = zhmcclient_mock.Session('fake-host', '2.13.1')
            self.session.hmc.add_resources({
                'cpcs': [
                    {
                        'properties': {
                            'name': 'cpc_1',
                            'description': 'CPC #1',
                        },
                    },
                ]
            })
            self.client = zhmcclient.Client(self.session)

        def test_list(self):
            cpcs = self.client.cpcs.list()
            self.assertEqual(len(cpcs), 1)
            self.assertEqual(cpcs[0].name, 'cpc_1')

In this example, the faked HMC of the faked session is preloaded with a
single CPC resource. For simplicity of the example, the CPC resource did not
have any child resources, but it is possible to define en entire resource tree
via :meth:`zhmcclient_mock.Hmc.add_resources`.

.. _`Faked session`:

Faked session
-------------

.. automodule:: zhmcclient_mock._session

.. autoclass:: zhmcclient_mock.Session
   :members:


.. _`Faked HMC`:

Faked HMC
---------

.. automodule:: zhmcclient_mock._hmc

.. autoclass:: zhmcclient_mock.Hmc
   :members:

.. autoclass:: zhmcclient_mock.CpcManager
   :members:

.. autoclass:: zhmcclient_mock.Cpc
   :members:

.. autoclass:: zhmcclient_mock.AdapterManager
   :members:

.. autoclass:: zhmcclient_mock.Adapter
   :members:

.. autoclass:: zhmcclient_mock.PortManager
   :members:

.. autoclass:: zhmcclient_mock.Port
   :members:

.. autoclass:: zhmcclient_mock.LocalResourceManager
   :members:

.. autoclass:: zhmcclient_mock.LocalResource
   :members:
