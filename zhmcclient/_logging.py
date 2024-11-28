# Copyright 2016,2021 IBM Corp. All Rights Reserved.
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
The zhmcclient supports logging using the standard Python :mod:`py:logging`
module, using standard Python :class:`~py:logging.Logger` objects with these
names:

* 'zhmcclient.api' for user-issued calls to zhmcclient API functions, at the
  debug level. Internal calls to API functions are not logged.

* 'zhmcclient.hmc' for operations from zhmcclient to the HMC, at the
  debug level.

* 'zhmcclient.jms' for notifications from the HMC to zhmcclient, at the
  debug, info, warning and error level. At this point, this logger is used only
  for the :ref:`auto-updating` support, but not for
  the :class:`~zhmcclient.NotificationReceiver` class.

* 'zhmcclient.os' for interactions with OS consoles, at the debug level.

For HMC operations and API calls that contain the HMC password or HMC session
tokens, the password is hidden in the log message by replacing it with a few
'*' characters.

All these loggers have a null-handler (see :class:`~py:logging.NullHandler`)
and have no log formatter (see :class:`~py:logging.Formatter`).

As a result, the loggers are silent by default. If you want to turn on logging,
add a log handler (see :meth:`~py:logging.Logger.addHandler`, and
:mod:`py:logging.handlers` for the handlers included with Python) and set the
log level (see :meth:`~py:logging.Logger.setLevel`, and :ref:`py:levels` for
the defined levels).

If you want to change the default log message format, use
:meth:`~py:logging.Handler.setFormatter`. Its ``form`` parameter is a format
string with %-style placeholders for the log record attributes (see Python
section :ref:`py:logrecord-attributes`).

Examples:

* To output the log records for all HMC operations to ``stdout`` in a
  particular format, do this::

      import logging

      handler = logging.StreamHandler()
      format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
      handler.setFormatter(logging.Formatter(format_string))
      logger = logging.getLogger('zhmcclient.hmc')
      logger.addHandler(handler)
      logger.setLevel(logging.DEBUG)

* This example uses the :func:`~py:logging.basicConfig` convenience function
  that sets the same format and level as in the previous example, but for the
  root logger. Therefore, it will output all log records, not just from this
  package::

      import logging

      format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
      logging.basicConfig(format=format_string, level=logging.DEBUG)
