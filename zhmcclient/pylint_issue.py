"""
Reproduce pylint issue
"""

from collections.abc import Mapping


def is_mapping(obj):
    """
    Return whether obj is a Mapping
    """
    return isinstance(obj, Mapping)
