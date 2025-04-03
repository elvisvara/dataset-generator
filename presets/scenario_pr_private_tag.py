from presets.scenario_base import ScenarioBase

class ScenarioPrivateTag(ScenarioBase):
    SCENARIO_NAME = "pr_private_tag"

    def build_scenario_config(self):
        config = super().build_scenario_config()

        prior = self.create_prior_config(is_cancerous=False)
        if prior["images"]:
            bad_img = prior["images"][-1]["tags"]
            bad_img["Private_9999_0010"] = "SomePrivateValue"
            bad_img["SeriesDescription"] = "Has Private Tag"
        config["internal_priors"].append(prior)
        return config
