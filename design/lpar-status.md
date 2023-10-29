# LPAR status, activation and loading

This document attempts to clarify the meaning of the LPAR 'status' property
values and the behavior for LPAR activation and loading w.r.t. the activation
profiles involved and the effects on the 'status' property.

The term "LPAR" refers to logical partitions in CPCs in the classic operational
mode; DPM mode is not described here.

All behaviors and properties are described from a perspective of the WS API
of the HMC.

Last updated: 2023-10-30


## Behavior of LPAR activation and loading

This section describes the actual behavior of the "Activate Logical Partition"
and "Load Logical Partition" WS-API operations.

Note: The "Load" WS-API operation introduced with HMC 2.16 is not covered yet.

### Requirements and facts

* For each LPAR, there needs to be an image profile with the same name as the
  LPAR. That is the only image profile that can be used to activate the LPAR.
  Specifying an image profile with a different name as the LPAR will cause the
  activation to fail.

* There cannot be a load profile with the same name as an image profile
  (i.e. as any LPAR name).

* An image profile contains activation parameters and load parameters.
  A load profile contains only load parameters.

### Behavior of "Activate Logical Partition" operation

If an image profile is specified in any way, it always must have the same name
as the LPAR. Therefore, the activation parameters are always taken from the
image profile that has the same name as the LPAR.

The load parameters (for an auto-load) can be taken from the image profile or
from a load profile, and since HMC 2.16, also from the "Activate Logical
Partition" operation parameters. Note that the `last-used-...` properties
of the LPAR object are never used for a load performed as part of the
"Activate Logical Partition" operation.

The following table shows whether activation or load happens and where the
parameters for the load come from, for all valid combinations of the relevant
operation parameters and profile & LPAR properties.

Any other combinations than those listed in the table are invalid and will
cause the "Activate Logical Partition" operation to fail.

Note: The influence of the LPAR 'group-uri' property is ignored for now (see
question 1, below).

The meaning of the columns is described below the table.

| AM         | LT (2.16)    | APN     | NAPN  | LAA   | Force | Status        | Activation | Load    | Load parameters |
|:---------- |:------------ |:------- |:----- |:----- |:----- |:------------- |:---------- |:------- |:--------------- |
| ssc/zaware | none/omitted | image   | any   | any   | any   | not-activated | activate   | load    | N/A (internal)  |
| ssc/zaware | none/omitted | image   | any   | any   | True  | operating     | reactivate | reload  | N/A (internal)  |
| ssc/zaware | none/omitted | omitted | image | any   | any   | not-activated | activate   | load    | N/A (internal)  |
| ssc/zaware | none/omitted | omitted | image | any   | True  | operating     | reactivate | reload  | N/A (internal)  |
| other      | none/omitted | image   | any   | False | any   | not-activated | activate   | no load | N/A (no load)   |
| other      | none/omitted | image   | any   | False | any   | not-operating | reactivate | no load | N/A (no load)   |
| other      | none/omitted | image   | any   | False | True  | operating     | reactivate | no load | N/A (no load)   |
| other      | none/omitted | image   | any   | True  | any   | not-activated | activate   | load    | image profile   |
| other      | none/omitted | image   | any   | True  | any   | not-operating | reactivate | load    | image profile   |
| other      | none/omitted | image   | any   | True  | True  | operating     | reactivate | load    | image profile   |
| other      | none/omitted | omitted | image | False | any   | not-activated | activate   | no load | N/A (no load)   |
| other      | none/omitted | omitted | image | False | any   | not-operating | reactivate | no load | N/A (no load)   |
| other      | none/omitted | omitted | image | False | True  | operating     | reactivate | no load | N/A (no load)   |
| other      | none/omitted | omitted | image | True  | any   | not-activated | activate   | load    | image profile   |
| other      | none/omitted | omitted | image | True  | any   | not-operating | reactivate | load    | image profile   |
| other      | none/omitted | omitted | image | True  | True  | operating     | reactivate | reload  | image profile   |
| other      | none/omitted | load    | any   | any   | any   | not-activated | activate   | load    | load profile    |
| other      | none/omitted | load    | any   | any   | any   | not-operating | no change  | load    | load profile    |
| other      | none/omitted | load    | any   | any   | True  | operating     | no change  | reload  | load profile    |
| other      | none/omitted | omitted | load  | any   | any   | not-activated | activate   | load    | load profile    |
| other      | none/omitted | omitted | load  | any   | any   | not-operating | no change  | load    | load profile    |
| other      | none/omitted | omitted | load  | any   | True  | operating     | no change  | reload  | load profile    |
| other      | other        | any     | any   | any   | any   | not-activated | activate   | load    | operation parms |
| other      | other        | any     | any   | any   | any   | not-operating | no change  | load    | operation parms |
| other      | other        | any     | any   | any   | True  | operating     | no change  | reload  | operation parms |

