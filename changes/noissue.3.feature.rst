Increased the timeout for HMC operations that is used in end2end tests, from
300 sec to 1800 sec. Note that this does not change the default timeout for
users of the zhmcclient library, which continues to be 3600 sec.
