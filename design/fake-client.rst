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

Design for fake client
======================

This document describes requirements and possible design options for a fake
zhmcclient.

Requirements
------------

* Must avoid the need for an actual HMC and still allow usage of the zhmcclient
  API.
* Both read-only and read-write operations must be supported.
* Read-write operations must reflect their changes properly (i.e. they must be
  visible in corresponding read operations).
* The resource state of the faked HMC must be preloaded (e.g. for resources
  that cannot be created by clients), and its resource descriptions must be
  easy to use (i.e. not in terms of REST URIs.
* It must be possible to define testcases with error injection.
* The solution must be usable in unit tests of zhmcclient users.
* The solution needs to perform fast, because it is used in a unit test.
* The solution should not rely on external componentry such as a small HTTP
  server.

It seems that with these requirements, we can assume that there is a need for
a faked HMC that can represent its resources and properties as Python objects,
so that changes can be applied consistently.

Design options
--------------

There are two basic design options for the fake client:

* Complete re-implementation of the zhmcclient API, that behaves the same
  way as the zhmcclient package, but consists of a different classes that
  implement a faked HMC.
* Usage of the zhmcclient package, and replacing its Session object
  with a fake session that implements a faked HMC.

The first design option is probably less effort, but it has the drawback that
subtle changes in the API may be forgotten. One example for that is the
recent introduction of an optimization for findall() by name, which now uses
a cached mapping of names to URIs, but had the subtle externally visible
change that the resource objects returned by findall(name) now only have
a very minimal set of properties, and no longer those that are returned by
list() which was the earlier implementation. For example, the "status"
property is no longer set in that case. The second design would automatically
represent this example of a change.

Design
------

In the following description, the second design option is used.

There is a fake session object that the user of the zhmcclient package
will use instead of `zhmcclient.Session`. The fake session object contains a
faked HMC that can represent all resources relevant for the zhmcclient.

This fake session object implements the same API as `zhmcclient.Session`, so
that the rest of the zhmcclient classes do not need to be changed.
The `get()`, `post()` and `delete()` methods of the fake session class will
be redirected to operate on the faked HMC.

The fake session object will have the ability to be populated with a resource
state. This is supported in two ways that can both be used:

* By adding an entire tree of resources.
* By invoking add/remove methods for each resource.

When adding an entire tree of resources, the resources are defined as a
dictionary of nested dictionaries, following this example::

    resources = {
        'cpcs': [  # name of manager attribute for this resource
            {
                'properties': {
                    # object-id and object-uri are auto-generated
                    'name': 'cpc_1',
                    . . .  # more properties
                },
                'adapters': [
                    {
                        'properties': {
                            # object-id and object-uri are auto-generated
                            'name': 'ad_1',
                            . . .  # more properties
                        },
                        'ports': [
                            {
                                'properties': {
                                    # element-id and element-uri are
                                    # auto-generated
                                    'name': 'port_1',
                                    . . .  # more properties
                                }
                            },
                            . . .  # more Ports
                        ],
                    },
                    . . .  # more Adapters
                ],
                . . .  # more CPC child resources
            },
            . . .  # more CPCs
        ]
    }

The dictionary keys for the resources in this dictionary structure are the
names of the attributes for navigating to the child resources within their
parent resources, in the zhmcclient package. For example, the 'cpcs' dictionary
key corresponds to the `zhmcclient.Client.cpcs` attribute name.

When invoking add/remove methods for each resource, the resource tree is built
up by the user, from top to bottom. Besides just being an alternative to
the bulk input with the resource dictionary, this approach also allows changing
the resource state incrementally between test cases.

In both approaches, the properties for object ID ("object-id" or "element-id")
and URI ("object-uri" or "element-uri") are auto-generated, if not provided by
the user. All other properties will only exist as provided by the user.

In both approaches, there is no checking for invalid properties (neither for
property name, nor for property type). Checking for invalid properties would
require knowing the names of all properties of all resource types. Right now,
the zhmcclient code and the code for the fake session/HMC have to know only a
very small number of properties (object-id, object-uri, name). Plus, the set of
properties depends on the HMC API version, and probably some properties even
depend on the CPC machine generation. It saves a significant effort not having
this knowledge in the zhmcclient code and in the code for the fake session/HMC.

For all operations against the faked HMC, a successful operation is
implemented by default.

The unit testcases of users can use the `side_effects` approach of the `mock`
package for error injection. The fake session/HMC does not need to do anything
for that to work.

Possible future extensions
--------------------------

Specific operation behavior
^^^^^^^^^^^^^^^^^^^^^^^^^^^

If a need arises to have other behavior in the operations than the default
implementation, the fake session object can have the ability to specify
non-standard behavior of HMC operations, at the level of the HTTP interactions,
following this example::

    operations = [
        {
            'method': 'get',           # used for matching the request
            'uri': '/api/version',     # used for matching the request
            'request_body': None,      # used for matching the request
            'response_status': 200,    # desired HTTP status code
            'response_body': {         # desired response body
                'api-minor-version': '1'
            }
        },
        {
            'method': 'get',           # used for matching the request
            'uri': '/api/cpcs',        # used for matching the request
            'request_body': None,      # used for matching the request
            'response_status': 400,    # desired HTTP status code
            'response_error': {        # desired error info
                'reason': 25,          # desired HMC reason code
                'message': 'bla',      # desired HMC message text
        }
    ]

This information is stored in the fake session and used in matching
HTTP requests instead of the standard, successful implementations.

It allows specifying successful operations with responses deviating from the
standard responses (see the first list item in the example above) as well as
error responses (see the second list item). Because the zhmcclient only
evaluates HTTP status code, HMC reason code and the message text, these are the
only attributes that can be specified (to keep it simple).

Note that normal error injection can already be done with the `side_effects`
approach of the `mock` package.
