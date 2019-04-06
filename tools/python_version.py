#!/usr/bin/env python

import sys

if len(sys.argv) != 2:
    print("Error: Incorrect number of command line arguments")
    print("Usage: {0}  version_level".format(sys.argv[0]))
    print("Where version_level is the number of components in the "
          "version string from 1 to 3, e.g. 3 means Python 2.7.11")

    sys.exit(2)

version_level = sys.argv[1]
if version_level not in ('1', '2', '3'):
    print("Error: Invalid version level; must be 1, 2, or 3")
    sys.exit(2)

version_level = int(version_level)
py_version = '.'.join([str(v) for v in sys.version_info[0:version_level]])
print(py_version)
