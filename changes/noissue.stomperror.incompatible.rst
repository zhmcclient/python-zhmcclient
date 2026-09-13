The :meth:`zhmcclient.AutoUpdater.open` method has been changed to no
longer raise stomp exceptions that may occur when connecting to the HMC.
Such exceptions are now raised as :exc:`zhmcclient.NotificationConnectionError`.
This change affects only users who use the auto-update feature of zhmcclient
(i.e. call the :meth:`zhmcclient.BaseResource.enable_auto_update` method) and
handle "stomp.StompException" exceptions or their subclasses in their code.
Such code needs to be changed to handle
:exc:`zhmcclient.NotificationConnectionError` instead.
Note that the :meth:`zhmcclient.NotificationReceiver.connect` method already
raised stomp exceptions as :exc:`zhmcclient.NotificationConnectionError`.
