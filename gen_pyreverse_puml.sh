#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./gen_pyreverse_puml.sh <project_name_or_path> <output_base_dir>
#
# Examples:
#   ./gen_pyreverse_puml.sh gui diagrams/static_analysis
#   ./gen_pyreverse_puml.sh code_extractor/ diagrams/static_analysis
#   ./gen_pyreverse_puml.sh code_extractor diagrams/static_analysis
#
# Output:
#   <output_base_dir>/<project_name>/classes_<project_name>.puml
#   <output_base_dir>/<project_name>/packages_<project_name>.puml

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <project_name_or_path> <output_base_dir>"
  echo "Example: $0 gui diagrams/static_analysis"
  exit 1
fi

INPUT_TARGET="$1"
OUTPUT_BASE="$2"

# Normalize:
# - remove trailing slashes
# - keep only the last path component as project name
INPUT_TARGET="${INPUT_TARGET%/}"
PROJECT_NAME="$(basename "${INPUT_TARGET}")"

# Run pyreverse on the given target
pyreverse -o puml -p "${PROJECT_NAME}" "${INPUT_TARGET}"

CANDIDATE_CLASSES=(
  "classes_${PROJECT_NAME}.puml"
  "classes_${PROJECT_NAME}_.puml"
)
CANDIDATE_PACKAGES=(
  "packages_${PROJECT_NAME}.puml"
  "packages_${PROJECT_NAME}_.puml"
)

find_first_existing() {
  local f
  for f in "$@"; do
    if [[ -f "$f" ]]; then
      echo "$f"
      return 0
    fi
  done
  return 1
}

CLASSES_FILE="$(find_first_existing "${CANDIDATE_CLASSES[@]}")" || {
  echo "ERROR: classes file not found. Tried: ${CANDIDATE_CLASSES[*]}"
  exit 2
}
PACKAGES_FILE="$(find_first_existing "${CANDIDATE_PACKAGES[@]}")" || {
  echo "ERROR: packages file not found. Tried: ${CANDIDATE_PACKAGES[*]}"
  exit 2
}

# Create output directory: <output_base>/<project_name>
OUT_DIR="${OUTPUT_BASE%/}/${PROJECT_NAME}"
mkdir -p "${OUT_DIR}"

# Move generated files into the destination directory
mv -f "${CLASSES_FILE}" "${OUT_DIR}/classes_${PROJECT_NAME}.puml"
mv -f "${PACKAGES_FILE}" "${OUT_DIR}/packages_${PROJECT_NAME}.puml"

echo "Generated PlantUML diagrams:"
echo "- ${OUT_DIR}/classes_${PROJECT_NAME}.puml"
echo "- ${OUT_DIR}/packages_${PROJECT_NAME}.puml"

