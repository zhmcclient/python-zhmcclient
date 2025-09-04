Fixed the exception handling of the 'Adapter.delete()' method on z16 or later
CPCs where the deletion is implemented by deleting the Partition Link of the
Adapter: If no Partition Link is found for the Adapter, the exception that is
raised is changed from zhmcclient.NotFound to zhmcclient.CeasedExistence,
because that means the adapter itself also no longer exists. If more than one
Partition Link is found for the Adapter, the exception that is raised is
changed from zhmcclient.NoUniqueMatch to zhmcclient.ConsistencyError, because
that should never happen and would be an inconsistency in zhmcclient or HMC.
