# Copyright 2016 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This library logs internal calls but doesn't output them to any handler.
If you are interested in those calls, add a handler and set the verbosity.
Be aware that the internally used loggers don't have a format specified for
the log records. For example, to output all *INFO* logs to the ``stdout``,
do this::

    import logging

    handler = logging.StreamHandler()
    format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)
    logging.getLogger("zhmcclient").addHandler(handler)
    logging.getLogger("zhmcclient").setLevel(logging.INFO)
"""

import functools
import logging

__all__ = []


def _get_logger(name):
    logger = logging.getLogger(name)
    # As this is a library used by different users in different contexts,
    # the user should decide about the logging behavior. That's why we
    # use the NullHandler as default. Otherwise we would unintentionally
    # spam the log files of the library users.
    logger.addHandler(logging.NullHandler())
    # NOTE(markus_z): In case you want to test it locally, just replace the
    # NullHandler with the StreamHandler and set the loglevel to INFO.
    return logger


def _log_call(func):
    # use the logger of the function's module to get the correct
    # information for log records.
    logger = _get_logger(func.__module__)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info("{mod}.{name} => entering...".format(
            mod=func.__module__, name=func.__name__))
        result = func(*args, **kwargs)
        logger.info("{mod}.{name} <= exit.".format(
            mod=func.__module__, name=func.__name__))
        return result
    return wrapper
