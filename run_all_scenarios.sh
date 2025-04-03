#!/usr/bin/env bash
set -euo pipefail

# 1) LOAD .env FOR SECRETS & ENV VARS 
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/.env" ]; then
  # Export all variables from .env (ignoring commented lines)
  export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
fi

# Ensure DB_PW is set (from .env or environment)
DB_PW="${DB_PW:-}"
if [ -z "$DB_PW" ]; then
  echo "[ERROR] DB_PW is not set. Please define it in .env or environment."
  exit 1
fi

# 2) COLORS & SYMBOLS
GREEN_CHECK="\033[0;32m\xE2\x9C\x94\033[0m"  
RED_X="\033[0;31m\xE2\x9C\x97\033[0m"       


# 4) PHASE 1: GENERATE STUDIES FOR ALL SCENARIOS
echo "================================================================"
echo "Phase 1: Generating studies (all scenarios)..."
echo "================================================================"

PY_VENV="${PY_VENV:-"/Users/elvis/Desktop/SUH/venv"}"
if [ -d "$PY_VENV" ]; then
  echo "[INFO] Activating Python venv: $PY_VENV"
  source "$PY_VENV/bin/activate"
else
  echo "[WARN] No local venv detected at '$PY_VENV'; using system Python..."
fi

GEN_SCRIPT="${GEN_SCRIPT:-"$SCRIPT_DIR/generate_dicom_dataset.py"}"

OUTPUT_BASE="${OUTPUT_BASE:-"$SCRIPT_DIR/generated_data"}"

# Full scenario list
SCENARIO_LIST=(
 
  "cu_private_tag"

)

echo "[INFO] Using GEN_SCRIPT='$GEN_SCRIPT'"
echo "[INFO] Output base folder='$OUTPUT_BASE'"
echo

for SCEN in "${SCENARIO_LIST[@]}"; do
  echo "[INFO] Generating scenario: $SCEN"
  python3 "$GEN_SCRIPT" --output "$OUTPUT_BASE" --scenario "$SCEN" > /dev/null
  if [ $? -ne 0 ]; then
    echo "[ERROR] Generation failed for scenario '$SCEN'"
  else
    echo "[INFO] Generation succeeded for scenario '$SCEN'"
  fi
done

echo "[INFO] All generation complete."

# 5) PHASE 2: MERGE GENERATED DATASETS
echo "================================================================"
echo "Phase 2: Merging generated datasets..."
echo "================================================================"

MERGED_DIR="$OUTPUT_BASE/merged_dataset"
mkdir -p "$MERGED_DIR/dicoms" "$MERGED_DIR/jsons"

# Copy DICOMs and JSON files from each scenario folder
for SCEN_DIR in "$OUTPUT_BASE"/scenario_*_dataset; do
  if [ -d "$SCEN_DIR/dicoms" ]; then
    echo "[MERGE] Merging dicoms from $(basename "$SCEN_DIR")"
    cp -R "$SCEN_DIR/dicoms/." "$MERGED_DIR/dicoms/"
  fi
  if [ -d "$SCEN_DIR/jsons" ]; then
    echo "[MERGE] Merging JSON files from $(basename "$SCEN_DIR")"
    cp -R "$SCEN_DIR/jsons/." "$MERGED_DIR/jsons/"
  fi
done
echo "[INFO] Merged dataset is at: $MERGED_DIR"


# 6) PHASE 3: INGEST MERGED DATASET AND WAIT FOR COMPLETION

echo "================================================================"
echo "Phase 3: Ingesting merged dataset..."
echo "================================================================"

PRODUCT_CORE="${PRODUCT_CORE:-"$SCRIPT_DIR"}"
if [ -d "$PRODUCT_CORE" ]; then
  echo "[INFO] Changing dir to '$PRODUCT_CORE' for ingestion..."
  cd "$PRODUCT_CORE" || {
    echo "[ERROR] Could not cd into '$PRODUCT_CORE'"
    exit 1
  }
fi

INGEST_RUNNER="${INGEST_RUNNER:-"$SCRIPT_DIR/ingest_runner.clj"}"

echo "[INFO] Starting ingestion..."
clojure -M:dev -i "$INGEST_RUNNER" --main ingest-runner "$MERGED_DIR"

SENTINEL="$MERGED_DIR/ingestion_complete.txt"
echo "[INFO] Waiting for ingestion completion signal..."
while [ ! -f "$SENTINEL" ]; do
  sleep 5
done

echo "[INFO] Ingestion complete signal detected."
echo "[INFO] Waiting an extra 20 seconds to allow DB updates..."
sleep 20


# 7) PHASE 4: QUERY & VERIFY STUDIES

cd "$SCRIPT_DIR" || true

echo "================================================================"
echo "Phase 4: Querying database for ingested studies..."
echo "================================================================"
echo "[INFO] Retrieving 'study_instance_uid' from merged JSON files..."

# parse each scenario's study UID, then run a DB query over SSH.
SSH_BASTION="${SSH_BASTION:-"elvisawanchiri@80.158.20.203:20389"}"
SSH_TARGET="${SSH_TARGET:-"elvisawanchiri@192.168.128.104"}"

for SCEN in "${SCENARIO_LIST[@]}"; do

  # Extract the first matching study_instance_uid from JSON
  STUDY_UID=$(
    jq -r --arg scen "$SCEN" '
      select((.study_description // "") | contains($scen))
      | .study_instance_uid // empty
    ' "$MERGED_DIR"/jsons/*.json | head -n 1
  )

  if [ -z "$STUDY_UID" ]; then
    echo "[WARN] No study_instance_uid found in JSON for '$SCEN'. Skipping..."
    continue
  fi

  # Prepare the remote command
  SSH_CMD=$(cat <<EOF
export PGPASSWORD="$DB_PW"
COUNT=\$(psql -h 192.168.128.153 -d edge -U root -t -A -c \
"SELECT COUNT(*) FROM study WHERE instance_uid = '$STUDY_UID';" \
| sed 's/^ *//;s/ *\$//')

echo "\${COUNT:-0}"
EOF
)

  RESULT_STR=$(ssh -J "$SSH_BASTION" "$SSH_TARGET" "$SSH_CMD" || echo "0")

  COUNT=${RESULT_STR:-0}

  if [ "$COUNT" -gt 0 ]; then
    echo -e "${GREEN_CHECK} [RESULT] $SCEN ingestion succeeded (found $COUNT record(s))."
  else
    echo -e "${RED_X} [RESULT] $SCEN ingestion failed (found 0 records)."
  fi
done

echo
echo "[INFO] Ingestion verification completed."
echo "[INFO] All done."
