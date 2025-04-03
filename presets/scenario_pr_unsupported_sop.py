# /Users/elvis/Desktop/SUH/presets/scenario_unsupported_sop.py
"""
TODO: Review this and understand what we support and what we dont! PR is def supported
ScenarioUnsupportedSOP:
- Generate 1 current study (normal MG),
- 1 prior with 4 images. The last image is an "unsupported SOP" (PR).
"""

from presets.scenario_base import ScenarioBase

class ScenarioUnsupportedSOP(ScenarioBase):
    SCENARIO_NAME = "pr_unsupported_sop"

    def build_scenario_config(self):
        config = super().build_scenario_config()

        # Create one internal prior, also normal except for the last image
        faulty_prior = self.create_prior_config(is_cancerous=False)

        if faulty_prior["images"]:
            # The last image has a PR SOP Class
            bad_img_tags = faulty_prior["images"][-1]["tags"]
            bad_img_tags["SOPClassUID"] = "1.2.840.10008.5.1.4.1.1.11.1"  # PR
            bad_img_tags["Modality"] = "PR"  # match the SOP
            bad_img_tags["SeriesDescription"] = "Unsupported SOP (PR)"

        # Attach this faulty prior to the scenario
        config["internal_priors"].append(faulty_prior)
        return config
