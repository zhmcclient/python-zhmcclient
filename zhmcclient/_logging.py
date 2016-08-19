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
This library logs calls to its public API and to some internal functions, but
doesn't output the log records by default.

It uses one :class:`~py:logging.Logger` object for each module. The name of
each such logger is the dotted module name (e.g. ``'zhmcclient._cpc'``). You
can also use the logger for the package name (``'zhmcclient'``) in order to
set up package-wide logging.

These loggers have a null-handler (see :class:`~py:logging.NullHandler`)
and have no log formatter (see :class:`~py:logging.Formatter`).

If you want to get the log output, add a log handler and set the log level
(see the :meth:`~py:logging.Logger.addHandler` and
:meth:`~py:logging.Logger.setLevel` methods of the
:class:`~py:logging.Logger` class).

For example, to output all warning level (and higher level) log records issued
by this library and by others to ``stdout`` in a particular format, do this:

::

    import logging

    handler = logging.StreamHandler()
    format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    handler.setFormatter(logging.Formatter(format_string))
    logger = getLogger('')  # root logger
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)

If you want to see only the info level (and higher level) log records issued by
the ``_session`` module of this library, use the logger for just that module:

::

    import logging

    handler = logging.StreamHandler()
    format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    handler.setFormatter(logging.Formatter(format_string))
    logger = getLogger('zhmcclient._session')
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
"""

import functools
import logging
import inspect


def _get_logger(name):
    """
    Return a :class:`~py:logging.Logger` object with the specified name.

    A :class:`~py:logging.NullHandler` is added to the logger (if it does not
    have one yet) in order for this library to be silent by default, and to
    leave the definition of 'real' logging handlers to the user of this
    library.
    """
    logger = logging.getLogger(name)
    if not any([isinstance(h, logging.NullHandler) for h in logger.handlers]):
        logger.addHandler(logging.NullHandler())
    # NOTE(markus_z): In case you want to test it locally, just replace the
    # NullHandler with the StreamHandler and set the loglevel to INFO.
    return logger


def _log_call(func):
    """
    Function decorator that causes the decorated function to log calls to
    itself to a logger.

    The logger's name is the dotted module name of the module defining the
    decorated function (e.g. 'zhmcclient._cpc').
    """
    mod = inspect.getmodule(func)
    try:
        modname = mod.__name__
    except AttributeError:
        raise TypeError("The _log_call decorator must be used on a function "
                        "(and not on top of the property decorator)")
    logger = _get_logger(modname)
    if inspect.isfunction(func):
        frames = inspect.getouterframes(inspect.currentframe())
        callername = frames[1][3]
        # At the time the decorator code gets control, the module has been
        # loaded, but class definitions of decorated methods are not complete
        # yet. Also, methods of the class are still functions at this point.
        if callername == '<module>':
            where = '{func}()'.format(func=func.__name__)
        else:  # it is a class name or outer function name
            where = '{caller}.{func}()'.format(caller=callername,
                                               func=func.__name__)
    else:
        raise TypeError("The _log_call decorator must be used on a function")

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """
        Log entry to and exit from the decorated function, at the debug level.

        Note that this wrapper function is called every time the decorated
        function/method is called, but that the log message only needs to be
        constructed when logging for this logger and for this log level is
        turned on. Therefore, we do as much as possible in the decorator
        function, plus we use %-formatting and lazy interpolation provided by
        the log functions, in order to save resources in this function here.
        """
        logger.debug("Entering %s", where)
        result = func(*args, **kwargs)
        logger.debug("Leaving %s", where)
        return result

    return wrapper
