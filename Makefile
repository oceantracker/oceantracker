.PHONY: help clean clean-build clean-pyc clean-test lint test test-all coverage docs install install-dev build upload upload-test

help:
	@echo "Available commands:"
	@echo "  clean          Remove all build, test, coverage and Python artifacts"
	@echo "  clean-build    Remove build artifacts"
	@echo "  clean-pyc      Remove Python file artifacts"
	@echo "  env            Generate environment.yml files from pyproject.toml"
# 	@echo "  clean-test     Remove test and coverage artifacts"
# 	@echo "  lint           Check style with flake8 and black"
# 	@echo "  format         Format code with black"
# 	@echo "  test           Run tests quickly with the default Python"
# 	@echo "  test-all       Run tests on every Python version with tox"
# 	@echo "  coverage       Check code coverage quickly with the default Python"
# 	@echo "  docs           Generate Sphinx HTML documentation"
	@echo "  install        Install the package to the active Python's site-packages"
# 	@echo "  install-dev    Install the package in development mode"
	@echo "  build          Build source and wheel package"
# 	@echo "  upload         Package and upload a release to PyPI"
	@echo "  upload-test    Package and upload a release to TestPyPI"

clean: clean-build clean-pyc
# clean: clean-build clean-pyc clean-test

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

# clean-test:
# 	rm -fr .tox/
# 	rm -f .coverage
# 	rm -fr htmlcov/
# 	rm -fr .pytest_cache

# lint:
# 	flake8 oceantracker tests
# 	black --check oceantracker tests

# format:
# 	black oceantracker tests

# test:
# 	python -m pytest

# test-all:
# 	tox

# coverage:
# 	coverage run --source oceantracker -m pytest
# 	coverage report -m
# 	coverage html

# docs:
# 	$(MAKE) -C docs clean
# 	$(MAKE) -C docs html

env:
	python generate_environment_yaml.py

install: clean
	pip install .

install-dev: clean
	pip install -e .[dev]

build: clean env
	python -m build

# upload: clean build
# 	python -m twine upload dist/*

upload-test: clean build
	python -m twine upload --repository testpypi dist/*