Added optional parameters to the :func:`zhmcclient.testutils.setup_hmc_session`
function: 'rt_config' allows to override the default retry/timeout config for
the HMC session; 'skip_on_failure' allows to select between pytest skipping and
raising exceptions if the HMC session cannot be established.
