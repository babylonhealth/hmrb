SHELL = /bin/bash
DOCKER_SHELL = /bin/bash


#############################################
### Makefile Definitions
#############################################

### Error codes

ERROR_PYTHON_VERSION = 10


### Main defs

PACKAGE_NAME = hmrb
PACKAGE_VERSION = 1.1.0

srcdir = $(CURDIR)/$(PACKAGE_NAME)
builddir = $(CURDIR)/build
distdir = $(CURDIR)/dist
docdir = $(CURDIR)/docs
autodocdir = $(docdir)/autodoc


### Tools

tools =

ifeq ($(shell uname -s),Darwin)
	SED = gsed
else
	SED = sed
endif

ifeq ($(shell which ${SED}),)
	tools += $(SED)
endif

GREPTOOL = rg
ifeq ($(shell which ${GREPTOOL}),)
	GREPTOOL = egrep
endif

AWK = awk
ifeq ($(shell which ${AWK}),)
	tools += $(AWK)
endif


### Python

PYTHON = python3
PYTHON_BIN = $(shell which ${PYTHON})
ifeq ($(PYTHON_BIN),)
	tools += $(PYTHON)
endif

PIP = $(PYTHON) -m pip

PYTHON3_VER = 3.8.6
PYTHON_VERSION_INFO = $(shell ${PYTHON} -c 'if 1: \
	from sys import version_info; \
	print("{v.major}.{v.minor}.{v.micro}".format(v=version_info)) \
	')
PYTHON_INFO = $(PYTHON_BIN) -> $(PYTHON_VERSION_INFO)

VIRTUALENV = virtualenv
VIRTUALENV_BIN = $(shell which ${VIRTUALENV})
ifeq ($(VIRTUALENV_BIN),)
	tools += $(VIRTUALENV)
endif

# use direnv structure: layout pyenv [version]
VENV_DIR = .direnv/python-${PYTHON3_VER}

PYTHON_STD_PKGS = \
	pip \
	setuptools \
	wheel


### Docker

DOCKER = docker
ifeq ($(shell which ${DOCKER}),)
	tools += $(DOCKER)
endif

DOCKER_PS_ARGS = -s

DOCKER_BASE_IMAGE = python:$(PYTHON3_VER)-slim-buster
DOCKER_PORT = 8088


#############################################
### All
#############################################

