Test: Added the option 'ignore-unpinned-requirements: False' to both
safety policy files because for safety 3.0, the default is to ignore
unpinned requirements (in requirements.txt).

Increased safety minimum version to 3.0 because the new option is not
tolerated by safety 2.x. Safety now runs only on Python >=3.7 because
that is what safety 3.0 requires.
