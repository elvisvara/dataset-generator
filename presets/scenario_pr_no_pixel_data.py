from presets.scenario_base import ScenarioBase

class ScenarioNoPixelData(ScenarioBase):
    SCENARIO_NAME = "pr_no_pixel_data"

    def build_scenario_config(self):
        config = super().build_scenario_config()

        prior = self.create_prior_config(is_cancerous=False)
        if prior["images"]:
            prior["images"][-1]["tags"]["no_pixel_data"] = True
            prior["images"][-1]["tags"]["SeriesDescription"] = "No PixelData"
        config["internal_priors"].append(prior)
        return config
