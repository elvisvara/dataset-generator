## Overview
This tool helps us **create DICOM studies** quickly, **tweak** their details, and **test ingestion** with various scenarios.

---

## Key Features

1. **Generate DICOM Datasets via Preset Mode**  
   There are somne pre-made scenarios like `pr_bits_mismatch`, `pr_private_tag`, etc. (all listed in the `/presets` folder).  
   There are presets for external prior study generation which you can adapt to generate external priors for Masc or Mammasoft by editing the patient details (like name and DOB).

2. **Generate DICOM Datasets via Power Customization**  
   This feature lets you design your own DICOM dataset using a JSON config. You control nearly every DICOM tag.

3. **Automated End-to-End Testing**  
   The `run_all_scenarios.sh` script automates all presets you choose: generation → ingestion → DB verification.

---

## How It Works (just an oveerviewl)

1. **Generation**  
    script calls a Python file (`generate_dicom_dataset.py`) to generate DICOM datasets for chosen scenarios.  
2. **Merging**  
   It copies all generated DICOM and JSON files into one **merged_dataset** folder.  
3. **Ingestion**  
   It runs the Clojure ingestion runner and waits for a sentinel file that signals completion.  
4. **Verification**  
   Finally, it queries the DB remotely (via SSH) to ensure the correct records are ingested.

---

## Prerequisites
1. **Python 3** (for the dataset generation)  
2. **Node.js** (for the Electron/React UI)  
3. **Clojure** (to run the ingestion runner)  
4. **SSH Key** (so the scripts can connect to the remote DB if you’re using that flow)

---

## Running the Electron App
```bash
npm start
```
That launches the UI in Electron, where you can pick folders, scenarios, or customize everything.

---

## Using the Python Scripts Directly
```bash
# List all preset scenarios
python3 generate_dicom_dataset.py --output . --list-scenarios

# Generate a scenario
python3 generate_dicom_dataset.py --output /path/to/out --scenario cu_bits_mismatch

# Or use the wizard approach (if you have a config.json from the UI)
python3 generate_dicom_dataset.py --output /path/to/out --power-customize config.json
```

---

## Automated Testing & Scripts
```bash
chmod +x run_all_scenarios.sh
./run_all_scenarios.sh
```
This does the full flow of generating, merging, ingesting, and verifying in the DB.

---

## requirements.txt
We have a simple `requirements.txt`:
```
numpy
pydicom
Pillow
```
Just install with:
```bash
pip install -r requirements.txt
```
in your Python environment.

---

## .env File
 secrets or override paths to be stored here, create a **.env**:

```bash
# .env example
DB_PW="yoursupersecret"
PRODUCT_CORE="/path/to/ingestion/folder"
SSH_BASTION=""
SSH_TARGET=""
PY_VENV=""
BOLUS2_PARTNER_NAME=""
BOLUS2_PASSWORD=""
```

---

## Folder Overview

- **`generate_dicom_dataset.py`**  
  The main Python script for generating DICOM datasets. Handles both preset scenarios and “power customize” mode.
- **`/presets/`**  
  Contains preset scenario files (like `scenario_cu_bits_mismatch.py`, etc.).
- **`run_all_scenarios.sh`**  
  A Bash script for automated generation, merging, ingestion, and DB verification.
- **`ingest_runner.clj`**  
  Clojure script that actually ingests the merged dataset into the system.
- **`src/PowerCustomizeWizard.jsx`**  
  An Electron/React component for the “power customize” UI.
- **`/presets/scenario_base.py`**  
  A base class providing default logic and common methods for scenarios.
```