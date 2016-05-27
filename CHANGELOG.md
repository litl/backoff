# Change Log

## [v1.0.3] - 2014-06-05
### Changed
- Make logging unicode safe
- Log on_predicate backoff as INFO rather than ERROR

## [v1.0.4] - 2014-08-12
### Added
- Python 2.6 support from @Bonko
- Python 3.0 support from @robyoung
- Run tests in Travis from @robyoung

## [v1.0.5] - 2015-02-03
### Changed
- Add a default interval of 1 second for the constant generator
- Improve on_predicate stop condition avoiding extra sleep

## [v1.0.6] - 2015-02-10
### Added
- Coveralls.io integration from @singingwolfboy

### Changed
- Fix logging bug for function calls with tuple params

## [v1.0.7] - 2015-02-10

### Changed
- Fix string formatting for python 2.6

## [v1.1.0] - 2015-12-08
### Added
- Event handling for success, backoff, and giveup
- Change log

### Changed
- Docs and test for multi exception invocations
- Update dev environment test dependencies

## [v1.2.0] - 2016-05-26
### Added
- 'Full jitter' algorithm from @jonascheng

### Changed
- Jitter function now accepts raw value and returns jittered value
- Change README to reST for the benefit of pypi :(
- Remove docstring doc generation and make README canonical

## [v1.2.1] - 2016-05-27
### Changed
- Documentation fixes
