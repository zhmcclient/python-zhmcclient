# LPAR status, activation and loading

This document attempts to clarify the meaning of the LPAR 'status' property
values and the behavior for LPAR activation and loading w.r.t. the activation
profiles involved and the effects on the 'status' property.

The term "LPAR" refers to logical partitions in CPCs in the classic operational
mode; DPM mode is not described here.

All behaviors and properties are described from a perspective of the WS API
of the HMC.

Status of this document: Draft, with review comments applied as of 2/22.


## Behavior of LPAR activation and loading

This section describes the actual behavior of the "Activate LPAR" and
"Load LPAR" WS-API operations.

### Requirements and facts

* For each LPAR, there needs to be an image profile with the same name as the
  LPAR. That is the only image profile that can be used to activate the LPAR.
  Specifying an image profile with a different name as the LPAR will cause the
  activation to fail.

* There cannot be a load profile with the same name as an image profile
  (i.e. as any LPAR name).

* An image profile contains activation parameters and load parameters.
  A load profile contains only load parameters.

### Behavior of "Activate LPAR" operation

The activation parameters are always taken from the image profile that has the
same name as the LPAR.

The load parameters are taken from an image profile or load profile as follows:

* If the 'activation-profile-name' operation parameter is specified, the
  specified image or load profile is used.

* Otherwise, if the 'next-activation-profile-name' LPAR property is not null,
  the image or load profile specified in that property is used.

* Otherwise, the image profile with the same name as the LPAR is used.

* Note that the load profile named 'DEFAULTLOAD' is not automatically used by
  default; it is only used when specified.

The operation behavior depends on the LPAR status as follows:

* If the LPAR has status 'not-activated', it will be activated and if
  'load-at-activation=True' it will also be loaded.

* If the LPAR has status 'not-operating', the behavior depends on whether a load
  profile or an image profile is used (see above, where load parameters are
  taken from):

  - If an image profile is used, the LPAR will be deactivated and reactivated
    and dependent on the 'load-at-activation' property, it will also be loaded.
    The deactivation happens always and does not dependent on whether the
    activation parameters in the image profile have changed.

  - If a load profile is used, the LPAR remains active and it will just be
    loaded.

    **TBD: Does the loading in this case only happen when 'load-at-activation=True'?**

* If the LPAR has status 'operating' and 'force=False' is specified or
  defaulted, the "Activate LPAR" operation will fail, regardless of whether an
  image or load profile or no profile has been specified.

* If the LPAR has status 'operating' and 'force=True' is specified, the behavior
  depends on whether a load profile or an image profile is used:

  - If an image profile is used, the control program in the LPAR will get the
    shutdown signal so it can perform an orderly shutdown. After the control
    program has stopped, the LPAR will be deactivated and reactivated and
    dependent on the 'load-at-activation' property, it will be loaded. The
    deactivation happens always and does not dependent on whether the activation
    parameters in the image profile have changed.

  - If a load profile is used, the control program in the LPAR will get the
    shutdown signal so it can perform an orderly shutdown. After the control
    program has stopped, the LPAR remains active and will be loaded again.

Notes:

* If a load is performed, the resulting LPAR status will go to 'operating' if
  the loading has succeeded and the control program got started. If the load
  parameters do not specify a valid control program, or if the load parameters
  are not valid for the control program, the LPAR status will go to
  'not-operating'.

### Behavior of "Load LPAR" operation

The load parameters are taken from an image profile or load profile as follows:

* If the 'next-activation-profile-name' LPAR property is not null, the specified
  image or load profile is used.

* Otherwise, the image profile with the same name as the LPAR is used.

* Note that the load profile named 'DEFAULTLOAD' is not automatically used by
  default; it is only used when specified.

The operation behavior depends on the LPAR status as follows:

* If the LPAR has status 'not-activated', the "Load LPAR" operation will fail.

* If the LPAR has status 'not-operating', the LPAR will be loaded with the
  load parameters from the image or load profile that is used (see above, where
  load parameters are taken from).

* If the LPAR has status 'operating' and 'force=False' is specified or
  defaulted, the "Load LPAR" operation will fail.

* If the LPAR has status 'operating' and 'force=True' is specified, the control
  program in the LPAR will get the shutdown signal so it can perform an orderly
  shutdown. After the control program has stopped, the LPAR will be loaded with
  the load parameters from the image or load profile that is used (see above,
  where load parameters are taken from).

Notes:

* If a load is performed, the resulting LPAR status will go to 'operating' if
  the loading has succeeded and the control program got booted. If the load
  parameters do not specify a valid control program, or if the load parameters
  are not valid for the control program, the LPAR status will go to
  'not-operating'.


## Documentation issues

This section lists some issues with the documentation in the z15 HMC WS API
book.

