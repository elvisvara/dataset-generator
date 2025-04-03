#!/usr/bin/env python3
"""
ScenarioMammasoftExternalPriorRandomPatientID:
Generate two external prior studies for Mammasoft cases.
For each external prior study:
  - Fixed patient details for name and birthdate are used, but the patient name is inverted (i.e. given and family names are swapped).
  - The PatientID (DICOM tag (0010,0020)) is randomly generated.
  - Unique values (UIDs, study date, study ID, accession number, etc.) are generated randomly.
  - Each study produces 4 DICOMs (one for each standard MG view).
  - A descriptive custom file name is added to each DICOM (in tag "CustomFileName") in the format:
      MammasoftExtPriorRandomPID_Study<studyIndex>_<View>_<InstanceNumber>.dcm

You can later update the fixed patient details with data from another DICOM if needed.
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

class ScenarioMammasoftExternalPriorRandomPatientID(ScenarioBase):
    SCENARIO_NAME = "mammasoft_ext_prior_random_pid"

    # Fixed patient details – update these as needed.
    STATIC_PATIENT_NAME = "TC301A^Klientin-1"  # normally in the form Family^Given
    STATIC_PATIENT_BIRTHDATE = "19630130"

    def __init__(self):
        super().__init__()
        # Override patient details: invert the patient name and use the fixed birthdate.
        self.patient_name = invert_name(self.STATIC_PATIENT_NAME)
        self.birth_date_yyyymmdd = self.STATIC_PATIENT_BIRTHDATE
        # Randomly generate a new patient ID (DICOM tag (0010,0020)).
        # Here we create a 10-digit random number prefixed with "PID-"
        self.patient_id = f"PID-{random.randint(1000000000, 9999999999)}"

    def create_external_prior_config(self, is_cancerous=False, study_index=1):
        """
        Generate a configuration for an external prior study.
        Unique fields (UIDs, study date, study ID, accession number) are generated randomly.
        Each of the 4 standard MG views gets a descriptive custom file name.
        """
        study_uid = random_uid()
        study_id = random_six_digit()
        # Generate a unique accession number: 6-digit number plus a hyphen and a random 4-digit number.
        accession = f"{random_six_digit()}-{random.randint(1000, 9999)}"
        # Generate an external prior study date between 2000 and 2020.
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
            tags["StudyDescription"] += " - External Prior (Mammasoft) with Random PID"
            tags["SeriesDescription"] += " - Preset: " + self.SCENARIO_NAME
            tags["cancerous"] = is_cancerous
            tags["InstanceNumber"] = i + 1
            # Set a custom file name to aid identification in the viewer.
            tags["CustomFileName"] = f"MammasoftExtPriorRandomPID_Study{study_index}_{vp}_{i+1}.dcm"
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
    # For testing: print the generated configuration as JSON.
    scenario = ScenarioMammasoftExternalPriorRandomPatientID()
    config = scenario.build_scenario_config()
    print(json.dumps(config, indent=2))
