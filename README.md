# Python Umich API Utilities

Utilities to simplify connecting to and using University of Michigan APIs from Python.

## Features

- Supports GET/POST/PUT/DELETE/HEAD/OPTIONS calls against APIs defined in the directory.
- Automatically obtains and renews OAuth tokens for long-running applications.
- Supports custom API configuration.
- Applies configured rate limits per API scope.
- Supports pagination via `get_next_page`.

## Installation

Install locally:

```bash
pip install .
```

Install with test dependencies:

```bash
pip install -e '.[test]'
```

Install from GitHub tag (example):

```bash
pip install git+https://github.com/tl-its-umich-edu/api-utils-python@v4.0.0
```

## Testing

Run local mocked tests (no external services required):

```bash
pytest
```

Run integration tests (real service calls):

1. Copy `tests/.env.sample` to `tests/.env`.
2. Fill in `url`, `client_id`, and `secret`.
3. Run:

```bash
pytest tests/test_integration.py
```

Integration tests are skipped automatically when required credentials are missing.

Run the Docker multi-version matrix (slim images):

```bash
bash ./docker-tests3.sh
```

This runs tests against Python 3.11, 3.12, 3.13, and 3.14.

## Notes

- This package is currently distributed through the repository (not published on PyPI).
- Please use GitHub issues for bugs and feature requests; pull requests are welcome.

## Future Ideas

- Automatic rate detection from API responses.
- Additional predefined APIs.
- Caching support.
- Improved pagination ergonomics.
