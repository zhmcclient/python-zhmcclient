#!/usr/bin/env python

import sys
try:
    from pbr.version import VersionInfo
except ImportError:
    # Version cannot be determined
    sys.exit(0)

if len(sys.argv) != 2:
    print("Error: Incorrect number of command line arguments")
    print("Usage: {0}  package_name".format(sys.argv[0]))
    sys.exit(2)

pkg_name = sys.argv[1]
pkg_version = VersionInfo(pkg_name).release_string()
print(pkg_version)
