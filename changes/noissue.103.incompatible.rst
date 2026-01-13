Removed support for Python 3.8, because (1) Python 3.8 is out of service since
2024-10-07, and (2) the license definition according to PEP 639 requires
setuptools >= 77.0.3 which requires Python >= 3.9, and pyproject.toml does
not support environment markers.
