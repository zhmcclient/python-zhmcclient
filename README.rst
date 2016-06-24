Python bindings to the z Systems Hardware Management Console Web Services API
=============================================================================

This is a Python API (the ``zhmcclient`` module) to
the z Systems Hardware Management Console Web Services API. 
The Python API does not implement 100% of the Web Services API.

See the `Hardware Management Console Web Services API`_ for information
on how to use the Web Services API.

.. _Hardware Management Console Web Services API: http://www-01.ibm.com/support/docview.wss?uid=isg29b97f40675618ba085257a6a00777bea&aid=1

python-zhmcclient is licensed under the Apache License.

* License: Apache License, Version 2.0
* `PyPi`_ - package installation
* `Online Documentation`_
* `Bugs`_ - issue tracking
* `Source`_
* `How to Contribute`_

.. _PyPi: https://pypi.python.org/pypi/zhmcclient
.. _Online Documentation: https://github.rtp.raleigh.ibm.com/openstack-zkvm/python-zhmcwsclient
.. _Bugs: https://github.rtp.raleigh.ibm.com/openstack-zkvm/python-zhmcwsclient
.. _Source: https://github.rtp.raleigh.ibm.com/openstack-zkvm/python-zhmcwsclient
.. _How to Contribute: https://github.rtp.raleigh.ibm.com/openstack-zkvm/python-zhmcwsclient


.. contents:: Contents:
   :local:


Python API
----------

Example code::

    >>> import zhmcclient
    >>> cl = zhmcclient.Client(VERSION, USER, PASSWORD, URL)
    >>> cl.cpcs.list()
    [...]
    >>> cpc = cl.cpcs.find(name='P0000P30')
    [...]
    >>> cpc.lpars.list()
    [...]
    >>> lpar = cpc.lpars.find(name='PART8')
    [...]
    >>> lpar.activate()


Testing
-------

There are multiple test targets that can be run to validate the code.

* tox -e pep8 - style guidelines enforcement
* tox -e py27 - traditional unit testing
