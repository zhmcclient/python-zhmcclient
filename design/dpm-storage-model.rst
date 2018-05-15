.. Copyright 2018 IBM Corp. All Rights Reserved.
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

=======================================
Design for DPM storage management model
=======================================

DPM introduces support for a new simplified way to manage the storage
attached to a CPC.

For simplicity, this design document uses the term "DPM storage management
model" to mean all changes related to Storage Groups (part of LI1170), FICON
Configuration (also part of LI1170), Feature List API (LI1421),
and any other changes to existing WS-API functionality that is related to
the new support.

The DPM storage management model only applies to CPCs in DPM mode that have
the "dpm-storage-management" feature enabled. Named features are also a newly
introduced concept.

The "dpm-storage-management" feature will be available for the z14 machine
generation and onwards, and will not be rolled back to machine generations
before z14. For the z14 machine generation (high end and mid range), the
"dpm-storage-management" feature will roll out in the service stream for the
machines. Once the service level containing support for it is applied to a
CPC, that CPC will exhibit the new support. There is no means to enable or
disable the "dpm-storage-management" feature for a CPC; it is always enabled
once the service providing it has been applied. The service providing the
"dpm-storage-management" feature is concurrent for the CPC but requires a
reboot of SE and HMC.
With the next machine generation after z14, the "dpm-storage-management"
feature will be available from day 1.

The DPM storage management model is incompatible for WS-API clients that used
the storage related functionality so far. For example, HBA objects no longer
exist.

This design document describes at a high level how the zhmcclient API will
expose the DPM storage management model.

Resource model
==============

The zhmcclient API implements a concept of Python manager objects and Python
resource objects to expose the HMC objects: A Python manager object is part of
its parent resource object and mainly provides methods for listing its own
resource objects, and for creating new resource objects. A Python resource
object represents a corresponding HMC object.

Because the DPM storage management model makes broad use of having resource URIs
back and forth, the zhmcclient resource model at the Python API level
distinguishes between child resources of a resource (over which lifecycle
control is exercised), and other referenced resources (over which no lifecycle
control is exercised).

Navigation from a Python resource object to its child resource objects and to
its referenced resources normally happens in the same way: A resource object
has an attribute for each type of child resource and for each type of
referenced resource. The attribute value is the Python manager object for the
set of child resources or referenced resources, respectively.
The difference is to which parent resource object the manager object of these
resource objects point back via its "parent" attribute: The manager object of
child resource objects always point back to their parent resource object (who
manages the lifecycle of the child resource), while the manager object of
referenced resource objects do not point back to their referencing resource,
but to their true parent resource (to which the referenced resource is a child
resource).

The previous paragraph described how it works for child resources or referenced
resources with a multiplicity of 0 or more (*). Some referenced resources have
a multiplicity of 1. For those referenced resources, the Python object setup is
simplified, in that there is no manager object. Instead, the attribute value if
directly the referenced resource object.

The following diagram shows the resource hierarchy that will be exposed by the
zhmcclient API. The manager objects (for resources with a multiplicity of *)
are not shown in the diagram, for simplicity. The names shown are the Python
class names of the resource classes.
In parenthesis follow the multiplicity, whether the resource object is a child
resource or a referenced resource, and optionally the role of these resources
within their parent or referencing resource.

The diagram shows resource classes for storage groups (which are
commonly used for FCP and FICON storage), the resource classes specific to the
FICON configuration, and existing resource classes to the extent they are
relevant for the DPM storage management model.

It is important to understand that the storage groups and the FICON
configuration are scoped to a single CPC, and represent that CPC’s view of a
set of storage resources. A second CPC’s storage groups and FICON configuration
may include resources that represent the same physical or logical entities, but
they are represented at the WS-API and thus at the zhmcclient API as separate
resource objects.

