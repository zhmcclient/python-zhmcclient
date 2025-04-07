Replaced any use of 'OrderedDict' with the standard Python 'dict', since they
are ordered since Python 3.6. As a result, the representation of resource
properties in 'repr()' methods of zhmcclient resources now uses the standard
dict representation and its properties are no longer sorted. This allowed to
eliminate the dependency to the 'yamlloader' package.
