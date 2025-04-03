from presets.scenario_base import ScenarioBase

class ScenarioMissingDicom(ScenarioBase):
    SCENARIO_NAME = "pr_missing_dicom"

    def build_scenario_config(self):
        config = super().build_scenario_config()

        prior = self.create_prior_config(is_cancerous=False)
        if prior["images"]:
            prior["images"][-1]["tags"]["SeriesDescription"] = "Missing DICOM (Not Written)"
        config["internal_priors"].append(prior)
        return config
