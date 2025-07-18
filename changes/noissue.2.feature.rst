Support for certificate validation for STOMP notifications, by adding a new
'verify_cert' parameter to zhmcclient.NotificationReceiver(). It works in
the same way as the 'verify_cert' parameter of zhmcclient.Session(), but its
default is False to maintain backwards compatibility. Therefore, it is
recommended to specify the 'verify_cert' parameter with a value other than
`False`.
