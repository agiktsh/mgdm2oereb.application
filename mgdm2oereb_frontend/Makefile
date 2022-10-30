# **********************
# Check if running on CI
# **********************

# ********************
# Variable definitions
# ********************

# Package name
PKG = mgdm2oereb_frontend

# Python source files
SRC_PY = $(shell find src/$(PKG) -name '*.py')

# Stylesheet source files
SRC_SCSS = $(shell find src/scss -name '*.scss')

# ******************
# Set up environment
# ******************


/external_libs/.timestamp:
	mkdir -p /external_libs
	touch $@


# **********************
# Download external libs
# **********************

/external_libs/bootstrap/.timestamp: /external_libs/.timestamp
	wget -q -O /external_libs/bootstrap.zip https://github.com/twbs/bootstrap/archive/v4.4.1.zip
	unzip /external_libs/bootstrap.zip -d /external_libs/bootstrap
	rm -f /external_libs/bootstrap.zip
	mv /external_libs/bootstrap/bootstrap-*/* /external_libs/bootstrap/
	rm -rf /external_libs/bootstrap/bootstrap-*
	touch $@

/external_libs/font-awesome/.timestamp: /external_libs/.timestamp
	wget -q -O /external_libs/font-awesome.zip https://fontawesome.com/v4.7.0/assets/font-awesome-4.7.0.zip
	unzip /external_libs/font-awesome.zip -d /external_libs/font-awesome
	rm -f /external_libs/font-awesome.zip
	mv /external_libs/font-awesome/font-awesome-*/* /external_libs/font-awesome/
	rm -rf /external_libs/font-awesome/font-awesome-*
	touch $@

/external_libs/jquery-3.4.1.min.js:
	wget -q -O $@ https://code.jquery.com/jquery-3.4.1.min.js

# *********************
# Build application CSS
# *********************

src/$(PKG)/static/css/app.min.css: /external_libs/bootstrap/.timestamp /external_libs/font-awesome/.timestamp /external_libs/jquery-3.4.1.min.js $(SRC_SCSS)
	cp -f /external_libs/font-awesome/fonts/* src/$(PKG)/static/fonts/
	cp -f /external_libs/bootstrap/dist/js/bootstrap.bundle.* src/$(PKG)/static/js/
	pysassc -m -t compressed src/scss/app.scss src/$(PKG)/static/css/app.min.css


# **************
# Common targets
# **************

.PHONY: clean
clean:
	rm -rf .venv
	rm -rf $(PKG).egg-info
	rm -rf .pytest_cache
	rm -f .coverage

.PHONY: install
install: requirements.txt setup.py
	pip3 install -r requirements.txt -r requirements-tests.txt

.PHONY: check
check: git-attributes lint test

.PHONY: git-attributes
git-attributes:
	git --no-pager diff --check `git log --oneline | tail -1 | cut --fields=1 --delimiter=' '`

.PHONY: lint
lint:
	flake8

.PHONY: test
test:
	py.test -vv --cov-config .coveragerc --cov-report term-missing:skip-covered --cov $(PKG) tests

.PHONY: build
build: install src/$(PKG)/static/css/app.min.css

.PHONY: build-dev
build-dev: build
	pip3 install -e .

.PHONY: serve-dev
serve-dev: app.ini build-dev
	gunicorn --paste /app/app.ini -b :8080 --chdir src/$(PKG) --reload --log-level debug

.PHONY: serve
serve: app.ini
	uwsgi --plugin python3 --http-socket :8080 --ini-paste-logged /app/app.ini
