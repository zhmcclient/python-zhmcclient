Added support for busy retries to 'Session.post()' and 'Session.delete()'
when the HTTP request returns HTTP status 409 with reason codes 1 or 2.
The waiting time between retries can also be specified. This can be used
by resource class methods that need that.
By default, no retries are performed.
Changed 'PartitionLink.update_properties()' and 'PartitionLink.delete()' to
specify busy retries.
