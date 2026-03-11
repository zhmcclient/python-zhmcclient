#!/usr/bin/env python

"""
Check that certain properties in the specified zhmcclient log file have a
blanked-out value.
"""

import sys
import re
import argparse
from zhmcclient import BLANKED_OUT_STRING


# Ends of property names that are checked for being blanked out.
# Keep in sync with BLANKED_OUT_PROPERTY_PATTERN in zhmcclient/_constants.py.
PROPERTY_NAME_ENDS = [
    "authentication-code",
    "credential",
    "key",
    "passcode",
    "password",
    "pw",
    "secret",
    "session",
    "Session"
]

# Pattern for matching a single property name and value
PROPERTY_PATTERN = re.compile(
    rf"""(['"])([^'"]*({'|'.join(PROPERTY_NAME_ENDS)}))\1"""
    r"""\s*:\s*"""
    r"""('(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*"|None|null)"""
)


def parse_args():
    """
    Parse input arguments
    """

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=f"""
Check that certain properties in the specified zhmcclient log file have a
blanked-out value.

The properties that are checked are those whose names end with:

  {'\n  '.join(PROPERTY_NAME_ENDS)}

The following syntax forms for the properties in the file are supported:

  'name': 'value'
  'name': "value"
  "name": 'value'
  "name": "value"
""")

    parser.add_argument(dest="file", metavar='FILE',
                        help="Path name of the zhmcclient log file to be "
                        "checked")

    return parser.parse_args(sys.argv[1:])


def main():
    """
    Main function
    """
    args = parse_args()
    file = args.file
    print(f"Checking blanked properties in file: {file}")

    checked_pnames = set()
    rc = 0
    with open(file, "r", encoding="utf-8") as fp:
        for lineno, line in enumerate(fp, start=1):
            for match in PROPERTY_PATTERN.finditer(line):
                pname = match.group(2)
                pvalue = match.group(4).strip('"').strip("'")
                checked_pnames.add(pname)
                if pvalue != BLANKED_OUT_STRING:
                    rc = 1
                    print(f"{file}({lineno}): Found property {pname!r} with "
                          f"non-blanked value {pvalue!r}")

    print("The file contains the following blanked properties: "
          f"{', '.join(checked_pnames)}")
    sys.exit(rc)


if __name__ == '__main__':
    main()
