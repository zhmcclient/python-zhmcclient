Mock: Consolidated the different assumptions in the zhmcclient mock support and
the end2end testcases regarding whether the implemented behavior depends on the
mocked HMC or CPC generation (e.g. support or not support the 'properties'
query parameter on some List operations). Now, the zhmcclient mock support
always implements only the behavior of the latest HMC / CPC generation.
