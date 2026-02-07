#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

INPUT_BASE="test/system_testing"
OUT_BASE=""

declare -a TCS=()

usage() {
  echo "Usage: $0 --out <path> [--tc <n|TCn>]... [--input-base <path>]"
  echo "Examples:"
  echo "  $0 --out output/system_testing_pre"
  echo "  $0 --out output/system_testing_pre --tc 7 --tc 11 --tc 16"
  echo "  $0 --out output/system_testing_pre --input-base test/system_testing"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tc)
      [[ $# -ge 2 ]] || { echo "ERROR: --tc requires a value"; exit 2; }
      TCS+=("$2")
      shift 2
      ;;
    --input-base)
      [[ $# -ge 2 ]] || { echo "ERROR: --input-base requires a path"; exit 2; }
      INPUT_BASE="$2"
      shift 2
      ;;
    --out)
      [[ $# -ge 2 ]] || { echo "ERROR: --out requires a path"; exit 2; }
      OUT_BASE="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument '$1'"
      usage
      exit 2
      ;;
  esac
done

if [[ -z "${OUT_BASE}" ]]; then
  echo "ERROR: --out is required (no default is used)."
  usage
  exit 2
fi

cd "${REPO_ROOT}"

if [[ ${#TCS[@]} -eq 0 ]]; then
  for i in $(seq 1 21); do
    TCS+=("$i")
  done
fi

PY_BIN="python"
if [[ -x "${REPO_ROOT}/venv/bin/python" ]]; then
  PY_BIN="${REPO_ROOT}/venv/bin/python"
fi

mkdir -p "${OUT_BASE}/logs"
mkdir -p "${OUT_BASE}/work"

SUMMARY_FILE="${OUT_BASE}/summary.csv"
echo "tc,input_dir,work_dir,output_dir,status,mode,py_files,total_smells,overview_csv,log_file" > "${SUMMARY_FILE}"

trim() { sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//'; }

extract_total_smells() {
  local logfile="$1"
  local n=""
  n="$(grep -E "Total code smells found in project|Total code smells found in all projects|Analysis completed\. Total code smells found:" "${logfile}" \
      | tail -n 1 \
      | sed -E 's/.*: ([0-9]+).*/\1/' \
      | tr -d '\r' \
      | trim || true)"
  echo "${n}"
}

count_py_root() {
  local dir="$1"
  find "${dir}" -maxdepth 1 -type f -name "*.py" 2>/dev/null | wc -l | tr -d ' '
}

count_py_all() {
  local dir="$1"
  find "${dir}" -type f -name "*.py" 2>/dev/null | wc -l | tr -d ' '
}

for tcnum in "${TCS[@]}"; do
  if [[ "${tcnum}" =~ ^TC[0-9]+$ ]]; then
    TC="${tcnum}"
  else
    TC="TC${tcnum}"
  fi

  INPUT_DIR="${INPUT_BASE%/}/${TC}"
  WORK_DIR="${OUT_BASE%/}/work/${TC}"
  OUTPUT_DIR="${OUT_BASE%/}/${TC}"
  LOG_FILE="${OUT_BASE%/}/logs/${TC}.log"

  if [[ ! -d "${INPUT_DIR}" ]]; then
    echo "WARN: input directory not found: ${INPUT_DIR}" | tee "${LOG_FILE}"
    echo "${TC},${INPUT_DIR},${WORK_DIR},${OUTPUT_DIR},SKIP_NO_DIR,,,,,${LOG_FILE}" >> "${SUMMARY_FILE}"
    continue
  fi

  PY_ROOT="$(count_py_root "${INPUT_DIR}")"
  PY_ALL="$(count_py_all "${INPUT_DIR}")"

  if [[ "${PY_ALL}" -eq 0 ]]; then
    echo "SKIP: no .py files in ${INPUT_DIR}" | tee "${LOG_FILE}"
    echo "${TC},${INPUT_DIR},${WORK_DIR},${OUTPUT_DIR},SKIP_NO_PY,,0,,,,${LOG_FILE}" >> "${SUMMARY_FILE}"
    continue
  fi

  rm -rf "${WORK_DIR}"
  mkdir -p "${WORK_DIR}"
  cp -a "${INPUT_DIR}/." "${WORK_DIR}/"

  MODE="single"
  EXTRA_ARGS=()
  if [[ "${PY_ROOT}" -eq 0 ]]; then
    MODE="multiple"
    EXTRA_ARGS+=(--multiple)
  fi

  echo "=== Running ${TC} (${MODE}) ===" > "${LOG_FILE}"
  echo "Input : ${INPUT_DIR}" >> "${LOG_FILE}"
  echo "Work  : ${WORK_DIR}" >> "${LOG_FILE}"
  echo "Output: ${OUTPUT_DIR}" >> "${LOG_FILE}"

  set +e
  "${PY_BIN}" -m cli.cli_runner --input "${WORK_DIR}" --output "${OUTPUT_DIR}" "${EXTRA_ARGS[@]}" >> "${LOG_FILE}" 2>&1
  EXIT_CODE=$?
  set -e

  STATUS="PASS"
  if [[ ${EXIT_CODE} -ne 0 ]]; then
    STATUS="FAIL"
  fi

  TOTAL_SMELLS="$(extract_total_smells "${LOG_FILE}")"
  OVERVIEW_CSV="${OUTPUT_DIR%/}/output/overview.csv"

  if [[ ! -f "${OVERVIEW_CSV}" ]]; then
    if [[ "${STATUS}" == "PASS" ]]; then
      STATUS="PASS_NO_OUTPUT"
    fi
    OVERVIEW_CSV=""
  fi

  echo "${TC},${INPUT_DIR},${WORK_DIR},${OUTPUT_DIR},${STATUS},${MODE},${PY_ALL},${TOTAL_SMELLS},${OVERVIEW_CSV},${LOG_FILE}" >> "${SUMMARY_FILE}"
done

echo "Done."
echo "Summary: ${SUMMARY_FILE}"
echo "Logs   : ${OUT_BASE%/}/logs/"
echo "Work   : ${OUT_BASE%/}/work/"

