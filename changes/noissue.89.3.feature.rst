Docs: Updated the descriptions of the :meth:`zhmcclient.NicManager.create`,
:meth:`zhmcclient.Partition.attach_network_link`,
:meth:`zhmcclient.PartitionLinkManager.create` and
:meth:`zhmcclient.PartitionLink.update_properties` methods
to describe the limitation of not supporting SSC management NICs backed by
Hipersocket adapters on z16 CPCs that have the API feature
"dpm-hipersockets-partition-link-management" enabled, and how to lift this
limitation.
