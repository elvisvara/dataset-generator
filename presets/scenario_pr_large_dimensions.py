from presets.scenario_base import ScenarioBase

class ScenarioLargeDimensions(ScenarioBase):
    SCENARIO_NAME = "pr_large_dimensions"

    def build_scenario_config(self):
        config = super().build_scenario_config()

        prior = self.create_prior_config(is_cancerous=False)
        if prior["images"]:
            # We'll pick the last image to have huge geometry
            big_img = prior["images"][-1]["tags"]
            big_img["Rows"] = 8000
            big_img["Columns"] = 8000
            big_img["force_large_dims"] = True  # key for final override
            big_img["SeriesDescription"] = "Huge Pixel Array (override geometry)"
        config["internal_priors"].append(prior)
        return config
