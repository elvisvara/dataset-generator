# /Users/elvis/Desktop/SUH/presets/scenario_uncorrupted_pixel.py

from presets.scenario_base import ScenarioBase

class ScenarioUncorruptedPixel(ScenarioBase):
    SCENARIO_NAME = "uncorrupted_pixel"

    def build_scenario_config(self):
        config = super().build_scenario_config()

        # Create a non-cancerous prior with 4 images
        prior = self.create_prior_config(is_cancerous=False)
        if prior["images"]:
            # We'll only label the last image, but we do NOT set force_corrupt_pixel
            prior["images"][-1]["tags"]["SeriesDescription"] = "Uncorrupted Pixel Data"

        config["internal_priors"].append(prior)
        return config
