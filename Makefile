# ------------------------------------------------------------------------------
# Makefile for zhmcclient project
#
# Supported OS platforms for this makefile:
#     Linux (any distro)
#     OS-X
#     Windows with UNIX-like env such as CygWin (with a UNIX-like shell and
#       Python in the UNIX-like env)
#     native Windows (with the native Windows command processor and Python in
#       Windows)
#
# Prerequisites for running this makefile:
#   These commands are used on all supported OS platforms. On native Windows,
#   they may be provided by UNIX-like environments such as CygWin:
#     make (GNU make)
#     python (via PYTHON_CMD, in the active Python environment)
#     pip (via PIP_CMD, in the active Python environment)
#     twine (in the active Python environment)
#   These additional commands are used on Linux, OS-X and on Windows with
#   UNIX-like environments:
#     uname
#     rm, find, xargs, cp
#   These additional commands are used on native Windows:
#     del, copy, rmdir
# ------------------------------------------------------------------------------

# No built-in rules needed:
MAKEFLAGS += --no-builtin-rules
.SUFFIXES:

# Python / Pip commands
ifndef PYTHON_CMD
  PYTHON_CMD := python
endif
ifndef PIP_CMD
  PIP_CMD := pip
endif

# Package level
ifndef PACKAGE_LEVEL
  PACKAGE_LEVEL := latest
endif
ifeq ($(PACKAGE_LEVEL),minimum)
  pip_level_opts := -c minimum-constraints.txt
  pip_level_opts_new :=
else
  ifeq ($(PACKAGE_LEVEL),latest)
    pip_level_opts := --upgrade
    pip_level_opts_new := --upgrade-strategy eager
  else
    $(error Error: Invalid value for PACKAGE_LEVEL variable: $(PACKAGE_LEVEL))
  endif
endif

# Make variables are case sensitive and some native Windows environments have
# ComSpec set instead of COMSPEC.
ifndef COMSPEC
  ifdef ComSpec
    COMSPEC = $(ComSpec)
  endif
endif

# Determine OS platform make runs on.
ifeq ($(OS),Windows_NT)
  ifdef PWD
    PLATFORM := Windows_UNIX
  else
    PLATFORM := Windows_native
    ifdef COMSPEC
      SHELL := $(subst \,/,$(COMSPEC))
    else
      SHELL := cmd.exe
    endif
    .SHELLFLAGS := /c
  endif
else
  # Values: Linux, Darwin
  PLATFORM := $(shell uname -s)
endif

ifeq ($(PLATFORM),Windows_native)
  # Note: The substituted backslashes must be doubled.
  # Remove files (blank-separated list of wildcard path specs)
  RM_FUNC = del /f /q $(subst /,\\,$(1))
  # Remove files recursively (single wildcard path spec)
  RM_R_FUNC = del /f /q /s $(subst /,\\,$(1))
  # Remove directories (blank-separated list of wildcard path specs)
  RMDIR_FUNC = rmdir /q /s $(subst /,\\,$(1))
  # Remove directories recursively (single wildcard path spec)
  RMDIR_R_FUNC = rmdir /q /s $(subst /,\\,$(1))
  # Copy a file, preserving the modified date
  CP_FUNC = copy /y $(subst /,\\,$(1)) $(subst /,\\,$(2))
  ENV = set
  WHICH = where
else
  RM_FUNC = rm -f $(1)
  RM_R_FUNC = find . -type f -name '$(1)' -delete
  RMDIR_FUNC = rm -rf $(1)
  RMDIR_R_FUNC = find . -type d -name '$(1)' | xargs -n 1 rm -rf
  CP_FUNC = cp -r $(1) $(2)
  ENV = env | sort
  WHICH = which
endif

# Default path names of HMC inventory and vault files used for end2end tests.
# Keep in sync with zhmcclient/testutils/_hmc_definitions.py
default_testinventory := $HOME/.zhmc_inventory.yaml
default_testvault := $HOME/.zhmc_vault.yaml

# Default group name or HMC nickname in HMC inventory file to test against.
# Keep in sync with zhmcclient/testutils/_hmc_definitions.py
default_testhmc := default

# Name of this Python package (top-level Python namespace + Pypi package name)
package_name := zhmcclient
mock_package_name := zhmcclient_mock

