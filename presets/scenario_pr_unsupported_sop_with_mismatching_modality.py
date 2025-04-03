#!/usr/bin/env python3
"""
fyi, mismatching modality just means that the modality deos not match the sopclass uid of the "unsupported dicom"
Generate one internal prior study where one DICOM is an unsupported Encapsulated PDF,
simulated by setting its SOPClassUID to the encapsulated PDF UID (1.2.840.10008.5.1.4.1.1.104.1).
However, we do NOT override the Modality field, so it remains "MG".
"""

from presets.scenario_base import (
    ScenarioBase,
    random_uid,
    random_six_digit,
    random_date_yyyymmdd
)
import json

class ScenarioPrUnsupportedSOPWithMismatchingModality(ScenarioBase):
    SCENARIO_NAME = "pr_unsupported_sop_with_mismatching_modality"

    def build_scenario_config(self):
        config = super().build_scenario_config()
        prior = self.create_prior_config(is_cancerous=False)
        if prior["images"]:
            prior["images"][-1]["tags"]["SeriesDescription"] = "Unsupported DICOM (Encapsulated PDF) with mismatching modality"
            prior["images"][-1]["tags"]["force_unsupported_dicom"] = True
            prior["images"][-1]["tags"]["SOPClassUID"] = "1.2.840.10008.5.1.4.1.1.104.1"
        config["internal_priors"].append(prior)
        return config

if __name__ == "__main__":
    scenario = ScenarioPrUnsupportedSOPWithMismatchingModality()
    config = scenario.build_scenario_config()
    print(json.dumps(config, indent=2))
