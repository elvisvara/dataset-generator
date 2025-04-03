#!/usr/bin/env python3
"""
Generate one internal prior study simulating a tomosynthesis study with a RIS/PACS ID mismatch.
This is achieved by forcing the first image's SOPInstanceUID to a simple numeric string (e.g., "123456"),
while leaving the other images intact.
"""

from presets.scenario_base import (
    ScenarioBase,
    random_uid,
    random_six_digit,
    random_date_yyyymmdd
)
import json

class ScenarioPrTomosynthesisRISPACSMismatch(ScenarioBase):
    SCENARIO_NAME = "pr_tomosynthesis_ris_pacs_mismatch"

    def build_scenario_config(self):
        config = super().build_scenario_config()
        prior = self.create_prior_config(is_cancerous=False)
        if prior["images"]:
            # Force the first image's SOPInstanceUID to a simple numeric string.
            prior["images"][0]["tags"]["SOPInstanceUID"] = "123456"
            prior["images"][0]["tags"]["SeriesDescription"] = "Tomosynthesis RIS/PACS Mismatch"
        config["internal_priors"].append(prior)
        return config

if __name__ == "__main__":
    scenario = ScenarioPrTomosynthesisRISPACSMismatch()
    config = scenario.build_scenario_config()
    print(json.dumps(config, indent=2))
