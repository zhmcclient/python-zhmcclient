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
#     git
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
  pip_level_opts := -c minimum-constraints-develop.txt -c minimum-constraints-install.txt
  pip_level_opts_new :=
else
  ifeq ($(PACKAGE_LEVEL),latest)
    pip_level_opts := --upgrade
    pip_level_opts_new := --upgrade-strategy eager
  else
    $(error Error: Invalid value for PACKAGE_LEVEL variable: $(PACKAGE_LEVEL))
  endif
endif

# Run type (normal, scheduled, release, local)
ifndef RUN_TYPE
  RUN_TYPE := local
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
  DEV_NULL = nul
else
  RM_FUNC = rm -f $(1)
  RM_R_FUNC = find . -type f -name '$(1)' -delete
  RMDIR_FUNC = rm -rf $(1)
  RMDIR_R_FUNC = find . -type d -name '$(1)' | xargs -n 1 rm -rf
  CP_FUNC = cp -r $(1) $(2)
  ENV = env | sort
  WHICH = which -a
  DEV_NULL = /dev/null
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

# Package version (e.g. "1.8.0a1.dev10+gd013028e" during development, or "1.8.0"
# when releasing).
# Note: The package version is automatically calculated by setuptools_scm based
# on the most recent tag in the commit history, increasing the least significant
# version indicator by 1.
package_version := $(shell $(PYTHON_CMD) -m setuptools_scm)

# The version file is recreated by setuptools-scm on every build, so it is
# excluuded from git, and also from some dependency lists.
version_file := $(package_name)/_version_scm.py

# Python versions
python_version := $(shell $(PYTHON_CMD) tools/python_version.py 3)
python_mn_version := $(shell $(PYTHON_CMD) tools/python_version.py 2)
python_m_version := $(shell $(PYTHON_CMD) tools/python_version.py 1)
pymn := py$(python_mn_version)

# Directory for the generated distribution files
dist_dir := dist

# Distribution archives (as built by 'build' tool)
bdist_file := $(dist_dir)/$(package_name)-$(package_version)-py3-none-any.whl
sdist_file := $(dist_dir)/$(package_name)-$(package_version).tar.gz

dist_files := $(bdist_file) $(sdist_file)