"""

import logging
import inspect
import functools
from collections.abc import Mapping, Sequence

from ._constants import API_LOGGER_NAME, BLANKED_OUT_STRING

__all__ = []


def log_escaped(string):
    """
    Return the escaped input string, for use in log messages.
    """
    return string.replace('\n', ' ').replace('  ', ' ').replace('  ', ' ').\
        replace('  ', ' ')


def get_logger(name):
    """
    Return a :class:`~py:logging.Logger` object with the specified name.

    A :class:`~py:logging.NullHandler` handler is added to the logger if it
    does not have any handlers yet and if it is not the Python root logger.
    This prevents the propagation of log requests up the Python logger
    hierarchy, and therefore causes this package to be silent by default.
    """
    logger = logging.getLogger(name)
    if name != '' and not logger.handlers:
        logger.addHandler(logging.NullHandler())
    return logger


def logged_api_call(
        org_func=None, *, blanked_properties=None, properties_pos=None):
    """
    Function decorator that causes the decorated API function or method to log
    calls to itself to a logger.

    The logger's name is the dotted module name of the module defining the
    decorated function (e.g. 'zhmcclient._cpc').

    Parameters:

      org_func (function object): The original function being decorated.
        Will be `None` if the decorator is specified with its optional
        argument 'blanked_properties'.

      blanked_properties (list of str): Optional: List of properties in the
        'properties' argument of the decorated API function that should be
        blanked out before being logged. Can be used to hide password
        properties.
        This parameter is required when 'properties_pos' is used.
        This parameter must be specified as a keyword argument.

      properties_pos (int): Optional: 0-based index of the 'properties'
        parameter in the argument list of the decorated API function.
        For methods, the 'self' or 'cls' parameter is included in the position.
        This parameter is needed in case the properties are passed as a
        positional argument by the caller of the API function.
        This parameter is required when 'blanked_properties' is used.
        This parameter must be specified as a keyword argument.

    Returns:

      function object: The function wrappering the original function being
        decorated.

    Raises:

      TypeError: The @logged_api_call decorator must be used on a function or
        method (and not on top of the @property decorator).
    """

    if blanked_properties is not None and properties_pos is None:
        raise TypeError(
            "If the @logged_api_call decorator is specified with "
            "'blanked_properties', 'properties_pos' must also be specified.")

    if properties_pos is not None and blanked_properties is None:
        raise TypeError(
            "If the @logged_api_call decorator is specified with "
            "'properties_pos', 'blanked_properties' must also be specified.")

    if blanked_properties is not None and (
            not isinstance(blanked_properties, Sequence) or  # noqa: W504
            isinstance(blanked_properties, str)):
        raise TypeError(
            "The 'blanked_properties' parameter of the @logged_api_call "
            "decorator must be a list of strings.")

    def _decorate(func):
        """
        The actual decorator function that always gets the original decorated
        function, independent of whether the 'logged_api_call' decorator was
        specified with or without its optional arguments.

        Parameters:

          func (function object): The original function being decorated.
        """

        # Note that in this decorator function, we are in a module loading
        # context, where the decorated functions are being defined. When this
        # decorator function is called, its call stack represents the
        # definition of the decorated functions. Not all global definitions in
        # the module have been defined yet, and methods of classes that are
        # decorated with this decorator are still functions at this point (and
        # not yet methods).

        if not inspect.isfunction(func):
            raise TypeError("The @logged_api_call decorator must be used on a "
                            "function or method (and not on top of the "
                            "@property decorator)")

        try:
            # We avoid the use of inspect.getouterframes() because it is slow,
            # and use the pointers up the stack frame, instead.

            this_frame = inspect.currentframe()  # this function
            apifunc_frame = this_frame.f_back  # the decorated API function
            if org_func:
                # In this case, there is one more decorator function nesting
                apifunc_frame = apifunc_frame.f_back
            apifunc_owner = inspect.getframeinfo(apifunc_frame)[2]

        finally:
            # Recommended way to deal with frame objects to avoid ref cycles
            del this_frame
            del apifunc_frame

        # TODO: For inner functions, show all outer levels instead of just one.

        func_name = getattr(func, '__name__', '<unknown>')
        if apifunc_owner == '<module>':
            # The decorated API function is defined globally (at module level)
            apifunc_str = f'{func_name}()'
        else:
            # The decorated API function is defined in a class or in a function
            apifunc_str = f'{apifunc_owner}.{func_name}()'

        logger = get_logger(API_LOGGER_NAME)

        def is_external_call():
            """
            Return a boolean indicating whether the call to the decorated API
            function is made from outside of the zhmcclient package.
            """
            try:
                # We avoid the use of inspect.getouterframes() because it is
                # slow, and use the pointers up the stack frame, instead.

                this_frame = inspect.currentframe()  # this function
                log_api_call_frame = this_frame.f_back  # log_api_call()
                apifunc_frame = log_api_call_frame.f_back  # the decorated func
                apicaller_frame = apifunc_frame.f_back  # caller of API func
                apicaller_module = inspect.getmodule(apicaller_frame)
                if apicaller_module is None:
                    apicaller_module_name = "<unknown>"
                else:
                    apicaller_module_name = apicaller_module.__name__
            finally:
                # Recommended way to deal with frame objects to avoid ref
                # cycles
                del this_frame
                del log_api_call_frame
                del apifunc_frame
                del apicaller_frame
                del apicaller_module

            # Log only if the caller is not from the zhmcclient package
            return apicaller_module_name.split('.')[0] != 'zhmcclient'

        def blanked_dict(properties):
            """
            Return a copy of the properties dict, with blanked out values
            according to the 'blanked_properties' and 'properties_pos'
            arguments of the 'logged_api_call' decorator.
            """
            # properties may also be a DictView (subclass of Mapping)
            assert isinstance(properties, Mapping)
            copied_properties = dict(properties)
            for pname in blanked_properties:
                if pname in copied_properties:
                    copied_properties[pname] = BLANKED_OUT_STRING
            return copied_properties

        def blanked_args(args, kwargs):
            """
            Return a copy of args and kwargs, whereby the 'properties' argument
            has items blanked out according to the 'blanked_properties' and
            'properties_pos' arguments of the 'logged_api_call' decorator.
            """
            logged_kwargs = dict(kwargs)
            logged_args = list(args)
            if blanked_properties is not None:
                if 'properties' in kwargs:
                    logged_kwargs['properties'] = \
                        blanked_dict(kwargs['properties'])
                else:
                    logged_args[properties_pos] = \
                        blanked_dict(args[properties_pos])
            return tuple(logged_args), logged_kwargs

        def log_call(args, kwargs):
            """
            Log the call to the API function.
            """
            logged_args, logged_kwargs = blanked_args(args, kwargs)
            logger.debug("Called: %s, args: %.500s, kwargs: %.500s",
                         apifunc_str,
                         log_escaped(repr(logged_args)),
                         log_escaped(repr(logged_kwargs)))

        def log_return(result):
            """
            Log the return from the API function.
            """
            logger.debug("Return: %s, result: %.1000s",
                         apifunc_str, log_escaped(repr(result)))

        @functools.wraps(func)
        def log_api_call(*args, **kwargs):
            """
            Log entry to and exit from the decorated function, at the debug
            level.

            Note that this wrapper function is called every time the decorated
            function/method is called, but that the log message only needs to
            be constructed when logging for this logger and for this log level
            is turned on. Therefore, we do as much as possible in the decorator
            function, plus we use %-formatting and lazy interpolation provided
            by the log functions, in order to save resources in this function
            here.

            Parameters:

              func (function object): The decorated function.

              *args: Any positional arguments for the decorated function.

              **kwargs: Any keyword arguments for the decorated function.
            """

            # Note that in this function, we are in the context where the
            # decorated function is actually called.
            _log_it = is_external_call() and logger.isEnabledFor(logging.DEBUG)

            if _log_it:
                log_call(args, kwargs)

            result = func(*args, **kwargs)  # The zhmcclient function

            if _log_it:
                log_return(result)

            return result

        return log_api_call

    # When the logged_api_call decorator is specified with its optional
    # arguments, org_func is None
    if org_func:
        return _decorate(org_func)
    return _decorate
