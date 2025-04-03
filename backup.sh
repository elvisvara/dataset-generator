#!/usr/bin/env bash
set -euo pipefail

##############################################################################
# COLORS & SYMBOLS
##############################################################################
GREEN_CHECK="\033[0;32m\xE2\x9C\x94\033[0m"  # "✔" in green
RED_X="\033[0;31m\xE2\x9C\x97\033[0m"       # "✗" in red

##############################################################################
# START SSH AGENT
##############################################################################
eval "$(ssh-agent -s)" >/dev/null 2>&1 || true
ssh-add ~/.ssh/id_ed25519 >/dev/null 2>&1 || true

##############################################################################
# PHASE 1: GENERATE STUDIES FOR ALL SCENARIOS
##############################################################################
echo "================================================================"
echo "Phase 1: Generating studies (all scenarios)..."
echo "================================================================"

# Activate the Python virtual environment
source /Users/elvis/Desktop/SUH/venv/bin/activate

OUTPUT_BASE="/Users/elvis/Desktop/test_suh"
GEN_SCRIPT="/Users/elvis/Desktop/SUH/generate_dicom_dataset.py"

# Full scenario list from your request
SCENARIO_LIST=(
  "pr_bits_mismatch"
  "pr_corrupted_pixel"
  "cu_bits_mismatch"
  "cu_corrupted_pixel"
  "cu_large_dimensions"
  "cu_missing_required_tag"
  "cu_no_pixel_data"
  "cu_null_byte_tag"
  "cu_overly_large_numeric"
  "cu_private_tag"
  "cu_studyuid_mismatch"
  "cu_unsupported_modality"
  "cu_unsupported_sop"
  "pr_large_dimensions"
  "pr_missing_required_tag"
  "pr_no_pixel_data"
  "pr_null_byte_tag"
  "pr_overly_large_numeric"
  "pr_pid_mismatch"
  "pr_private_tag"
  "pr_unsupported_modality"
  "pr_unsupported_sop"
)

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

##############################################################################
# PHASE 2: MERGE GENERATED DATASETS
##############################################################################
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

##############################################################################
# PHASE 3: INGEST MERGED DATASET AND WAIT FOR COMPLETION
##############################################################################
echo "================================================================"
echo "Phase 3: Ingesting merged dataset..."
echo "================================================================"

cd /Users/elvis/edison-product/core || {
  echo "[ERROR] Could not cd into /Users/elvis/edison-product/core"
  exit 1
}

echo "[INFO] Starting ingestion..."
clojure -M:dev -i /Users/elvis/Desktop/SUH/ingest_runner.clj --main ingest-runner "$MERGED_DIR"

SENTINEL="$MERGED_DIR/ingestion_complete.txt"
echo "[INFO] Waiting for ingestion completion signal..."
while [ ! -f "$SENTINEL" ]; do
  sleep 5
done

echo "[INFO] Ingestion complete signal detected."
echo "[INFO] Waiting an extra 20 seconds to allow DB updates..."
sleep 20

##############################################################################
# PHASE 4: QUERY & VERIFY STUDIES
##############################################################################
echo "================================================================"
echo "Phase 4: Querying database for ingested studies..."
echo "================================================================"

echo "[INFO] Retrieving 'study_instance_uid' from merged JSON files..."

DB_PW="9ufcHu-RMU0YLe5sD3I4CogkrbJKQASY"

# We'll loop over each scenario again, parse out the 'study_instance_uid'
# from the merged JSON, then check the DB for row counts.
#
# >0 rows => "ingestion succeeded"
#  0 rows => "ingestion failed"
#

for SCEN in "${SCENARIO_LIST[@]}"; do
  
  # Extract the first matching study_instance_uid from JSON
  STUDY_UID=$(
    jq -r --arg scen "$SCEN" '
      select((.study_description // "") | contains($scen)) 
      | .study_instance_uid // empty
    ' "$MERGED_DIR"/jsons/*.json | head -n 1
  )
  
  # If no UID found, just warn and skip
  if [ -z "$STUDY_UID" ]; then
    echo "[WARN] No study_instance_uid found in JSON for '$SCEN'. Skipping..."
    continue
  fi

  # Query the remote DB
  SSH_CMD=$(cat <<EOF
export PGPASSWORD="$DB_PW"
COUNT=\$(psql -h 192.168.128.153 -d edge -U root -t -A -c \
"SELECT COUNT(*) FROM study WHERE instance_uid = '$STUDY_UID';" \
| sed 's/^ *//;s/ *\$//')

echo "\${COUNT:-0}"
EOF
)

  RESULT_STR=$(ssh -J elvisawanchiri@80.158.20.203:20389 \
               elvisawanchiri@192.168.128.104 "$SSH_CMD" \
               || echo "0")
  
  COUNT=${RESULT_STR:-0}

  # Show final result for this scenario
  if [ "$COUNT" -gt 0 ]; then
    echo -e "${GREEN_CHECK} [RESULT] $SCEN ingestion succeeded (found $COUNT record(s))."
  else
    echo -e "${RED_X} [RESULT] $SCEN ingestion failed (found 0 records)."
  fi
  
done

echo
echo "[INFO] Ingestion verification completed."
echo "[INFO] All done."
