#!/usr/bin/env python3
"""
Generate two external prior studies for MASC cases.
For each external prior study:
  - Patient details (name, birthdate, and PatientID) are fixed, matching typical MASC DICOM values.
  - Unique values (UIDs, study date, study ID, accession number, etc.) are generated randomly.
  - Each study produces 4 DICOMs (one for each standard MG view).
  - A custom file name is added to each DICOM (in the tag "CustomFileName") in the format:
      MascExtPrior_Study<studyIndex>_<View>_<InstanceNumber>.dcm

we can later update the fixed patient details if we wanna create an ext. prior for another study.
"""

from presets.scenario_base import (
    ScenarioBase,
    random_uid,
    random_six_digit,
    random_date_yyyymmdd,
)
import random
import json

class ScenarioMascExtPrior(ScenarioBase):
    SCENARIO_NAME = "masc_ext_prior"

    # Fixed patient details for a typical MASC DICOM
    STATIC_PATIENT_NAME = "Dummy_31955^TestVornamee"
    STATIC_PATIENT_BIRTHDATE = "19660101"
    STATIC_PATIENT_ID = "1.2.276.0.85.049.20.55.0000000270"

    def __init__(self):
        super().__init__()
        self.patient_name = self.STATIC_PATIENT_NAME
        self.birth_date_yyyymmdd = self.STATIC_PATIENT_BIRTHDATE
        self.patient_id = self.STATIC_PATIENT_ID

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
            # Override fields to mimic a MASC DICOM:
            tags["ImageType"] = "DERIVED\\PRIMARY\\\\LEFT"  
            tags["Manufacturer"] = "SIEMENS"
            tags["ManufacturerModelName"] = "Mammomat Novation DR"
            # Set fixed patient details:
            tags["PatientName"] = self.patient_name
            tags["PatientBirthDate"] = self.birth_date_yyyymmdd
            tags["PatientID"] = self.patient_id
            # Add a descriptive custom file name
            tags["CustomFileName"] = f"MascExtPrior_Study{study_index}_{vp}_{i+1}.dcm"
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
    scenario = ScenarioMascExtPrior()
    config = scenario.build_scenario_config()
    print(json.dumps(config, indent=2))