# Source files in the packages, excluding the $(version_file)
package_py_files := \
    $(filter-out $(version_file), $(wildcard $(package_name)/*.py)) \
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
    $(version_file) \
    examples/example_hmc_inventory.yaml \
    examples/example_hmc_vault.yaml \

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

# Directory for .done files
done_dir := done

# Determine whether pytest has the --no-print-logs option.
pytest_no_log_opt := $(shell pytest --help 2>/dev/null |grep '\--no-print-logs' >/dev/null; if [ $$? -eq 0 ]; then echo '--no-print-logs'; else echo ''; fi)

# Flake8 config file
flake8_rc_file := .flake8

# Ruff config file
ruff_rc_file := .ruff.toml

# PyLint config file
pylint_rc_file := .pylintrc

# PyLint additional options
pylint_opts := --disable=fixme

# Safety policy file (for packages needed for installation)
safety_install_policy_file := .safety-policy-install.yml
safety_develop_policy_file := .safety-policy-develop.yml

# Bandit config file
bandit_rc_file := .bandit.toml

# Source files for check (with PyLint and Flake8)
check_py_files := \
    $(package_py_files) \
    $(test_unit_py_files) \
    $(test_end2end_py_files) \
    $(test_common_py_files) \
    $(doc_conf_dir)/conf.py \
    $(wildcard docs/notebooks/*.py) \

# Packages whose dependencies are checked using pip-missing-reqs
check_reqs_packages := pip_check_reqs virtualenv tox pipdeptree build pytest coverage coveralls flake8 ruff pylint jupyter notebook safety bandit towncrier sphinx

ifdef TESTCASES
  pytest_opts := $(TESTOPTS) -k "$(TESTCASES)"
else
  pytest_opts := $(TESTOPTS)
endif

pytest_cov_opts := --cov $(package_name) --cov $(mock_package_name) --cov-config .coveragerc --cov-append --cov-report=html
pytest_cov_files := .coveragerc

# Files to be built
build_files := $(bdist_file) $(sdist_file)

# Files the distribution archives depend upon.
dist_dependent_files := \
    pyproject.toml \
    LICENSE \
    README.md \
    AUTHORS.md \
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
	@echo "  install    - Install package in active Python environment (non-editable)"
	@echo "  develop    - Prepare the development environment by installing prerequisites"
	@echo "  check_reqs - Perform missing dependency checks"
	@echo "  check      - Run Flake8 on sources"
	@echo "  ruff       - Run Ruff (an alternate lint tool) on sources"
	@echo "  pylint     - Run PyLint on sources"
	@echo "  safety     - Run safety for install and all"
	@echo "  bandit     - Run bandit checker"
	@echo "  test       - Run unit tests (adds to coverage results)"
	@echo "  end2end_mocked - Run end2end tests against example mock environments (adds to coverage results)"
	@echo "  installtest - Run install tests"
	@echo "  build      - Build the distribution files in: $(dist_dir)"
	@echo "  builddoc   - Build documentation in: $(doc_build_dir)"
	@echo "  all        - Do all of the above"
	@echo "  end2end    - Run end2end tests (adds to coverage results)"
	@echo "  end2end_show - Show HMCs defined for end2end tests"
	@echo "  authors    - Generate AUTHORS.md file from git log"
	@echo "  uninstall  - Uninstall package from active Python environment"
	@echo "  release_branch - Create a release branch when releasing a version (requires VERSION and optionally BRANCH to be set)"
	@echo "  release_publish - Publish to PyPI when releasing a version (requires VERSION and optionally BRANCH to be set)"
	@echo "  start_branch - Create a start branch when starting a new version (requires VERSION and optionally BRANCH to be set)"
	@echo "  start_tag - Create a start tag when starting a new version (requires VERSION and optionally BRANCH to be set)"
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
	@echo "        minimum - Minimum versions as defined in minimum-constraints*.txt"
	@echo "      Optional, defaults to 'latest'."
	@echo "  PYTHON_CMD=... - Name of python command. Default: python"
	@echo "  PIP_CMD=... - Name of pip command. Default: pip"
	@echo "  VERSION=... - M.N.U version to be released or started"
	@echo "  BRANCH=... - Name of branch to be released or started (default is derived from VERSION)"

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

.PHONY: _always
_always:

.PHONY: env
env:
	@echo "Makefile: Environment variables as seen by make:"
	$(ENV)

$(done_dir)/base_$(pymn)_$(PACKAGE_LEVEL).done: base-requirements.txt minimum-constraints-develop.txt minimum-constraints-install.txt
	-$(call RM_FUNC,$@)
	@echo "Installing/upgrading pip, setuptools and wheel with PACKAGE_LEVEL=$(PACKAGE_LEVEL)"
	$(PYTHON_CMD) -m pip install $(pip_level_opts) -r base-requirements.txt
	echo "done" >$@

.PHONY: develop
develop: $(done_dir)/develop_$(pymn)_$(PACKAGE_LEVEL).done
	@echo "Makefile: $@ done."

$(done_dir)/develop_$(pymn)_$(PACKAGE_LEVEL).done: $(done_dir)/base_$(pymn)_$(PACKAGE_LEVEL).done $(done_dir)/install_$(pymn)_$(PACKAGE_LEVEL).done dev-requirements.txt minimum-constraints-develop.txt minimum-constraints-install.txt
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

$(doc_build_dir)/html/docs/index.html: $(done_dir)/develop_$(pymn)_$(PACKAGE_LEVEL).done $(doc_dependent_files)
	@echo "Running Sphinx to create HTML pages"
	-$(call RM_FUNC,$@)
	$(doc_cmd) -b html $(doc_opts) $(doc_build_dir)/html
	@echo
	@echo "Done: Created the HTML pages with top level file: $@"

.PHONY: pdf
pdf: $(done_dir)/develop_$(pymn)_$(PACKAGE_LEVEL).done $(doc_dependent_files)
	@echo "Running Sphinx to create PDF files"
	$(doc_cmd) -b latex $(doc_opts) $(doc_build_dir)/pdf
	@echo "Running LaTeX files through pdflatex..."
	$(MAKE) -C $(doc_build_dir)/pdf all-pdf
	@echo
	@echo "Done: Created the PDF files in: $(doc_build_dir)/pdf/"
	@echo "Makefile: $@ done."

.PHONY: man
man: $(done_dir)/develop_$(pymn)_$(PACKAGE_LEVEL).done $(doc_dependent_files)
	@echo "Running Sphinx to create manual pages"
	$(doc_cmd) -b man $(doc_opts) $(doc_build_dir)/man
	@echo
	@echo "Done: Created the manual pages in: $(doc_build_dir)/man/"
	@echo "Makefile: $@ done."

.PHONY: docchanges
docchanges: $(doc_dependent_files)
	@echo "Running Sphinx to create the doc changes overview file"
	$(doc_cmd) -b changes $(doc_opts) $(doc_build_dir)/changes
	@echo
	@echo "Done: Created the doc changes overview file in: $(doc_build_dir)/changes/"
	@echo "Makefile: $@ done."

.PHONY: doclinkcheck
doclinkcheck: $(doc_dependent_files)
	@echo "Running Sphinx to check the doc links"
	$(doc_cmd) -b linkcheck $(doc_opts) $(doc_build_dir)/linkcheck
	@echo
	@echo "Done: Look for any errors in the above output or in: $(doc_build_dir)/linkcheck/output.txt"
	@echo "Makefile: $@ done."

.PHONY: doccoverage
doccoverage: $(doc_dependent_files)
	@echo "Running Sphinx to doc coverage results"
	$(doc_cmd) -b coverage $(doc_opts) $(doc_build_dir)/coverage
	@echo "Done: Created the doc coverage results in: $(doc_build_dir)/coverage/python.txt"
	@echo "Makefile: $@ done."

.PHONY: check
check: $(done_dir)/flake8_$(pymn)_$(PACKAGE_LEVEL).done
	@echo "Makefile: $@ done."

.PHONY: ruff
ruff: $(done_dir)/ruff_$(pymn)_$(PACKAGE_LEVEL).done
	@echo "Makefile: $@ done."

.PHONY: pylint
pylint: $(done_dir)/pylint_$(pymn)_$(PACKAGE_LEVEL).done
	@echo "Makefile: $@ done."

.PHONY: safety
safety: $(done_dir)/safety_develop_$(pymn)_$(PACKAGE_LEVEL).done $(done_dir)/safety_install_$(pymn)_$(PACKAGE_LEVEL).done
	@echo "Makefile: $@ done."

.PHONY: bandit
bandit: $(done_dir)/bandit_$(pymn)_$(PACKAGE_LEVEL).done
	@echo "Makefile: $@ done."

.PHONY: check_reqs
check_reqs: $(done_dir)/check_reqs_$(pymn)_$(PACKAGE_LEVEL).done
	@echo "Makefile: $@ done."

.PHONY: install
install: $(done_dir)/install_$(pymn)_$(PACKAGE_LEVEL).done
	@echo "Makefile: $@ done."

$(done_dir)/install_$(pymn)_$(PACKAGE_LEVEL).done: $(done_dir)/base_$(pymn)_$(PACKAGE_LEVEL).done requirements.txt extra-testutils-requirements.txt minimum-constraints-develop.txt minimum-constraints-install.txt
	-$(call RM_FUNC,$@)
	@echo "Installing $(package_name) (non-editable) and runtime reqs with PACKAGE_LEVEL=$(PACKAGE_LEVEL)"
	$(PYTHON_CMD) -m pip install $(pip_level_opts) $(pip_level_opts_new) .
	$(PYTHON_CMD) -c "import $(package_name); print('ok')"
	$(PYTHON_CMD) -c "import $(mock_package_name); print('ok')"
	$(PYTHON_CMD) -m pip install $(pip_level_opts) $(pip_level_opts_new) .[testutils]
	$(PYTHON_CMD) -c "import $(package_name).testutils; print('ok')"
	echo "done" >$@

.PHONY: uninstall
uninstall:
	bash -c '$(PIP_CMD) show $(package_name) >/dev/null; if [ $$? -eq 0 ]; then $(PIP_CMD) uninstall -y $(package_name); fi'
	@echo "Makefile: $@ done."

.PHONY: clobber
clobber: clean
	-$(call RM_FUNC,$(dist_files))
	-$(call RM_R_FUNC,*.done)
	-$(call RMDIR_FUNC,$(doc_build_dir) htmlcov htmlcov.end2end .tox)
	@echo "Makefile: $@ done."

.PHONY: clean
clean:
	-$(call RM_R_FUNC,*.pyc)
	-$(call RM_R_FUNC,*.tmp)
	-$(call RM_R_FUNC,tmp_*)
	-$(call RM_R_FUNC,.DS_Store)
	-$(call RMDIR_R_FUNC,__pycache__)
	-$(call RMDIR_R_FUNC,.pytest_cache)
	-$(call RMDIR_R_FUNC,.ruff_cache)
	-$(call RM_FUNC,MANIFEST MANIFEST.in AUTHORS ChangeLog .coverage)
	-$(call RMDIR_FUNC,build .cache $(package_name).egg-info .eggs)
	@echo "Makefile: $@ done."

.PHONY: all
all: install develop check_reqs check ruff pylint test end2end_mocked safety bandit installtest build builddoc
	@echo "Makefile: $@ done."

.PHONY: release_branch
release_branch:
	@bash -c 'if [ -z "$(VERSION)" ]; then echo ""; echo "Error: VERSION env var is not set"; echo ""; false; fi'
	@bash -c 'if [ -n "$$(git status -s)" ]; then echo ""; echo "Error: Local git repo has uncommitted files:"; echo ""; git status; false; fi'
	git fetch origin
	@bash -c 'if [ -z "$$(git tag -l $(VERSION)a0)" ]; then echo ""; echo "Error: Release start tag $(VERSION)a0 does not exist (the version has not been started)"; echo ""; false; fi'
	@bash -c 'if [ -n "$$(git tag -l $(VERSION))" ]; then echo ""; echo "Error: Release tag $(VERSION) already exists (the version has already been released)"; echo ""; false; fi'
	@bash -c 'if [[ -n "$${BRANCH}" ]]; then echo $${BRANCH} >branch.tmp; elif [[ "$${VERSION#*.*.}" == "0" ]]; then echo "master" >branch.tmp; else echo "stable_$${VERSION%.*}" >branch.tmp; fi'
	@bash -c 'if [ -z "$$(git branch --contains $(VERSION)a0 $$(cat branch.tmp))" ]; then echo ""; echo "Error: Release start tag $(VERSION)a0 is not in target branch $$(cat branch.tmp), but in:"; echo ""; git branch --contains $(VERSION)a0;. false; fi'
	@echo "==> This will start the release of $(package_name) version $(VERSION) to PyPI using target branch $$(cat branch.tmp)"
	@echo -n '==> Continue? [yN] '
	@bash -c 'read answer; if [ "$$answer" != "y" ]; then echo "Aborted."; false; fi'
	bash -c 'git checkout $$(cat branch.tmp)'
	git pull
	@bash -c 'if [ -z "$$(git branch -l release_$(VERSION))" ]; then echo "Creating release branch release_$(VERSION)"; git checkout -b release_$(VERSION); fi'
	git checkout release_$(VERSION)
	make authors
	towncrier build --version $(VERSION) --yes
	git commit -asm "Release $(VERSION)"
	git push --set-upstream origin release_$(VERSION)
	rm -f branch.tmp
	@echo "Done: Pushed the release branch to GitHub - now go there and create a PR."
	@echo "Makefile: $@ done."

.PHONY: release_publish
release_publish:
	@bash -c 'if [ -z "$(VERSION)" ]; then echo ""; echo "Error: VERSION env var is not set"; echo ""; false; fi'
	@bash -c 'if [ -n "$$(git status -s)" ]; then echo ""; echo "Error: Local git repo has uncommitted files:"; echo ""; git status; false; fi'
	git fetch origin
	@bash -c 'if [ -n "$$(git tag -l $(VERSION))" ]; then echo ""; echo "Error: Release tag $(VERSION) already exists (the version has already been released)"; echo ""; false; fi'
	@bash -c 'if [[ -n "$${BRANCH}" ]]; then echo $${BRANCH} >branch.tmp; elif [[ "$${VERSION#*.*.}" == "0" ]]; then echo "master" >branch.tmp; else echo "stable_$${VERSION%.*}" >branch.tmp; fi'
	@bash -c 'if [ "$$(git log --format=format:%s origin/$$(cat branch.tmp)~..origin/$$(cat branch.tmp))" != "Release $(VERSION)" ]; then echo ""; echo "Error: Release PR for $(VERSION) has not been merged yet"; echo ""; false; fi'
	@echo "==> This will publish $(package_name) version $(VERSION) to PyPI using target branch $$(cat branch.tmp)"
	@echo -n '==> Continue? [yN] '
	@bash -c 'read answer; if [ "$$answer" != "y" ]; then echo "Aborted."; false; fi'
	bash -c 'git checkout $$(cat branch.tmp)'
	git pull
	git tag -f $(VERSION)
	git push -f --tags
	git branch -D release_$(VERSION)
	git branch -D -r origin/release_$(VERSION)
	rm -f branch.tmp
	@echo "Done: Triggered the publish workflow - now wait for it to finish and verify the publishing."
	@echo "Makefile: $@ done."

.PHONY: start_branch
start_branch:
	@bash -c 'if [ -z "$(VERSION)" ]; then echo ""; echo "Error: VERSION env var is not set"; echo ""; false; fi'
	@bash -c 'if [ -n "$$(git status -s)" ]; then echo ""; echo "Error: Local git repo has uncommitted files:"; echo ""; git status; false; fi'
	git fetch origin
	@bash -c 'if [ -n "$$(git tag -l $(VERSION))" ]; then echo ""; echo "Error: Release tag $(VERSION) already exists (the version has already been released)"; echo ""; false; fi'
	@bash -c 'if [ -n "$$(git tag -l $(VERSION)a0)" ]; then echo ""; echo "Error: Release start tag $(VERSION)a0 already exists (the new version has alreay been started)"; echo ""; false; fi'
	@bash -c 'if [ -n "$$(git branch -l start_$(VERSION))" ]; then echo ""; echo "Error: Start branch start_$(VERSION) already exists (the start of the new version is already underway)"; echo ""; false; fi'
	@bash -c 'if [[ -n "$${BRANCH}" ]]; then echo $${BRANCH} >branch.tmp; elif [[ "$${VERSION#*.*.}" == "0" ]]; then echo "master" >branch.tmp; else echo "stable_$${VERSION%.*}" >branch.tmp; fi'
	@echo "==> This will start new version $(VERSION) using target branch $$(cat branch.tmp)"
	@echo -n '==> Continue? [yN] '
	@bash -c 'read answer; if [ "$$answer" != "y" ]; then echo "Aborted."; false; fi'
	bash -c 'git checkout $$(cat branch.tmp)'
	git pull
	git checkout -b start_$(VERSION)
	echo "Dummy change for starting new version $(VERSION)" >changes/noissue.$(VERSION).notshown.rst
	git add changes/noissue.$(VERSION).notshown.rst
	git commit -asm "Start $(VERSION)"
	git push --set-upstream origin start_$(VERSION)
	rm -f branch.tmp
	@echo "Done: Pushed the start branch to GitHub - now go there and create a PR."
	@echo "Makefile: $@ done."

.PHONY: start_tag
start_tag:
	@bash -c 'if [ -z "$(VERSION)" ]; then echo ""; echo "Error: VERSION env var is not set"; echo ""; false; fi'
	@bash -c 'if [ -n "$$(git status -s)" ]; then echo ""; echo "Error: Local git repo has uncommitted files:"; echo ""; git status; false; fi'
	git fetch origin
	@bash -c 'if [ -n "$$(git tag -l $(VERSION)a0)" ]; then echo ""; echo "Error: Release start tag $(VERSION)a0 already exists (the new version has alreay been started)"; echo ""; false; fi'
	@bash -c 'if [[ -n "$${BRANCH}" ]]; then echo $${BRANCH} >branch.tmp; elif [[ "$${VERSION#*.*.}" == "0" ]]; then echo "master" >branch.tmp; else echo "stable_$${VERSION%.*}" >branch.tmp; fi'
	@bash -c 'if [ "$$(git log --format=format:%s origin/$$(cat branch.tmp)~..origin/$$(cat branch.tmp))" != "Start $(VERSION)" ]; then echo ""; echo "Error: Start PR for $(VERSION) has not been merged yet"; echo ""; false; fi'
	@echo "==> This will complete the start of new version $(VERSION) using target branch $$(cat branch.tmp)"
	@echo -n '==> Continue? [yN] '
	@bash -c 'read answer; if [ "$$answer" != "y" ]; then echo "Aborted."; false; fi'
	bash -c 'git checkout $$(cat branch.tmp)'
	git pull
	git tag -f $(VERSION)a0
	git push -f --tags
	git branch -D start_$(VERSION)
	git branch -D -r origin/start_$(VERSION)
	rm -f branch.tmp
	@echo "Done: Pushed the release start tag and cleaned up the release start branch."
	@echo "Makefile: $@ done."

# Distribution archives.
$(sdist_file): pyproject.toml $(dist_dependent_files)
	@echo "Makefile: Building the source distribution archive: $(sdist_file)"
	$(PYTHON_CMD) -m build --sdist --outdir $(dist_dir) .
	@echo "Makefile: Done building the source distribution archive: $(sdist_file)"

$(bdist_file) $(version_file): pyproject.toml $(dist_dependent_files)
	@echo "Makefile: Building the wheel distribution archive: $(bdist_file)"
	$(PYTHON_CMD) -m build --wheel --outdir $(dist_dir) -C--universal .
	@echo "Makefile: Done building the wheel distribution archive: $(bdist_file)"

$(done_dir)/pylint_$(pymn)_$(PACKAGE_LEVEL).done: $(done_dir)/develop_$(pymn)_$(PACKAGE_LEVEL).done $(pylint_rc_file) $(check_py_files)
	@echo "Makefile: Running Pylint"
	-$(call RM_FUNC,$@)
	pylint $(pylint_opts) --rcfile=$(pylint_rc_file) --output-format=text $(check_py_files)
	echo "done" >$@
	@echo "Makefile: Done running Pylint"

$(done_dir)/safety_develop_$(pymn)_$(PACKAGE_LEVEL).done: $(done_dir)/develop_$(pymn)_$(PACKAGE_LEVEL).done $(safety_develop_policy_file) minimum-constraints-develop.txt minimum-constraints-install.txt
	@echo "Makefile: Running Safety for development packages (and tolerate safety issues when RUN_TYPE is normal or scheduled)"
	-$(call RM_FUNC,$@)
	bash -c "safety check --policy-file $(safety_develop_policy_file) -r minimum-constraints-develop.txt --full-report || test '$(RUN_TYPE)' == 'normal' || test '$(RUN_TYPE)' == 'scheduled' || exit 1"
	echo "done" >$@
	@echo "Makefile: Done running Safety for development packages"

$(done_dir)/safety_install_$(pymn)_$(PACKAGE_LEVEL).done: $(done_dir)/develop_$(pymn)_$(PACKAGE_LEVEL).done $(safety_install_policy_file) minimum-constraints-install.txt
	@echo "Makefile: Running Safety for install packages (and tolerate safety issues when RUN_TYPE is normal)"
	-$(call RM_FUNC,$@)
	bash -c "safety check --policy-file $(safety_install_policy_file) -r minimum-constraints-install.txt --full-report || test '$(RUN_TYPE)' == 'normal' || exit 1"
	echo "done" >$@
	@echo "Makefile: Done running Safety for install packages"

$(done_dir)/bandit_$(pymn)_$(PACKAGE_LEVEL).done: $(done_dir)/develop_$(pymn)_$(PACKAGE_LEVEL).done $(bandit_rc_file) $(check_py_files)
	@echo "Makefile: Running Bandit"
	-$(call RM_FUNC,$@)
	bandit -c $(bandit_rc_file) -l -r $(package_name) $(mock_package_name)
	echo "done" >$@
	@echo "Makefile: Done running Bandit"

$(done_dir)/flake8_$(pymn)_$(PACKAGE_LEVEL).done: $(done_dir)/develop_$(pymn)_$(PACKAGE_LEVEL).done $(flake8_rc_file) $(check_py_files)
	@echo "Makefile: Running Flake8"
	-$(call RM_FUNC,$@)
	flake8 $(check_py_files)
	echo "done" >$@
	@echo "Makefile: Done running Flake8"

$(done_dir)/ruff_$(pymn)_$(PACKAGE_LEVEL).done: $(done_dir)/develop_$(pymn)_$(PACKAGE_LEVEL).done $(ruff_rc_file) $(check_py_files)
	@echo "Makefile: Running Ruff"
	-$(call RM_FUNC,$@)
	ruff --version
	ruff check --unsafe-fixes --config $(ruff_rc_file) $(check_py_files)
	echo "done" >$@
	@echo "Makefile: Done running Ruff"

$(done_dir)/check_reqs_$(pymn)_$(PACKAGE_LEVEL).done: $(done_dir)/develop_$(pymn)_$(PACKAGE_LEVEL).done minimum-constraints-develop.txt minimum-constraints-install.txt requirements.txt extra-testutils-requirements.txt
	-$(call RM_FUNC,$@)
	@echo "Makefile: Checking missing dependencies of this package"
	cat requirements.txt extra-testutils-requirements.txt >tmp_requirements.txt
	pip-missing-reqs $(package_name) --ignore-module $(package_name) --ignore-module $(mock_package_name) --requirements-file=tmp_requirements.txt
	$(call RM_FUNC,tmp_requirements.txt)
	pip-missing-reqs $(package_name) --ignore-module $(package_name) --ignore-module $(mock_package_name) --requirements-file=minimum-constraints-install.txt
	@echo "Makefile: Done checking missing dependencies of this package"
ifeq ($(PLATFORM),Windows_native)
# Reason for skipping on Windows is https://github.com/r1chardj0n3s/pip-check-reqs/issues/67
	@echo "Makefile: Warning: Skipping the checking of missing dependencies of site-packages directory on native Windows" >&2
else
	@echo "Makefile: Checking missing dependencies of some development packages in our minimum versions"
	cat minimum-constraints-develop.txt minimum-constraints-install.txt >tmp_minimum-constraints.txt
	@rc=0; for pkg in $(check_reqs_packages); do dir=$$($(PYTHON_CMD) -c "import $${pkg} as m,os; dm=os.path.dirname(m.__file__); d=dm if not dm.endswith('site-packages') else m.__file__; print(d)"); cmd="pip-missing-reqs $${dir} --requirements-file=tmp_minimum-constraints.txt"; echo $${cmd}; $${cmd}; rc=$$(expr $${rc} + $${?}); done; exit $${rc}
	rm -f tmp_minimum-constraints.txt
	@echo "Makefile: Done checking missing dependencies of some development packages in our minimum versions"
endif
	echo "done" >$@

.PHONY: test
test: $(done_dir)/develop_$(pymn)_$(PACKAGE_LEVEL).done $(package_py_files) $(test_unit_py_files) $(test_common_py_files) $(pytest_cov_files)
	-$(call RMDIR_R_FUNC,htmlcov)
	pytest --color=yes $(pytest_no_log_opt) -s $(test_dir)/unit $(pytest_cov_opts) $(pytest_opts)
	@echo "Makefile: $@ done."

.PHONY: installtest
installtest: $(bdist_file) $(sdist_file) $(test_dir)/installtest/test_install.sh
ifeq ($(PLATFORM),Windows_native)
	@echo "Makefile: Warning: Skipping install test on native Windows" >&2
else
	@echo "Makefile: Running install tests"
	$(test_dir)/installtest/test_install.sh $(bdist_file) $(sdist_file) $(PYTHON_CMD)
	@echo "Makefile: Done running install tests"
endif

.PHONY:	end2end
end2end: $(done_dir)/develop_$(pymn)_$(PACKAGE_LEVEL).done $(package_py_files) $(test_end2end_py_files) $(test_common_py_files) $(pytest_cov_files)
	-$(call RMDIR_R_FUNC,htmlcov.end2end)
	bash -c "TESTEND2END_LOAD=true pytest --color=yes $(pytest_no_log_opt) -v -s $(test_dir)/end2end $(pytest_cov_opts) $(pytest_opts)"
	@echo "Makefile: $@ done."

# TODO: Enable rc checking again once the remaining issues are resolved
.PHONY:	end2end_mocked
end2end_mocked: $(done_dir)/develop_$(pymn)_$(PACKAGE_LEVEL).done $(package_py_files) $(test_end2end_py_files) $(test_common_py_files) $(pytest_cov_files) tests/end2end/mocked_inventory.yaml tests/end2end/mocked_vault.yaml tests/end2end/mocked_hmc_z16.yaml
	-$(call RMDIR_R_FUNC,htmlcov.end2end)
	bash -c "TESTEND2END_LOAD=true TESTINVENTORY=tests/end2end/mocked_inventory.yaml TESTVAULT=tests/end2end/mocked_vault.yaml pytest --color=yes $(pytest_no_log_opt) -v -s $(test_dir)/end2end $(pytest_cov_opts) $(pytest_opts)"
	@echo "Makefile: $@ done."

.PHONY: authors
authors: AUTHORS.md
	@echo "Makefile: $@ done."

# Make sure the AUTHORS.md file is up to date but has the old date when it did
# not change to prevent redoing dependent targets.
AUTHORS.md: _always
	echo "# Authors of this project" >AUTHORS.md.tmp
	echo "" >>AUTHORS.md.tmp
	echo "Sorted list of authors derived from git commit history:" >>AUTHORS.md.tmp
	echo '```' >>AUTHORS.md.tmp
	sh -c "git shortlog --summary --email HEAD | cut -f 2 | sort >>AUTHORS.md.tmp"
	echo '```' >>AUTHORS.md.tmp
	sh -c "if ! diff -q AUTHORS.md.tmp AUTHORS.md; then echo 'Updating AUTHORS.md as follows:'; diff AUTHORS.md.tmp AUTHORS.md; mv AUTHORS.md.tmp AUTHORS.md; else echo 'AUTHORS.md was already up to date'; rm AUTHORS.md.tmp; fi"

.PHONY:	end2end_show
end2end_show:
	bash -c "TESTEND2END_LOAD=true $(PYTHON_CMD) -c 'from zhmcclient.testutils import print_hmc_definitions; print_hmc_definitions()'"
