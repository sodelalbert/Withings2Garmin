#!/bin/bash

# Set reports directory variable

isort_status=0
black_status=0
flake8_status=0
mypy_status=0

# Change to the project root directory
# This ensures the script runs from the correct context
cd "$(dirname "$0")/.."

echo "Running static code analysis..."

TEMP_DIR=$(mktemp -d)

# Run isort
uv run isort . > "$TEMP_DIR/isort_output.txt" 2>&1
isort_status=$?

# Run Black
uv run black . --exclude="\.venv" > "$TEMP_DIR/black_output.txt" 2>&1
black_status=$?

# Run Flake8
uv run flake8 . --exclude=".venv" > "$TEMP_DIR/flake8_report.txt" 2>&1
flake8_status=$?

# Run Mypy
uv run mypy . --exclude="\.venv" > "$TEMP_DIR/mypy_report.txt" 2>&1
mypy_status=$?

# Print Summary
printf "%-8s %s\n" "isort:"  "$([ $isort_status -eq 0 ] && echo '✅' || echo '❌')"
printf "%-8s %s\n" "Black:"  "$([ $black_status -eq 0 ] && echo '✅' || echo '❌')"
printf "%-8s %s\n" "Flake8:" "$([ $flake8_status -eq 0 ] && echo '✅' || echo '❌')"
printf "%-8s %s\n" "Mypy:"   "$([ $mypy_status -eq 0 ] && echo '✅' || echo '❌')"

# Show output of failing checks
if [ $isort_status -ne 0 ]; then
    echo -e "\n--- isort Output ---"
    cat "$TEMP_DIR/isort_output.txt"
fi
if [ $black_status -ne 0 ]; then
    echo -e "\n--- Black Output ---"
    cat "$TEMP_DIR/black_output.txt"
fi
if [ $flake8_status -ne 0 ]; then
    echo -e "\n--- Flake8 Output ---"
    cat "$TEMP_DIR/flake8_report.txt"
fi
if [ $mypy_status -ne 0 ]; then
    echo -e "\n--- Mypy Output ---"
    cat "$TEMP_DIR/mypy_report.txt"
fi

echo
if [ $isort_status -eq 0 ] && [ $black_status -eq 0 ] && [ $flake8_status -eq 0 ] && [ $mypy_status -eq 0 ]; then
    echo "🎉 All checks passed!"
else
    echo "⚠️  Some checks failed. See above for details."
fi

# Clean up reports
rm -rf "$TEMP_DIR"