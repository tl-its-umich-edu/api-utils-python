#!/bin/bash

set -euo pipefail

VERSIONS=("3.11" "3.12" "3.13" "3.14")
VERBOSE=0
SELECTED_VERSION=""

# Parse arguments: optional -v flag and optional Python version
for arg in "$@"; do
	case "$arg" in
		-v|--verbose) VERBOSE=1 ;;
		*) SELECTED_VERSION="$arg" ;;
	esac
done

if [ -n "$SELECTED_VERSION" ]; then
	if [[ ! " ${VERSIONS[*]} " =~ " ${SELECTED_VERSION} " ]]; then
		echo "Unsupported Python version: $SELECTED_VERSION"
		echo "Supported versions: ${VERSIONS[*]}"
		echo "Usage: ./docker-tests3.sh [-v] [3.11|3.12|3.13|3.14]"
		exit 2
	fi
	RUN_VERSIONS=("$SELECTED_VERSION")
else
	RUN_VERSIONS=("${VERSIONS[@]}")
fi

# -v shows test names; default (-q) shows just dots and summary
PYTEST_FLAGS="-q"
if [ "$VERBOSE" -eq 1 ]; then
	PYTEST_FLAGS="-v"
fi

LOG_DIR="$(mktemp -d)"
FAILED=0

for version in "${RUN_VERSIONS[@]}"; do
	log_file="$LOG_DIR/python-${version}.log"
	echo "--- python:${version}-slim ---"
	# Always suppress pip noise; stream pytest output directly to terminal
	if docker run --rm --name "api-utils-${version//./-}" \
		-v "$PWD":/usr/src/myapp \
		-w /usr/src/myapp \
		"python:${version}-slim" \
		bash -lc "pip install -q '.[test]' 2>/dev/null && pytest ${PYTEST_FLAGS}" \
		2>"$log_file"; then
		echo "python:${version}-slim PASS"
		rm -f "$log_file"
	else
		echo "python:${version}-slim FAIL"
		if [ -s "$log_file" ]; then
			echo "Errors:"
			cat "$log_file"
		fi
		FAILED=1
	fi
	echo ""
done

if [ "$FAILED" -eq 0 ]; then
	rmdir "$LOG_DIR"
	echo "All Docker test runs passed for: ${RUN_VERSIONS[*]}"
else
	echo "One or more Docker test runs failed."
	exit 1
fi