Columns:

* AM = `activation-mode` property of the Image Activation Profile object
* LT (2.16) = `load-type` parameter of the "Activate Logical Partition" operation
  (requires HMC>=2.16, and HMC<=2.15 behaves is if it was omitted)
* LAA = `load-at-activation` property of the Image Activation Profile object
* APN = `activation-profile-name` parameter of the "Activate Logical Partition" operation
* NAPN = `next-activation-profile-name` property of the LPAR object
* Force = `force` parameter of the "Activate Logical Partition" operation
* Status = `status` property of the LPAR object before the operation
* Activation = what happens related to activation when the activation operation
  is performed
* Load = what happens related to load when the activation operation is performed
* Load parameters = where are the parameters for the load taken from

Values:

* omitted = this optional operation parameter has not been provided
* other = any other value than those in the table rows above
* any = the property or parameter can have any valid value and is not relevant
  for this case

Some more notable details about some of these cases:

* If the LPAR has status 'not-operating', the activation behavior depends on
  whether a load profile or an image profile is used:

  - If an image profile is used, the LPAR will be deactivated and reactivated
    (and possibly loaded).
    The deactivation happens always and does not dependent on whether the
    activation parameters in the image profile have changed.

  - If a load profile is used, the LPAR remains active and it will just be
    loaded.

* If the LPAR has status 'operating' and 'force=True' is specified, the behavior
  depends on whether a load profile or an image profile is used:

  - If an image profile is used, the control program in the LPAR will get the
    shutdown signal so it can perform an orderly shutdown. After the control
    program has stopped, the LPAR will be deactivated and reactivated (and
    possibly loaded). The deactivation happens always and does not dependent
    on whether the activation parameters in the image profile have changed.

  - If a load profile is used, the control program in the LPAR will get the
    shutdown signal so it can perform an orderly shutdown. After the control
    program has stopped, the LPAR remains active and will be loaded again.

* If a load is performed, the resulting LPAR status will go to 'operating' if
  the loading has succeeded and the control program got started. If the load
  parameters do not specify a valid control program, or if the load parameters
  are not valid for the control program, the LPAR status will go to
  'not-operating'.

### Behavior of "Load Logical Partition" operation

The load parameters are taken from an image profile or load profile as follows:

* If the 'next-activation-profile-name' LPAR property is not null, the specified
  image or load profile is used.

* Otherwise, the image profile with the same name as the LPAR is used.

* Note that the load profile named 'DEFAULTLOAD' is not automatically used by
  default; it is only used when specified.

The operation behavior depends on the LPAR status as follows:

* If the LPAR has status 'not-activated', the "Load Logical Partition" operation
  will fail.

* If the LPAR has status 'not-operating', the LPAR will be loaded with the
  load parameters from the image or load profile that is used (see above, where
  load parameters are taken from).

* If the LPAR has status 'operating' and 'force=False' is specified or
  defaulted, the "Load Logical Partition" operation will fail.

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

* Description of behavior of the "Activate Logical Partition" and "Load Logical
  Partition" operations:

  The description of the operation behavior in the current documentation does
  not allow understanding the behavior for all the cases described in the
  previous sections.

  The documentation for these operations should be updated accordingly.

* The "Activate Logical Partition" operation describes its
  'activation-profile-name' parameter as follows:

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


## Questions

1. LPAR 'group-uri' and 'next-activation-profile-name' properties

   The 'next-activation-profile-name' property is defined to be writeable,
   which normally means a value written to the property sticks and is returned
   when the LPAR properties are retrieved.

   However, the property description includes this statement:

   "The 'group-uri' query parameter can be used on a 'Get Logical Partition
   Properties' operation to specify the object URI of the Custom Group object
   used for determining the next activation profile name to be used. If not
   specified, the system-defined Logical Partition group is used for this
   determination."

   Questions:

   - Does the specification of a group-uri query parameter on a Get Logical
     Partition Properties operation influence the 'next-activation-profile-name'
     property that is returned?

   - If so, what does it mean for the 'next-activation-profile-name' property
     to be writeable?

   - What is the "system-defined Logical Partition group"?

2. 'load-type' parameter of activate operation for SSC/zAware partitions

   The new 'load-type' parameter of the "Activate Logical Partition" operation
   in HMC>=2.16 is silent about whether it can be used for LPARs whose
   image activation profile specifies 'activation-mode' as 'ssc' or 'zaware'.

   Answer: it cannot be used, and using it will fail with reason code 306.

3. Is it possible that the 'next-activation-profile-name' LPAR property does not
   specify an activation profile, and how is that done? Note that its
   description requires a string that is at least one character long.
