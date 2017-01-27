PY_VERSION := $(wordlist 2,4,$(subst ., ,$(shell python --version 2>&1)))
PY_MAJOR := $(word 1,${PY_VERSION})
PY_MINOR := $(word 2,${PY_VERSION})
PY_GTE_34 = $(shell echo $(PY_MAJOR).$(PY_MINOR)\>=3.4 | bc)
PY_GTE_27 = $(shell echo $(PY_MAJOR).$(PY_MINOR)\>=2.7 | bc)


.PHONY: all pep8 flake8 clean test check

all:
	@echo 'pep8              check pep8 compliance'
	@echo 'pyflakes          check for unused imports (requires pyflakes)'
	@echo 'clean             cleanup the source tree'
	@echo 'test              run the unit tests'
	@echo 'check             make sure you are ready to commit'
	@echo 'docs              generate README.md from module docstring'

pep8:
	@pep8 backoff tests

flake8:
ifeq ($(PY_GTE_34),1)
	@flake8 backoff tests
else ifeq ($(PY_GTE_27),1)
	@flake8 --exclude tests/test_backoff_async.py,backoff/_async.py backoff tests
else
	@echo 'Not running flake8 for Python < 2.7'
endif

clean:
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -delete
	@rm -rf build dist .coverage

test: clean
ifeq ($(PY_GTE_34),1)
	@PYTHONPATH=. py.test --cov-config .coveragerc-py34 --cov backoff tests
else
	@PYTHONPATH=. py.test --cov-config .coveragerc-py2 --cov backoff tests/test_backoff.py
endif

check: pep8 flake8 test
	@coverage report | grep 100% >/dev/null || { echo 'Unit tests coverage is incomplete.'; exit 1; }
