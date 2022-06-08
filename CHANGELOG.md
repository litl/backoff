# Changelog

## [v2.1.1] - 2022-06-08
### Fixed

- Fix bug with max_tries/max_time callables https://github.com/litl/backoff/issues/164

## [v2.1.0] - 2022-06-07
### Changed

- Get max_tries/max_time values for every call fixes #160 (from @jvrsantacruz)

## [v2.0.1] - 2022-04-27
### Changed
- Allow None for jitter keyword arg (typing)


## [v2.0.0] - 2022-04-26
### Added
- Add raise_on_giveup keyword arg for decorators
- Add backoff.runtime wait generator for dynamically setting wait times based
  on target function return value or exception details
### Changed
- Improve type hints for on_success, on_backoff, on_giveup handlers
- Use decorator-specific detail and handler type hints
- Optionally use typing_extensions for python 3.7 type hinting
- Drop python 3.6 support
- Add python 3.10 support

## [v1.11.1] - 2021-07-14
### Fixed
- Update __version__ in backoff module

## [v1.11.0] - 2021-07-12
### Added
- Configurable logging levels for backoff and giveup events
### Changed
- Minor documentation fixes

## [v1.10.0] - 2019-12-07
### Changed
- Allow sync decorator call from async function
- NOTE: THIS WILL BE THE FINAL PYTHON 2.7 COMPATIBLE RELEASE.

## [v1.9.2] - 2019-11-19
### Changed
- Don't include tests and changelog in distribution

## [v1.9.1] - 2019-11-18
### Changed
- Include tests and changelog in distribution

## [v1.9.0] - 2019-11-16
### Changed
- Support python 3.8

## [v1.8.1] - 2019-10-11
### Changed
- Use arguments in log messages rather than fully formatting log
  https://github.com/litl/backoff/pull/82 from @lbernick

## [v1.8.0] - 2018-12-20
### Added
- Custom loggers
- Iterable intervals for constant wait_gen for predefined wait sequences
### Changed
- Give up on StopIteration raised in wait generators
- Nullary jitter signature deprecation warning

## [v1.7.0] - 2018-11-23
### Changed
- Support Python 3.7
- Drop support for async in Python 3.4
- Drop support for Python 2.6
- Update development dependencies
- Use poetry for dependencies and packaging

## [v1.6.0] - 2018-07-14
### Changed
- Change default log level from ERROR to INFO
- Log retries on exception as INFO

## [v1.5.0] - 2018-04-11
### Added
- Add max_time keyword argument

## [v1.4.3] - 2017-05-22
### Changed
- Add license to source distribution

## [v1.4.2] - 2017-04-25
### Changed
- Use documented logger name https://github.com/litl/backoff/pull/32
  from @pquentin

## [v1.4.1] - 2017-04-21
### Added
- Expose __version__ at package root
### Changed
- Fix checking for running sync version in coroutine in case when event
  loop is not set from @rutsky

## [v1.4.0] - 2017-02-05
### Added
- Async support via `asyncio` coroutines (Python 3.4) from @rutsky
### Changed
- Refactor `backoff` module into package with identical API

## [v1.3.2] - 2016-11-18
### Changed
- Don't log retried args and kwargs by default
- README.rst syntax highlighting from @dethi

## [v1.3.1] - 2016-08-08
### Changed
- Include README.rst in source distribution (fixes package)

## [v1.3.0] - 2016-08-08
### Added
- Support runtime configuration with optional callable kwargs
- Add giveup kwarg for exception inspection
### Changed
- Documentation fixes

## [v1.2.1] - 2016-05-27
### Changed
- Documentation fixes


## [v1.2.0] - 2016-05-26
### Added
- 'Full jitter' algorithm from @jonascheng

### Changed
- Jitter function now accepts raw value and returns jittered value
- Change README to reST for the benefit of pypi :(
- Remove docstring doc generation and make README canonical

## [v1.1.0] - 2015-12-08
### Added
- Event handling for success, backoff, and giveup
- Change log
### Changed
- Docs and test for multi exception invocations
- Update dev environment test dependencies

## [v1.0.7] - 2015-02-10
### Changed
- Fix string formatting for python 2.6

## [v1.0.6] - 2015-02-10
### Added
- Coveralls.io integration from @singingwolfboy
### Changed
- Fix logging bug for function calls with tuple params

## [v1.0.5] - 2015-02-03
### Changed
- Add a default interval of 1 second for the constant generator
- Improve on_predicate stop condition avoiding extra sleep

## [v1.0.4] - 2014-08-12
### Added
- Python 2.6 support from @Bonko
- Python 3.0 support from @robyoung
- Run tests in Travis from @robyoung

## [v1.0.3] - 2014-06-05
### Changed
- Make logging unicode safe
- Log on_predicate backoff as INFO rather than ERROR
