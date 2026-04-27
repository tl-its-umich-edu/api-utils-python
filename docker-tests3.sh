#!/bin/bash

set -euo pipefail

VERSIONS=("3.11" "3.12" "3.13" "3.14")
LOG_DIR="$(mktemp -d)"
FAILED=0

for version in "${VERSIONS[@]}"; do
	log_file="$LOG_DIR/python-${version}.log"
	if docker run --rm --name "api-utils-${version//./-}" \
		-v "$PWD":/usr/src/myapp \
		-w /usr/src/myapp \
		"python:${version}-slim" \
		bash -lc "pip install -q '.[test]' && pytest -q" >"$log_file" 2>&1; then
		echo "python:${version}-slim PASS"
		rm -f "$log_file"
	else
		echo "python:${version}-slim FAIL"
		echo "Last 40 lines from $log_file:"
		tail -n 40 "$log_file"
		FAILED=1
	fi
done

if [ "$FAILED" -eq 0 ]; then
	rmdir "$LOG_DIR"
	echo "All Docker test runs passed for: ${VERSIONS[*]}"
else
	echo "One or more Docker test runs failed. Full logs are in: $LOG_DIR"
	exit 1
fi
