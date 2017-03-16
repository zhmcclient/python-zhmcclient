.. Copyright 2016 IBM Corp. All Rights Reserved.
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..    http://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.
..

.. _`Command line interface`:

Command line interface
======================

This package provides a command line interface (CLI) that utilizes the API of
the zhmcclient package in order to support shell scripting or simply manual
command use in a terminal session.

.. _`Modes of operation`:

Modes of operation
------------------

The zhmc CLI supports two modes of operation:

* `Interactive mode`_: Invoking an interactive zhmc shell for typing zhmc
  sub-commands.
* `Command mode`_: Using it as a standalone non-interactive command.

.. _`Interactive mode`:

Interactive mode
----------------

In interactive mode, an interactive shell environment is brought up that allows
typing zhmc commands, internal commands (for operating the zhmc shell), and
external commands (that are executed in the standard shell for the user).

This zhmc shell is started when the ``zhmc`` command is invoked without
specifying any (sub-)commands::

    $ zhmc [GENERAL-OPTIONS]
    > _

Alternatively, the zhmc shell can also be started by specifying the ``repl``
(sub-)command::

    $ zhmc [GENERAL-OPTIONS] repl
    > _

The zhmc shell uses the ``>`` prompt, and the cursor is shown in the examples
above as an underscore ``_``.

General options may be specified on the ``zhmc`` command, and they serve as
defaults for the zhmc commands that can be typed in the zhmc shell.

The zhmc commands that can be typed in the zhmc shell are simply the command
line arguments that would follow the ``zhmc`` command when used in
`command mode`_::

    $ zhmc -h zhmc.example.com -u hmcuser
    Enter password: <password>
    > cpc list
    . . . <list of CPCs managed by this HMC>
    > partition list JLSE1
    . . . <list of partitions in CPC JLSE1>
    > :q

For example, the zhmc shell command ``cpc list`` in the example above has the
same effect as the standalone command::

    $ zhmc -h zhmc.example.com -u hmcuser cpc list
    Enter password: <password>
    . . . <list of CPCs managed by this HMC>

However, the zhmc shell will prompt for a password only once during its
invocation, while the standalone command will prompt for a password every time.
See also `Environment variables and avoiding password prompts`_.

The internal commands ``:?``, ``:h``, or ``:help`` display general help
information for external and internal commands::

    > :help
    REPL help:

      External Commands:
        prefix external commands with "!"

      Internal Commands:
        prefix internal commands with ":"
        :?, :h, :help     displays general help information
        :exit, :q, :quit  exits the repl

In this help text, "REPL" stands for "Read-Execute-Print-Loop" which is a
term that denotes the approach used in the zhmc shell (or in any shell, for
that matter).

In addition to using one of the internal shell commands shown in the help text
above, you can also exit the zhmc shell by typing `Ctrl-D`.

Typing ``--help`` in the zhmc shell displays general help information for the
zhmc commands, which includes global options and a list of the supported
commands::

    > --help
    Usage: zhmc  [OPTIONS] COMMAND [ARGS]...

      Command line interface for the z Systems HMC.
      . . .

    Options:
      -h, --host TEXT                 Hostname or IP address of the HMC (Default:
                                      ZHMC_HOST environment variable).
      -u, --userid TEXT               Username for the HMC (Default: ZHMC_USERID
                                      environment variable).
      -o, --output-format [[table|plain|simple|psql|rst|mediawiki|html|latex|
                          json]]
                                      Output format (Default: table).
      -t, --timestats                 Show time statistics of HMC operations.
      --version                       Show the version of this command and exit.
      --help                          Show this message and exit.

    Commands:
      cpc        Command group for managing CPCs.
      info       Show information about the HMC.
      lpar       Command group for managing LPARs.
      partition  Command group for managing partitions.
      repl       Start an interactive shell.
      session    Command group for managing sessions.

The usage line in this help text show the standalone command use. Within the
zhmc shell, the ``zhmc`` word is ommitted and the remainder is typed in.

Typing ``COMMAND --help`` in the zhmc shell displays help information for the
specified zhmc command, for example::

    > cpc --help
    Usage: zhmc  cpc [OPTIONS] COMMAND [ARGS]...

      Command group for managing CPCs.

    Options:
      --help  Show this message and exit.

    Commands:
      list  List the CPCs.
      show  Show details of a CPC.

The zhmc shell supports popup help text while typing, where the valid choices
are shown based upon what was typed so far, and where an item from the popup
list can be picked with <TAB> or with the cursor keys. In the following
examples, an underscore ``_`` is shown as the cursor::

    > --_
        --host           Hostname or IP address of the HMC (Default: ZHMC_HOST environment variable).
        --userid         Username for the HMC (Default: ZHMC_USERID environment variable).
        --output-format  Output format (Default: table).
        --timestats      Show time statistics of HMC operations.
        --version        Show the version of this command and exit.

    > c_
       cpc    Command group for managing CPCs.

The zhmc shell supports history (within one invocation of the shell, not
persisted across zhmc shell invocations).

.. _`Command mode`:

Command mode
------------

In command mode, the ``zhmc`` command performs its task and terminates, like any
other standalone non-interactive command.

