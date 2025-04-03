#!/usr/bin/env python3
"""
Generate two external prior studies for Mammasoft but use "mg" (lowercase)
as the Modality (instead of "MG"). Also invert the patient name.. this seems to be an issue with our ORTHANC configuration.. a ticket has been raised for this an we need to fixn this
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
    parts = name.split("^")
    if len(parts) == 2:
        return f"{parts[1]}^{parts[0]}"
    return name

class ScenarioMammasoftExtPriorVariantModality(ScenarioBase):
    SCENARIO_NAME = "mammasoft_ext_prior_variant_modality"

    STATIC_PATIENT_NAME = "TC303A^Klientin-1"
    STATIC_PATIENT_BIRTHDATE = "19630330"

    def __init__(self):
        super().__init__()
        self.patient_name = invert_name(self.STATIC_PATIENT_NAME)
        self.birth_date_yyyymmdd = self.STATIC_PATIENT_BIRTHDATE

    def create_external_prior_config(self, study_index=1):
        study_uid = random_uid()
        study_id = random_six_digit()
        accession = f"{random_six_digit()}-{random.randint(1000, 9999)}"
        external_date = random_date_yyyymmdd(2010, 2020)

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
            # Use "mg" instead of "MG"
            tags["Modality"] = "mg"
            tags["StudyDescription"] += " - External Prior (Variant Mod)"
            tags["SeriesDescription"] += " - 'mg'"
            tags["InstanceNumber"] = i + 1
            tags["CustomFileName"] = f"MammasoftExtVarMod_Study{study_index}_{vp}_{i+1}.dcm"
            images.append({"tags": tags})

        return {
            "cancerous": False,
            "count": len(images),
            "images": images
        }

    def build_scenario_config(self):
        ext_prior1 = self.create_external_prior_config(study_index=1)
        ext_prior2 = self.create_external_prior_config(study_index=2)

        return {
            "current_study": {"cancerous": False, "count": 0, "images": []},
            "internal_priors": [],
            "external_priors": [ext_prior1, ext_prior2]
        }

if __name__ == "__main__":
    scenario = ScenarioMammasoftExtPriorVariantModality()
    config = scenario.build_scenario_config()
    print(json.dumps(config, indent=2))