# Package version (full version, including any pre-release suffixes, e.g. "0.1.0.dev1")
# Note: The package version is defined in zhmcclient/_version.py.
package_version := $(shell $(PYTHON_CMD) setup.py --version)

# Python versions
python_version := $(shell $(PYTHON_CMD) tools/python_version.py 3)
python_mn_version := $(shell $(PYTHON_CMD) tools/python_version.py 2)
python_m_version := $(shell $(PYTHON_CMD) tools/python_version.py 1)
pymn := py$(python_mn_version)

# Directory for the generated distribution files
dist_dir := dist

# Distribution archives (as built by 'build' tool)
bdist_file := $(dist_dir)/$(package_name)-$(package_version)-py2.py3-none-any.whl
sdist_file := $(dist_dir)/$(package_name)-$(package_version).tar.gz

dist_files := $(bdist_file) $(sdist_file)

# Source files in the packages
package_py_files := \
    $(wildcard $(package_name)/*.py) \
    $(wildcard $(package_name)/*/*.py) \
    $(wildcard $(mock_package_name)/*.py) \
    $(wildcard $(mock_package_name)/*/*.py) \

# Directory for generated API documentation
doc_build_dir := build_doc

# Directory where Sphinx conf.py is located
doc_conf_dir := docs

# Documentation generator command
doc_cmd := sphinx-build
doc_opts := -v -d $(doc_build_dir)/doctrees -c $(doc_conf_dir) .

# Dependents for Sphinx documentation build
doc_dependent_files := \
    $(doc_conf_dir)/conf.py \
    $(wildcard $(doc_conf_dir)/*.rst) \
    $(wildcard $(doc_conf_dir)/notebooks/*.ipynb) \
    $(package_py_files) \

# Directory with test source files
test_dir := tests

# Source files with test code
test_unit_py_files := \
    $(wildcard $(test_dir)/unit/*.py) \
    $(wildcard $(test_dir)/unit/*/*.py) \
    $(wildcard $(test_dir)/unit/*/*/*.py) \

test_end2end_py_files := \
    $(wildcard $(test_dir)/end2end/*.py) \
    $(wildcard $(test_dir)/end2end/*/*.py) \
    $(wildcard $(test_dir)/end2end/*/*/*.py) \

test_common_py_files := \
    $(wildcard $(test_dir)/common/*.py) \
    $(wildcard $(test_dir)/common/*/*.py) \
    $(wildcard $(test_dir)/common/*/*/*.py) \

# Determine whether py.test has the --no-print-logs option.
pytest_no_log_opt := $(shell py.test --help 2>/dev/null |grep '\--no-print-logs' >/dev/null; if [ $$? -eq 0 ]; then echo '--no-print-logs'; else echo ''; fi)

# Flake8 config file
flake8_rc_file := .flake8

# PyLint config file
pylint_rc_file := .pylintrc

# PyLint additional options
pylint_opts := --disable=fixme

# Safety policy file
safety_policy_file := .safety-policy.yml

