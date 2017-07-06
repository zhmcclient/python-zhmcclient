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

.. _`Tutorial`:
.. _`Tutorials`:

Tutorials
=========

This section contains tutorials explaining the use of the zhmcclient package.

Each tutorial is a
`Jupyter Notebook <http://jupyter-notebook-beginner-guide.readthedocs.io/>`_
(formerly known as IPython Notebook).
In order to view a tutorial, just click on a link in the table below.
This will show the tutorial in the online
`Jupyter Notebook Viewer <http://nbviewer.jupyter.org/>`_.

==================================  ===========================================
Tutorial                            Short description
==================================  ===========================================
:nbview:`01_notebook_basics.ipynb`  1: Basics about Jupyter notebooks
:nbview:`02_connections.ipynb`      2: Connecting to an HMC
:nbview:`03_datamodel.ipynb`        3: Basics about working with HMC resources
:nbview:`04_error_handling.ipynb`   4: Error handling
==================================  ===========================================

Executing code in the tutorials
-------------------------------

In order to execute and also modify the code in the tutorials, Jupyter Notebook
needs to be installed in a Python environment, preferrably in a
`virtual Python environment <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_,
and you need to have the notebook files locally.

There are two options on how to do that:

1. Set up the development environment for zhmcclient (see
   :ref:`Setting up the development environment`). This will provide you with
   an installation of Jupyter Notebook and with all the tutorial notebooks in
   directory ``docs/notebooks``.

   To start Jupyter Notebook with all tutorial notebooks, issue from the repo
   work directory:

   .. code-block:: text

       $ jupyter notebook --notebook-dir=docs/notebooks

   If you intend to keep your changes locally, you may want to work on a copy
   of the ``docs/notebooks`` directory that is outside of the repo work
   directory.

2. Install Jupyter Notebook and the zhmcclient package into a Python
   environment (preferrably virtual):

   .. code-block:: text

       $ pip install jupyter zhmcclient

   and download the tutorial notebooks using the download button in the Jupyter
   Notebook Viewer (following the links in the table above).

   To start Jupyter Notebook with the downloaded tutorial notebooks, issue:

   .. code-block:: text

       $ jupyter notebook --notebook-dir={your-notebook-dir}
