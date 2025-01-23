Added support for waiting for partition links to reach one of a specified set
of states with a new 'zhmcclient.PartitionLink.wait_for_states()' method.
This can be used to ensure that a partition link is in a stable state before
proceeding with other operations on it.
