from presets.scenario_base import ScenarioBase

class ScenarioMissingRequiredTag(ScenarioBase):
    SCENARIO_NAME = "pr_missing_required_tag"

    def build_scenario_config(self):
        config = super().build_scenario_config()

        prior = self.create_prior_config(is_cancerous=False)
        if prior["images"]:
            bad_img = prior["images"][-1]["tags"]
            # Remove rows/columns 
            if "Rows" in bad_img:
                del bad_img["Rows"]
            if "Columns" in bad_img:
                del bad_img["Columns"]
            bad_img["SeriesDescription"] = "Missing Rows/Columns"
        config["internal_priors"].append(prior)
        return config
