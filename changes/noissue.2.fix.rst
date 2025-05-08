Added a dependency to the 'idna' package even though that is used only by the
requests package, to ensure that users of zhmcclient use idna>=3.7 to fix an
issue.
