#!/usr/bin/env python3
"""
ScenarioMascExtPriorPatientIDMismatch:
Generate two external prior studies for MASC cases but with a patient ID mismatch.
For each external prior study:
  - Fixed patient details (name and birthdate) are used as in a typical MASC DICOM.
  - The PatientID (DICOM tag (0010,0020)) is randomly generated so that it does not match the expected fixed value.
  - Unique values (UIDs, study date, study ID, accession number, etc.) are generated randomly.
  - Each study produces 4 DICOMs (one for each standard MG view).
  - A custom file name is added to each DICOM (in tag "CustomFileName") in the format:
      MascExtPriorPIDMismatch_Study<studyIndex>_<View>_<InstanceNumber>.dcm
"""

from presets.scenario_base import (
    ScenarioBase,
    random_uid,
    random_six_digit,
    random_date_yyyymmdd,
)
import random
import json

class ScenarioMascExtPriorPatientIDMismatch(ScenarioBase):
    SCENARIO_NAME = "masc_ext_prior_pid_mismatch"

    # Fixed patient details (except PatientID) for a typical MASC DICOM
    STATIC_PATIENT_NAME = "Dummy_31955^TestVornamee"
    STATIC_PATIENT_BIRTHDATE = "19660101"

    def __init__(self):
        super().__init__()
        self.patient_name = self.STATIC_PATIENT_NAME
        self.birth_date_yyyymmdd = self.STATIC_PATIENT_BIRTHDATE
        # For a mismatch, generate a random PatientID that does NOT match the expected value.
        self.patient_id = f"PID-{random.randint(1000000000, 9999999999)}"

    def create_external_prior_config(self, is_cancerous=False, study_index=1):
        study_uid = random_uid()
        study_id = random_six_digit()
        accession = f"{random_six_digit()}-{random.randint(1000, 9999)}"
        external_date = random_date_yyyymmdd(2023, 2025)
        views = ["RCC", "LCC", "RMLO", "LMLO"]
        images = []
        for i, vp in enumerate(views):
            tags = self.make_mg_image_tags(
                view_position=vp,
                is_cancerous=is_cancerous,
                study_uid=study_uid,
                study_date=external_date,
                study_id=study_id,
                accession=accession,
            )
            tags["ImageType"] = "DERIVED\\PRIMARY\\\\LEFT"
            tags["Manufacturer"] = "SIEMENS"
            tags["ManufacturerModelName"] = "Mammomat Novation DR"
            tags["PatientName"] = self.patient_name
            tags["PatientBirthDate"] = self.birth_date_yyyymmdd
            # Override PatientID with the random (mismatched) value.
            tags["PatientID"] = self.patient_id
            tags["CustomFileName"] = f"MascExtPriorPIDMismatch_Study{study_index}_{vp}_{i+1}.dcm"
            images.append({"tags": tags})
        return {
            "cancerous": is_cancerous,
            "count": len(images),
            "images": images
        }

    def build_scenario_config(self):
        ext_prior1 = self.create_external_prior_config(is_cancerous=False, study_index=1)
        ext_prior2 = self.create_external_prior_config(is_cancerous=False, study_index=2)
        return {
            "current_study": {"cancerous": False, "count": 0, "images": []},
            "internal_priors": [],
            "external_priors": [ext_prior1, ext_prior2]
        }

if __name__ == "__main__":
    scenario = ScenarioMascExtPriorPatientIDMismatch()
    config = scenario.build_scenario_config()
    print(json.dumps(config, indent=2))
