"""
ScenarioPidMismatch:
- Generates a normal "current" study of 4 MG images with a certain patient ID.
- Also generates an "internal" prior with 4 MG images that have a *different* patient ID.

Goal:
- Illustrate how an internal prior might get skipped or cause confusion if its 
  PatientID doesn't match the current study's PatientID (some systems enforce a match).
- This scenario is specifically *not* external-prior-based. Both studies are "internal";
  they just differ by patient ID, which can trigger mismatch logic in ingestion.
"""

import random
from presets.scenario_base import ScenarioBase

class ScenarioPidMismatch(ScenarioBase):
    SCENARIO_NAME = "pr_pid_mismatch"

    def build_scenario_config(self):
        """
        We produce:
          - 1 current study (4 MG images) with a 'normal' patient ID
            (e.g. 6-digit or UID-like).
          - 1 'internal' prior with 4 MG images that have a *different* ID.
        """
        config = super().build_scenario_config()

        cur_study = config["current_study"]
        if cur_study["images"]:
            first_img_tags = cur_study["images"][0]["tags"]
            normal_id = str(random.randint(100000, 999999))
            first_img_tags["PatientID"] = normal_id

            for imgobj in cur_study["images"]:
                imgobj["tags"]["PatientID"] = normal_id

            cur_study["images"][-1]["tags"]["StudyDescription"] = \
                "Current Study (PID Mismatch Demo)"

        mismatch_prior = self.create_prior_config(is_cancerous=False)
        if mismatch_prior["images"]:
            mismatch_id = str(random.randint(100000, 999999))
            while mismatch_id == normal_id:
                mismatch_id = str(random.randint(100000, 999999))

            for imgobj in mismatch_prior["images"]:
                imgobj["tags"]["PatientID"] = mismatch_id

            mismatch_prior["images"][-1]["tags"]["SeriesDescription"] = \
                "Internal Prior with Different PID"

        config["internal_priors"].append(mismatch_prior)

        return config