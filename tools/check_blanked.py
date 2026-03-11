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
    # Property name, including quotes
    rf"""(['"])([^'"]*({'|'.join(PROPERTY_NAME_ENDS)}))\1"""
    # Separator
    r"""\s*:\s*"""
    # Property value, including quotes
    r"""('(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*"|None|null)"""
)

# On Python 3.9, f-strings must not contain backslashes literally, so we set
# the backslash sequence in a variable.
NL_SEP = "\n  "


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

  {NL_SEP.join(PROPERTY_NAME_ENDS)}

The following syntax forms for the properties in the file are supported:

  'name': 'value'
  'name': "value"
  "name": 'value'
  "name": "value"
""")

    parser.add_argument("--accept-null", action="store_true",
                        help="accept 'null', 'None' or None as blanked-out "
                        "values.")

    parser.add_argument(dest="file", metavar='FILE',
                        help="path name of the zhmcclient log file to be "
                        "checked")

    return parser.parse_args(sys.argv[1:])


def main():
    """
    Main function
    """
    args = parse_args()
    file = args.file
    accept_null = args.accept_null

    print(f"Checking blanked properties in file: {file}")

    checked_pnames = set()
    rc = 0
    with open(file, "r", encoding="utf-8") as fp:
        for lineno, line in enumerate(fp, start=1):
            for match in PROPERTY_PATTERN.finditer(line):
                pname = match.group(2)
                pvalue = match.group(4).strip('"').strip("'")
                checked_pnames.add(pname)
                if not (pvalue == BLANKED_OUT_STRING or
                        accept_null and (pvalue is None or pvalue == "None" or
                                         pvalue == "null")):
                    rc = 1
                    print(f"{file}({lineno}): Found property {pname!r} with "
                          f"non-blanked value {pvalue!r}")

    print("The file contains the following blanked properties: "
          f"{', '.join(checked_pnames)}")
    sys.exit(rc)


if __name__ == '__main__':
    main()