all: help
ifdef tools
	$(error Can't find tools:${tools})
endif
	@if [[ "$(PYTHON_VERSION_INFO)" == "$(PYTHON3_VER)" ]]; then \
		echo "INFO: Found Python interpreter: $(PYTHON_INFO)"; \
	else \
		echo -n "WARNING: Incompatible Python interpreter version: $(PYTHON_INFO) "; \
		echo "(instead of $(PYTHON3_VER))"; \
		echo "INFO: Try \`make python-install\`"; \
		exit $(ERROR_PYTHON_VERSION); \
	fi


#############################################
### Initializing repo
#############################################

.PHONY: init
init:
	git init
	git add -f *
	git add .gitignore
	git add .flake8
	git commit -m "build: cookiecutter-python"

#############################################
### Updating requirements
#############################################

.PHONY: requirements
# target: requirements - Compile Pip requirements
requirements:
	@echo
	@if (! docker stats --no-stream > /dev/null); then \
		pip install nox; \
		nox -rs requirements; \
	else \
		$(DOCKER) run -it --rm \
			-v "$(CURDIR)/requirements.in:/requirements.in" \
			-v "$(CURDIR)/requirements.txt:/requirements.txt" \
		"$(DOCKER_BASE_IMAGE)" "$(DOCKER_SHELL)" -c \
			'pip install -U pip pip-tools && \
			CUSTOM_COMPILE_COMMAND="make requirements" \
				pip-compile -o requirements.tmp requirements.in && \
			cat requirements.tmp > requirements.txt'; \
	fi

#############################################
### Installing requirements and package
#############################################

.PHONY: install
# target: install - Install project sources in "development mode"
install: requirements.txt requirements-test.txt
	@echo
	@if ! [[ -d "$(VENV_DIR)" ]]; then \
		$(VIRTUALENV) -p $(PYTHON3_VER) "$(VENV_DIR)"; \
	fi
	@if [[ -d "$(VENV_DIR)" ]]; then \
		\
		source "$(VENV_DIR)/bin/activate"; \
		\
			$(PIP) install -U $(PYTHON_STD_PKGS); \
			$(PIP) install -Ur $<; \
			$(PIP) install -Ur $(word 2,$^); \
		\
		echo ""; \
		$(PIP) list; \
		echo ""; \
		\
		deactivate; \
	fi
	@echo
	@$(PYTHON) setup.py develop

.PHONY: uninstall
# target: uninstall - Uninstall project sources
uninstall:
	@echo
	@$(PYTHON) setup.py develop --uninstall


#############################################
### Running
#############################################

run:
	@echo
	@$(PYTHON) $(PACKAGE_NAME)/__main__.py

#############################################
# Linting
#############################################

black:
	@echo
	@nox -rs black

lint:
	@echo
	@nox -rs lint

safety:
	@echo
	@nox -rs safety

type:
	@echo
	@nox -rs types

#############################################
### Testing
#############################################


.PHONY: tests
# target: tests - Run tests
tests:
	@echo
	@nox -rs tests

##
# Building and packaging
.PHONY: changelog
changelog:
	@echo
	@nox -rs changelog

#############################################
### Publishing
#############################################

.PHONY: sdist
# target: sdist - Create a source distribution
sdist:
	@echo
	@[[ ! -f "$(distdir)"/*.tar.gz ]] && $(PYTHON) setup.py sdist

.PHONY: dist
# target: dist - Create a binary (wheel) distribution
dist:
	@echo
	@[[ ! -f "$(distdir)"/*.whl ]] && $(PYTHON) setup.py bdist_wheel

# publish to testpypi
.PHONY: publish
publish:
	@echo
	@nox -rs publish

# publish to pypi
.PHONY: publish-confirm
publish-confirm:
	@echo
	@nox -rs publish -- -r pypi

#############################################
### Docker
#############################################

.PHONY: docker-build
# target: docker-build - Build image from scratch
docker-build: dist
	@echo
	@$(DOCKER) build -f "$(CURDIR)/Dockerfile" -t $(PACKAGE_NAME):$(PACKAGE_VERSION) \
		--no-cache .

.PHONY: docker-run
# target: docker-run - Run temporary container in an interactive mode
docker-run:
	@echo
	@$(DOCKER) run -it --rm -p $(DOCKER_PORT):$(DOCKER_PORT) \
		$(PACKAGE_NAME):$(PACKAGE_VERSION)

.PHONY: docker-clean
# target: docker-clean - Remove all unused images, built containers and volumes
docker-clean:
	@echo
	@$(DOCKER) ps -aq | xargs $(DOCKER) rm -fv
	@$(DOCKER) system prune -af --volumes


#############################################
### Documentation
#############################################

SPHINX_BUILDDIR = $(docdir)/_build
AUTODOC_EXCLUDE_MODULES =
SPHINX_OPTS = -d "$(SPHINX_BUILDDIR)/doctrees" "$(docdir)"

.PHONY: docs
docs:
	@echo
	@nox -rs docs -- sphinx-build -b html $(SPHINX_OPTS) "$(SPHINX_BUILDDIR)/html"

.PHONY: apidoc
# target: apidoc - Create one reST file with automodule directives per package
apidoc: docs
	@echo
	@nox -rs docs -- sphinx-apidoc --force --private -o "$(autodocdir)" $(PACKAGE_NAME) \
		$(foreach module,$(AUTODOC_EXCLUDE_MODULES),$(PACKAGE_NAME)/$(module))

.PHONY: html
# target: html - Render standalone HTML files
html:
	@echo
	@nox -rs docs -- sphinx-autobuild $(SPHINX_OPTS) "$(SPHINX_BUILDDIR)/html"

#############################################
### Auxiliary targets
#############################################

.PHONY: help
# target: help - Display all callable targets
help:
	@echo
	@$(GREPTOOL) "^\s*#\s*target\s*:\s*" [Mm]akefile \
	| $(SED) -r "s/^\s*#\s*target\s*:\s*//g"

#############################################
### Cleaners
#############################################

.PHONY: clean
# target: clean - Clean the project's directory
clean:
	@find "$(CURDIR)" -path "$(CURDIR)/$(VENV_DIR)" -prune -o \
			\
		-name ".cache" -type d -exec rm -rfv {} + -o \
		-name ".mypy_cache" -type d -exec rm -rf {} + -o \
		-name ".pytest_cache" -type d -exec rm -rf {} + -o \
		-name "__pycache__" -type d -exec rm -rf {} + -o \
			\
		-name "*.py[cod]" -exec rm -f {} +
	@find hmrb -name "*.c" -delete
	@find hmrb -name "*.so" -delete
.PHONY: distclean
# target: distclean - Clean the project's build output
distclean:
	@find "$(CURDIR)" -path "$(CURDIR)/$(VENV_DIR)" -prune -o \
			\
		-name ".eggs" -type d -exec rm -rf {} + -o \
		-name "*.dist-info" -type d -exec rm -rf {} + -o \
		-name "*.egg-info" -type d -exec rm -rf {} +
	@rm -rf \
		"$(builddir)" \
		"$(distdir)"

	@find "$(CURDIR)" -name "$(autodocdir)/*.rst" -exec rm -f {} +
	@rm -rf \
		"$(SPHINX_BUILDDIR)" \
		"$(SPHINX_STATIC)" \
		"$(SPHINX_TEMPLATES)"

.PHONY: mostlyclean
# target: mostlyclean - Delete almost everything
mostlyclean: clean distclean
	@find "$(CURDIR)" -name .DS_Store -exec rm -fv {} +
	@rm -rf "$(VENV_DIR)"

build_protoc:
	protoc -I=hmrb --python_out=hmrb hmrb/response.proto

install-fast-re:
	git clone https://github.com/google/re2
	cd re2; make
	cd re2; sudo make install
	pip3 install fb-re2==1.0.7
