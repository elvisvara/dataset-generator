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

        # 1) Overwrite the current study's PatientID so it's stable/clear
        cur_study = config["current_study"]
        if cur_study["images"]:
            first_img_tags = cur_study["images"][0]["tags"]
            # e.g. pick a stable or random "normal" ID, say 6 digits
            normal_id = str(random.randint(100000, 999999))
            first_img_tags["PatientID"] = normal_id

            # Also unify the rest of the current study images
            for imgobj in cur_study["images"]:
                imgobj["tags"]["PatientID"] = normal_id

            # Optionally refine the StudyDescription so we can see it easily
            cur_study["images"][-1]["tags"]["StudyDescription"] = \
                "Current Study (PID Mismatch Demo)"

        # 2) Create an internal prior with a *different* patient ID
        mismatch_prior = self.create_prior_config(is_cancerous=False)
        if mismatch_prior["images"]:
            # Let's pick a second random ID that won't match the current
            mismatch_id = str(random.randint(100000, 999999))
            while mismatch_id == normal_id:
                mismatch_id = str(random.randint(100000, 999999))

            # Overwrite each image's PatientID
            for imgobj in mismatch_prior["images"]:
                imgobj["tags"]["PatientID"] = mismatch_id

            # Tweak the last image's description so it's noticeable
            mismatch_prior["images"][-1]["tags"]["SeriesDescription"] = \
                "Internal Prior with Different PID"

        # 3) Append that mismatch prior to config
        config["internal_priors"].append(mismatch_prior)

        return config