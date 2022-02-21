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

## Image and load activation profiles

Existing documentation:

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

Documentation issues:

* Doc clarification: The 'activation-profile-name' parameter of the
  'Activate Logical Partition' operation can specify the name of an image
  profile or a load profile, like the 'next-activation-profile-name' property
  can. However, the documentation is unspecific about that. It should be made
  explicit and mention that it can specify image or a load profiles.

Discussion results / questions:

* For each LPAR, there needs to be an image profile with the same name as the
  LPAR, otherwise the LPAR activation will fail.

* There cannot be an image profile and a load profile with the same name
  (in the same CPC).

  That also applies to the image and load profiles visible at the WS-API.

* The profile name specified with the 'Activate Logical Partition' operation
  must be one of:

  - if it is an image profile, it must have the same name as the targeted LPAR.
  - if it is a load profile, it must not have the name of any LPAR in the CPC.

  That requirement applies to both:

  - the name specified in the 'activation-profile-name' operation parameter.
  - the name specified in the 'next-activation-profile-name' LPAR property,
    if the 'activation-profile-name' operation parameter is not specified.

  Otherwise, the activation will fail.

* If an inactive LPAR is activated through the 'Activate Logical Partition'
  operation with 'activation-profile-name' set to a load activation profile
  name (that is different from the LPAR name), the following parameters
  are used:

  - the activation related parameters from the image profile with the same
    name as the LPAR.
  - the load related parameters from the specified load profile.

* The load activation profile named 'DEFAULTLOAD' is not automatically used
  by default; it is only used when specified.


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

| LPAR operation                              | Status before    | Status after                         | Verified on M96 | Confirmed |
|:------------------------------------------- |:---------------- |:------------------------------------ |:--------------- |:--------- |
| Activate w/ image profile                   | not-activated    | not-operating (1)                    | Yes             | TBD       |
| Activate w/ load profile                    | not-activated    | not-operating (2)                    | No              | TBD       |
| Activate w/ image profile (unchanged)       | not-operating    | not-operating (no reactivation) (3)  | No              | TBD       |
| Activate w/ load pr. (image pr. unchanged)  | not-operating    | not-operating (no reactivation) (4)  | No              | TBD       |
| Activate w/ image profile (modified)        | not-operating    | not-operating (reactivation) (5)     | No              | TBD       |
| Activate w/ force (image pr. unchanged)     | operating        | not-operating (no reactivation) (6)  | No              | TBD       |
| Activate w/ force (image pr. modified)      | operating        | not-operating (reactivation) (7)     | No              | TBD       |
| Load                                        | not-operating    | operating                            | ? (500,263)     | TBD       |
| Load (force)                                | operating        | operating (newly loaded) (8)         | No              | TBD       |
| Deactivate                                  | not-operating    | not-activated                        | Yes             | TBD       |
| Deactivate (force)                          | operating        | not-activated                        | No              | TBD       |
| Stop                                        | not-operating    | not-operating (noop ?)               | Yes             | TBD       |
| Stop                                        | operating        | ?                                    | No              | TBD       |
| Start                                       | not-operating    | ?                                    | No              | TBD       |
| Start                                       | operating        | ?                                    | No              | TBD       |
| Reset Normal/Clear                          | operating        | ?                                    | No              | TBD       |
| Reset Normal/Clear                          | not-operating    | ?                                    | No              | TBD       |

(1) Activation parameters are taken from the specified image profile (must have same name as LPAR). Due to load-at-activation=False, the
    LPAR is not loaded, so the load parameters in the image profile are ignored.

(2) Activation parameters are taken from the image profile with same name as the LPAR. Due to load-at-activation=False, the LPAR is not
    loaded, so the specified load profile is ignored.

(3) No re-activation occurs, since the image activation profile is unchanged. Due to load-at-activation=False, the
    LPAR is not loaded, so the load parameters in the image profile are ignored.

(4) No re-activation occurs, since the image activation profile is unchanged. Due to load-at-activation=False, the LPAR is not
    loaded, so the specified load profile is ignored.

