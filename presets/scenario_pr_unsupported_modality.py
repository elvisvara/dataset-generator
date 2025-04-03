# /Users/elvis/Desktop/SUH/presets/scenario_unsupported_modality.py
"""
ScenarioUnsupportedModality:
- Generate 1 current study (normal MG),
- 1 prior with 4 images. The last image has a contradictory Modality = OT
  (but still uses the standard MG SOP Class).
"""

from presets.scenario_base import ScenarioBase

class ScenarioUnsupportedModality(ScenarioBase):
    SCENARIO_NAME = "pr_unsupported_modality"

    def build_scenario_config(self):
        # Normal current study
        config = super().build_scenario_config()

        # Create one internal prior with 4 images
        faulty_prior = self.create_prior_config(is_cancerous=False)

        if faulty_prior["images"]:
            #  keep standard MG SOPClassUID, but set Modality=OT
            bad_img_tags = faulty_prior["images"][-1]["tags"]
            # The typical MG SOP Class for reference is 1.2.840.10008.5.1.4.1.1.1.2
            bad_img_tags["SOPClassUID"] = "1.2.840.10008.5.1.4.1.1.1.2"  # still an MG SOP
            bad_img_tags["Modality"] = "OT"  # 'Occupational Therapy'? definitely not MG
            bad_img_tags["SeriesDescription"] = "Unsupported Modality=OT"

        config["internal_priors"].append(faulty_prior)
        return config
