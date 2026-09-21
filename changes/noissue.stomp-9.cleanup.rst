Changed pinning of stomp.py from <8.3.0 to <9.0.0. The 8.3.0 version is
meanwhile yanked, but the changes in version 9.0.0 have not yet been
accommodated in zhmcclient. In preparation of future version 9 support,
added explicit enabling or disabling of certificate validation with stomp,
in the :class:`zhmcclient.NotificationReceiver` and
:class:`zhmcclient.AutoUpdater` classes.
