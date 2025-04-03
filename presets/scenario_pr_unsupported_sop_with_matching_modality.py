#!/usr/bin/env python3
"""
fyi, matching modality just means that the modality indeed matches the sopclass uid of the "unsupported dicom"
Generate one internal prior study where one DICOM is an unsupported Encapsulated PDF and has OT in the modality field.
We simulate this by setting its SOPClassUID to the encapsulated PDF UID (1.2.840.10008.5.1.4.1.1.104.1)
and adding a custom flag 'force_unsupported_dicom'.
We also override the Modality to "OT" for this unsupported file.
"""

from presets.scenario_base import (
    ScenarioBase,
    random_uid,
    random_six_digit,
    random_date_yyyymmdd
)
import json

class ScenarioPrUnsupportedSOPWithMatchingModality(ScenarioBase):
    SCENARIO_NAME = "pr_unsupported_sop_with_matching_modality"

    def build_scenario_config(self):
        config = super().build_scenario_config()
        prior = self.create_prior_config(is_cancerous=False)
        if prior["images"]:
            # simulate an unsupported Encapsulated PDF for the last image.
            prior["images"][-1]["tags"]["SeriesDescription"] = "Unsupported DICOM (Encapsulated PDF)"
            prior["images"][-1]["tags"]["force_unsupported_dicom"] = True
            prior["images"][-1]["tags"]["SOPClassUID"] = "1.2.840.10008.5.1.4.1.1.104.1"
            prior["images"][-1]["tags"]["Modality"] = "OT"
        config["internal_priors"].append(prior)
        return config

if __name__ == "__main__":
    scenario = ScenarioPrUnsupportedEncapPDF()
    config = scenario.build_scenario_config()
    print(json.dumps(config, indent=2))