This mode is used when the ``zhmc`` command is invoked with a (sub-)command::

    $ zhmc [GENERAL-OPTIONS] COMMAND [ARGS...] [COMMAND-OPTIONS]

Examples::

    $ zhmc -h zhmc.example.com -u hmcuser cpc list
    Enter password: <password>
    . . . <list of CPCs managed by this HMC>

    $ zhmc -h zhmc.example.com info
    Enter password: <password>
    . . . <information about this HMC>

In command mode, bash tab completion is also supported, but must be enabled
first as follows (in a bash shell)::

    $ eval "$(_ZHMC_COMPLETE=source zhmc)"

Bash tab completion for zhmc is used like any other bash tab completion::

    $ zhmc --<TAB><TAB>
    ... <shows the global options to select from>

    $ zhmc <TAB><TAB>
    ... <shows the commands to select from>

    $ zhmc cpc <TAB><TAB>
    ... <shows the cpc sub-commands to select from>

.. _`Environment variables and avoiding password prompts`:

Environment variables and avoiding password prompts
---------------------------------------------------

The zhmc CLI has command line options for specifying the HMC host and the HMC
userid to be used. For security reasons, it does not have a command line option
for specifying the password of the HMC userid.

If the HMC operations performed by a particular zhmc command require a
password, the password is prompted for (in both modes of operation)::

      $ zhmc -h zhmc.example.com -u hmcuser cpc list
      Enter password: <password>
      . . . <list of CPCs managed by this HMC>

If the HMC operations performed by a particular zhmc command do not require a
password, no password is prompted for::

      $ zhmc -h zhmc.example.com info
      . . . <information about this HMC>

For script integration, it is important to have a way to avoid the interactive
password prompt. This can be done by storing the session-id string returned by
the HMC when logging on, in an environment variable.

The ``zhmc`` command supports a ``session create`` (sub-)command that outputs
the (bash) shell commands to set all needed environment variables::

      $ zhmc -h zhmc.example.com -u hmcuser session create
      Enter password: <password>
      export ZHMC_HOST=zhmc.example.com
      export ZHMC_USERID=hmcuser
      export ZHMC_SESSION_ID=<session-id>

This ability can be used to set those environment variables and thus to persist
the session-id in the shell environment, from where it will be used in
any subsequent zhmc commands::

      $ eval $(zhmc -h zhmc.example.com -u hmcuser session create)
      Enter password: <password>

      $ env |grep ZHMC
      ZHMC_HOST=zhmc.example.com
      ZHMC_USERID=hmcuser
      ZHMC_SESSION_ID=<session-id>

      $ zhmc cpc list
      . . . <list of CPCs managed by this HMC>

As you can see from this example, the password is only prompted for when
creating the session, and the session-id stored in the shell environment is
utilized in the ``zhmc cpc list`` command, avoiding another password prompt.

Using the session-id from the environment is also a performance improvement,
because it avoids the HMC Logon operation that otherwise would take place.

We believe that storing passwords in shell scripting environments should be
avoided for security reasons, and using the session-id from the ZHMC_SESSION_ID
environment variable should be a reasonable compromise between security
and convenience.

The ZHMC_HOST and ZHMC_USERID environment variables act as defaults for the
corresponding command line options.

.. _`CLI commands`:

CLI commands
------------

For a description of the commands supported by the zhmc CLI, consult its
help system. For example::

      $ zhmc --help
      . . . <general help, listing the general options and possible commands>

      $ zhmc cpc --help
      . . . <help for cpc command, listing its arguments and command-specific options>

Note that the help text for any zhmc (sub-)commands (such as ``cpc``) will
not show the general options again. This is caused by flaws in the tooling
environment used for the zhmc CLI.
The general options (listed by ``zhmc --help``) can still be specified together
with (sub-)commands even though they are not listed in their help text, but
they must be specified before the (sub-)command, and any command-specific
options (listed by ``zhmc COMMAND --help``) must be specified after the
(sub-)command, like shown here::

      $ zhmc [GENERAL-OPTIONS] COMMAND [ARGS...] [COMMAND-OPTIONS]

.. _`Output formats`:

Output formats
--------------

There are different output formats for the command results.
This output format can be selected by the ``-o`` or
``--output-format`` option. For example::

      $ zhmc -o plain cpc list
      /name      status
      P0004711  operating
      P0000815  operating

* table: Maps to output format 'psql'. This is the default.

* plain: Results in tables without borders.

* simple: Corresponds to ``simple_tables`` in `Pandoc Markdown extensions`_.

* psql: Results in tables formatted like Postgres' psql cli tables.

* rst: Formats data like a simple table of the `reStructuredText`_ format .

* mediawiki: Results in table markup used in `Wikipedia`_.

* html: Results in tables formatted in standard HTML markup.

* latex: Results in tables formatted in LaTeX markup.

* json: Results in `JSON`_ format.

.. _`Pandoc Markdown extensions`: http://johnmacfarlane.net/pandoc/README.html#tables
.. _`reStructuredText`: http://docutils.sourceforge.net/docs/user/rst/quickref.html#tables
.. _`Wikipedia`: http://www.mediawiki.org/wiki/Help:Tables
.. _`JSON`: http://json.org/example.html

