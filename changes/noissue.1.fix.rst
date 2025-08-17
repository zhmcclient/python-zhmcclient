Dev: Fixed issue where the package version used for distribution archive file
names were generated inconsistently between setuptools_scm (used in Makefile)
and the 'build' module, by using no build isolation ('--no-isolation' option
of the 'build' module) and increasing the minimum version of 'setuptools-scm'
to 9.2.0, which fixes a number of version related issues.
