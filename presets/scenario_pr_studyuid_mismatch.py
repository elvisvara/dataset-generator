# /Users/elvis/Desktop/SUH/presets/scenario_studyuid_mismatch.py

from presets.scenario_base import ScenarioBase
from pydicom.uid import generate_uid

class ScenarioStudyUidMismatch(ScenarioBase):
    SCENARIO_NAME = "pr_studyuid_mismatch"

    def build_scenario_config(self):
        config = super().build_scenario_config()

        prior = self.create_prior_config(is_cancerous=False)
        if prior["images"]:
            tags = prior["images"][-1]["tags"]
            tags["StudyInstanceUID"] = generate_uid()
            tags["SeriesDescription"] = "Study UID Mismatch"
        config["internal_priors"].append(prior)
        return config
