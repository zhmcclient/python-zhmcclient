Dev: Fixed the dependencies in the Makefile: Because the package is no longer
installed in edit mode, the Python source files now needed to be added to
the dependency list of the 'install' target. Also, 'install' is no longer
a dependency of 'develop', because none of the targets that need 'develop'
need the package to be installed. Added Makefile as a dependent on rules
that produce files.
