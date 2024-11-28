Fixed that all password-like properties are no longer written in clear text to
the Python loggers "zhmcclient.api" and "zhmcclient.hmc", but are now blanked
out. Previously, that was done only for the "zhmcclient.hmc" logger for creation
and update of HMC users.
