# LPAR status, activation and loading

This document attempts to clarify the meaning of the LPAR 'status' property
values and the behavior for LPAR activation and loading w.r.t. the activation
profiles involved and the effecs on the 'status' property.

The term "LPAR" refers to logical partitions in CPCs in the classic operational
mode; DPM mode is not described here.

All behaviors and properties are described from a perspective of the WS API
of the HMC.

Status of this document: Draft

## Meaning of LPAR 'status' property values

Facts:

* The z15 HMC WS API book has this description for the 'status' property of LPAR:

      One of the following values:
      * "operating" - the logical partition has a active control program
      * "not-operating" - the logical partition's CPC is non operational
      * "not-activated" - the logical partition does not have an active
        control program
      * "exceptions" - the logical partition's CPC has one or more
        unusual conditions
      * "acceptable" - indicates all channels are not operating, but
        their statuses are acceptable. This value is only returned from
        the Support Element.

Issues:

* Doc issue: The description of "not-operating" is in conflict with the behavior
  of actual systems, which do show "not-operating" for LPARs that are active but
  not loaded. In that case, the CPC is definitely operational. The description
  should be fixed accordingly.

* Doc issue: The description of "not-activated" is misleading, because in actual
  systems it indicates that the LPAR is inactive. However, the description
  allows for the case that the LPAR is active but not loaded. The description
  should be fixed accordingly.

* Doc clarification: The value "exceptions" implies that the LPAR is in an
  active or loaded state, i.e. not inactive. The description should be amended
  with this information.

* Doc clarification: The value "acceptable" implies that the LPAR is in an
  active or loaded state, i.e. not inactive. The description should be amended
  with this information.

## Activation profiles

Facts:

* The 'next-activation-profile-name' property of the LPAR object is described as:

      Image activation profile name or load activation profile name to be used
      on the next activate.

* The 'Activate Logical Partition' operation describes its
  'activation-profile-name' parameter as follows:

      The name of the activation profile to be used for the request. If not
      provided, the request uses the profile name specified in the
      next-activation-profile-name property for the Logical Partition object.

* The 'Load Logical Partition' operation does not have a means to specify any
  activation profile.

Issues:

* Doc clarification: The 'activation-profile-name' parameter of the
  'Activate Logical Partition' operation can specify the name of an image
  profile or a load profile, like the 'next-activation-profile-name' property
  can. However, the documentation is unspecific about that. It should be made
  explicit and mention that it can specify image or a load profiles.

Questions:

* For a given LPAR name, does there need to be an image activation profile with
  the same name?
  Answer: No.

* For a given image activation profile, does there need to be a load activation
  profile with the same name?
  Answer: No.

* Can an LPAR be activated through the 'Activate Logical Partition' operation
  when specifying an image activation profile with a different name than the
  LPAR name?
  Answer: TBD

* If an LPAR that was previously deactivated, is activated through the
  'Activate Logical Partition' operation with a load activation profile name
  (and no same-named image activation profile exists), is this rejected?
  Answer: TBD

  If not rejected, which image profile is used?
  Answer: TBD

* If an LPAR that was previously activated but not loaded, is loaded through the
  'Load Logical Partition' operation, which load parameters are used?
  Answer: TBD

* In which cases is the DEFAULTLOAD load activation profile used?
  Answer: TBD


## Operations and LPAR status

This section describes WS-API operations on LPARs that affect its status.

For simplicity, the tables below only show the three main status values
'not-activated', 'not-operating', and 'operating'.

If any of these main status values is not shown as a before-status for an
operation, this means the operation will fail when performed with that
before-status.

### Linux-type LPAR without auto-loading

Image Profile:
* load-at-activation = False
* ipl-type = ipl-type-standard

LPAR:
* activation-mode = linux

| Operation                | Status before    | Status after               | Verified on M96 | Confirmed |
|:------------------------ |:---------------- |:-------------------------- |:--------------- |:--------- |
| CPC IML                  | N/A              | not-activated              | No              | TBD       |
| Activate LPAR            | not-activated    | not-operating (1)          | Yes             | TBD       |
| Activate LPAR            | not-operating    | not-operating (noop ?)     | Yes             | TBD       |
| Activate LPAR (force)    | operating        | not-operating              | No              | TBD       |
| Stop LPAR                | not-operating    | not-operating (noop ?)     | Yes             | TBD       |
| Stop LPAR                | operating        | ?                          | No              | TBD       |
| Start LPAR               | not-operating    | ?                          | No              | TBD       |
| Start LPAR               | operating        | ?                          | No              | TBD       |
| Load LPAR                | not-operating    | operating                  | ? (500,263)     | TBD       |
| Load LPAR (force)        | operating        | operating (newly loaded)   | No              | TBD       |
| Reset Normal/Clear       | operating        | ?                          | No              | TBD       |
| Reset Normal/Clear       | not-operating    | ?                          | No              | TBD       |
| Deactivate LPAR          | not-operating    | not-activated              | Yes             | TBD       |
| Deactivate LPAR (force)  | operating        | not-activated              | No              | TBD       |

(1) Due to load-at-activation = False

### Linux-type LPAR with auto-loading

Image Profile:
* load-at-activation = True
* ipl-type = ipl-type-standard

LPAR:
* activation-mode = linux

TBD: Same as without auto-loading, except for:

| Operation                | Status before    | Status after               | Verified on M96 | Confirmed |
|:------------------------ |:---------------- |:-------------------------- |:--------------- |:--------- |
| Activate LPAR            | not-activated    | operating                  | No              | TBD       |

### SSC-type LPAR

TBD: Same as Linux-type

### ESA390-type LPAR

TBD: Same as Linux-type
