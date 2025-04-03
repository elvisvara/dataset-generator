#!/usr/bin/env python3
"""
Generate two external prior studies for Mammasoft cases. In each study:
  - Patient details (name and birthdate) are fixed—but the patient name is inverted
    (the given name and family name are swapped).
  - Unique values (UIDs, study date, study ID, accession number, etc.) are generated randomly.
  - Each study produces 4 DICOMs (one for each standard MG view).
  - A custom file name is added to each DICOM (in the tag "CustomFileName") in the format:
      MammasoftExtPrior_Study<studyIndex>_<View>_<InstanceNumber>.dcm

Good thing here is you can later update the fixed patient details with data from another DICOM if needed.
"""

from presets.scenario_base import (
    ScenarioBase,
    random_uid,
    random_six_digit,
    random_date_yyyymmdd,
    parse_yyyymmdd,
    format_yyyymmdd,
)
import random
import json

# Helper function to invert a DICOM patient name formatted as "Family^Given"
def invert_name(name):
    parts = name.split("^")
    if len(parts) == 2:
        return f"{parts[1]}^{parts[0]}"
    return name

class ScenarioMammasoftExternalPriorTwo(ScenarioBase):
    SCENARIO_NAME = "mammasoft_ext_prior_two"

    # Fixed patient details – update these as needed.
    STATIC_PATIENT_NAME = "TC303A^Klientin-1"  # normally in the form Family^Given
    STATIC_PATIENT_BIRTHDATE = "19630330"

    def __init__(self):
        super().__init__()
        self.patient_name = invert_name(self.STATIC_PATIENT_NAME)
        self.birth_date_yyyymmdd = self.STATIC_PATIENT_BIRTHDATE

    def create_external_prior_config(self, is_cancerous=False, study_index=1):
        """
        Generate a configuration for an external prior study.
        Unique fields such as UIDs, study date, study ID, and accession number are generated randomly.
        The accession number is built as a six-digit number plus a hyphen and a random 4-digit number.
        For each of the 4 standard MG views, a custom file name is added under "CustomFileName".
        """
        study_uid = random_uid()
        study_id = random_six_digit()
        accession = f"{random_six_digit()}-{random.randint(1000, 9999)}"
        external_date = random_date_yyyymmdd(2000, 2020)
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
            tags["StudyDescription"] += " - External Prior (Mammasoft)"
            tags["SeriesDescription"] += " - Preset: " + self.SCENARIO_NAME
            tags["cancerous"] = is_cancerous
            tags["InstanceNumber"] = i + 1
            tags["CustomFileName"] = f"MammasoftExtPrior_Study{study_index}_{vp}_{i+1}.dcm"
            images.append({"tags": tags})
        return {
            "cancerous": is_cancerous,
            "count": len(images),
            "images": images
        }

    def build_scenario_config(self):
        """
        Build the overall configuration.
        The current study is empty and there are no internal priors.
        Two external prior studies are generated.
        """
        external_prior1 = self.create_external_prior_config(is_cancerous=False, study_index=1)
        external_prior2 = self.create_external_prior_config(is_cancerous=False, study_index=2)
        return {
            "current_study": {"cancerous": False, "count": 0, "images": []},
            "internal_priors": [],
            "external_priors": [external_prior1, external_prior2]
        }

if __name__ == "__main__":
    scenario = ScenarioMammasoftExternalPriorTwo()
    config = scenario.build_scenario_config()
    print(json.dumps(config, indent=2))
