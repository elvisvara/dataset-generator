#!/usr/bin/env python3
"""
fyi, mismatching modality just means that the modality deos not match the sopclass uid of the "unsupported dicom":
Generate one current study where one DICOM is unsupported because its SOPClassUID is set to
the Encapsulated PDF UID (1.2.840.10008.5.1.4.1.1.104.1), but we do not override the Modality.
 modality remains the default (e.g. "MG"), creating a mismatch.
"""

from presets.scenario_base import (
    ScenarioBase,
    random_uid,
    random_six_digit,
    random_date_yyyymmdd
)
import json

class ScenarioCuUnsupportedSOPWithMismatchingModality(ScenarioBase):
    SCENARIO_NAME = "cu_unsupported_sop_with_mismatching_modality"

    def build_scenario_config(self):
        config = super().build_scenario_config()
        images = config["current_study"]["images"]
        if images:
            bad_img = images[-1]["tags"]
            bad_img["SeriesDescription"] = "Current w/ Unsupported SOP (Mismatching Modality)"
            bad_img["force_unsupported_dicom"] = True
            bad_img["SOPClassUID"] = "1.2.840.10008.5.1.4.1.1.104.1"
        return config

if __name__ == "__main__":
    scenario = ScenarioCuUnsupportedSOPWithMismatchingModality()
    config = scenario.build_scenario_config()
    print(json.dumps(config, indent=2))