.. code-block:: text

    client
      |
      +-- CPC (*/child)
      |     |
      |     +-- Adapter (*/child, storage adapter, type: FCP or FICON)
      |     |     |
      |     |     +-- Port (*/child, storage port)
      |     |           |
      |     |           +-- StorageSwitch (1/ref, the switch connected to this port)
      |     |           |
      |     |           +-- StorageSubsystem (1/ref, the subsystem connected to this port)
      |     |
      |     +-- Partition (*/child)
      |     |     |
      |     |     +-- HBA (*/child readonly, future?)
      |     |
      |     +-- StorageGroup (*/child, type: FCP or FICON)
      |           |
      |           +-- StorageVolume (*/child)
      |           |     |
      |           |     +-- StorageControlUnit (*/ref, FICON SGs only)
      |           |
      |           +-- VirtualStorageResource (*/child)
      |           |     |
      |           |     +-- Partition (1/ref, partition to which this VSR is attached)
      |           |     |
      |           |     +-- Port (*/ref, actually used port, for FCP SGs)
      |           |     |
      |           |     +-- StorageVolume (*/ref, volume, for FICON SGs)
      |           |
      |           +-- Partition (*/ref, partitions to which this SG is attached)
      |           |
      |           +-- Port (*/ref, FCP SGs only, candidate ports to be used in this SG)
      |
      +-- StorageSite (1-2/child, FICON only)
      |     |
      |     +-- CPC (*/ref, the CPCs using this FICON configuration - currently always 1)
      |     |
      |     +-- StorageSubsystem (*/ref, the subsystems in this site)
      |     |
      |     +-- StorageSwitch (*/ref, the switches in this site)
      |
      +-- StorageFabric (*/child, FICON only)
      |     |
      |     +-- CPC (*/ref, the CPCs using this FICON configuration - currently always 1)
      |     |
      |     +-- StorageSwitch (*/ref, the switches in this fabric)
      |
      +-- StorageSwitch (*/child, FICON only, all switches)
      |     |
      |     +-- StorageSite (1/ref, the site this switch is in)
      |     |
      |     +-- StorageFabric (1/ref, the fabric this switch is in)
      |
      +-- StorageSubsystem (*/child, FICON only, all subsystems)
            |
            +-- StorageControlUnit (*/child, the logical control units of the subsystem)
            |     |
            |     +-- StoragePath (*/child, the paths that connect this control unit to a port on a switch and ultimately on an adapter of the CPC)
            |           |
            |           +-- StorageSwitch (0-1/ref, the exit switch for this path)
            |           |
            |           +-- Adapter (1/ref, the adapter for this path (its port is specified as a property)
            |
            +-- StorageSite (1/ref, the site this subsystem is in)
            |
            +-- StorageSwitch (*/ref, the connected switches)
            |
            +-- Adapter (*/ref, the connected adapters (their ports are specified as a property)

Here are brief descriptions of the resource classes added by the DPM storage
management model:

Storage group support:

* StorageGroup - A container for storage volumes (FCP or ECKD).

  A particular storage group can be attached to zero or more partitions. In
  case of more than one partition, the volumes in the group are being shared
  between the partitions.

  A particular partition may have multiple storage groups attached, which means
  that all volumes in these storage groups are attached to the partition.

* StorageVolume - A storage volume (FCP or ECKD) on a storage subsystem.

  The storage volume resource objects can be created, but the act of actually
  allocating the volume on the storage subsystem is not performed by the creation
  operation and is instead performed separately. That act is termed "fulfillment".
  Thus, a storage volume resource object has a fulfillment status.

  When a storage group is attached to a partition, the group’s fulfilled storage
  volumes are virtualized for that partition and the partition’s view of them is
  represented by a set of virtual storage resource objects.

* VirtualStorageResource - A storage volume (FCP or ECKD) that is attached to a
  partition. If the same StorageVolume resource is attached to two partitions,
  there is one VirtualStorageResource resource for each of thoser attachments.

FICON configuration support:

* StorageSite - A site housing storage subsystems and storage switches that are
  accessible to a CPC (FICON only).

  A storage site HMC object is a child resource of a CPC HMC object and
  represents the view of the CPC on its storage. The same physical storage
  subsystems and storage switches can be represented in multiple storage site
  resources.

  A primary storage site resource always exists by default for a CPC.
  A secondary storage site resource for a CPC can optionally be defined.
  Primary sites are typically local to the CPC. Secondary sites are typically
  remote to the CPC, and are often used for redundancy.

* StorageSwitch - A physical storage switch (FICON only).

* StorageSubsystem - A physical storage subsystem (storage unit) (FICON only).

  Storage subsystems are physically connected (cabled) to a set of storage
  switches or directly to a set of storage adapters in the CPC.

  Storage subsystems are subdivided into logical control units, which provide
  access to a subset of a subsystem’s storage resources.

* StorageControlUnit - A logical control unit within a storage subsystem (FICON
  only).

* StorageFabric - A logical construct that encompasses the set of all storage
  switches that are interconnected (FICON only).

  In a multi-site configuration, switches from both sites are interconnected,
  therefore in such configurations, a fabric will span multiple sites.

The other resource classes shown in the diagram already exist today in the
zhmcclient API:

* Adapter

* Port

* Partition

* CPC

TBD: Info on features.

TBD: Info on storage resources and operations that are different or not
available anymore (e.g. HBA).


Mapping HMC operations to the zhmcclient API
============================================

In the following tables, "mgr" refers to the Python manager object for the
resource, and "res" refers to the Python resource object for the resource.

**Storage group support (FCP only)**

Partition
---------

=====================================================  ==============================  ==========================================
HMC Operation Name                                     zhmcclient API                  HTTP method and URI
=====================================================  ==============================  ==========================================
Attach Storage Group                                   res.attach_storage_group()      POST /api/partitions/{partition-id}/operations/attach-storage-group
Detach Storage Group                                   res.detach_storage_group()      POST /api/partitions/{partition-id}/operations/detach-storage-group
=====================================================  ==============================  ==========================================

StorageGroup
------------

==========================  =============  ===================================
Resource Attribute          kind           Python class      
==========================  =============  ===================================
storage_volumes             */child        StorageVolumeManager
virtual_storage_resources   */child        VirtualStorageResourceManager
==========================  =============  ===================================

=====================================================  ==============================  ==========================================
HMC Operation Name                                     zhmcclient API                  HTTP method and URI
=====================================================  ==============================  ==========================================
List Storage Groups                                    mgr.list()                      GET /api/cpcs/{cpc-id}/storage-groups
Create Storage Group                                   mgr.create()                    POST /api/cpcs/{cpc-id}/storage-groups
Delete Storage Group                                   res.delete()                    DELETE /api/storage-groups/{storage-group-id}
Get Storage Group Properties                           res.properties                  GET /api/storage-groups/{storage-group-id}
Modify Storage Group Properties                        res.update_properties()         POST /api/storage-groups/{storage-group-id}
Add Candidate Adapter Ports to an FCP Sto.Grp.         res.add_candidate_ports()       POST /api/storage-groups/{storage-group-id}/operations/add-candidate-adapter-ports
Remove Candidate Adapter Ports from an FCP Sto.Grp.    res.remove_candidate_ports()    POST /api/storage-groups/{storage-group-id}/operations/remove-candidate-adapter-ports
Request Storage Group Fulfillment                      res.request_fulfillment()       POST /api/storage-groups/{storage-group-id}/operations/request-fulfillment
Get Partitions for a Storage Group                     res.list_attached_partitions()  GET /api/storage-groups/{storage-group-id}/operations/get-partitions
candidate-adapterport-uris property of storage group   res.list_candidate_ports()      
=====================================================  ==============================  ==========================================

StorageVolume
-------------

=====================================================  ==============================  ==========================================
HMC Operation Name                                     zhmcclient API                  HTTP method and URI
=====================================================  ==============================  ==========================================
List Storage Volumes of a Storage Group                mgr.list()                      GET /api/storage-groups/{storage-group-id}/storage-volumes
Modify Storage Group Properties (to create a volume)   mgr.create()
Modify Storage Group Properties (to delete a volume)   mgr.delete()
Get Storage Volume Properties                          res.properties                  GET /api/storage-groups/{storage-group-id}/storage-volumes/{storage-volume-id}
Modify Storage Group Properties (to update a volume)   res.update_properties()
Fulfill FICON Storage Volume                           res.fulfill_ficon()             POST /api/storage-groups/{storage-group-id}/storage-volumes/{storage-volume-id}/operations/fulfill-ficon-storage-volume
Unfulfill FICON Storage Volume                         res.unfulfill_ficon()           POST /api/storage-groups/{storage-group-id}/storage-volumes/{storage-volume-id}/operations/unfulfill-ficon-storage-volume
Fulfill FCP Storage Volume                             res.fulfill_fcp()               POST /api/storage-groups/{storage-group-id}/storage-volumes/{storage-volume-id}/operations/fulfill-fcp-storage-volume
=====================================================  ==============================  ==========================================

VirtualStorageResource
----------------------

==========================  =============  ===================================
Resource Attribute          kind           Python class      
==========================  =============  ===================================
attached_partition          1/ref          Partition
==========================  =============  ===================================

=====================================================  ==============================  ==========================================
HMC Operation Name                                     zhmcclient API                  HTTP method and URI
=====================================================  ==============================  ==========================================
List Virtual Storage Resources of a Storage Group      mgr.list()                      GET /api/storage-groups/{storage-group-id}/virtual-storage-resources
Get Virtual Storage Resource Properties                res.properties                  GET /api/storage-groups/{storage-group-id}/virtual-storage-resources/{virtual-storage-resource-id}
Update Virtual Storage Resource Properties             res.update_properties()         POST /api/storage-groups/{storage-group-id}/virtual-storage-resources/{virtual-storage-resource-id}
adapter-port-uris property of VSR                      res.list_actual_adapter_ports()
=====================================================  ==============================  ==========================================

**FICON configuration support**

TBD
