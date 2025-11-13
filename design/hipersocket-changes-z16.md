# Hipersocket changes since z16

This summarizes the changes to Hipersocket related operations at the HMC WS-API
since z16.

These changes apply to the indicated CPC version, regardless of the HMC version
(as long as the HMC version is supported for the CPC, of course).

## Changes in z16 CPCs (GA 1.0)

* Support for Partition Links for SMC-D was added.
  - indicated by firmware feature "dpm-smcd-partition-link-management"

* Virtual Switches are still supported.

* No changes to Hipersocket related operations:
  - Hipersocket adapters can be created only by "Create Hipersocket".
  - Hipersocket-backed NICs can be created only by "Create NIC" with backing
    vswitch.
  - Creating an SSC management NIC backed by Hipersockets is supported.

## Changes in z16 CPCs (GA 1.5)

* Support for Partition Links was extended to add Hipersocket (and CTC) support.
  - indicated by API feature "dpm-hipersockets-partition-link-management".

* Virtual Switches are still supported.

* Hipersocket adapters now can be created in two ways:
  - "Create Hipersocket", as before.
  - "Create Partition Link" with type hipersocket.

* Hipersocket-backed NICs now can be created in two ways:
  - "Create NIC", with backing vswitch, as before.
  - "Modify Partition Link" with "added-connections".

* Creating an SSC management NIC backed by Hipersockets is not supported, unless
  the "dpm-hipersockets-partition-link-management" API feature gets disabled.
  That can be achieved by installing the firmware feature "DPM IQD Links - Disable",
  which can be requested by customers from IBM support.

## Changes in z17 CPCs (GA 1.0)

* "Create Hipersocket" is no longer supported.
  - indicated by API feature "network-express-support".

* Virtual Switches are no longer supported.
  - indicated by API feature "network-express-support".

* Hipersocket adapters now can be created only by:
  - "Create Partition Link" with type hipersocket.

* Hipersocket-backed NICs can still be created in two ways:
  - "Create NIC", but now with backing adapter port.
    - The requirement to use the backing port is indicated by API feature
      "network-express-support".
  - "Modify Partition Link" with "added-connections".

* Creating an SSC management NIC backed by Hipersockets is supported again,
  using any of the two ways to create NICs.