(5) The activation state of the LPAR is adjusted to reflect the modified image profile. Due to load-at-activation=False, the
    LPAR is not loaded, so the load parameters in the image profile are ignored.

    - Question: For which properties of the image activation profile does this happen?

(6) Since 'force' is specified, the OS in the LPAR is shut down, the activation state of the LPAR is adjusted based
    on the changed activation parameters, but due to load-at-activation=False the LPAR is not loaded again.

(7) Since 'force' is specified, the OS in the LPAR is shut down, the activation state of the LPAR is not adjusted due
    to the unchanged activation parameters, and due to load-at-activation=False the LPAR is not loaded again.

(8) Since 'force' is specified, the OS in the LPAR is shut down, the activation state of the LPAR is adjusted based
    on the activation parameters, and the LPAR is loaded again.

    - Question: Is the LPAR always re-loaded, even when the activation parameters do not need to be changed?

### Linux-type LPAR with auto-loading

Image Profile:
* load-at-activation = True
* ipl-type = ipl-type-standard

LPAR:
* activation-mode = linux

Same as without auto-loading, except that activation is followed by a load:

| LPAR operation                              | Status before    | Status after                         | Verified on M96 | Confirmed |
|:------------------------------------------- |:---------------- |:------------------------------------ |:--------------- |:--------- |
| Activate w/ image profile                   | not-activated    | operating (1)                        | No              | TBD       |
| Activate w/ load profile                    | not-activated    | operating (2)                        | No              | TBD       |
| Activate w/ image profile (unchanged)       | not-operating    | operating (no reactivation) (3)      | No              | TBD       |
| Activate w/ load pr. (image pr. unchanged)  | not-operating    | operating (no reactivation) (4)      | No              | TBD       |
| Activate w/ image profile (modified)        | not-operating    | operating (reactivation) (5)         | No              | TBD       |
| Activate w/ force (image+load pr. unchanged)| operating        | operating (no react./no reload) (6)  | No              | TBD       |
| Activate w/ force (image pr. modified)      | operating        | operating (react+reload) (7)         | No              | TBD       |
| Activate w/ force (load pr. modified)       | operating        | operating (react+reload) (8)         | No              | TBD       |

(1) Activation parameters are taken from the specified image profile. Due to load-at-activation=True, the LPAR is loaded with load
    parameters taken from the specified image profile (must have same name as LPAR).

(2) Activation parameters are taken from the image profile with same name as the LPAR. Due to load-at-activation=True, the LPAR
    is loaded with load parameters taken from the specified load profile.

(3) No re-activation occurs, since the image activation profile is unchanged. Due to load-at-activation=True, the LPAR is loaded
    with load parameters taken from the specified image profile (must have same name as LPAR).

(4) No re-activation occurs, since the image activation profile is unchanged. Due to load-at-activation=True, the LPAR is loaded
    with load parameters taken from the specified load profile.

(5) The activation state of the LPAR is adjusted to reflect the modified image profile. Due to load-at-activation=True, the LPAR
    is loaded with load parameters taken from the specified image profile (must have same name as LPAR).

(6) Since 'force' is specified, the OS in the LPAR could be shut down. However, because the image and load profiles are unchanged,
    there is no need to reload the LPAR, so the OS is not shut down and keeps on running.

(7) Since 'force' is specified, the OS in the LPAR is shut down. The activation state of the LPAR is adjusted based on the modified
    image profile. Due to load-at-activation=True, the LPAR is loaded with load parameters taken from the image profile with same
    name as the LPAR.

(8) Since 'force' is specified, the OS in the LPAR is shut down. The activation state of the LPAR is adjusted based on the modified
    image profile. Due to load-at-activation=True, the LPAR is loaded with load parameters taken from the image profile with same
    name as the LPAR.

### SSC-type LPAR

Same as Linux-type: Yes?

### ESA390-type LPAR

Same as Linux-type: Yes?
