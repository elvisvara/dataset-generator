#!/usr/bin/env python3
"""
ScenarioMammasoftExtPriorPartialMR:
Generate two external prior studies for Mammasoft with the following twist:
  - In each external prior study, we create 4 images: 3 are MG, 1 is MR.
  - We invert the patient's name from "Family^Given" to "Given^Family".
  - All other fields (UIDs, date, ID, etc.) are randomly generated.
"""

import random
import json
from presets.scenario_base import (
    ScenarioBase,
    random_uid,
    random_six_digit,
    random_date_yyyymmdd
)

def invert_name(name):
    """
    Invert "Family^Given" => "Given^Family".
    """
    parts = name.split("^")
    if len(parts) == 2:
        return f"{parts[1]}^{parts[0]}"
    return name

class ScenarioMammasoftExtPriorPartialMR(ScenarioBase):
    SCENARIO_NAME = "mammasoft_ext_prior_partial_mr"

    STATIC_PATIENT_NAME = "TC303A^Klientin-1"
    STATIC_PATIENT_BIRTHDATE = "19630330"

    def __init__(self):
        super().__init__()
        # Invert the name, keep the same birthdate
        self.patient_name = invert_name(self.STATIC_PATIENT_NAME)
        self.birth_date_yyyymmdd = self.STATIC_PATIENT_BIRTHDATE

    def create_external_prior_config(self, study_index=1):
        """
        Creates a single external prior with 4 images:
          - The first 3 images are MG.
          - The 4th image is MR (the "faulty" one).
        """
        study_uid = random_uid()
        study_id  = random_six_digit()
        # Accession is 6-digit plus random 4-digit suffix, e.g. "123456-9999"
        accession = f"{random_six_digit()}-{random.randint(1000, 9999)}"
        external_date = random_date_yyyymmdd(2000, 2020)

        # We'll just label the 4 images "RCC", "LCC", "RMLO", "LMLO"
        # but set the Modality differently for the last one.
        views = ["RCC", "LCC", "RMLO", "LMLO"]
        images = []
        for i, vp in enumerate(views):
            tags = self.make_mg_image_tags(
                view_position=vp,
                is_cancerous=False,
                study_uid=study_uid,
                study_date=external_date,
                study_id=study_id,
                accession=accession
            )

            # For the first 3 images, keep MG. For the 4th, switch to MR
            if i < 3:
                tags["Modality"] = "MG"
            else:
                tags["Modality"] = "MR"  # "Faulty" single MR

            tags["StudyDescription"] += " - External Prior (PartialMR)"
            tags["SeriesDescription"] += " - 3MG+1MR"
            tags["InstanceNumber"] = i + 1
            # Add a custom file name
            # e.g. "MammasoftExtPartialMR_Study2_RMLO_3.dcm" for the 3rd image of study 2
            tags["CustomFileName"] = f"MammasoftExtPartialMR_Study{study_index}_{vp}_{i+1}.dcm"
            images.append({"tags": tags})

        return {
            "cancerous": False,
            "count": len(images),
            "images": images
        }

    def build_scenario_config(self):
        """
        Build a scenario with two external prior studies, each having 3 MG + 1 MR.
        """
        ext1 = self.create_external_prior_config(study_index=1)
        ext2 = self.create_external_prior_config(study_index=2)

        # No current study, no internal priors
        return {
            "current_study": {"cancerous": False, "count": 0, "images": []},
            "internal_priors": [],
            "external_priors": [ext1, ext2]
        }

if __name__ == "__main__":
    scenario = ScenarioMammasoftExtPriorPartialMR()
    config = scenario.build_scenario_config()
    print(json.dumps(config, indent=2))
