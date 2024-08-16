
PIP_COMMAND=pip

# ********************
# Variable definitions
# ********************

# Package name
PACKAGE = mgdm2oereb_service
LOCATION = src

# Python source files
SRC_PY = $(shell find $(LOCATION)/$(PACKAGE) -name '*.py')

# **************
# Common targets
# **************

$(PYGEOAPI_OPENAPI): $(PYGEOAPI_CONFIG)
	pygeoapi openapi generate $(PYGEOAPI_CONFIG) > $(PYGEOAPI_OPENAPI)

.PHONY: install
install: setup.py requirements.txt
	$(PIP_COMMAND) install -r requirements.txt

.PHONY: install-test
install-test: setup.py requirements.txt requirements-tests.txt
	$(PIP_COMMAND) install -r requirements.txt -r requirements-tests.txt

.PHONY: build-dev
build-dev: setup.py install
	pip install -e .

.PHONY: git-attributes
git-attributes:
	git --no-pager diff --check `git log --oneline | tail -1 | cut --fields=1 --delimiter=' '`

.PHONY: lint
lint:
	flake8

.PHONY: test
test: install-test build-dev
	py.test -vv --cov-config .coveragerc --cov $(PACKAGE) --cov-report term-missing:skip-covered tests

.PHONY: check
check: git-attributes lint test

.PHONY: updates
updates: requirements.txt requirements-tests.txt
	pip list --outdated

.PHONY: serve-dev
serve-dev: $(PYGEOAPI_OPENAPI)
	gunicorn mgdm2oereb_service.app:app --config $(GUNICORN_CONFIG) --reload --log-level debug --workers=8
