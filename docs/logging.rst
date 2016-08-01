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

.. _`Logging`:

Logging
=======

This library logs internal calls but doesn't output them to any handler.
If you are interested in those calls, add a handler and set the verbosity.
Be aware that the internally used loggers don't have a format specified for
the log records. For example, to output all *INFO* logs to the ``stdout``,
do this:

.. code-block::

    import logging

    handler = logging.StreamHandler()
    format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)
    logging.getLogger("zhmcclient").addHandler(handler)
    logging.getLogger("zhmcclient").setLevel(logging.INFO)
