from presets.scenario_base import ScenarioBase

class ScenarioOverlyLargeNumeric(ScenarioBase):
    SCENARIO_NAME = "pr_overly_large_numeric"

    def build_scenario_config(self):
        config = super().build_scenario_config()

        prior = self.create_prior_config(is_cancerous=False)
        if prior["images"]:
            bad_img = prior["images"][-1]["tags"]
            bad_img["WindowCenter"] = "9999999999999999999999999999"  # extremely large
            bad_img["WindowWidth"] = "8888888888888888888888888888"
            bad_img["SeriesDescription"] = "Huge Numeric Values"
        config["internal_priors"].append(prior)
        return config
