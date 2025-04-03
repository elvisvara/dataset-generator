from presets.scenario_base import ScenarioBase

class ScenarioCorruptedPixel(ScenarioBase):
    SCENARIO_NAME = "pr_corrupted_pixel"

    def build_scenario_config(self):
        config = super().build_scenario_config()

        prior = self.create_prior_config(is_cancerous=False)
        if prior["images"]:
            prior["images"][-1]["tags"]["SeriesDescription"] = "Corrupted Pixel Data"
            prior["images"][-1]["tags"]["force_corrupt_pixel"] = True

        config["internal_priors"].append(prior)
        return config