* Description of behavior of the "Activate LPAR" and "Load LPAR" operations:

  The description of the operation behavior in the current documentation does
  not allow understanding the behavior for all the cases described in the
  previous sections.

  The documentation for these operations should be updated accordingly.

* The "Activate LPAR" operation describes its 'activation-profile-name'
  parameter as follows:

      The name of the activation profile to be used for the request. If not
      provided, the request uses the profile name specified in the
      next-activation-profile-name property for the Logical Partition object.

  Issues:

  * This description leaves it open whether the activation profile can be an
    image profile or a load profile. It should be clarified that both types
    of profiles can be specified.

  * The phrase "for the request" is too unspecific, because the activation
    parameters are always taken from the image profile that has the same name
    as the LPAR, and the 'activation-profile-name' parameter only determines
    the image or load profile from which the load parameters are taken.
    That should be clarified in the description.

* The description for the 'status' property of LPAR is:

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

  * The description of "not-operating" is in conflict with the behavior
    of actual systems, which do show "not-operating" for LPARs that are active
    but not loaded. In that case, the CPC is definitely operational. The
    description should be fixed accordingly.

  * The description of "not-activated" is misleading, because in actual
    systems it indicates that the LPAR is inactive. However, the description
    allows for the case that the LPAR is active but not loaded. The description
    should be fixed accordingly.

  * The value "exceptions" implies that the LPAR is in an
    active or loaded state, i.e. not inactive. The description should be amended
    with this information.

  * The value "acceptable" implies that the LPAR is in an
    active or loaded state, i.e. not inactive. The description should be amended
    with this information.

* The 'next-activation-profile-name' property of the LPAR object is described
  as:

      Image activation profile name or load activation profile name to be used
      on the next activate.

  Issues:

  * The phrase "on the next activate" is misleading, because the activation
    parameters are always taken from the image profile that has the same name
    as the LPAR, and the 'next-activation-profile-name' property only determines
    the image or load profile from which the load parameters are taken.
    That should be clarified in the description.


## Verification

This section shows the actual behavior of WS-API operations on LPARs that
affect its status.

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

| LPAR operation                              | Status before    | Expected status after                | Verified    |
|:------------------------------------------- |:---------------- |:------------------------------------ |:----------- |
| Activate w/ image profile                   | not-activated    | not-operating                        | Yes         |
| Activate w/ load profile                    | not-activated    | not-operating                        | No          |
| Activate w/ image profile (unchanged)       | not-operating    | not-operating (no reactivation)      | No          |
| Activate w/ load pr. (image pr. unchanged)  | not-operating    | not-operating (no reactivation)      | No          |
| Activate w/ image profile (modified)        | not-operating    | not-operating (reactivation)         | No          |
| Activate w/ force (image pr. unchanged)     | operating        | not-operating (no reactivation)      | No          |
| Activate w/ force (image pr. modified)      | operating        | not-operating (reactivation)         | No          |
| Load                                        | not-operating    | operating                            | ? (500,263) |
| Load (force)                                | operating        | operating (newly loaded) (8)         | No          |
| Deactivate                                  | not-operating    | not-activated                        | Yes         |
| Deactivate (force)                          | operating        | not-activated                        | No          |
| Stop                                        | not-operating    | not-operating (noop ?)               | Yes         |
| Stop                                        | operating        | ?                                    | No          |
| Start                                       | not-operating    | ?                                    | No          |
| Start                                       | operating        | ?                                    | No          |
| Reset Normal/Clear                          | operating        | ?                                    | No          |
| Reset Normal/Clear                          | not-operating    | ?                                    | No          |

### Linux-type LPAR with auto-loading

Image Profile:
* load-at-activation = True
* ipl-type = ipl-type-standard

LPAR:
* activation-mode = linux

Same as without auto-loading, except that activation is followed by a load:

| LPAR operation                              | Status before    | Expected status after                | Verified    |
|:------------------------------------------- |:---------------- |:------------------------------------ |:----------- |
| Activate w/ image profile                   | not-activated    | operating                            | No          |
| Activate w/ load profile                    | not-activated    | operating                            | No          |
| Activate w/ image profile (unchanged)       | not-operating    | operating (no reactivation)          | No          |
| Activate w/ load pr. (image pr. unchanged)  | not-operating    | operating (no reactivation)          | No          |
| Activate w/ image profile (modified)        | not-operating    | operating (reactivation)             | No          |
| Activate w/ force (image+load pr. unchanged)| operating        | operating (no react./no reload)      | No          |
| Activate w/ force (image pr. modified)      | operating        | operating (react+reload)             | No          |
| Activate w/ force (load pr. modified)       | operating        | operating (react+reload)             | No          |

### SSC-type LPAR

Same as Linux-type: Yes?

### ESA390-type LPAR

Same as Linux-type: Yes?
