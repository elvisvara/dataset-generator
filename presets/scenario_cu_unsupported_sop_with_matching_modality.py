#!/usr/bin/env python3
"""
fyi, matching modality just means that the modality indeed matches the sopclass uid of the "unsupported dicom"
Generate one current study where one DICOM is unsupported because its SOPClassUID is set to
the Encapsulated PDF UID (1.2.840.10008.5.1.4.1.1.104.1) and its Modality is overridden to "OT"
(Other) so that the unsupported type is consistent.
"""

from presets.scenario_base import (
    ScenarioBase,
    random_uid,
    random_six_digit,
    random_date_yyyymmdd
)
import json

class ScenarioCuUnsupportedSOPWithMatchingModality(ScenarioBase):
    SCENARIO_NAME = "cu_unsupported_sop_with_matching_modality"

    def build_scenario_config(self):
        config = super().build_scenario_config()
        images = config["current_study"]["images"]
        if images:
            bad_img = images[-1]["tags"]
            bad_img["SeriesDescription"] = "Current w/ Unsupported SOP (Matching Modality)"
            bad_img["force_unsupported_dicom"] = True
            bad_img["SOPClassUID"] = "1.2.840.10008.5.1.4.1.1.104.1"
            bad_img["Modality"] = "OT"
        return config

if __name__ == "__main__":
    scenario = ScenarioCuUnsupportedSOPWithMatchingModality()
    config = scenario.build_scenario_config()
    print(json.dumps(config, indent=2))