# Source files for check (with PyLint and Flake8)
check_py_files := \
    setup.py \
    $(package_py_files) \
    $(test_unit_py_files) \
    $(test_end2end_py_files) \
    $(test_common_py_files) \
    $(doc_conf_dir)/conf.py \
    $(wildcard docs/notebooks/*.py) \

# Packages whose dependencies are checked using pip-missing-reqs
ifeq ($(python_m_version),2)
  check_reqs_packages := pip_check_reqs virtualenv tox pipdeptree build pytest coverage coveralls flake8 pylint sphinx twine jupyter notebook
else
ifeq ($(python_mn_version),3.5)
  check_reqs_packages := pip_check_reqs virtualenv tox pipdeptree build pytest coverage coveralls flake8 pylint sphinx twine jupyter notebook
else
  check_reqs_packages := pip_check_reqs virtualenv tox pipdeptree build pytest coverage coveralls flake8 pylint sphinx twine jupyter notebook safety
endif
endif

ifdef TESTCASES
  pytest_opts := $(TESTOPTS) -k "$(TESTCASES)"
else
  pytest_opts := $(TESTOPTS)
endif

pytest_cov_opts := --cov $(package_name) --cov $(mock_package_name) --cov-config .coveragerc --cov-report=html
pytest_cov_files := .coveragerc
pytest_e2e_cov_opts := --cov $(package_name) --cov $(mock_package_name) --cov-config .coveragerc.end2end --cov-report=html
pytest_e2e_cov_files := .coveragerc.end2end

# Files to be built
build_files := $(bdist_file) $(sdist_file)

# Files the distribution archive depends upon.
# This is also used for 'include' statements in MANIFEST.in.
# Wildcards can be used directly (i.e. without wildcard function).
dist_included_files := \
    setup.py \
    LICENSE \
    README.rst \
    requirements.txt \
    extra-testutils-requirements.txt \
    $(package_py_files) \

# No built-in rules needed:
.SUFFIXES:

.PHONY: help
help:
	@echo "Makefile for $(package_name) project"
	@echo "Package version will be: $(package_version)"
	@echo ""
	@echo "Make targets:"
	@echo "  install    - Install package in active Python environment"
	@echo "  develop    - Prepare the development environment by installing prerequisites"
	@echo "  check_reqs - Perform missing dependency checks"
	@echo "  check      - Run Flake8 on sources"
	@echo "  pylint     - Run PyLint on sources"
	@echo "  safety     - Run safety on sources"
	@echo "  test       - Run unit tests (and test coverage)"
	@echo "  installtest - Run install tests"
	@echo "  build      - Build the distribution files in: $(dist_dir)"
	@echo "  builddoc   - Build documentation in: $(doc_build_dir)"
	@echo "  all        - Do all of the above"
	@echo "  end2end    - Run end2end tests (and test coverage)"
	@echo "  end2end_show - Show HMCs defined for end2end tests"
	@echo "  uninstall  - Uninstall package from active Python environment"
	@echo "  upload     - Upload the distribution files to PyPI"
	@echo "  clean      - Remove any temporary files"
	@echo "  clobber    - Remove any build products"
	@echo "  platform   - Display the information about the platform as seen by make"
	@echo "  debuginfo  - Display the debug information for the package"
	@echo "  env        - Display the environment as seen by make"
	@echo ""
	@echo "Environment variables:"
	@echo "  TESTCASES=... - Testcase filter for pytest -k"
	@echo "  TESTOPTS=... - Options for pytest"
	@echo "  TESTHMC=... - HMC group or host name in HMC inventory file to be used in end2end tests. Default: $(default_testhmc)"
	@echo "  TESTINVENTORY=... - Path name of HMC inventory file used in end2end tests. Default: $(default_testinventory)"
	@echo "  TESTVAULT=... - Path name of HMC vault file used in end2end tests. Default: $(default_testvault)"
	@echo "  TESTRESOURCES=... - The resources to test with in end2end tests, as follows:"
	@echo "      random - one random choice from the complete list of resources (default)"
	@echo "      all - the complete list of resources"
	@echo "      <pattern> - the resources with names matching the regexp pattern"
	@echo "  TESTLOGFILE=... - Enable logging in end2end tests to that file. Default: no logging"
	@echo "  PACKAGE_LEVEL - Package level to be used for installing dependent Python"
	@echo "      packages in 'install' and 'develop' targets:"
	@echo "        latest - Latest package versions available on Pypi"
	@echo "        minimum - A minimum version as defined in minimum-constraints.txt"
	@echo "      Optional, defaults to 'latest'."
	@echo "  PYTHON_CMD=... - Name of python command. Default: python"
	@echo "  PIP_CMD=... - Name of pip command. Default: pip"

.PHONY: platform
platform:
	@echo "Makefile: Platform information as seen by make:"
	@echo "Platform: $(PLATFORM)"
	@echo "Shell used for commands: $(SHELL)"
	@echo "Shell flags: $(.SHELLFLAGS)"
	@echo "Make version: $(MAKE_VERSION)"
	@echo "Python command name: $(PYTHON_CMD)"
	@echo "Python command location: $(shell $(WHICH) $(PYTHON_CMD))"
	@echo "Python version: $(python_version)"
	@echo "Pip command name: $(PIP_CMD)"
	@echo "Pip command location: $(shell $(WHICH) $(PIP_CMD))"
	@echo "$(package_name) package version: $(package_version)"

.PHONY: debuginfo
debuginfo:
	@echo "Makefile: Debug information:"
	$(PYTHON_CMD) -c "import $(package_name); print($(package_name).debuginfo())"

.PHONY: pip_list
pip_list:
	@echo "Makefile: Python packages as seen by make:"
	$(PIP_CMD) list

.PHONY: env
env:
	@echo "Makefile: Environment variables as seen by make:"
	$(ENV)

.PHONY: _check_version
_check_version:
ifeq (,$(package_version))
	$(error Package version could not be determined)
endif

pip_upgrade_$(pymn).done: Makefile
	-$(call RM_FUNC,$@)
	bash -c 'pv=$$($(PIP_CMD) --version); if [[ $$pv =~ (^pip [1-8]\..*) ]]; then $(PYTHON_CMD) -m pip install pip==9.0.1; fi'
	@echo "Installing/upgrading pip, setuptools and wheel with PACKAGE_LEVEL=$(PACKAGE_LEVEL)"
	$(PYTHON_CMD) -m pip install $(pip_level_opts) pip setuptools wheel
	echo "done" >$@

.PHONY: develop
develop: develop_$(pymn).done
	@echo "Makefile: $@ done."

develop_$(pymn).done: pip_upgrade_$(pymn).done install_$(pymn).done dev-requirements.txt requirements.txt
	-$(call RM_FUNC,$@)
	@echo 'Installing development requirements with PACKAGE_LEVEL=$(PACKAGE_LEVEL)'
	$(PYTHON_CMD) -m pip install $(pip_level_opts) $(pip_level_opts_new) -r dev-requirements.txt
	echo "done" >$@

.PHONY: build
build: $(build_files)
	@echo "Makefile: $@ done."

.PHONY: builddoc
builddoc: html
	@echo "Makefile: $@ done."

.PHONY: html
html: $(doc_build_dir)/html/docs/index.html
	@echo "Makefile: $@ done."

$(doc_build_dir)/html/docs/index.html: Makefile develop_$(pymn).done $(doc_dependent_files)
	-$(call RM_FUNC,$@)
	$(doc_cmd) -b html $(doc_opts) $(doc_build_dir)/html
	@echo "Done: Created the HTML pages with top level file: $@"

.PHONY: pdf
pdf: Makefile develop_$(pymn).done $(doc_dependent_files)
	$(doc_cmd) -b latex $(doc_opts) $(doc_build_dir)/pdf
	@echo "Running LaTeX files through pdflatex..."
	$(MAKE) -C $(doc_build_dir)/pdf all-pdf
	@echo "Done: Created the PDF files in: $(doc_build_dir)/pdf/"
	@echo "Makefile: $@ done."

.PHONY: man
man: Makefile develop_$(pymn).done $(doc_dependent_files)
	$(doc_cmd) -b man $(doc_opts) $(doc_build_dir)/man
	@echo "Done: Created the manual pages in: $(doc_build_dir)/man/"
	@echo "Makefile: $@ done."

.PHONY: docchanges
docchanges:
	$(doc_cmd) -b changes $(doc_opts) $(doc_build_dir)/changes
	@echo
	@echo "Done: Created the doc changes overview file in: $(doc_build_dir)/changes/"
	@echo "Makefile: $@ done."

.PHONY: doclinkcheck
doclinkcheck:
	$(doc_cmd) -b linkcheck $(doc_opts) $(doc_build_dir)/linkcheck
	@echo
	@echo "Done: Look for any errors in the above output or in: $(doc_build_dir)/linkcheck/output.txt"
	@echo "Makefile: $@ done."

.PHONY: doccoverage
doccoverage:
	$(doc_cmd) -b coverage $(doc_opts) $(doc_build_dir)/coverage
	@echo "Done: Created the doc coverage results in: $(doc_build_dir)/coverage/python.txt"
	@echo "Makefile: $@ done."

.PHONY: check
check: flake8_$(pymn).done
	@echo "Makefile: $@ done."

.PHONY: pylint
pylint: pylint_$(pymn).done
	@echo "Makefile: $@ done."

.PHONY: safety
safety: safety_$(pymn).done
	@echo "Makefile: $@ done."

.PHONY: install
install: install_$(pymn).done
	@echo "Makefile: $@ done."

install_$(pymn).done: pip_upgrade_$(pymn).done requirements.txt extra-testutils-requirements.txt
	-$(call RM_FUNC,$@)
	@echo "Installing $(package_name) (editable) and runtime reqs with PACKAGE_LEVEL=$(PACKAGE_LEVEL)"
	$(PYTHON_CMD) -m pip install $(pip_level_opts) $(pip_level_opts_new) -e .
	$(PYTHON_CMD) -c "import $(package_name); print('ok')"
	$(PYTHON_CMD) -c "import $(mock_package_name); print('ok')"
	$(PYTHON_CMD) -m pip install $(pip_level_opts) $(pip_level_opts_new) -e .[testutils]
	$(PYTHON_CMD) -c "import $(package_name).testutils; print('ok')"
	echo "done" >$@

.PHONY: uninstall
uninstall:
	bash -c '$(PIP_CMD) show $(package_name) >/dev/null; if [ $$? -eq 0 ]; then $(PIP_CMD) uninstall -y $(package_name); fi'
	@echo "Makefile: $@ done."

.PHONY: clobber
clobber: clean
	-$(call RM_FUNC,*.done $(dist_files))
	-$(call RMDIR_FUNC,$(doc_build_dir) htmlcov .tox)
	@echo "Makefile: $@ done."

.PHONY: clean
clean:
	-$(call RM_R_FUNC,*.pyc)
	-$(call RM_R_FUNC,*.tmp)
	-$(call RM_R_FUNC,tmp_*)
	-$(call RMDIR_R_FUNC,__pycache__)
	-$(call RM_FUNC,MANIFEST MANIFEST.in AUTHORS ChangeLog .coverage)
	-$(call RMDIR_FUNC,build .cache $(package_name).egg-info .eggs)
	@echo "Makefile: $@ done."

.PHONY: all
all: install develop check_reqs check pylint test installtest build builddoc
	@echo "Makefile: $@ done."

.PHONY: upload
upload: _check_version uninstall $(dist_files)
ifeq (,$(findstring .dev,$(package_version)))
	@echo "==> This will upload $(package_name) version $(package_version) to PyPI!"
	@echo -n '==> Continue? [yN] '
	@bash -c 'read answer; if [ "$$answer" != "y" ]; then echo "Aborted."; false; fi'
	twine upload $(dist_files)
	@echo "Done: Uploaded $(package_name) version to PyPI: $(package_version)"
	@echo "Makefile: $@ done."
else
	@echo "Error: A development version $(package_version) of $(package_name) cannot be uploaded to PyPI!"
	@false
endif

# Note: distutils depends on the right files specified in MANIFEST.in, even when
# they are already specified e.g. in 'package_data' in setup.py.
# We generate the MANIFEST.in file automatically, to have a single point of
# control (this Makefile) for what gets into the distribution archive.
MANIFEST.in: Makefile $(dist_included_files)
	@echo "Makefile: Creating the manifest input file"
	echo "# MANIFEST.in file generated by Makefile - DO NOT EDIT!!" >$@
ifeq ($(PLATFORM),Windows_native)
	for %%f in ($(dist_included_files)) do (echo include %%f >>$@)
else
	echo "$(dist_included_files)" | xargs -n 1 echo include >>$@
endif
	@echo "Makefile: Done creating the manifest input file: $@"

# Distribution archives.
# Note: Deleting MANIFEST causes distutils (setup.py) to read MANIFEST.in and to
# regenerate MANIFEST. Otherwise, changes in MANIFEST.in will not be used.
# Note: Deleting build is a safeguard against picking up partial build products
# which can lead to incorrect hashbangs in scripts in wheel archives.
$(bdist_file) $(sdist_file): Makefile MANIFEST.in $(dist_included_files)
	-$(call RM_FUNC,MANIFEST)
	-$(call RMDIR_FUNC,build $(package_name).egg-info-INFO .eggs)
	$(PYTHON_CMD) -m build --outdir $(dist_dir)

pylint_$(pymn).done: develop_$(pymn).done Makefile $(pylint_rc_file) $(check_py_files)
ifeq ($(python_m_version),2)
	@echo "Makefile: Warning: Skipping Pylint on Python $(python_version)" >&2
else
	@echo "Makefile: Running Pylint"
	-$(call RM_FUNC,$@)
	pylint $(pylint_opts) --rcfile=$(pylint_rc_file) --output-format=text $(check_py_files)
	echo "done" >$@
	@echo "Makefile: Done running Pylint"
endif

safety_$(pymn).done: develop_$(pymn).done Makefile $(safety_policy_file) minimum-constraints.txt
ifeq ($(python_m_version),2)
	@echo "Makefile: Warning: Skipping Safety on Python $(python_version)" >&2
else
ifeq ($(python_mn_version),3.5)
	@echo "Makefile: Warning: Skipping Safety on Python $(python_version)" >&2
else
	@echo "Makefile: Running Safety"
	-$(call RM_FUNC,$@)
	safety check --policy-file $(safety_policy_file) -r minimum-constraints.txt --full-report
	echo "done" >$@
	@echo "Makefile: Done running Safety"
endif
endif

flake8_$(pymn).done: develop_$(pymn).done Makefile $(flake8_rc_file) $(check_py_files)
	-$(call RM_FUNC,$@)
	flake8 $(check_py_files)
	echo "done" >$@

.PHONY: check_reqs
check_reqs: develop_$(pymn).done minimum-constraints.txt requirements.txt extra-testutils-requirements.txt
ifeq ($(python_m_version),2)
	@echo "Makefile: Warning: Skipping the checking of missing dependencies on Python $(python_version)" >&2
else
	@echo "Makefile: Checking missing dependencies of this package"
	bash -c "cat requirements.txt extra-testutils-requirements.txt >tmp_requirements.txt; pip-missing-reqs $(package_name) --requirements-file=tmp_requirements.txt"
	-$(call RM_FUNC,tmp_requirements.txt)
	pip-missing-reqs $(package_name) --requirements-file=minimum-constraints.txt
	@echo "Makefile: Done checking missing dependencies of this package"
ifeq ($(PLATFORM),Windows_native)
# Reason for skipping on Windows is https://github.com/r1chardj0n3s/pip-check-reqs/issues/67
	@echo "Makefile: Warning: Skipping the checking of missing dependencies of site-packages directory on native Windows" >&2
else
	@echo "Makefile: Checking missing dependencies of some development packages in our minimum versions"
	@rc=0; for pkg in $(check_reqs_packages); do dir=$$($(PYTHON_CMD) -c "import $${pkg} as m,os; dm=os.path.dirname(m.__file__); d=dm if not dm.endswith('site-packages') else m.__file__; print(d)"); cmd="pip-missing-reqs $${dir} --requirements-file=minimum-constraints.txt"; echo $${cmd}; $${cmd}; rc=$$(expr $${rc} + $${?}); done; exit $${rc}
	@echo "Makefile: Done checking missing dependencies of some development packages in our minimum versions"
endif
endif
	@echo "Makefile: $@ done."

.PHONY: test
test: Makefile develop_$(pymn).done $(package_py_files) $(test_unit_py_files) $(test_common_py_files) $(pytest_cov_files)
	-$(call RMDIR_R_FUNC,htmlcov)
	py.test --color=yes $(pytest_no_log_opt) -s $(test_dir)/unit $(pytest_cov_opts) $(pytest_opts)
	@echo "Makefile: $@ done."

.PHONY: installtest
installtest: $(bdist_file) $(sdist_file) $(test_dir)/installtest/test_install.sh
	@echo "Makefile: Running install tests"
ifeq ($(PLATFORM),Windows_native)
	@echo "Makefile: Warning: Skipping install test on native Windows" >&2
else
	$(test_dir)/installtest/test_install.sh $(bdist_file) $(sdist_file) $(PYTHON_CMD)
endif
	@echo "Makefile: Done running install tests"

.PHONY:	end2end
end2end: Makefile develop_$(pymn).done $(package_py_files) $(test_end2end_py_files) $(test_common_py_files) $(pytest_e2e_cov_files)
	-$(call RMDIR_R_FUNC,htmlcov.end2end)
	bash -c "TESTEND2END_LOAD=true py.test --color=yes $(pytest_no_log_opt) -v -s $(test_dir)/end2end $(pytest_e2e_cov_opts) $(pytest_opts)"
	@echo "Makefile: $@ done."

.PHONY:	end2end_show
end2end_show:
	bash -c "TESTEND2END_LOAD=true $(PYTHON_CMD) -c 'from zhmcclient.testutils import print_hmc_definitions; print_hmc_definitions()'"
