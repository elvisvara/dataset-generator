from presets.scenario_base import ScenarioBase

class ScenarioNullByteTag(ScenarioBase):
    SCENARIO_NAME = "pr_null_byte_tag"

    def build_scenario_config(self):
        config = super().build_scenario_config()

        prior = self.create_prior_config(is_cancerous=False)
        if prior["images"]:
            bad_img_tags = prior["images"][-1]["tags"]
            # Insert an actual null char in the string
            bad_img_tags["SeriesDescription"] = "HasNullByte\0Here"

        config["internal_priors"].append(prior)
        return config
