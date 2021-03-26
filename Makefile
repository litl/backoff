PY_VERSION := $(wordlist 2,4,$(subst ., ,$(shell python --version 2>&1)))
PY_MAJOR := $(word 1,${PY_VERSION})
PY_MINOR := $(word 2,${PY_VERSION})
PY_GTE_35 = $(shell echo $(PY_MAJOR).$(PY_MINOR)\>=3.5 | bc)


.PHONY: all flake8 clean test check

all:
	@echo 'flake8            check flake8 compliance'
	@echo 'clean             cleanup the source tree'
	@echo 'test              run the unit tests'
	@echo 'check             make sure you are ready to commit'

flake8:
	@flake8 --ignore=E741,W503,W504 backoff tests

clean:
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -delete
	@rm -rf build dist .coverage MANIFEST

test: clean
	@PYTHONPATH=. py.test --cov-config .coveragerc --cov backoff tests

check: flake8 test
	@coverage report | grep 100% >/dev/null || { echo 'Unit tests coverage is incomplete.'; exit 1; }
