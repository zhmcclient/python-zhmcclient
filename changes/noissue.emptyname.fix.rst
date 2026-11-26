Fixed that resources with an empty string as the name (e.g. a default MFA
Server Definition) are correctly handled in
:meth:`~zhmcclient.BaseManager.find_by_name`. Previously, they were not found
in the name to URI cache and :exc:`~zhmcclient.NotFound` was raised.
