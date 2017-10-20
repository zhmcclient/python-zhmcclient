.. Copyright 2016-2017 IBM Corp. All Rights Reserved.
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
``zhmcclient_mock`` Python package. That package allows users of zhmcclient to
easily define a faked HMC that is populated with resources as needed by the
test case.

The faked HMC environment is set up by creating an instance of the
:class:`zhmcclient_mock.FakedSession` class instead of the
:class:`zhmcclient.Session` class:

.. code-block:: python

    import zhmcclient
    import zhmcclient_mock

    session = zhmcclient_mock.FakedSession('fake-host', 'fake-hmc', '2.13.1',
                                           '1.8')
    client = zhmcclient.Client(session)
    cpcs = client.cpcs.list()
    . . .

Other than using a different session class, the code operates against the same
zhmcclient API as before. For example, you can see in the example above that
the client object is set up from the same :class:`zhmcclient.Client` class as
before, and that the CPCs can be listed through the API of the client object as
before.

The difference is that the faked session object contains a faked HMC and
does not communicate at all with an actual HMC.

The faked HMC of the faked session object can be accessed via the
:attr:`~zhmcclient_mock.FakedSession.hmc` attribute of the faked session object
in order to populate it with resources, for example to build up an initial
resource environment for a test case.

The following example of a unit test case shows how an initial set of resources
that is defined as a dictionary and loaded into the faked HMC using the
:meth:`~zhmcclient_mock.FakedHmc.add_resources` method:

.. code-block:: python

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
                                    'adapter-family': 'osa',
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

In this example, the ``test_list()`` method tests the CPC list method of the
zhmcclient package, but the same approach is used for testing code that
uses the zhmcclient package.

As an alternative to bulk-loading resources via the input dictionary, it is
also possible to add resources one by one using the ``add()`` methods of the
faked resource manager classes, as shown in the following example:

.. code-block:: python

    class MyTests(unittest.TestCase):

        def setUp(self):

            self.session = zhmcclient_mock.FakedSession(
                'fake-host', 'fake-hmc', '2.13.1', '1.8')

            cpc1 = self.session.hmc.cpcs.add({
                'name': 'cpc_1',
                'description': 'CPC #1',
            })
            adapter1 = cpc1.adapters.add({
                'name': 'osa_1',
                'description': 'OSA #1',
                'adapter-family': 'osa',
            })
            port1 = adapter1.ports.add({
                'name': 'osa_1_1',
                'description': 'OSA #1 Port #1',
            })

            self.client = zhmcclient.Client(self.session)

As you can see, the resources need to be added from top to bottom in the
resource tree, starting at the :attr:`~zhmcclient_mock.FakedSession.hmc`
attribute of the faked session object.

Section :ref:`Faked HMC` describes all faked resource and manager classes
that you can use to add resources that way.

Section :ref:`Faked session` describes the faked session class.


.. _`Faked session`:

Faked session
-------------

.. automodule:: zhmcclient_mock._session

.. autoclass:: zhmcclient_mock.FakedSession
   :members:


.. _`Faked HMC`:

Faked HMC
---------

.. automodule:: zhmcclient_mock._hmc

.. autoclass:: zhmcclient_mock.InputError
   :members:

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

.. autoclass:: zhmcclient_mock.FakedConsoleManager
   :members:

.. autoclass:: zhmcclient_mock.FakedConsole
   :members:

.. autoclass:: zhmcclient_mock.FakedCpcManager
   :members:

.. autoclass:: zhmcclient_mock.FakedCpc
   :members:

.. autoclass:: zhmcclient_mock.FakedHbaManager
   :members:

.. autoclass:: zhmcclient_mock.FakedHba
   :members:

.. autoclass:: zhmcclient_mock.FakedLdapServerDefinitionManager
   :members:

.. autoclass:: zhmcclient_mock.FakedLdapServerDefinition
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

.. autoclass:: zhmcclient_mock.FakedPasswordRuleManager
   :members:

.. autoclass:: zhmcclient_mock.FakedPasswordRule
   :members:

.. autoclass:: zhmcclient_mock.FakedPortManager
   :members:

.. autoclass:: zhmcclient_mock.FakedPort
   :members:

.. autoclass:: zhmcclient_mock.FakedTaskManager
   :members:

.. autoclass:: zhmcclient_mock.FakedTask
   :members:

.. autoclass:: zhmcclient_mock.FakedUnmanagedCpcManager
   :members:

.. autoclass:: zhmcclient_mock.FakedUnmanagedCpc
   :members:

.. autoclass:: zhmcclient_mock.FakedUserManager
   :members:

.. autoclass:: zhmcclient_mock.FakedUser
   :members:

.. autoclass:: zhmcclient_mock.FakedUserPatternManager
   :members:

.. autoclass:: zhmcclient_mock.FakedUserPattern
   :members:

.. autoclass:: zhmcclient_mock.FakedUserRoleManager
   :members:

.. autoclass:: zhmcclient_mock.FakedUserRole
   :members:

.. autoclass:: zhmcclient_mock.FakedVirtualFunctionManager
   :members:

.. autoclass:: zhmcclient_mock.FakedVirtualFunction
   :members:

.. autoclass:: zhmcclient_mock.FakedVirtualSwitchManager
   :members:

.. autoclass:: zhmcclient_mock.FakedVirtualSwitch
   :members:

.. autoclass:: zhmcclient_mock.FakedMetricsContextManager
   :members:

.. autoclass:: zhmcclient_mock.FakedMetricsContext
   :members:

.. autoclass:: zhmcclient_mock.FakedBaseManager
   :members:

.. autoclass:: zhmcclient_mock.FakedBaseResource
   :members:


.. _`URI handler`:

URI handler
-----------

.. automodule:: zhmcclient_mock._urihandler

.. autoclass:: zhmcclient_mock.LparActivateHandler
   :members: get_status, post

.. autoclass:: zhmcclient_mock.LparDeactivateHandler
   :members: get_status, post

.. autoclass:: zhmcclient_mock.LparLoadHandler
   :members: get_status, post
