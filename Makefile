PY_VERSION := $(wordlist 2,4,$(subst ., ,$(shell python --version 2>&1)))
PY_MAJOR := $(word 1,${PY_VERSION})
PY_MINOR := $(word 2,${PY_VERSION})
PY_GTE_35 = $(shell echo $(PY_MAJOR).$(PY_MINOR)\>=3.5 | bc)
SMOKE_FLAGS = -m 'not smoke'

.PHONY: all flake8 clean test smoke check supercheck

all:
	@echo 'flake8            check flake8 compliance'
	@echo 'clean             clean up the source tree'
	@echo 'test              run the unit tests'
	@echo 'smoke             run network smoke tests'
	@echo 'check             run flake8 and unit tests'
	@echo 'supercheck        run flake8, unit, and smoke tests'

flake8:
ifeq ($(PY_GTE_35),1)
	@flake8 backoff tests
else
	@flake8 --exclude tests/python35,backoff/_async.py backoff tests
endif

clean:
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -delete
	@rm -rf build dist .coverage MANIFEST

test: clean
ifeq ($(PY_GTE_35),1)
	@PYTHONPATH=. py.test ${SMOKE_FLAGS} --cov-config .coveragerc-py35 --cov backoff tests
else
	@PYTHONPATH=. py.test ${SMOKE_FLAGS} --cov-config .coveragerc-py2 --cov backoff tests/test_*.py
endif

check: flake8 test
	@coverage report | grep 100% >/dev/null || { echo 'Unit tests coverage is incomplete.'; exit 1; }

smoke: SMOKE_FLAGS=-m smoke
smoke: test

supercheck: SMOKE_FLAGS=
supercheck: check
