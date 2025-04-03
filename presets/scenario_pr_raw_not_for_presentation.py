#!/usr/bin/env python3
"""
Generate one internal prior study simulating a raw DICOM not meant for presentation.
This is achieved by setting PresentationIntentType to "RAW" and adding a flag 'force_raw_dicom'.
"""

from presets.scenario_base import (
    ScenarioBase,
    random_uid,
    random_six_digit,
    random_date_yyyymmdd
)
import json

class ScenarioPrRawNotForPresentation(ScenarioBase):
    SCENARIO_NAME = "pr_raw_not_for_presentation"

    def build_scenario_config(self):
        config = super().build_scenario_config()
        prior = self.create_prior_config(is_cancerous=False)
        if prior["images"]:
            for img in prior["images"]:
                img["tags"]["PresentationIntentType"] = "RAW"
            prior["images"][-1]["tags"]["force_raw_dicom"] = True
            prior["images"][-1]["tags"]["SeriesDescription"] = "Raw DICOM (Not for Presentation)"
        config["internal_priors"].append(prior)
        return config

if __name__ == "__main__":
    scenario = ScenarioPrRawNotForPresentation()
    config = scenario.build_scenario_config()
    print(json.dumps(config, indent=2))
